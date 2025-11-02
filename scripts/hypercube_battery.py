#!/usr/bin/env python3
"""
Battery of hypercube simulations and diagnostics.

Blocks implemented:
1) Baseline ballistic (coined walk, Grover coin as balanced coin)
2) Hitting (antipode) statistics
3) SKW-like search (Grover coin everywhere, -I at marked)
4) Noise sweep (coin dephasing / position depolarizing via stochastic unraveling)
5) Coin comparison (Grover, Fourier, Hadamard-like)
6) Symmetry reduction (classical reduced shells comparison)
7) Phase defects and localization

Produces plots in results/hypercube_battery/ (one subfolder per block)

Notes/assumptions:
- Uses coined, flip-flop shift: coin dim = n, coin acts on coin index, shift flips the selected bit.
- Noise implemented via stochastic resets (ensemble average) to approximate channels.
- For 'hadamard' coin we use Walsh-Hadamard when n is power of 2, otherwise fallback to Grover.

This script is a diagnostic suite, not an optimized research code. It aims to expose clear signals
that indicate correctness (ballistic spreading, hitting times, noise-induced transition, etc.).
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from math import comb
import time


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def bitcount(x):
    return bin(x).count('1')


def create_coin(name, n):
    # returns an (n,n) unitary coin
    if name == 'grover':
        s = np.ones((n, 1)) / np.sqrt(n)
        G = 2 * (s @ s.T) - np.eye(n)
        return G.astype(complex)
    if name == 'fourier':
        omega = np.exp(2j * np.pi / n)
        j = np.arange(n)
        k = j.reshape((-1, 1))
        F = omega ** (j * k) / np.sqrt(n)
        return F.astype(complex)
    if name == 'hadamard':
        # Walsh-Hadamard if n is power of 2
        p = 1
        while 2 ** p < n:
            p += 1
        if 2 ** p == n:
            H = np.array([[1]], dtype=float)
            for _ in range(p):
                H = np.kron(H, np.array([[1, 1], [1, -1]]))
            H = H / np.sqrt(n)
            return H.astype(complex)
        else:
            # fallback to Grover (uniform mixing)
            s = np.ones((n, 1)) / np.sqrt(n)
            G = 2 * (s @ s.T) - np.eye(n)
            return G.astype(complex)
    raise ValueError('unknown coin')


def init_state(n):
    N = 1 << n
    # initial position |0...0> and coin uniform |s_c>
    state = np.zeros((N, n), dtype=complex)
    state[0, :] = 1.0 / np.sqrt(n)
    return state


def normalize_state(state):
    norm = np.sqrt(np.sum(np.abs(state) ** 2))
    if norm == 0:
        return state
    return state / norm


def step_coined(state, coin):
    # state: shape (N, n)
    N, n = state.shape
    # apply coin on coin index for each position
    # new_state_pos_d = sum_{d'} coin[d, d'] * state_pos_d'
    state = state @ coin.T
    # shift: flip bit d of position index
    new = np.zeros_like(state)
    for d in range(n):
        mask = 1 << d
        # positions array 0..N-1
        pos = np.arange(N)
        dest = pos ^ mask
        new[dest, d] += state[pos, d]
    return new


def measure_position_probs(state):
    # sum over coin
    p = np.sum(np.abs(state) ** 2, axis=1)
    return p


def classical_step(p):
    # p shape (N,)
    N = p.size
    n = int(np.log2(N))
    pnext = np.zeros_like(p)
    for d in range(n):
        mask = 1 << d
        pos = np.arange(N)
        dest = pos ^ mask
        pnext[dest] += p[pos] / n
    return pnext


def shell_distribution(p, n):
    N = p.size
    Pk = np.zeros(n + 1)
    for x in range(N):
        k = bitcount(x)
        Pk[k] += p[x]
    return Pk


def variance_from_Pk(Pk):
    ks = np.arange(Pk.size)
    mean = np.sum(ks * Pk)
    var = np.sum(((ks - mean) ** 2) * Pk)
    return var, mean


def IPR_from_p(p):
    return np.sum(p ** 2)


def run_baseline(n, tmax, coin_name='grover'):
    coin = create_coin(coin_name, n)
    state = init_state(n)
    N = 1 << n
    Pk_t = np.zeros((n + 1, tmax + 1))
    var_t = np.zeros(tmax + 1)
    p_target_t = np.zeros(tmax + 1)
    # initial
    p = measure_position_probs(state)
    Pk_t[:, 0] = shell_distribution(p, n)
    var_t[0], _ = variance_from_Pk(Pk_t[:, 0])
    p_target_t[0] = p[-1]
    for t in range(1, tmax + 1):
        state = step_coined(state, coin)
        p = measure_position_probs(state)
        Pk_t[:, t] = shell_distribution(p, n)
        var_t[t], _ = variance_from_Pk(Pk_t[:, t])
        p_target_t[t] = p[-1]
    return Pk_t, var_t, p_target_t


def run_classical(n, tmax):
    N = 1 << n
    p = np.zeros(N)
    p[0] = 1.0
    Pk_t = np.zeros((n + 1, tmax + 1))
    var_t = np.zeros(tmax + 1)
    p_target_t = np.zeros(tmax + 1)
    Pk_t[:, 0] = shell_distribution(p, n)
    var_t[0], _ = variance_from_Pk(Pk_t[:, 0])
    p_target_t[0] = p[-1]
    for t in range(1, tmax + 1):
        p = classical_step(p)
        Pk_t[:, t] = shell_distribution(p, n)
        var_t[t], _ = variance_from_Pk(Pk_t[:, t])
        p_target_t[t] = p[-1]
    return Pk_t, var_t, p_target_t


def run_search_skw(n, tmax):
    # SKW-style: Grover coin everywhere, but at marked vertex apply -I on coin
    coin = create_coin('grover', n)
    state = init_state(n)
    N = 1 << n
    Pk_t = np.zeros((n + 1, tmax + 1))
    p_target_t = np.zeros(tmax + 1)
    # precompute masked coin application: we will apply coin to all positions and then for marked vertex multiply coin state by -1
    marked = N - 1
    Pk_t[:, 0] = shell_distribution(measure_position_probs(state), n)
    p_target_t[0] = measure_position_probs(state)[marked]
    for t in range(1, tmax + 1):
        state = step_coined(state, coin)
        # apply -I at marked: multiply coin amplitudes at marked by -1
        state[marked, :] *= -1
        p = measure_position_probs(state)
        Pk_t[:, t] = shell_distribution(p, n)
        p_target_t[t] = p[marked]
    return Pk_t, p_target_t


def stochastic_noise_step(state, coin, p_dephase=0.0, p_depol=0.0):
    # apply coin and shift; then with probability p_depol per position depolarize coin (random coin vector)
    state = step_coined(state, coin)
    N, n = state.shape
    for pos in range(N):
        if p_depol > 0 and np.random.rand() < p_depol:
            mass = np.sum(np.abs(state[pos, :]) ** 2)
            if mass > 0:
                # random unit vector
                v = np.random.normal(size=n) + 1j * np.random.normal(size=n)
                v = v / np.linalg.norm(v)
                state[pos, :] = np.sqrt(mass) * v
        if p_dephase > 0:
            # apply random phases to coin components with probability p_dephase
            if np.random.rand() < p_dephase:
                phases = np.exp(1j * 2 * np.pi * np.random.rand(n))
                state[pos, :] *= phases
    return state


def run_noise_sweep(n, tmax, p_list, trials=20):
    coin = create_coin('grover', n)
    results = {}
    for p in p_list:
        Pk_acc = np.zeros((n + 1, tmax + 1))
        var_acc = np.zeros(tmax + 1)
        for tr in range(trials):
            state = init_state(n)
            for t in range(1, tmax + 1):
                state = stochastic_noise_step(state, coin, p_dephase=p, p_depol=0.0)
                ppos = measure_position_probs(state)
                Pk_acc[:, t] += shell_distribution(ppos, n)
                var_acc[t] += variance_from_Pk(shell_distribution(ppos, n))[0]
        Pk_acc /= trials
        var_acc /= trials
        results[p] = (Pk_acc, var_acc)
    return results


def compare_coins(n, tmax, coin_names=['grover', 'fourier', 'hadamard']):
    results = {}
    for name in coin_names:
        try:
            Pk_t, var_t, p_target = run_baseline(n, tmax, coin_name=name if name!='hadamard' else 'hadamard')
            results[name] = (Pk_t, var_t, p_target)
        except Exception as e:
            print('coin', name, 'failed:', e)
    return results


def symmetry_reduced_classical(n, tmax):
    # classical reduced Markov chain on shells 0..n
    # from shell k, probability to go to k+1 is (n-k)/n, to k-1 is k/n
    Pk = np.zeros(n + 1)
    Pk[0] = 1.0
    Pk_t = np.zeros((n + 1, tmax + 1))
    Pk_t[:, 0] = Pk.copy()
    for t in range(1, tmax + 1):
        new = np.zeros_like(Pk)
        for k in range(n + 1):
            if Pk[k] == 0:
                continue
            # each step flips a random bit; from shell k, # of bits 1 is k
            # choosing a 0 -> increases k: prob (n-k)/n
            if k < n:
                new[k + 1] += Pk[k] * (n - k) / n
            if k > 0:
                new[k - 1] += Pk[k] * k / n
        Pk = new
        Pk_t[:, t] = Pk.copy()
    return Pk_t


def apply_phase_defect(state, defect_positions, phi):
    # multiply position amplitude by e^{i phi} at given positions (all coin components)
    for pos in defect_positions:
        state[pos, :] *= np.exp(1j * phi)
    return state


def run_defect_experiment(n, tmax, phi=0.1, defect_pos=None):
    coin = create_coin('grover', n)
    state = init_state(n)
    N = 1 << n
    if defect_pos is None:
        defect_pos = [N // 2]  # arbitrary
    Pk_t = np.zeros((n + 1, tmax + 1))
    ipr_t = np.zeros(tmax + 1)
    for t in range(0, tmax + 1):
        ppos = measure_position_probs(state)
        Pk_t[:, t] = shell_distribution(ppos, n)
        ipr_t[t] = IPR_from_p(ppos)
        if t < tmax:
            state = step_coined(state, coin)
            # introduce phase on edges entering defect: approximate via applying phase on defect position coin amplitudes
            state = apply_phase_defect(state, defect_pos, phi)
    return Pk_t, ipr_t


def save_heatmap_Pk(Pk_t, outpath, title='Pk(t)'):
    ensure_dir(os.path.dirname(outpath))
    plt.figure(figsize=(6, 4))
    plt.imshow(Pk_t, aspect='auto', origin='lower', cmap='viridis')
    plt.colorbar(label='P_k')
    plt.xlabel('t')
    plt.ylabel('k')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def save_p_target_curve(p_target, outpath, title='p_target(t)'):
    plt.figure(figsize=(6, 3))
    t = np.arange(p_target.size)
    plt.plot(t, p_target, marker='o')
    tstar = np.argmax(p_target)
    plt.axvline(tstar, color='red', linestyle='--')
    plt.scatter([tstar], [p_target[tstar]], color='red')
    plt.xlabel('t')
    plt.ylabel('p_target')
    plt.title(f"{title} (peak t*={tstar}, pmax={p_target[tstar]:.3f})")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def save_var_loglog(var_t, outpath, title='Var(t)'):
    t = np.arange(var_t.size)
    mask = t > 0
    tt = t[mask]
    vv = var_t[mask]
    # avoid zeros
    vv = np.maximum(vv, 1e-12)
    coeffs = np.polyfit(np.log10(tt), np.log10(vv), 1)
    alpha = coeffs[0]
    plt.figure(figsize=(5, 4))
    plt.loglog(tt, vv, label='Var(t)')
    plt.loglog(tt, 10 ** (coeffs[1]) * tt ** alpha, '--', label=f'fit slope={alpha:.2f}')
    plt.xlabel('t')
    plt.ylabel('Var(t)')
    plt.title(f"{title} (alpha={alpha:.2f})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    return alpha


def save_comparison_bars(values_dict, outpath, ylabel='value', title='Comparison'):
    names = list(values_dict.keys())
    vals = [values_dict[k] for k in names]
    plt.figure(figsize=(6, 4))
    plt.bar(names, vals)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def main():
    outdir = os.path.join('results', 'hypercube_battery')
    ensure_dir(outdir)
    ns = [4, 6, 8, 10, 12]
    p_list = [0.0, 0.01, 0.02, 0.05, 0.1, 0.2]
    coin_names = ['grover', 'fourier', 'hadamard']

    summary = {}
    for n in ns:
        print('\n=== n=', n, '===')
        tmax = 4 * n
        sub = os.path.join(outdir, f'n_{n}')
        ensure_dir(sub)

        # Baseline
        t0 = time.time()
        Pk_t, var_t, p_target = run_baseline(n, tmax, coin_name='grover')
        save_heatmap_Pk(Pk_t, os.path.join(sub, 'baseline_Pk_heatmap.png'), title=f'Baseline Pk n={n}')
        alpha = save_var_loglog(var_t, os.path.join(sub, 'baseline_var.png'), title=f'Baseline Var n={n}')
        save_p_target_curve(p_target, os.path.join(sub, 'baseline_p_target.png'), title=f'Baseline p_target n={n}')
        print('baseline done in', time.time() - t0)

        # Hitting statistics (antipode)
        t0 = time.time()
        ptarget = p_target
        tstar = int(np.argmax(ptarget))
        pmax = float(np.max(ptarget))
        summary[f'n{n}_hitting'] = {'tstar': tstar, 'pmax': pmax}
        print('hitting', tstar, pmax)

        # SKW-like search
        t0 = time.time()
        Pk_skw, ptarget_skw = run_search_skw(n, tmax)
        save_heatmap_Pk(Pk_skw, os.path.join(sub, 'skw_Pk_heatmap.png'), title=f'SKW Pk n={n}')
        save_p_target_curve(ptarget_skw, os.path.join(sub, 'skw_p_target.png'), title=f'SKW p_target n={n}')
        print('skw done in', time.time() - t0)

        # Noise sweep (only coin dephasing modeled stochastically)
        t0 = time.time()
        results_noise = run_noise_sweep(n, tmax, p_list, trials=20)
        # save var exponent vs p
        alphas = {}
        for p in p_list:
            _, varp = results_noise[p]
            alpha_p = save_var_loglog(varp, os.path.join(sub, f'noise_var_p{p:.3f}.png'), title=f'Noise p={p} n={n}')
            alphas[p] = alpha_p
        save_comparison_bars(alphas, os.path.join(sub, 'noise_alpha_vs_p.png'), ylabel='alpha', title=f'alpha vs p n={n}')
        print('noise sweep done in', time.time() - t0)

        # Coin comparison
        t0 = time.time()
        coin_results = compare_coins(n, tmax, coin_names)
        # compute metrics: peak p_target
        peak_vals = {name: float(np.max(coin_results[name][2])) for name in coin_results}
        save_comparison_bars(peak_vals, os.path.join(sub, 'coins_peak_p_target.png'), ylabel='pmax', title=f'coins pmax n={n}')
        print('coins compare done in', time.time() - t0)

        # Symmetry reduction (classical)
        Pk_reduced = symmetry_reduced_classical(n, tmax)
        # classical full
        Pk_classical, var_classical, _ = run_classical(n, tmax)
        save_heatmap_Pk(Pk_classical, os.path.join(sub, 'classical_full_Pk.png'), title=f'Classical full Pk n={n}')
        save_heatmap_Pk(Pk_reduced, os.path.join(sub, 'classical_reduced_Pk.png'), title=f'Classical reduced Pk n={n}')
        # compare difference
        diff = np.abs(Pk_classical - Pk_reduced)
        plt.figure(figsize=(6, 3))
        plt.imshow(diff, aspect='auto', origin='lower', cmap='magma')
        plt.colorbar()
        plt.title('classical full - reduced |diff|')
        plt.tight_layout()
        plt.savefig(os.path.join(sub, 'classical_full_minus_reduced.png'), dpi=200)
        plt.close()

        # Defect experiment
        t0 = time.time()
        Pk_def, ipr_def = run_defect_experiment(n, tmax, phi=0.5)
        save_heatmap_Pk(Pk_def, os.path.join(sub, 'defect_Pk.png'), title=f'Defect Pk n={n}')
        plt.figure(figsize=(5, 3))
        plt.plot(ipr_def)
        plt.title('IPR over time')
        plt.xlabel('t')
        plt.ylabel('IPR')
        plt.tight_layout()
        plt.savefig(os.path.join(sub, 'defect_ipr.png'), dpi=200)
        plt.close()
        print('defect done in', time.time() - t0)

        # Save some summary numbers
        summary[f'n{n}_baseline_alpha'] = float(alpha)
        summary[f'n{n}_coins_peak'] = peak_vals

    # dump summary
    import json
    with open(os.path.join(outdir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    print('All done. Results in', outdir)


if __name__ == '__main__':
    main()
