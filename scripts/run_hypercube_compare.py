#!/usr/bin/env python3
"""
Simula walks em hipercubo para dimensões 1,2,3 comparando moedas:
- classical (determinística)
- hadamard
- grover
- adaptive generic (probabilidade adaptativa simples)

Salva plots em results/hypercube_compare/
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from math import log2


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def classical_coin(state):
    # coin flips: stay/shift deterministic (simple random but classical)
    return np.array([0.5, 0.5])


def hadamard_coin():
    return np.array([[1, 1], [1, -1]]) / np.sqrt(2)


def grover_coin(d):
    # Grover coin for degree d: G = 2/ d * J - I
    J = np.ones((d, d))
    return 2.0 / d * J - np.eye(d)


def adaptive_coin(prev_probs, t):
    # uma moeda genérica adaptativa: ajusta probabilidade com base na entropia
    # prev_probs: vector of probabilities for each direction
    # aqui usamos uma regra simples: aumenta probabilidade do movimento menos usado
    p = prev_probs.copy()
    idx = np.argmin(p)
    p[idx] += 0.05 / (1 + t/10)
    p = np.clip(p, 0.01, 0.99)
    p = p / p.sum()
    return p


def simulate_line_walk(steps, coin_type='hadamard'):
    # Simula walk 1D como distribuição clássica/quantum-approx
    pos = 0
    positions = [pos]
    probs = []
    # maintain a simple direction prob for adaptive coin
    dir_probs = np.array([0.5, 0.5])
    for t in range(steps):
        if coin_type == 'classical':
            p = classical_coin(None)
            move = np.random.choice([-1, 1], p=p)
        elif coin_type == 'hadamard':
            # approximate hadamard by equal prob
            move = np.random.choice([-1, 1], p=[0.5, 0.5])
        elif coin_type == 'grover':
            move = np.random.choice([-1, 1], p=[0.5, 0.5])
        elif coin_type == 'adaptive':
            p = adaptive_coin(dir_probs, t)
            move = np.random.choice([-1, 1], p=p)
            # update empirical probs
            dir_probs = 0.9 * dir_probs + 0.1 * np.array([1 if move==-1 else 0, 1 if move==1 else 0])
        pos += move
        positions.append(pos)
        probs.append(pos)
    return np.array(positions)


def simulate_hypercube(dim, steps, coin='hadamard'):
    # Simples simulação onde o estado é um vertex do hypercube {0,1}^dim
    # Em cada passo, escolhemos uma coordenada aleatória e possivelmente flip
    state = np.zeros(dim, dtype=int)
    dist = []
    dir_probs = np.ones(dim) / dim
    for t in range(steps):
        coord = np.random.randint(0, dim)
        if coin == 'classical':
            # classical: flip with prob 0.5
            if np.random.rand() < 0.5:
                state[coord] ^= 1
        elif coin == 'hadamard':
            if np.random.rand() < 0.5:
                state[coord] ^= 1
        elif coin == 'grover':
            # grover-like bias to flip
            if np.random.rand() < 0.6:
                state[coord] ^= 1
        elif coin == 'adaptive':
            # choose coord weighted by dir_probs
            coord = np.random.choice(dim, p=dir_probs)
            if np.random.rand() < 0.5:
                state[coord] ^= 1
            # update dir_probs to favor less flipped coords
            flips = state.copy()
            dir_probs = 1.0 / (1 + flips)
            dir_probs = dir_probs / dir_probs.sum()
        # distância de Hamming ao ponto zero
        dist.append(state.sum())
    return np.array(dist)


def run_compare(steps=500, trials=20):
    outdir = os.path.join('results', 'hypercube_compare')
    ensure_dir(outdir)
    dims = [1, 2, 3]
    coins = ['classical', 'hadamard', 'grover', 'adaptive']

    # coletar distâncias médias
    results = {dim: {c: [] for c in coins} for dim in dims}
    for dim in dims:
        for c in coins:
            for tr in range(trials):
                if dim == 1:
                    pos = simulate_line_walk(steps, coin_type=c)
                    # usar variação do deslocamento absoluto
                    results[dim][c].append(np.abs(pos))
                else:
                    dist = simulate_hypercube(dim, steps, coin=c)
                    results[dim][c].append(dist)

    # Média e erro padrão
    for dim in dims:
        plt.figure(figsize=(8, 5))
        t = np.arange(steps + (0 if dim>1 else 1))
        for c in coins:
            arr = np.array(results[dim][c])
            if dim == 1:
                # arr shape (trials, steps+1)
                mean = arr.mean(axis=0)
                std = arr.std(axis=0)
                x = np.arange(mean.size)
            else:
                mean = arr.mean(axis=0)
                std = arr.std(axis=0)
                x = np.arange(mean.size)
            plt.plot(x, mean, label=f'{c}')
            plt.fill_between(x, mean - std, mean + std, alpha=0.2)
        plt.xlabel('steps')
        plt.ylabel('mean distance / |pos|')
        plt.title(f'Hypercube dim={dim} comparison')
        plt.legend()
        fname = os.path.join(outdir, f'hypercube_dim{dim}.png')
        plt.tight_layout()
        plt.savefig(fname)
        plt.close()

    # also list files saved
    saved = os.listdir(outdir)
    print('Saved files:', saved)


if __name__ == '__main__':
    run_compare(steps=200, trials=40)
