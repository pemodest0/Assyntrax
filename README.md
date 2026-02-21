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
1. Rodar jobs diarios (`scripts/ops/run_daily_jobs.ps1` no Windows, `scripts/ops/run_daily_jobs.sh` no Linux/Mac).
2. Validar contrato e gates.
3. Publicar snapshot com `api_snapshot.jsonl` + `summary.json` + `audit_pack.json`.
4. Frontend consome apenas ultimo run valido.

## Criterio de pronto para producao
- Contrato de saida valido.
- Data adequacy gate aprovado.
- Drift diario sem bloqueio de deployment.
- Global verdict em estado aceitavel para publicacao.

## Comandos uteis
- Sincronizacao canonica (forca remoto sobre local):
  - `./scripts/ops/git_sync_canonical.sh`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\ops\\git_sync_canonical.ps1`
- Pipeline diario:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\ops\\run_daily_jobs.ps1 -Seed 17 -MaxAssets 80`
  - `./scripts/ops/run_daily_jobs.sh 17 80`
  - validacao de gate antes de publicar: `python3 scripts/ops/publish_latest_if_gate_ok.py`
- Healthcheck completo do repo:
  - `./scripts/ops/run_repo_healthcheck.sh`
- Frontend local:
  - `cd website-ui`
  - `npm run dev`

## Telas operacionais principais
- `website-ui/app/app/dashboard/page.tsx`: painel central do motor com filtros de ativo/setor/janela/periodo.
- `website-ui/app/app/setores/page.tsx`: leitura setorial, ranking e historico de niveis.
- `website-ui/app/app/operacao/page.tsx`: rotina diaria, gate de publicacao e relatorio.
- `website-ui/app/app/venda/page.tsx`: proposta comercial, pacotes e material de reuniao.

## Documentacao recomendada
- `docs/OPS_EXECUTION_FLOW.md`
- `docs/ENGINE_GUIDE.md`
- `docs/DAILY_PIPELINE.md`
- `docs/REPO_REFACTOR_PLAN.md`
- `docs/notes/MAC_HANDOFF.md`
- `docs/operacao/REPO_HEALTHCHECK.md`
- `docs/operacao/GITHUB_CANONICO.md`
