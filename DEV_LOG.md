# Dev Log (Resumo Atual)

## 2026-02
- API de engine unificada em `engine/`.
- Imports de scripts migrados para `engine.*`.
- Wrappers criados em `spa/` e `graph_engine/` para compatibilidade.
- Pipeline diario consolidado em `scripts/ops/`.
- Contrato e gates de saida formalizados via config.
- Frontend ajustado para leitura de snapshots validados.
- Normalizacao defensiva de `domain` na API do site para evitar valores sujos/typos no payload.
- Parser JSONL robusto no backend do site para tolerar `NaN/Infinity` sem derrubar rotas.
- Diagnostico de ativos inconclusivos automatizado em `results/validation/inconclusive_diagnosis_latest.csv`.
- Suite de validacao de produto executada com status `ok` (18/18) em `scripts/bench/validation/run_product_pipeline.py`.
- VERDICT consolidado com status `pass` em `results/validation/VERDICT.json`.
- Copiloto IA em tempo real implementado no site (`/app/copiloto`) com endpoint `/api/copilot`.
- Modelo B e Modelo C conectados em shadow via artefato operacional por run.
- Script novo `scripts/ops/build_copilot_shadow.py` adicionado ao pipeline diario.
- Nucleo de instrucoes versionado em `config/copilot_instruction_core.v1.json`.
- Publicacao do copiloto bloqueada por gate/integridade quando `publishable=false`.
- Banco SQLite da plataforma implementado em `results/platform/assyntrax_platform.db` via `scripts/ops/build_platform_db.py`.
- Endpoint de status do banco: `/api/platform/latest`.
- Pagina operacional de plataforma: `/app/plataforma`.
- Launcher unico local: `scripts/ops/start_platform_local.ps1` (opcionalmente roda pipeline + website).

## Fechamento do dia (motor + site + deploy)
- Contrato operacional mantido: `status`, `regime`, `confidence`, `quality`, `instability_score`, `reason`, `data_adequacy`, `run_id`.
- Snapshot validado mantido como fonte principal da API/site.
- Checklist tecnico executado:
  - `npm run lint` (ok)
  - `npm run typecheck` (ok)
  - `npm run build` (bloqueio de ambiente: `spawn EPERM` em Windows, pendente de saneamento local).
- Proxima acao direta antes do deploy final:
  - sanear ambiente Windows para build de producao do Next e rerodar smoke completo de rotas/API.

## Proximo checkpoint
- Limpeza final de legado nao operacional.
- Atualizacao de docs para rename do repositorio.
- Checklist final de regressao pre-commit.
