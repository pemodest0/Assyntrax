# Ops Playbook

## Objetivo
Operar o motor com reproducibilidade, auditoria e gate de publicacao.

## Runbook diario
1. Executar `run_daily_jobs.ps1`.
2. Verificar `summary.json` do run.
3. Verificar `results/ops/diff/summary.json`.
4. Se bloqueado, manter frontend em modo diagnostico.
5. Se aprovado, publicar snapshot latest.

## Incidente (gate bloqueado)
- Nao remover bloqueio manualmente.
- Revisar data adequacy, drift e contrato.
- Registrar motivo no log operacional.

## Pre-commit tecnico
- compileall python
- validacao dos scripts de ops
- lint/typecheck frontend
- checklist de regressao
