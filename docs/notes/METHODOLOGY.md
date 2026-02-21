# Metodologia do Motor (Estado Atual)

Documento metodologico operacional do motor de regimes e risco.

## Objetivo
Detectar mudancas estruturais e regime de risco com auditabilidade.
Nao e motor de previsao de preco por si so.

## Camadas
1. Dados:
- ingestao por dominio
- normalizacao
- checagem de adequacao

2. Dinamica:
- embedding
- microestados
- transicoes
- entropia e persistencia

3. Operacional:
- score de confianca/qualidade
- gate por dominio
- status `validated/watch/inconclusive`

## Regras essenciais
- Data adequacy gate obrigatorio antes do diagnostico.
- Gate adaptativo por dominio/ativo (sem threshold global unico).
- Histerese de status para evitar troca diaria espuria.
- Regime com calibracao causal walk-forward (limiares em t usam apenas historico ate t-1).
- Saida padronizada para API e auditoria.

## Evidencia minima exigida
- Sanity
- Robustez
- Placebo/ablation
- Drift diario
- Auditoria por run

## Artefatos canonicos
- `results/ops/snapshots/<run_id>/api_snapshot.jsonl`
- `results/ops/snapshots/<run_id>/summary.json`
- `results/ops/snapshots/<run_id>/audit_pack.json`
- `results/validation/VERDICT.json`

## Documentacao relacionada
- `README.md`
- `docs/notes/SCOPE.md`
- `docs/notes/BUSINESS_OUTCOME.md`
- `docs/ENGINE_GUIDE.md`
- `docs/OPS_EXECUTION_FLOW.md`
- `docs/INDEX.md`
