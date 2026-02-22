# Rotina Diária Master

## Comando único

```bash
python3 scripts/ops/run_daily_master.py
```

Atalho shell (Linux/Mac):

```bash
./scripts/ops/run_daily_jobs.sh
```

Atalho Windows:

```powershell
scripts\ops\run_daily_jobs.cmd
```

Modo com análises pesadas:

```bash
python3 scripts/ops/run_daily_master.py --with-heavy
```

## O que ele faz
1. Roda validação diária.
2. Gera snapshot.
3. Valida contrato de saída.
4. Gera diff diário.
5. Roda alertas setoriais.
6. (Opcional) Roda diagnóstico motor 470 e suíte de crise.

## Gate de publicação
- Arquivo: `results/ops/runs/<run_id>/publish_gate.json`
- Se regras mínimas falharem: cria `PUBLISH_BLOCKED` e retorna erro.
- Validação de publicação isolada:

```bash
python3 scripts/ops/publish_latest_if_gate_ok.py
```

## Relatórios gerados
- `results/ops/runs/<run_id>/daily_report.txt`
- `results/ops/runs/<run_id>/sanity.json`
- `results/ops/runs/<run_id>/history_compare.json`
- `results/ops/runs/<run_id>/steps.json`
