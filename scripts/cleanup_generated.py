#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import shutil

TO_REMOVE = [
    # outputs
    'outputs/phase_space_3d.png',
    'outputs/phase_space_3d_elegant.png',
    'outputs/collective_center_of_mass_3d.csv',
    'outputs/sp500_3d.csv',
    'outputs/ibov_3d.csv',
    'outputs/dax_3d.csv',
    'outputs/cac40_3d.csv',
    # state_space generated
    'dados/state_space/sp500_phases.csv',
    'dados/state_space/sp500_phases_confirmed.csv',
    'dados/state_space/sp500_local_regime.csv',
    'dados/state_space/sp500_embedding_d3_tau1.csv',
    'dados/state_space/sp500_embedding_d3_tau1.npy',
    'dados/state_space/sp500_phase_tests.json',
    'dados/state_space/sp500_phase_summary.json',
    'dados/state_space/sp500_metrics.csv',
    'dados/state_space/ibov_phases.csv',
    'dados/state_space/ibov_phases_confirmed.csv',
    'dados/state_space/ibov_local_regime.csv',
    'dados/state_space/ibov_embedding_d3_tau1.csv',
    'dados/state_space/ibov_embedding_d3_tau1.npy',
    'dados/state_space/ibov_phase_tests.json',
    'dados/state_space/ibov_phase_summary.json',
    'dados/state_space/ibov_metrics.csv',
    'dados/state_space/cac40_phases.csv',
    'dados/state_space/cac40_phases_confirmed.csv',
    'dados/state_space/cac40_local_regime.csv',
    'dados/state_space/cac40_embedding_d3_tau1.csv',
    'dados/state_space/cac40_embedding_d3_tau1.npy',
    'dados/state_space/cac40_phase_tests.json',
    'dados/state_space/cac40_phase_summary.json',
    'dados/state_space/cac40_metrics.csv',
    'dados/state_space/tests_summary.json',
]

SCRIPTS_REMOVE = [
    'scripts/analyze_market_phases.py',
    'scripts/report_phase_stats.py',
    'scripts/compute_local_regime.py',
    'scripts/evaluate_phase_space_tests.py',
    'scripts/print_local_regime_counts.py',
    'scripts/refine_and_map_phases.py',
    'scripts/run_collective_phase_space.py',
    'scripts/plot_phase_space_3d_elegant.py',
    'scripts/run_phase_space_pipeline.py',
]


def remove_path(p: Path):
    if p.exists():
        try:
            if p.is_file():
                p.unlink()
                print('Removed file', p)
            elif p.is_dir():
                shutil.rmtree(p)
                print('Removed directory', p)
        except Exception as e:
            print('Failed to remove', p, e)


def main():
    for s in SCRIPTS_REMOVE:
        remove_path(Path(s))

    for t in TO_REMOVE:
        remove_path(Path(t))

    # remove outputs dir if empty
    out = Path('outputs')
    if out.exists() and not any(out.iterdir()):
        out.rmdir()
        print('Removed empty outputs directory')

    print('Cleanup finished.')


if __name__ == '__main__':
    main()
