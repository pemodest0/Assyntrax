# Mac Handoff (Assyntrax)

Guia de continuidade para Mac com foco no fluxo oficial do motor e do produto.

## O que copiar
- `engine/`
- `scripts/`
- `config/`
- `website-ui/`
- `docs/`
- `models/` (se necessario)

## O que pode ser regenerado
- `results/` (exceto artefatos que voce quer preservar para auditoria)
- caches locais

## Setup rapido (Mac)
1. Instalar Python 3.11+.
2. Instalar Node 20+ para `website-ui`.
3. Instalar dependencias Python do projeto.
4. Rodar pipeline diario e validar snapshots.

## Fluxo recomendado
1. `scripts/ops/run_daily_jobs.ps1` (ou equivalente shell no Mac).
2. Conferir `results/ops/snapshots/<run_id>/summary.json`.
3. Subir frontend e validar endpoints:
   - `/api/run/latest`
   - `/api/assets`
   - `/api/risk-truth`

## Criterios de handoff concluido
- Snapshot valido gerado no dia.
- Contrato de saida validado.
- Frontend lendo snapshot mais recente sem fallback quebrado.
- Auditoria por run presente (`audit_pack.json`).

## Documentacao relacionada
- `README.md`
- `docs/notes/METHODOLOGY.md`
- `docs/OPS_EXECUTION_FLOW.md`
- `docs/DAILY_PIPELINE.md`
- `docs/ENGINE_GUIDE.md`
- `docs/INDEX.md`
