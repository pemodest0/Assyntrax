# Core Puro: Plano de Migracao

Objetivo: remover dependencias de `engine/*` em `spa` e `graph_engine`, consolidando implementacao real dentro de `engine/`.

## Estado inicial (2026-02-11)
- `engine/` ainda possui facades para codigo legado.
- Auditoria atual: `29` imports legados em `engine/`.
- Baseline de controle: `config/engine_purity_baseline.json`.

## Checkpoint atual (2026-02-11)
- Auditoria apos migracoes incrementais: `0` imports legados em `engine/`.
- Modulos migrados para implementacao local:
  - `engine/models/baselines.py`
  - `engine/models/takens_knn.py`
  - `engine/forecasting/forecasters.py`
  - `engine/forecasting/regime_gating.py`
  - `engine/graph/schema.py`
  - `engine/graph/version.py`
  - `engine/graph/diagnostics.py`
  - `engine/graph/embedding.py`
  - `engine/graph/export.py`
  - `engine/graph/risk_thresholds.py`
  - `engine/graph/sanity.py`
  - `engine/graph/graph_builder.py`
  - `engine/graph/merge_existing.py`
  - `engine/graph/metastable.py`
  - `engine/graph/plots.py`
  - `engine/graph/labels.py`
  - `engine/graph/microstates.py`
  - `engine/graph/report.py`
  - `engine/graph/core.py`
  - `engine/graph/__init__.py`
  - `engine/api_records.py`
  - `engine/io.py`
  - `engine/sanity.py`
  - `engine/validation_gate.py`
  - `engine/forecast.py`
  - `engine/finance_utils.py`
  - `engine/preprocess.py`
  - `engine/report.py`
  - `engine/adapters/ons.py`
  - `engine/features/phase_features.py`
  - `engine/temporal/temporal_engine.py`
  - `engine/temporal/__init__.py`
  - `engine/diagnostics.py`
  - `engine/diagnostics/auto_regime_model.py`
  - `engine/diagnostics/macro_context.py`
  - `engine/diagnostics/predictability.py`
  - `engine/diagnostics/regime_labels.py`

## Regras de seguranca
- Nao fazer big-bang.
- Migrar por blocos funcionais pequenos.
- Cada bloco deve manter compatibilidade externa (`engine.*` continua estavel).
- Produzir rollback simples (reverter commit do bloco).

## Guardrails obrigatorios
1. Rodar auditoria:
   - `python tools/engine_purity_audit.py`
2. Trava de regressao:
   - `pytest -q tests/test_engine_purity_budget.py`
3. Verificacao operacional minima:
   - pipeline daily/snapshot
   - endpoints de `website-ui` que dependem do bloco migrado

## Fases

### Fase 0: Congelar superficie
- Congelar API publica de `engine/__init__.py`.
- Proibir novos imports de `spa`/`graph_engine` dentro de `engine/`.
- Saida: budget nao aumenta.

### Fase 1: Graph Core
- Migrar primeiro `engine/graph/*` (core, schema, export, diagnostics).
- Substituir `from graph_engine...` por implementacao local em `engine/graph/*`.
- Manter wrappers em `graph_engine/` apontando para `engine.graph.*` (inversao da dependencia).
- Saida: `engine_to_graph_engine_refs == 0`.

### Fase 2: Temporal + Forecasting
- Migrar `engine/temporal/*`, `engine/forecasting/*`, `engine/models/*`.
- Eliminar dependencia de `spa.engine.temporal_engine` e `spa.forecasting`.
- Saida: blocos temporais e forecast 100% locais.

### Fase 3: Diagnostics + IO/Preprocess
- Migrar `engine/diagnostics/*`, `engine/io.py`, `engine/preprocess.py`, `engine/report.py`.
- Normalizar imports internos para `engine.*`.
- Saida: `engine_to_spa_refs == 0`.

### Fase 4: Compatibilidade reversa
- Manter `spa/` e `graph_engine/` apenas como wrappers.
- Wrappers devem importar de `engine.*` (nunca o contrario).
- Saida: dependencia unidirecional `legacy -> engine`.

## Ordem recomendada de trabalho por modulo
1. Copiar implementacao legado para modulo-alvo em `engine/`.
2. Ajustar imports internos para `engine.*`.
3. Adicionar/atualizar teste do modulo.
4. Validar `website-ui` nas rotas que usam o modulo.
5. Remover import legado daquele modulo.
6. Atualizar baseline (reduzindo contagem).

## Criterio de pronto do Core Puro
- `python tools/engine_purity_audit.py --json` retorna `total_legacy_imports = 0`.
- `engine/` nao importa `spa` nem `graph_engine`.
- `spa/` e `graph_engine/` viram somente camada de compatibilidade.
- pipeline operacional e dashboard continuam funcionais.
