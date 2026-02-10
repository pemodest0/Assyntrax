# Daily Pipeline

## Comando oficial (Windows)
`powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\ops\\run_daily_jobs.ps1 -Seed 17 -MaxAssets 80`

## O que gera
- Snapshot diario com run_id.
- Validacao de contrato.
- Comparacao com dia anterior (drift).
- Pacote de auditoria.

## Artefatos
- `results/ops/snapshots/<run_id>/api_snapshot.jsonl`
- `results/ops/snapshots/<run_id>/summary.json`
- `results/ops/snapshots/<run_id>/audit_pack.json`
- `results/ops/diff/summary.json`

## Agendamento
- Registrar task via `scripts/ops/register_tasks_windows.ps1`.
- Rodar em horario fixo diario.

## Politica de publicacao
- Publicar no frontend apenas ultimo run com gate valido.
