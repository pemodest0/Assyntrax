# PTBP Benchmark (Assyntrax Eigen Engine)

Este benchmark implementa um protocolo inicial de validacao de transicao estrutural.

- Cenarios sinteticos:
  - `lorenz` (com/sem drift)
  - `rossler` (com/sem drift)
  - `mackey_glass` (com/sem drift)
- Baselines:
  - `vol` (volatilidade realizada)
  - `garch_lr` (GARCH(1,1) + teste LR de quebra em variancia dos residuos)
  - `cusum`
  - `perm_entropy`
  - `ssa90` (SSA com rank por 90% da energia)
- Metrica desafiadora:
  - `eigen` (score espectral estrutural via AR + entropia espectral + gap, com hardening por persistencia + consenso parcial com baselines)
  - `rmt_gate` (auditor secundario RMT, gated por contexto estrutural do eigen)

## Execucao

### Smoke test

```powershell
python scripts/bench/run_eigen_ptbp.py --n 1800 --runs 1 --snr-db 15 --outdir results/benchmarks/ptbp_smoke
```

### Execucao padrao

```powershell
python scripts/bench/run_eigen_ptbp.py --n 10000 --runs 8 --snr-db 20 --outdir results/benchmarks/ptbp
```

## Saidas

- `ptbp_detail.csv`: deteccao por cenario e modelo
- `ptbp_summary.csv`: agregacao por modelo (`has_shift` vs `no_shift`)
- `ptbp_summary.json`: resumo institucional de lead-time, alert rate, CDaR proxy e IC95%

## Interpretacao

- `lead_time` positivo: alerta antes do evento de transicao.
- `lead_pos_rate`: fracao de cenarios com lead time positivo.
- `false_alert_rate_no_shift` baixo: menos falsos positivos em cenarios estaveis.
- `cdar_mean_after_alert_shift`: proxy de severidade apos alerta.

## Observacoes

- Este protocolo e versao inicial para comparacao relativa.
- Proxima etapa: integrar filtros RMT explicitos e versao com dados financeiros reais walk-forward.
