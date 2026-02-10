# Assyntrax Engine + Product Platform

Este repositorio contem o motor de deteccao de regimes e risco, os pipelines de validacao/auditoria e o frontend operacional.

## Estado atual
- Motor unificado em `engine/` com wrappers de compatibilidade em `spa/` e `graph_engine/`.
- Pipelines operacionais em `scripts/ops/`.
- Validacoes cientificas e operacionais em `scripts/bench/validation/`.
- Site/API em `website-ui/` consumindo snapshots validados.
- Artefatos canonicos em `results/ops/snapshots/<run_id>/` e `results/validation/`.

## Estrutura principal
- `engine/`: API estavel do motor (camada oficial para novos imports).
- `scripts/ops/`: rotina diaria, snapshot, contrato, drift e auditoria.
- `scripts/bench/validation/`: testes de robustez, placebo, adequacao e utilidade.
- `config/`: contrato de saida e gates versionados.
- `website-ui/`: frontend e rotas API para consumo dos artefatos.
- `legacy/`: arquivos antigos ou fora do fluxo atual.

## Fluxo oficial (alto nivel)
1. Rodar jobs diarios (`scripts/ops/run_daily_jobs.ps1`).
2. Validar contrato e gates.
3. Publicar snapshot com `api_snapshot.jsonl` + `summary.json` + `audit_pack.json`.
4. Frontend consome apenas ultimo run valido.

## Criterio de pronto para producao
- Contrato de saida valido.
- Data adequacy gate aprovado.
- Drift diario sem bloqueio de deployment.
- Global verdict em estado aceitavel para publicacao.

## Comandos uteis
- Pipeline diario:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\ops\\run_daily_jobs.ps1 -Seed 17 -MaxAssets 80`
- Frontend local:
  - `cd website-ui`
  - `npm run dev`

## Documentacao recomendada
- `docs/OPS_EXECUTION_FLOW.md`
- `docs/ENGINE_GUIDE.md`
- `docs/DAILY_PIPELINE.md`
- `docs/REPO_REFACTOR_PLAN.md`
- `MAC_HANDOFF.md`
