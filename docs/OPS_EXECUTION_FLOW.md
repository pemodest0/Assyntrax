# Fluxo Oficial de Execucao

Este e o fluxo unico para motor + validacao + publicacao.

## Entry point
- `scripts/ops/run_daily_jobs.ps1`
- Revalidacao mensal: `scripts/ops/run_monthly_revalidation.py`

## Etapas
1. Validacao diaria (`run_daily_validation.py`).
2. Build de snapshot (`build_daily_snapshot.py`).
3. Validacao de contrato (`validate_output_contract.py`).
4. Diff/drift vs dia anterior (`daily_diff_report.py`).
5. Pacote de auditoria (`build_run_audit_pack.py`).
6. Pacote setorial para painel (`run_daily_sector_alerts.py`).
   - Politica padrao e parametros vem do perfil congelado em `config/sector_alerts_profile.json`.
   - Sinal em duas camadas: rapido e confirmado (`two_layer_mode`).
   - Anti-ruido por `min_alert_gap_days` para reduzir repeticao de alerta.
   - Politicas alternativas: `regime_balanced` (mais estrita), `regime_guarded` (muito estrita) e `regime_auto` (calibracao por setor usando apenas janela de calibracao).
   - Baseline estatistico: usar `random_baseline_method=both` para comparar dias aleatorios e blocos temporais.
   - Persiste snapshot em banco sqlite (`results/event_study_sectors/sector_alerts.db`).
   - Gera comparacao semanal (`weekly_compare.json`).
   - Gera monitor de drift por z-score (`drift_monitor.json`, `drift/latest_drift.json`).
   - Gera alerta de saida de verde (`results/event_study_sectors/alerts/latest_alert.json`).
   - Gera health report e trilha de auditoria (`health/latest_health.json`, `audit_trail.jsonl`).
7. Copiloto shadow B+C (`build_copilot_shadow.py`).
   - Gera risco estrutural agregado B+C com gate de publicacao.
   - Registra `publishable=true/false` e bloqueadores.
8. Banco da plataforma (`build_platform_db.py`).
   - Indexa snapshot + copiloto por `run_id` em SQLite.
   - Publica snapshot consolidado do banco para consumo do site/API.
9. Revalidacao mensal (`run_monthly_revalidation.py`).
   - Roda hiper simulacao de parametros.
   - Compara baseline atual contra candidata em walkforward anual com gate fixo ou adaptativo (`--walkforward-gate-mode`).
   - Em gate adaptativo: janela sem eventos de drawdown e avaliada por disciplina de alerta (falso alerta), nao por recall.
   - Decide promover ou manter baseline.

## Saidas obrigatorias
- `results/ops/snapshots/<run_id>/api_snapshot.jsonl`
- `results/ops/snapshots/<run_id>/summary.json`
- `results/ops/snapshots/<run_id>/audit_pack.json`
- `results/ops/diff/summary.json`
- `results/ops/copilot/<run_id>/shadow_summary.json`
- `results/ops/copilot/latest_release.json`
- `results/platform/assyntrax_platform.db`
- `results/platform/latest_db_snapshot.json`
- `results/platform/latest_release.json`
- `results/event_study_sectors/latest_run.json`
- `results/event_study_sectors/<run_id_setorial>/sector_alert_levels_latest.csv`
- `results/event_study_sectors/sector_alerts.db`
- `results/event_study_sectors/alerts/latest_alert.json`
- `results/event_study_sectors/drift/latest_drift.json`
- `results/event_study_sectors/health/latest_health.json`
- `results/event_study_sectors/audit_trail.jsonl`

## Opcional de notificacao externa
- Variavel de ambiente `SECTOR_ALERT_WEBHOOK_URL`
  - Quando definida, envia POST JSON automatico se algum setor sair de verde.

## Agendamentos
- Diario: `scripts/ops/cron_daily.sh`
- Mensal: `scripts/ops/cron_monthly_revalidation.sh`

## Regras de bloqueio
- Falha em contrato: bloqueia publicacao.
- Falha em data adequacy: bloqueia publicacao.
- Drift acima do limite: `deployment_gate.blocked=true`.

## Perfil atual (tuning)
- Perfil oficial: `config/sector_alerts_profile.json`.
- Ultima hiper rodada grande: `results/hyper_sector_search/20260220T014134Z`.
- Ultima revalidacao mensal: `results/monthly_revalidation/20260220T024324Z`.
- Decisao mensal: manter baseline (sem promocao automatica).

## Documentacao relacionada
- `docs/DAILY_PIPELINE.md`
- `docs/ops_playbook.md`
- `docs/ENGINE_GUIDE.md`
- `docs/DASHBOARD_SPEC.md`
- `docs/COMMIT_CHECKLIST_FINAL.md`
- `docs/INDEX.md`
- `docs/MOTOR_ACTION_RULEBOOK.md`
- `docs/OFERTA_COMERCIAL_MOTOR.md`
