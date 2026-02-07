# Guia do Motor Assyntrax (Uso e Interpretação)

Este guia descreve como rodar o motor e interpretar as saídas principais.

## 1) Execução rápida (universo)
```
python3 scripts/bench/run_graph_regime_universe.py \
  --tickers "SPY,QQQ,GLD" \
  --timeframes daily,weekly \
  --mode heavy \
  --n-micro 800 \
  --n-regimes 6 \
  --k-nn 15 \
  --theiler 10 \
  --alpha 2.0 \
  --outdir results/latest_graph
```

## 2) Execução com embedding automático
```
python3 scripts/bench/run_graph_regime_universe.py \
  --tickers "SPY,QQQ,GLD" \
  --timeframes daily,weekly \
  --mode heavy \
  --auto-embed \
  --tau-method ami \
  --m-method cao \
  --outdir results/latest_graph
```

## 3) Interpretação de outputs

### 3.1 Regimes por ativo
Arquivos:
- `results/latest_graph/assets/{ASSET}_{TF}.json`
- `results/latest_graph/assets/{ASSET}_{TF}_plots/timeline_regime.png`

Interpretação:
- **STABLE**: dinâmica com maior previsibilidade.
- **TRANSITION**: sinais de mudança de regime (alerta).
- **UNSTABLE/NOISY**: ruído alto, baixa confiabilidade.

### 3.2 Embedding e microestados
Arquivos:
- `assets/{ASSET}_{TF}_embedding.csv`
- `embedding_2d.png`
Uso:
- Visualiza a geometria local do atrator.
- Densidade e dispersão ajudam a avaliar estabilidade.

### 3.3 Diagnósticos RQA
Extraídos em `graph_engine/diagnostics.py`:
- **DET** (determinismo): alto = maior previsibilidade.
- **LAM** (laminaridade): alto = mercado “travado”.
- **TT** (trapping time): persistência em estados.

### 3.4 Forecast por regime
Arquivos:
- `results/forecast_suite/{ASSET}/{TF}/{ASSET}_{TF}_log_return_h{H}.json`
Interpretação:
- `predictions`: lista de modelos.
- `auto_best` / `auto_best_ens`: melhores modelos por regime.

## 4) Boas práticas
- Comparar regimes com benchmarks oficiais (USREC, NFCI, VIX).
- Usar `--state-smooth hmm` para reduzir flicker.
- Evitar overfit: manter parâmetros de embedding com validação.

## 5) Troubleshooting
- Se falhar em embedding: verifique tamanho mínimo da série.
- Se o motor “oscilar”: aumente `theiler` e aplique smoothing HMM.
