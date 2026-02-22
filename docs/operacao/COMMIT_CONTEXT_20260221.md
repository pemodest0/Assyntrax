# Commit Contexto 2026-02-21

Este documento registra, de forma objetiva, o que foi consolidado no repositorio para continuidade entre Mac, Windows e execucoes do Codex.

## Escopo consolidado

- Snapshot amplo do estado atual do projeto (motor, site, docs, scripts, dados).
- Organizacao de documentacao em trilhas claras:
  - `docs/notes/` para memoria operacional e metodologia.
  - `docs/operacao/` para runbooks e continuidade.
  - `docs/motor/` para teoria e manual mestre.
  - `docs/venda/` para materiais comerciais.
- Inclusao de handoff completo para novo agente:
  - `docs/operacao/HANDOFF_CONTEXTO_NOVO_CODEX_20260221.md`
- Politica de GitHub canonico reforcada:
  - `docs/operacao/GITHUB_CANONICO.md`

## Regra canonica (remoto vence local)

Foram adicionados scripts oficiais para forcar sincronizacao com `origin/main` quando necessario:

- Mac/Linux: `scripts/ops/git_sync_canonical.sh`
- Windows: `scripts/ops/git_sync_canonical.ps1`

Ambos executam:

1. `git fetch --prune`
2. `git reset --hard origin/main` (ou remoto/branch informado)
3. `git clean -fd`

## Site e UX

- Correcoes recentes de UX ja integradas no estado canonico:
  - rota `/app/venda` sem dead-end;
  - estados sem dados/falha mais robustos;
  - pagina teorica e referencias;
  - blindagem de links vazios em cards/fontes.

## Operacao

- Pipeline diario e gate de publicacao mantidos como referencia:
  - `scripts/ops/run_daily_master.py`
  - `scripts/ops/publish_latest_if_gate_ok.py`
  - `scripts/ops/run_repo_healthcheck.sh`

## Objetivo deste registro

Garantir que qualquer nova sessao em outra maquina comece do mesmo baseline, reduzindo divergencia local e perda de contexto historico.
