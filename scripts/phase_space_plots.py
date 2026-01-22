import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

out = Path('results/phase_space_demo')
out_plots = out / 'plots'
out_plots.mkdir(parents=True, exist_ok=True)

metrics = pd.read_csv(out / 'state_metrics.csv', parse_dates=['date'], index_col='date')
states = pd.read_csv(out / 'states.csv', parse_dates=['date'], index_col='date')
P = np.load(out / 'transition_matrix.npy')

# 1) phase-space scatter: coherence x volatility colored by entropy
plt.figure(figsize=(6,6))
sc = plt.scatter(metrics['coherence'], metrics['volatility_norm'], c=metrics['entropy_local'], cmap='viridis', s=30)
plt.colorbar(sc, label='entropy_local')
plt.xlabel('coherence')
plt.ylabel('volatility_norm')
plt.title('Phase space: coherence vs volatility (color=entropy)')
plt.xlim(0,1)
plt.ylim(0,1)
plt.grid(alpha=0.2)
plt.tight_layout()
plt.savefig(out_plots / 'phase_space_scatter.png', dpi=150)
plt.close()

# 2) hypercube occupancy projection: parse state_tuple and aggregate counts for (coherence_bin, entropy_bin)
# state_tuple stored as string like '(0, 4, 4, 3)'
state_tuples = states['state_tuple'].apply(lambda s: tuple(int(x.strip()) for x in s.strip('()').split(',')))
state_df = pd.DataFrame(state_tuples.tolist(), index=states.index, columns=['coh_bin','vol_bin','ent_bin','pers_bin'])
# occupancy heatmap for coherence vs entropy bins
occ = state_df.groupby(['coh_bin','ent_bin']).size().unstack(fill_value=0)
plt.figure(figsize=(6,5))
plt.imshow(occ, origin='lower', cmap='magma', aspect='auto')
plt.colorbar(label='count')
plt.xlabel('entropy_bin')
plt.ylabel('coherence_bin')
plt.title('Hypercube occupancy (coherence_bin x entropy_bin)')
plt.xticks(ticks=np.arange(occ.shape[1]), labels=occ.columns.astype(str))
plt.yticks(ticks=np.arange(occ.shape[0]), labels=occ.index.astype(str))
plt.tight_layout()
plt.savefig(out_plots / 'hypercube_occupancy_coh_ent.png', dpi=150)
plt.close()

# 3) transition matrix heatmap (log-scaled for visibility)
plt.figure(figsize=(6,5))
m = P.copy()
# small epsilon
eps = 1e-9
plt.imshow(m + eps, cmap='coolwarm', aspect='auto')
plt.colorbar(label='P(s\'|s)')
plt.title('Transition matrix')
plt.xlabel("next state")
plt.ylabel('current state')
plt.tight_layout()
plt.savefig(out_plots / 'transition_matrix.png', dpi=150)
plt.close()

# 4) price + sample walks overlay
prices = pd.read_csv('dados/brutos/aapl.csv', parse_dates=['date']).sort_values('date').set_index('date')
price_col = 'price' if 'price' in prices.columns else prices.columns[0]
prices = prices[price_col].astype(float)
# plot tail
tail = prices.tail(80)
plt.figure(figsize=(8,4))
plt.plot(tail.index, tail.values, label='price (historical)')
# read up to 3 walks
for i in range(5):
    f = out / f'price_walk_{i}.csv'
    if f.exists():
        arr = pd.read_csv(f, header=None).iloc[:,0].values
        # align first element with last historical price index
        start_idx = tail.index[-1]
        # create incremental integer index after last date for visualization
        idxs = [start_idx + pd.Timedelta(days=j+1) for j in range(len(arr))]
        plt.plot(idxs, arr, linestyle='--', label=f'walk_{i}')
plt.legend()
plt.title('Price and sample phase-space walks (walks start after last date)')
plt.tight_layout()
plt.savefig(out_plots / 'price_with_walks.png', dpi=150)
plt.close()

print('Plots saved to', out_plots)
