# Plano de Refactor do Repo

Objetivo: consolidar a base em torno do pacote `engine/` sem quebrar compatibilidade.

## Fase 1 (concluida)
- Criar API unificada em `engine/`.
- Adicionar wrappers em `spa/` e `graph_engine/`.
- Migrar imports dos scripts para `engine.*`.

## Fase 2 (em andamento)
- Limpar arquivos nao operacionais da raiz.
- Mover artefatos antigos para `legacy/`.
- Atualizar toda documentacao para estado atual.

## Fase 3 (antes do commit)
- Checklist de regressao.
- Validar pipeline diario.
- Validar frontend + endpoints.
- Preparar rename `A-firma` -> `Assyntrax`.

## Criterio de conclusao
- Um unico fluxo operacional documentado.
- Sem dependencia funcional de imports antigos.
- Repositorio pronto para commit e publicacao.

## Documentacao relacionada
- `docs/OPS_EXECUTION_FLOW.md`
- `docs/ENGINE_GUIDE.md`
- `docs/CORE_PURE_MIGRATION_PLAN.md`
- `docs/LEGACY_CANDIDATES.md`
- `docs/REGRESSION_CHECKLIST_PRECOMMIT.md`
- `docs/COMMIT_CHECKLIST_FINAL.md`
- `docs/INDEX.md`
