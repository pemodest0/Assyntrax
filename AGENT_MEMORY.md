# Agent Memory (Atual)

## Nome do projeto
- Marca alvo: `Assyntrax`
- Repo atual: `A-firma` (planejado rename)

## Motor oficial
- `engine/` e a API estavel.
- `spa/` e `graph_engine/` ficam como wrappers de compatibilidade e legado controlado.

## Fluxo oficial
- `scripts/ops/run_daily_jobs.ps1`
- outputs em `results/ops/snapshots/<run_id>/`
- frontend le ultimo run valido

## Artefatos canonicos por run
- `api_snapshot.jsonl`
- `summary.json`
- `audit_pack.json`

## Gates
- status por ativo: `validated/watch/inconclusive`
- gate global e drift influenciam publicacao
- data adequacy e obrigatorio

## Frontend
- consumir apenas artefatos validados
- ocultar acao para `inconclusive`
- exibir motivo do gate e caveats
- copiloto em `/app/copiloto` lendo `/api/copilot`

## Copiloto (B + C shadow)
- script operacional: `scripts/ops/build_copilot_shadow.py`
- artefato por run: `results/ops/copilot/<run_id>/shadow_summary.json`
- ponteiro: `results/ops/copilot/latest_release.json`
- nucleo de instrucoes: `config/copilot_instruction_core.v1.json`
- se `publishable=false`, status visivel deve ser `NAO PUBLICAVEL`

## Banco operacional (plataforma)
- ingestao: `scripts/ops/build_platform_db.py`
- arquivo sqlite: `results/platform/assyntrax_platform.db`
- snapshot para API/site: `results/platform/latest_db_snapshot.json`
- endpoint: `/api/platform/latest`
- pagina: `/app/plataforma`

## Legado
- mover itens nao operacionais para `legacy/`
- remover duplicidade gradual mantendo wrappers
