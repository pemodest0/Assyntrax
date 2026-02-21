# Padrão de Nomes de Saída

## Regra geral
- Formato de run: `YYYYMMDDTHHMMSSZ`
- Exemplo: `20260220T171218Z`

## Pastas principais
- `results/ops/runs/<run_id>/`
- `results/ops/snapshots/<run_id>/`
- `results/ops/daily/<run_id>/`

## Arquivos obrigatórios por run
- `steps.json`
- `sanity.json`
- `publish_gate.json`
- `daily_report.txt`
- `history_compare.json`
- `daily_master_summary.json`

## Ponteiro de última execução
- `results/ops/runs/latest_run.json`

