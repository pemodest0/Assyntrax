# Repo Healthcheck

Checklist unico para validar o projeto inteiro (motor + ops + frontend) antes de commit/push/deploy.

## Comando unico

```bash
./scripts/ops/run_repo_healthcheck.sh
```

Opcional com run id fixo:

```bash
./scripts/ops/run_repo_healthcheck.sh PRE_DEPLOY_20260221
```

## O que valida
1. Compilacao Python (`compileall`) em `engine/`, `scripts/`, `tools/`, `tests/`.
2. Pureza do motor (`tools/engine_purity_audit.py`).
3. Integridade de payload para UI (`scripts/ops/audit_frontend_payloads.py`).
4. Orquestrador diario em modo seguro (`run_daily_master.py --dry-run`).
5. Frontend completo (`lint`, `typecheck`, `build`) em `website-ui/`.

## Saida gerada
- `results/ops/healthcheck/<run_id>/healthcheck.log`
- `results/ops/healthcheck/<run_id>/checks.tsv`
- `results/ops/healthcheck/<run_id>/report.md`
- `results/ops/healthcheck/<run_id>/git_status.txt`

## Regra operacional
- Se qualquer check falhar, o script retorna erro (`exit 1`).
- Publicacao/merge deve ocorrer apenas com healthcheck `ok`.

