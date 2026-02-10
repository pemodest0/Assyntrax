# Fluxo Oficial de Execucao

Este e o fluxo unico para motor + validacao + publicacao.

## Entry point
- `scripts/ops/run_daily_jobs.ps1`

## Etapas
1. Validacao diaria (`run_daily_validation.py`).
2. Build de snapshot (`build_daily_snapshot.py`).
3. Validacao de contrato (`validate_output_contract.py`).
4. Diff/drift vs dia anterior (`daily_diff_report.py`).
5. Pacote de auditoria (`build_run_audit_pack.py`).

## Saidas obrigatorias
- `results/ops/snapshots/<run_id>/api_snapshot.jsonl`
- `results/ops/snapshots/<run_id>/summary.json`
- `results/ops/snapshots/<run_id>/audit_pack.json`
- `results/ops/diff/summary.json`

## Regras de bloqueio
- Falha em contrato: bloqueia publicacao.
- Falha em data adequacy: bloqueia publicacao.
- Drift acima do limite: `deployment_gate.blocked=true`.

## Documentacao relacionada
- `docs/DAILY_PIPELINE.md`
- `docs/ops_playbook.md`
- `docs/ENGINE_GUIDE.md`
- `docs/DASHBOARD_SPEC.md`
- `docs/COMMIT_CHECKLIST_FINAL.md`
- `docs/INDEX.md`
