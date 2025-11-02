#!/usr/bin/env python3
"""
Simulação da Urna de Ehrenfest:
- Sistema com N bolas distribuídas entre duas urnas (A e B)
- A cada passo, uma bola é escolhida aleatoriamente e movida para a outra urna
- Demonstra reversibilidade microscópica e convergência para equilíbrio
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns

# Configuração do matplotlib para estilo científico
plt.style.use('seaborn-v0_8-darkgrid')
RESULTS = Path('results/ehrenfest')
RESULTS.mkdir(parents=True, exist_ok=True)

def simulate_ehrenfest(n_balls=100, n_steps=1000, n_trials=10):
    """
    Simula múltiplas realizações da urna de Ehrenfest.
    
    Args:
        n_balls: Número total de bolas
        n_steps: Número de passos de tempo
        n_trials: Número de realizações independentes
    
    Returns:
        trajectories: Array (n_trials, n_steps) com número de bolas na urna A
    """
    trajectories = np.zeros((n_trials, n_steps))
    
    for trial in range(n_trials):
        # Começa com todas as bolas na urna A
        balls_in_a = n_balls
        trajectory = [balls_in_a]
        
        for step in range(n_steps-1):
            # Probabilidade de escolher bola da urna A
            p_choose_a = balls_in_a / n_balls
            
            # Move uma bola aleatoriamente
            if np.random.random() < p_choose_a:
                balls_in_a -= 1  # Bola sai de A
            else:
                balls_in_a += 1  # Bola entra em A
            
            trajectory.append(balls_in_a)
        
        trajectories[trial] = trajectory
    
    return trajectories

def plot_trajectories(trajectories, n_balls):
    """Plota trajetórias e estatísticas."""
    n_trials, n_steps = trajectories.shape
    t = np.arange(n_steps)
    
    # Plot 1: Trajetórias individuais e média
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plotar algumas trajetórias individuais com transparência
    for traj in trajectories[:5]:
        ax.plot(t, traj, alpha=0.3, color='gray', linewidth=1)
    
    # Média e desvio padrão
    mean_traj = trajectories.mean(axis=0)
    std_traj = trajectories.std(axis=0)
    
    ax.plot(t, mean_traj, 'r-', label='Média', linewidth=2)
    ax.fill_between(t, mean_traj-std_traj, mean_traj+std_traj, 
                   color='r', alpha=0.2, label='±1 Desvio Padrão')
    
    # Valor de equilíbrio teórico
    eq_value = n_balls/2
    ax.axhline(y=eq_value, color='k', linestyle='--', 
               label='Equilíbrio Teórico')
    
    ax.set_xlabel('Passos de Tempo')
    ax.set_ylabel('Número de Bolas na Urna A')
    ax.set_title('Evolução do Sistema de Urnas de Ehrenfest')
    ax.legend()
    fig.savefig(RESULTS / 'trajectories.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Plot 2: Histograma da distribuição final
    fig, ax = plt.subplots(figsize=(8, 6))
    
    final_states = trajectories[:, -100:].flatten()  # últimos 100 passos
    sns.histplot(data=final_states, stat='density', ax=ax)
    
    # Distribuição binomial teórica
    x = np.arange(n_balls + 1)
    from scipy.stats import binom
    p = 0.5  # probabilidade no equilíbrio
    binom_dist = binom.pmf(x, n_balls, p)
    ax.plot(x, binom_dist, 'r-', label='Distribuição Teórica')
    
    ax.set_xlabel('Número de Bolas na Urna A')
    ax.set_ylabel('Densidade de Probabilidade')
    ax.set_title('Distribuição de Equilíbrio')
    ax.legend()
    fig.savefig(RESULTS / 'equilibrium_dist.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Plot 3: Evolução da entropia
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Calcular entropia para cada passo de tempo
    def entropy(p):
        """Entropia de Boltzmann."""
        return -p * np.log(p) - (1-p) * np.log(1-p)
    
    p_t = trajectories.mean(axis=0) / n_balls
    S_t = entropy(p_t)
    
    ax.plot(t, S_t, 'b-', label='Entropia do Sistema')
    ax.set_xlabel('Passos de Tempo')
    ax.set_ylabel('Entropia (S/k_B)')
    ax.set_title('Evolução da Entropia')
    ax.legend()
    fig.savefig(RESULTS / 'entropy.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

def main():
    # Parâmetros da simulação
    N_BALLS = 100
    N_STEPS = 1000
    N_TRIALS = 50
    
    print(f"Simulando sistema com {N_BALLS} bolas por {N_STEPS} passos...")
    trajectories = simulate_ehrenfest(N_BALLS, N_STEPS, N_TRIALS)
    
    print("Gerando plots...")
    plot_trajectories(trajectories, N_BALLS)
    print(f"Plots salvos em {RESULTS}")

if __name__ == '__main__':
    main()