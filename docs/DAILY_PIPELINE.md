# Daily Pipeline

## Comando oficial (Windows)
`powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\ops\\run_daily_jobs.ps1 -Seed 17 -MaxAssets 80`

## O que gera
- Snapshot diario com run_id.
- Validacao de contrato.
- Comparacao com dia anterior (drift).
- Pacote de auditoria.
- Shadow do copiloto (modelo B + modelo C) com gate de publicacao.
- Indexacao no banco SQLite da plataforma.

## Artefatos
- `results/ops/snapshots/<run_id>/api_snapshot.jsonl`
- `results/ops/snapshots/<run_id>/summary.json`
- `results/ops/snapshots/<run_id>/audit_pack.json`
- `results/ops/diff/summary.json`
- `results/ops/copilot/<run_id>/shadow_summary.json`
- `results/ops/copilot/<run_id>/executive_summary.txt`
- `results/ops/copilot/<run_id>/technical_summary.md`
- `results/ops/copilot/latest_release.json`
- `results/platform/assyntrax_platform.db`
- `results/platform/latest_db_snapshot.json`
- `results/platform/latest_release.json`

## Agendamento
- Registrar task via `scripts/ops/register_tasks_windows.ps1`.
- Rodar em horario fixo diario.
- Launcher local unico: `scripts/ops/start_platform_local.ps1` (opcional).

## Politica de publicacao
- Publicar no frontend apenas ultimo run com gate valido.
- No copiloto, usar `publishable=true` do shadow; se falso, exibir `NAO PUBLICAVEL`.
