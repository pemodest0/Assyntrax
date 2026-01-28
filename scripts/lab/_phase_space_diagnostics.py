import pandas as pd
import numpy as np
import sys

try:
    metrics = pd.read_csv('results/phase_space_demo/state_metrics.csv', parse_dates=['date'], index_col='date')
    prices = pd.read_csv('dados/brutos/aapl.csv', parse_dates=['date']).sort_values('date').set_index('date')
    price_col = 'price' if 'price' in prices.columns else prices.columns[0]
    prices = prices[price_col].astype(float)

    fwd1 = prices.pct_change().shift(-1)
    returns = prices.pct_change()
    fwd5_vol = returns.shift(-1).rolling(5).std() * np.sqrt(252.0)

    df = metrics.join(fwd1.rename('fwd1'), how='left')
    df = df.join(fwd5_vol.rename('fwd5_vol'), how='left')
    df = df.dropna(subset=['fwd1'])
    df['abs_fwd1'] = df['fwd1'].abs()

    q75 = df['coherence'].quantile(0.75)
    q25 = df['coherence'].quantile(0.25)
    mean_top = df[df['coherence']>=q75]['abs_fwd1'].mean()
    mean_bot = df[df['coherence']<=q25]['abs_fwd1'].mean()

    corr = df[['coherence','volatility_norm','entropy_local','persistence','abs_fwd1']].corr()

    P = np.load('results/phase_space_demo/transition_matrix.npy')
    diag_mean = float(np.mean(np.diag(P)))
    row_ent = -np.sum(np.where(P>0, P * np.log2(P), 0), axis=1)
    row_ent_mean = float(np.nanmean(row_ent))

    thr = metrics['entropy_local'].quantile(0.9)
    chaos_dates = metrics[metrics['entropy_local']>=thr].index
    joined = df.copy()
    chaos_vol = float(joined.loc[joined.index.isin(chaos_dates),'fwd5_vol'].mean())
    nonchaos_vol = float(joined.loc[~joined.index.isin(chaos_dates),'fwd5_vol'].mean())

    print('\nSUMMARY:')
    print(f"mean_abs_fwd1_top_quartile_coherence = {mean_top:.6f}")
    print(f"mean_abs_fwd1_bottom_quartile_coherence = {mean_bot:.6f}")
    if mean_bot and not np.isnan(mean_bot):
        print(f"top/bottom ratio = {mean_top/mean_bot:.3f}")
    print('\nTransition matrix:')
    print(f"mean diagonal (stability) = {diag_mean:.4f}")
    print(f"mean row entropy = {row_ent_mean:.4f} bits")
    print('\nChaos vs non-chaos forward 5-day vol (annualized):')
    print(f"chaos_mean_fwd5_vol = {chaos_vol:.6f}")
    print(f"nonchaos_mean_fwd5_vol = {nonchaos_vol:.6f}")

    print('\nCorrelations (excerpt):')
    print(corr.to_string())

    print('\nSAMPLE state_metrics head:')
    print(metrics.head().to_string())

except Exception as e:
    print('Error in diagnostics:', e)
    sys.exit(2)

