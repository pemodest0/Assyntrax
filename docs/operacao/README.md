# Operação

Documentos da rotina diária e controle de publicação.

## Rotina principal
- `scripts/ops/run_daily_master.py`
- `docs/operacao/ROTINA_DIARIA_MASTER.md`
- `scripts/ops/run_repo_healthcheck.sh`
- `docs/operacao/REPO_HEALTHCHECK.md`
- `docs/operacao/GITHUB_CANONICO.md`
- `docs/operacao/GUIA_AUTONOMO_ASSYNTRAX.md`
- `docs/operacao/CHECKLIST_SITE_DEPLOY.md`
- `docs/operacao/RELATORIO_VERIFICACAO_SITE_20260221.md`

## Fluxo
1. Executa validação e snapshot.
2. Executa checagem de contrato e diff diário.
3. Executa alertas setoriais.
4. Gera sanidade, gate de publicação e relatório diário.
5. Compara com run anterior.

## Referências
- `docs/OPS_EXECUTION_FLOW.md`
- `docs/DAILY_PIPELINE.md`
- `docs/ops_playbook.md`

## Limpeza e organização
- Arquivar resultados antigos: `python3 scripts/maintenance/clean_old_results.py --apply`
- Arquivar docs legados: `python3 scripts/maintenance/archive_legacy_docs.py --apply`
- Organização segura de workspace (dry-run por padrão): `scripts/maintenance/organize_workspace.sh`
