# Dashboard Spec (Atual)

## Objetivo
Mostrar estado operacional real, nao previsao promocional.

## Blocos por ativo
1. Estado atual (`regime`).
2. Confiabilidade (`confidence`, `quality`, `data_adequacy`).
3. Motivo do gate (`reason`, `status`).

## Regras de UI
- `validated`: sinal exibido como operacional.
- `watch`: alerta exibido com cautela.
- `inconclusive`: mostrar apenas diagnostico; esconder acao.

## Fontes de dados
- `results/ops/snapshots/<run_id>/api_snapshot.jsonl`
- `results/ops/snapshots/<run_id>/summary.json`
- `results/validation/VERDICT.json`
- `results/validation/risk_truth_panel.json`

## Rotas de API esperadas
- `/api/run/latest`
- `/api/assets`
- `/api/assets/[asset]`
- `/api/risk-truth`
