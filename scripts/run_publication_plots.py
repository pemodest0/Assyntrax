#!/usr/bin/env python3
"""
Gera figuras estilo publicação comparando "classical" vs "quantum-like" em uma grade 2D.
Cada figura contém:
 - Um plot 3D com barras de probabilidade
 - Um heatmap reduzido no canto
 - Uma vista isométrica com um caminho simulado (linha)

Salva em results/publication_plots/
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def simulate_2d_distribution(size=21, peak=(10,10), spread=3, mode='classical'):
    x = np.arange(size)
    y = np.arange(size)
    X, Y = np.meshgrid(x, y)
    dx = X - peak[0]
    dy = Y - peak[1]
    r2 = dx**2 + dy**2
    if mode == 'classical':
        Z = np.exp(-r2 / (2 * spread**2))
    else:
        # quantum-like: create interference pattern with rings
        Z = np.exp(-r2 / (2 * spread**2)) * (0.5 + 0.5 * np.cos(0.5 * np.sqrt(r2)))
        Z = np.abs(Z)
    Z = Z / Z.sum()
    return X, Y, Z


def sample_path_on_grid(size=21, length=30, mode='classical'):
    # Simula um caminho que parte do centro
    center = size // 2
    x, y = center, center
    path = [(x, y)]
    for t in range(length):
        if mode == 'classical':
            dx, dy = np.random.choice([-1, 0, 1]), np.random.choice([-1, 0, 1])
        else:
            # quantum-like tends to move outward more
            choices = [(-1,0),(1,0),(0,-1),(0,1),(1,1),(-1,-1),(1,-1),(-1,1),(0,0)]
            probs = np.array([1,1,1,1,0.6,0.6,0.6,0.6,0.2], dtype=float)
            probs = probs / probs.sum()
            dx, dy = choices[np.random.choice(len(choices), p=probs)]
        x = np.clip(x + dx, 0, size-1)
        y = np.clip(y + dy, 0, size-1)
        path.append((x, y))
    return np.array(path)


def plot_publication_figure(size=21, mode='classical', outpath='out.png'):
    X, Y, Z = simulate_2d_distribution(size=size, mode=mode)
    path = sample_path_on_grid(size=size, length=40, mode=mode)

    fig = plt.figure(figsize=(10, 7))

    # 3D bar plot (left/top)
    ax1 = fig.add_axes([0.05, 0.35, 0.55, 0.6], projection='3d')
    xs = X.flatten()
    ys = Y.flatten()
    zs = np.zeros_like(xs)
    dx = dy = 0.6
    dz = Z.flatten() * 50  # escala para visual
    ax1.bar3d(xs, ys, zs, dx, dy, dz, shade=True)
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.set_zlabel('Probability')
    ax1.view_init(elev=30, azim=45)

    # heatmap inset (top-right)
    ax2 = fig.add_axes([0.64, 0.65, 0.28, 0.28])
    im = ax2.imshow(Z, cmap='viridis', origin='lower')
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title('Heatmap')

    # perspective path plot (bottom)
    ax3 = fig.add_axes([0.05, 0.05, 0.87, 0.25])
    # render grid as circles
    center = size // 2
    for i in range(size):
        for j in range(size):
            c = 'lightblue' if (i+j)%2==0 else 'white'
            ax3.scatter(i, j, s=20, color='lightgray', alpha=0.6)
    # plot path
    ax3.plot(path[:,0], path[:,1], color='red', linewidth=2)
    ax3.scatter([path[0,0]],[path[0,1]], color='yellow', s=80, zorder=5)
    ax3.set_xlim(-1, size)
    ax3.set_ylim(-1, size)
    ax3.set_aspect('equal')
    ax3.set_xticks([])
    ax3.set_yticks([])

    plt.suptitle('Classical Walk' if mode=='classical' else 'Quantum-like Walk', fontsize=16)
    plt.savefig(outpath, dpi=200)
    plt.close()


def run_all():
    outdir = os.path.join('results', 'publication_plots')
    ensure_dir(outdir)
    modes = ['classical', 'quantum']
    for m in modes:
        out = os.path.join(outdir, f'publication_{m}.png')
        plot_publication_figure(size=31, mode=('classical' if m=='classical' else 'quantum-like'), outpath=out)
    print('Saved publication plots in', outdir)


if __name__ == '__main__':
    run_all()
