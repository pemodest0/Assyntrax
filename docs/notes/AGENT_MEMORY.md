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

## Legado
- mover itens nao operacionais para `legacy/`
- remover duplicidade gradual mantendo wrappers
