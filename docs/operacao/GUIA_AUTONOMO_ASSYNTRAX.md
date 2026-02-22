# Guia Autonomo Assyntrax (Repo + Site + APIs + Operacao)

Este guia foi feito para voce tocar o projeto sozinho: entender estrutura, validar, publicar e debugar.

## 1) Estado atual validado

Ultima verificacao completa local:
- comando: `./scripts/ops/run_repo_healthcheck.sh HC_LOCAL_20260221_FINAL`
- relatorio: `results/ops/healthcheck/HC_LOCAL_20260221_FINAL/report.md`
- status: `ok` (0 falhas)

## 2) Mapa do repositorio

Pastas principais:
- `engine/`: nucleo do motor de regime/risco.
- `scripts/ops/`: operacao diaria, snapshot, gate, auditoria, publicacao.
- `scripts/bench/`: validacoes e estudos de desempenho.
- `scripts/maintenance/`: limpeza e organizacao controlada do workspace.
- `config/`: contratos e politicas de gate.
- `results/`: saidas do motor, snapshots, validacoes e historicos.
- `website-ui/`: frontend Next.js (site + app + APIs HTTP).
- `docs/`: documentacao tecnica, operacao e material comercial.

## 3) Comandos essenciais (dia a dia)

### Verificacao completa antes de commit/deploy
```bash
./scripts/ops/run_repo_healthcheck.sh PRE_PUSH
```

### Rotina diaria do motor
```bash
python3 scripts/ops/run_daily_master.py
```

Atalho Linux/Mac:
```bash
./scripts/ops/run_daily_jobs.sh
```

### Rodar frontend local
```bash
cd website-ui
npm run dev
```

### Build de producao frontend
```bash
cd website-ui
npm run build -- --webpack
```

## 4) Fluxo de dados (o que alimenta o site)

Pipeline oficial:
1. `run_daily_validation.py` valida motor.
2. `build_daily_snapshot.py` gera `api_snapshot.jsonl`.
3. `validate_output_contract.py` valida contrato de saida.
4. `daily_diff_report.py` mede drift e gate.
5. `run_daily_sector_alerts.py` gera pacote setorial.
6. `run_daily_master.py` consolida `sanity`, `gate`, `history`, `daily_report`.

Arquivos canonicos consumidos pela UI:
- `results/ops/snapshots/<run_id>/api_snapshot.jsonl`
- `results/ops/snapshots/<run_id>/summary.json`
- `results/ops/runs/<run_id>/daily_master_summary.json`
- `results/ops/runs/<run_id>/publish_gate.json`
- `results/event_study_sectors/<run_id>/sector_alert_levels_latest.csv`

Leitura no backend do site:
- `website-ui/lib/server/data.ts`
  - acha o ultimo run valido (`findLatestValidRun`)
  - le snapshot (`readLatestSnapshot`)
  - aplica sanitizacao de encoding (`sanitizeEncoding`)
- `website-ui/lib/server/validated.ts`
  - le status de ativos por timeframe (`readAssetStatusMap`)

## 5) Layout e navegacao do site

Arquivos estruturais:
- `website-ui/app/layout.tsx`: metadata global e root HTML.
- `website-ui/app/(site)/layout.tsx`: layout do site institucional.
- `website-ui/app/app/layout.tsx`: layout do app interno com menu lateral.
- `website-ui/lib/site/features.ts`: feature flags de navegacao.

Flags atuais (`website-ui/lib/site/features.ts`):
- `financeOnlyMode: true`
- `showSetoresNav: false`
- `showRealEstateNav: false`

## 6) Paginas (o que cada uma faz)

### Site institucional (`website-ui/app/(site)/...`)
- `/` -> `website-ui/app/(site)/page.tsx`: landing com secoes Hero/Problema/Metodo/Produto/Use cases/Prova/CTA.
- `/about` -> espelho de `/pt/about`.
- `/contact` -> formulario de contato.
- `/methods` -> conteudo metodologico (`MethodsPageClient`).
- `/product` -> pagina de produto, mock e saida JSON.
- `/proposta` -> proposta comercial e links docs de venda.
- `/privacy` -> politica de privacidade.
- `/pt/*` -> paginas espelho com canonical para rotas principais.

