# Checklist Site + Deploy (Operacao)

Checklist objetivo para validar site, APIs e deploy sem perder tempo.

## 1) Integridade local (obrigatorio)

```bash
./scripts/ops/run_repo_healthcheck.sh PRE_DEPLOY
```

Esperado:
- status `ok`
- 0 falhas

## 2) Build do frontend (obrigatorio)

```bash
cd website-ui
npm run build -- --webpack
```

Esperado:
- compilacao `successful`
- rotas app/api listadas no final do build

## 3) Deploy em producao (Vercel)

```bash
cd website-ui
npx vercel --prod --yes
```

Esperado:
- URL de producao nova
- alias aplicado em `https://assyntrax.vercel.app`

## 4) Smoke test publico (apos deploy)

Rodar do seu terminal com internet/DNS normal:

```bash
BASE="https://assyntrax.vercel.app"
for p in \
  "/" \
  "/app/dashboard" \
  "/app/teoria" \
  "/app/venda" \
  "/methods" \
  "/product" \
  "/api/run/latest" \
  "/api/ops/latest" \
  "/api/lab/corr/latest?window=120" \
  "/api/sectors/alerts?days=90" \
  "/api/assets"; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE$p")
  echo "$code $p"
done
```

Esperado:
- paginas: `200`
- APIs: `200` (ou `401` em endpoint protegido por chave, quando aplicavel)

## 5) Se der erro de "Sem dados/Falha ao carregar"

1. Rodar healthcheck de novo:
```bash
./scripts/ops/run_repo_healthcheck.sh DEBUG_EMPTY
```
2. Ver logs:
- `results/ops/healthcheck/<run_id>/healthcheck.log`
3. Ver run valido:
- `results/ops/snapshots/<run_id>/api_snapshot.jsonl`
- `results/ops/snapshots/<run_id>/summary.json`
4. Regerar dados:
```bash
python3 scripts/ops/run_daily_master.py
```

## 6) Resultado mais recente executado

Data: 2026-02-21  
Status local: OK  
Healthcheck: `results/ops/healthcheck/HC_SITE_DEPLOY_20260221_RECHECK/report.md`  
Deploy prod: `https://assyntrax-m2tzkvcvv-pemodest0s-projects.vercel.app`  
Alias: `https://assyntrax.vercel.app`

