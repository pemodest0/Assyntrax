from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

from core.state_space.dimensions import compute_state_metrics
from core.state_space.discretization import StateDiscretizer
from core.dynamics.transitions import estimate_transition_matrix
from core.dynamics.walkers import simulate_walks
from core.observables.price import map_state_to_price, reconstruct_prices_from_walks
from visualizacao.phase_space_animation import animate_phase_space


def main():
    parser = argparse.ArgumentParser(description='Phase-space demo runner (AAPL default).')
    parser.add_argument('--csv', type=str, default='dados/brutos/aapl.csv')
    parser.add_argument('--output', type=str, default='results/phase_space_demo')
    parser.add_argument('--bins', type=int, default=5)
    parser.add_argument('--walks', type=int, default=20)
    parser.add_argument('--steps', type=int, default=60)
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.csv, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = df.rename(columns={df.columns[0]: 'date'})
    dates = pd.to_datetime(df['date'])
    price_col = 'price' if 'price' in df.columns else df.columns[1]
    prices = df[price_col]
    # ensure prices are indexed by dates for downstream rolling/reindex operations
    prices.index = dates

    metrics = compute_state_metrics(dates, prices, window=21)
    metrics.to_csv(out / 'state_metrics.csv')

    disc = StateDiscretizer(bins=args.bins)
    states = disc.discretize_series(metrics)
    states.to_csv(out / 'states.csv')

    state_series = states['state_flat']
    n_states = int(state_series.max()) + 1
    P = estimate_transition_matrix(state_series, n_states=n_states, smooth=1.0)
    np.save(out / 'transition_matrix.npy', P)

    # identify chaotic states as those with high entropy_local
    entropy = metrics['entropy_local']
    threshold = entropy.quantile(0.9)
    chaos_states = list(states[entropy >= threshold]['state_flat'].unique())

    walks = simulate_walks(int(state_series.iloc[-1]), P, n_steps=args.steps, n_walks=args.walks, chaos_states=chaos_states)
    # build state_map -> drift using historical returns
    returns = prices.pct_change().fillna(0.0)
    state_map = map_state_to_price(state_series, returns)

    price_walks = reconstruct_prices_from_walks(walks, state_map, last_price=float(prices.iloc[-1]))
    # save one example trajectory
    for i, s in enumerate(price_walks[:5]):
        s.to_csv(out / f'price_walk_{i}.csv', index=False)

    # animation
    try:
        animate_phase_space(metrics, states, walks, out / 'phase_space.mp4')
    except Exception:
        pass

    print('Phase-space demo outputs in', out)


if __name__ == '__main__':
    main()