### App interno (`website-ui/app/app/...`)
- `/app/dashboard` -> `MotorControlCenter` + `SectorDashboard`.
- `/app/aplicacoes` -> casos de uso, cronologia de eventos, aplicacao operacional.
- `/app/casos` -> storytelling de casos reais + fontes.
- `/app/venda` -> pacotes comerciais e material de reuniao.
- `/app/teoria` -> teoria formal (equacoes/latex + referencias).
- `/app/finance`, `/app/imoveis`, `/app/macro`, `/app/operacao`, `/app/real-estate`, `/app/setores`, `/app/sobre`, `/app/metodologia` -> rotas de redirecionamento.

## 7) APIs do site (endpoint -> arquivo -> funcao)

### Core de snapshot/risco
- `GET /api/run/latest` -> `website-ui/app/api/run/latest/route.ts`: ultimo run valido.
- `GET /api/runs` -> `website-ui/app/api/runs/route.ts`: lista runs/index.
- `GET /api/latest` -> `website-ui/app/api/latest/route.ts`: ultimo registro.
- `GET /api/history` -> `website-ui/app/api/history/route.ts`: historico de registros.
- `GET /api/overview` -> `website-ui/app/api/overview/route.ts`: resumo agregado.
- `GET /api/risk-truth` -> `website-ui/app/api/risk-truth/route.ts`: painel de verdade de risco.
- `GET /api/methodology` -> `website-ui/app/api/methodology/route.ts`: status global + metodologia.
- `GET /api/index` -> `website-ui/app/api/index/route.ts`: indice de resultados.
- `GET /api/search` -> `website-ui/app/api/search/route.ts`: busca de arquivos.
- `GET /api/files/[...path]` -> `website-ui/app/api/files/[...path]/route.ts`: leitura de arquivo especifico.

### Ativos
- `GET /api/assets` -> `website-ui/app/api/assets/route.ts`
  - lista registros normalizados
  - filtra por `domain`, `status`, `include_inconclusive`
  - fallback para `public/data/latest` se sem run valido
- `GET /api/assets/[asset]` -> `website-ui/app/api/assets/[asset]/route.ts`
  - detalhe por ativo
  - retorna 503 se sem run valido

### Dashboard app interno
- `GET /api/dashboard/overview` -> `website-ui/app/api/dashboard/overview/route.ts`: overview do dashboard.
- `GET /api/ops/latest` -> `website-ui/app/api/ops/latest/route.ts`
  - le `results/ops/runs/latest_run.json`
  - fallback para `public/data/lab_corr_macro/latest`
- `GET /api/lab/corr/latest` -> `website-ui/app/api/lab/corr/latest/route.ts`
  - contrato principal do `MotorControlCenter`
  - parametros: `window`, `include_rows`, `period_days`, `asset`, `sector`
  - retorna 503 com `no_valid_lab_run` se nao houver run valido
- `GET /api/sectors/alerts` -> `website-ui/app/api/sectors/alerts/route.ts`
  - contrato principal do `SectorAlertsDashboard`
  - parametros: `days`, `level`, `sector`, `min_assets`
  - auth opcional via `ASSYNTRAX_REQUIRE_API_KEY_FOR_SECTORS`
  - retorna 404 `no_sector_run` se nao houver pacote setorial

### Graph/estudos
- `GET /api/graph/universe`
- `GET /api/graph/regimes`
- `GET /api/graph/regimes-batch`
- `GET /api/graph/series-batch`
- `GET /api/graph/sector`
- `GET /api/graph/backtest`
- `GET /api/graph/hypertest`
- `GET /api/graph/official`
- `GET /api/graph/sanity`
- `GET /api/graph/validation`

Todos em `website-ui/app/api/graph/*/route.ts`.

### Real estate
- `GET /api/realestate/summary`
- `GET /api/realestate/asset`
- `GET /api/realestate/series`

Arquivos: `website-ui/app/api/realestate/*/route.ts`.

### Contato
- `POST /api/contact` -> recebe lead e grava/encaminha.
- `GET /api/contact` -> status basico.

Arquivo: `website-ui/app/api/contact/route.ts`.

## 8) Componentes criticos (frontend)

- `website-ui/components/MotorControlCenter.tsx`
  - principal painel tecnico do motor.
  - carrega `/api/lab/corr/latest`.
  - trata vazio com `emptyNotice` (sem "falha fantasma").
- `website-ui/components/SectorAlertsDashboard.tsx`
  - principal painel setorial.
  - carrega `/api/sectors/alerts`.
  - diferencia `no_sector_run` (vazio esperado) de erro real.
