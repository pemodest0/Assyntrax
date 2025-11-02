#!/usr/bin/env python3
"""Validar pipeline de discretização usando o oscilador de Duffing.
Gera sweep no parâmetro gamma para mover o sistema entre regimes periódicos e caóticos.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.integrate import odeint

from src.adaptive_discretizer import discretize_system
from src.regime_analysis import detect_regime, compute_alpha
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

OUT = Path('results/duffing_validation')
OUT.mkdir(parents=True, exist_ok=True)


def duffing(xy, t, delta, alpha, beta, gamma, omega):
    x, y = xy
    dx = y
    dy = -delta * y - alpha * x - beta * x**3 + gamma * np.cos(omega * t)
    return [dx, dy]


def simulate_duffing(gamma, T=800, dt=0.05, drop_transient=200):
    t = np.arange(0, T, dt)
    params = dict(delta=0.2, alpha=-1.0, beta=1.0, gamma=gamma, omega=1.2)
    x0 = [0.1, 0.0]
    sol = odeint(duffing, x0, t, args=(params['delta'], params['alpha'], params['beta'], params['gamma'], params['omega']))
    x = sol[:,0]
    if drop_transient > 0:
        drop_idx = int(drop_transient / dt)
        if drop_idx < len(x):
            x = x[drop_idx:]
            t = t[drop_idx:]
    return t, x


def ground_truth_regime(gamma):
    # heuristic: small gamma -> periodic, medium -> bifurcation/transitional, large -> chaotic
    if gamma < 0.2:
        return 'Periodic'
    if gamma < 0.9:
        return 'Transitional'
    return 'Chaotic'


def map_detected_to_gt(detected):
    # detected from detect_regime returns 'Difusivo'/'Caotico'/'Interferencia'
    if detected == 'Difusivo':
        return 'Periodic'
    if detected == 'Caotico':
        return 'Chaotic'
    return 'Transitional'


def compute_psd(x, dt=0.05):
    """Computa densidade espectral de potência."""
    from scipy.signal import welch
    freqs, psd = welch(x, fs=1/dt)
    return np.sum(psd * np.log2(psd + 1e-10))  # entropia espectral

def compute_permutation_entropy(x, order=3, delay=1):
    """Computa entropia de permutação."""
    from itertools import permutations
    n = len(x)
    perms = list(permutations(range(order)))
    counts = np.zeros(len(perms))
    
    for i in range(n - delay * (order - 1)):
        pattern = x[i:i + delay * order:delay]
        idx = np.argsort(pattern)
        pattern_idx = perms.index(tuple(idx))
        counts[pattern_idx] += 1
    
    probs = counts / counts.sum()
    return -np.sum(probs * np.log2(probs + 1e-10))

def run_sweep(gammas):
    results = []
    for gamma in gammas:
        print(f'Running gamma = {gamma:.3f}')
        t, x = simulate_duffing(gamma, T=800, dt=0.05, drop_transient=200)
        
        # Métricas do grafo
        graph, states, centers, stats = discretize_system(x, dim=3)
        entropy = stats['entropy_symbolic']
        t_grid = np.arange(len(states))
        alpha = compute_alpha(states, t_grid)
        n_clusters = stats['n_clusters']
        
        # Métricas dinâmicas
        lyap = estimate_lyapunov(x, emb_dim=6, delay=1)
        psd_entropy = compute_psd(x)
        perm_entropy = compute_permutation_entropy(x)
        
        # Classificação do regime
        gt = 'Chaotic' if lyap > 0.01 else 'NonChaotic'
        
        results.append({
            'gamma': gamma,
            'entropy': entropy,
            'alpha': alpha,
            'n_clusters': n_clusters,
            'psd_entropy': psd_entropy,
            'perm_entropy': perm_entropy,
            'gt_lyap': gt,
            'lyap': lyap
        })
    
    return pd.DataFrame(results)


def estimate_lyapunov(x, emb_dim=6, delay=1, theiler=10, max_t=100, dt=0.05):
    """Estimate largest Lyapunov exponent using Rosenstein's algorithm (simplified).
    Returns exponent in 1/time units.
    """
    x = np.asarray(x)
    N = len(x)
    # build embedding
    M = []
    L = N - delay * (emb_dim - 1)
    if L <= 50:
        return 0.0
    for i in range(emb_dim):
        M.append(x[i * delay:i * delay + L])
    M = np.vstack(M).T
    nbrs = NearestNeighbors(n_neighbors=2).fit(M)
    dists, idxs = nbrs.kneighbors(M)
    nn = idxs[:,1]
    # apply Theiler window
    theiler = max(theiler, int(1/dt))
    valid = np.where(np.abs(nn - np.arange(len(nn))) > theiler)[0]
    if len(valid) < 10:
        return 0.0
    valid = valid[:min(200, len(valid))]
    max_k = min(100, L//4)
    divergences = np.zeros(max_k)
    counts = np.zeros(max_k)
    for i in valid:
        j = nn[i]
        max_k_local = min(max_k, L - max(i, j) - 1)
        for k in range(max_k_local):
            dist = np.linalg.norm(M[i+k] - M[j+k])
            if dist > 0:
                divergences[k] += np.log(dist)
                counts[k] += 1
    mask = counts > 0
    if mask.sum() < 5:
        return 0.0
    avg = divergences[mask] / counts[mask]
    times = np.arange(len(avg)) * dt
    # linear fit on early times
    try:
        a, b = np.polyfit(times[:max(5, len(avg)//4)], avg[:max(5, len(avg)//4)], 1)
        return float(a)
    except Exception:
        return 0.0


def evaluate_clusters_vs_lyap(df):
    # cluster by (entropy, alpha) into 2 groups and compare to lyap-based GT
    X = df[['entropy', 'alpha']].fillna(0.0).values
    kmeans = KMeans(n_clusters=2, random_state=0).fit(X)
    labels = kmeans.labels_
    # map labels to gt_lyap by majority
    gt = (df['gt_lyap'] == 'Chaotic').astype(int).values
    ari = adjusted_rand_score(gt, labels)
    acc = (gt == labels).mean()
    print('Cluster vs Lyap: ARI=%.3f accuracy=%.3f' % (ari, acc))
    return ari, acc


def plot_results(df):
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(df['gamma'], df['entropy'], marker='o')
    ax.set_xlabel('gamma')
    ax.set_ylabel('Symbolic Entropy')
    ax.set_title('Duffing sweep: entropy vs gamma')
    fig.savefig(OUT / 'entropy_vs_gamma.png', dpi=200)
    print('Saved figure to', OUT / 'entropy_vs_gamma.png')


def summary_metrics(df):
    # Calcular acurácia da classificação de regimes
    print('\nMétricas de classificação:')
    print(f'Total de amostras: {len(df)}')
    print(f'Regimes caóticos: {(df["gt_lyap"] == "Chaotic").sum()}')
    print(f'Regimes não-caóticos: {(df["gt_lyap"] == "NonChaotic").sum()}')
    
    # Salvar resultados
    df.to_csv(OUT / 'duffing_summary.csv', index=False)
    print(f'\nResultados salvos em {OUT / "duffing_summary.csv"}')


def plot_phase_space(t, x, y, gamma, save_path):
    """Plota espaço de fases da trajetória."""
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, 'b.', alpha=0.5, markersize=1)
    plt.title(f'Espaço de Fases (γ={gamma:.2f})')
    plt.xlabel('x')
    plt.ylabel('dx/dt')
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()

def plot_time_series(t, x, gamma, save_path):
    """Plota série temporal."""
    plt.figure(figsize=(10, 4))
    plt.plot(t, x, 'b-', linewidth=1)
    plt.title(f'Série Temporal (γ={gamma:.2f})')
    plt.xlabel('t')
    plt.ylabel('x')
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()

def generate_multiple_runs(gamma, n_runs=5):
    """Gera múltiplas simulações com mesmo gamma mas diferentes condições iniciais."""
    results = []
    for i in range(n_runs):
        x0 = [0.1 * np.random.randn(), 0.1 * np.random.randn()]  # diferentes condições iniciais
        t = np.arange(0, 800, 0.05)
        params = dict(delta=0.2, alpha=-1.0, beta=1.0, gamma=gamma, omega=1.2)
        sol = odeint(duffing, x0, t, args=(params['delta'], params['alpha'], params['beta'], params['gamma'], params['omega']))
        x = sol[:,0][4000:]  # remover transientes
        results.append(x)
    return results

def main():
    # Mais pontos no sweep e múltiplas runs
    gammas = np.linspace(0.05, 1.5, 50)
    np.random.seed(42)  # reproducibilidade
    
    # Rodar sweep com múltiplas simulações por gamma
    all_results = []
    for gamma in gammas:
        print(f'Running gamma = {gamma:.3f}')
        runs = generate_multiple_runs(gamma, n_runs=5)
        for x in runs:
            # Computar features para cada simulação
            graph, states, centers, stats = discretize_system(x, dim=3)
            lyap = estimate_lyapunov(x, emb_dim=6, delay=1)
            
            result = {
                'gamma': gamma,
                'entropy': stats['entropy_symbolic'],
                'alpha': compute_alpha(states, np.arange(len(states))),
                'n_clusters': stats['n_clusters'],
                'gt_lyap': 'Chaotic' if lyap > 0.01 else 'NonChaotic',
                'lyap': lyap
            }
            all_results.append(result)
    
    df = pd.DataFrame(all_results)
    
    # Plots básicos
    plot_results(df)
    
    # Exemplo detalhado para 3 regimes
    for gamma in [0.1, 0.5, 1.2]:  # periódico, transição, caótico
        t, x = simulate_duffing(gamma, T=800, dt=0.05, drop_transient=200)
        y = np.gradient(x, t)  # dx/dt
        
        # Plotar espaço de fases
        plot_phase_space(t, x, y, gamma, OUT / f'phase_space_g{gamma:.1f}.png')
        
        # Plotar série temporal
        plot_time_series(t, x, gamma, OUT / f'time_series_g{gamma:.1f}.png')
    
    # Análise de regimes
    summary_metrics(df)
    
    # Plot da distribuição de regimes
    plt.figure(figsize=(8, 5))
    df['gt_lyap'].value_counts().plot(kind='bar')
    plt.title('Distribuição dos Regimes')
    plt.xlabel('Regime')
    plt.ylabel('Contagem')
    plt.tight_layout()
    plt.savefig(OUT / 'regime_distribution.png', dpi=200)
    plt.close()


if __name__ == '__main__':
    main()
