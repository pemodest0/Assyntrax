# Registro de Execucao do Codex

Este registro guarda historico das acoes tecnicas e resultados de teste.

## Arquivos
- Historico completo: `results/codex/worklog.jsonl`
- Ultima entrada: `results/codex/worklog_latest.json`

## Como gravar entrada manual
```bash
python3 scripts/ops/log_codex_work.py \
  --kind result \
  --title "Rodada de validacao anual" \
  --summary "walkforward 2020-2025 concluido" \
  --artifacts "results/walkforward_sector_stability/20260220T044621Z/summary.json" \
  --tags "walkforward,regime,sector" \
  --metrics-json '{"pass_rate":1.0,"n_pass":6,"n_windows":6}'
```

## Como rodar busca da meta de 80%
```bash
python3 scripts/bench/search_recall80_target.py \
  --target-recall 0.80 \
  --event-def drawdown20 \
  --lookback 10 \
  --n-random 40 \
  --max-cases 10
```

Saidas da busca:
- `results/recall80_search/<timestamp>/search_results.csv`
- `results/recall80_search/<timestamp>/summary.json`
- `results/recall80_search/<timestamp>/report_recall80.txt`

Observacao:
- Esta meta de 80% deve ser analisada junto com falso alerta e precisao.

## Como rodar comparacao diaria de 2 modos
```bash
python3 scripts/ops/run_dual_mode_compare.py \
  --profile-useful config/sector_alerts_profile_useful.json \
  --profile-aggressive config/sector_alerts_profile_aggressive97.json \
  --n-random 20 \
  --lookbacks 10,20,30
```

Saidas:
- `results/dual_mode_compare/<timestamp>/summary.json`
- `results/dual_mode_compare/<timestamp>/mode_results.csv`
- `results/dual_mode_compare/history.csv`
- `results/dual_mode_compare/summary_7d.json`