- `website-ui/components/SectorDashboard.tsx`
  - bloco de leitura por ativo/finance no dashboard.
- `website-ui/components/RealEstateDashboard.tsx`
  - painel imobiliario.

## 9) Scripts ops que voce precisa dominar

Arquivos chave:
- `scripts/ops/run_daily_master.py`: orquestrador unico diario.
- `scripts/ops/run_daily_validation.py`: validacao diaria.
- `scripts/ops/build_daily_snapshot.py`: snapshot API.
- `scripts/ops/validate_output_contract.py`: contrato de saida.
- `scripts/ops/daily_diff_report.py`: drift/gate.
- `scripts/ops/run_daily_sector_alerts.py`: pacote setorial.
- `scripts/ops/update_prediction_truth_daily.py`: historico de acerto.
- `scripts/ops/publish_latest_if_gate_ok.py`: bloqueia publish se gate ruim.
- `scripts/ops/run_repo_healthcheck.sh`: checklist completo repo.
- `scripts/ops/audit_frontend_payloads.py`: valida payload para UI.

## 10) GitHub canonico (evitar bagunca entre maquinas)

Fluxo recomendado:
```bash
git fetch origin --prune
git pull --ff-only origin main
./scripts/ops/run_repo_healthcheck.sh PRE_PUSH
git add <arquivos_do_escopo>
git commit -m "mensagem objetiva"
git push origin main
```

Referencia: `docs/operacao/GITHUB_CANONICO.md`.

## 11) Deploy (site)

Pre-deploy:
1. `./scripts/ops/run_repo_healthcheck.sh PRE_DEPLOY`
2. confirmar `status: ok` no relatorio.

Deploy:
```bash
cd website-ui
npx vercel --prod --yes
```

Pos deploy:
1. abrir `/app/dashboard`
2. abrir `/app/teoria`
3. abrir `/app/venda`
4. checar APIs basicas:
   - `/api/run/latest`
   - `/api/ops/latest`
   - `/api/lab/corr/latest?window=120`
   - `/api/sectors/alerts?days=90`

## 12) Como debugar "Sem dados / Falha ao carregar"

Ordem de diagnostico:
1. rodar `./scripts/ops/run_repo_healthcheck.sh DEBUG_EMPTY`
2. verificar `results/ops/healthcheck/<run_id>/healthcheck.log`
3. testar endpoint da tela que falhou
4. conferir se existe run valido em `results/ops/snapshots/<run_id>`
5. se faltar dado, rodar `python3 scripts/ops/run_daily_master.py`

Casos comuns:
- `no_valid_lab_run` -> falta snapshot lab valido.
- `no_sector_run` -> falta pacote setorial.
- `unauthorized` em setores -> chave/API config.
- `file_not_found` -> indice/snapshot incompleto.

## 13) Inventario de funcoes (comandos para inspecao rapida)

Listar todas as rotas Next:
```bash
find website-ui/app -type f \( -name 'page.tsx' -o -name 'route.ts' -o -name 'layout.tsx' \) | sort
```

Listar funcoes exportadas:
```bash
rg -n "export (default )?function|export async function (GET|POST|PUT|PATCH|DELETE)" website-ui/app website-ui/components website-ui/lib
```

Listar scripts operacionais:
```bash
ls -1 scripts/ops | sort
```

## 14) Prompt pronto para pedir ajuda ao Codex

Se quiser usar IA de forma eficiente, copie este prompt base:

```text
Objetivo: <descreva objetivo final em 1 frase>.
Escopo permitido: <arquivos/pastas>.
Nao pode quebrar: <rotas, APIs, telas, dados>.
Validacoes obrigatorias: run_repo_healthcheck + lint + typecheck + build.
Entrega: patch aplicado + resumo das mudancas + comandos de verificacao.
```

Prompts curtos uteis:
- "Mapeie todas as APIs e diga quem consome cada endpoint no frontend."
- "Corrija apenas erro de estado vazio/sem dados sem criar fallback fake."
- "Prepare commit limpo so com arquivos alterados neste escopo."
- "Valide deploy readiness e me entregue checklist binario (ok/falha)."

## 15) Limites importantes do sistema

- O motor nao e recomendacao de compra/venda.
- O motor nao garante retorno.
- O valor principal e governanca de risco e consistencia operacional.
- Sempre valide gate e contrato antes de publicar.

