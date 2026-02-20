# Motor: Status Atual (simples)

## O que foi feito agora
- Pacote local montado com 41 ativos e 204861 linhas em dias uteis.
- Regras de validade adicionadas no motor:
  - limite de janela insuficiente por horizonte,
  - minimo de ativos usados por dia,
  - limite matematico T dividido por ativos usados,
  - calendario em dias uteis.
- Simulacoes do laboratorio e clusters globais rerodadas.
- Simulador temporal corrigido para nao usar futuro sem querer.

## Resultado do motor local (pesquisa)
- Status: `fail`
- Bloqueado: `True`
- Motivos: qa_failed, baseline_universe_mismatch, baseline_delta_p1_exceeds_threshold, baseline_delta_deff_exceeds_threshold
- Nucleo usado: 41 ativos
- Robustez 60 dias: 0.467
- Retorno anual (estrategia): 0.0536
- Retorno anual (referencia): 0.0764
- Queda maxima (estrategia): -0.2026
- Queda maxima (referencia): -0.2772
- Checks que falharam: T60_insufficient_ratio, T120_insufficient_ratio, T252_insufficient_ratio

## Resultado oficial publicado (mais confiavel)
- Run: `20260213T074220Z` | status: `ok` | bloqueado: `False`
- Nucleo usado: 477 ativos
- Retorno anual (estrategia): 0.0169
- Retorno anual (referencia): 0.0781
- Queda maxima (estrategia): -0.1956
- Queda maxima (referencia): -0.4212

## Clusters globais (conjunto de ativos)
### Metodo auto
- Amostras: 1793 | ativos: 41 | grupos: 3
- Troca de grupo entre dias: 0.640
- Novidade media: 1.192 | novidade p99: 4.408
- Distribuicao: g0=619 (34.5%), g1=621 (34.6%), g2=553 (30.8%)

### Metodo kmeans
- Amostras: 1793 | ativos: 41 | grupos: 8
- Troca de grupo entre dias: 0.884
- Novidade media: 1.195 | novidade p99: 4.644
- Distribuicao: g0=242 (13.5%), g1=226 (12.6%), g2=221 (12.3%), g3=239 (13.3%), g4=89 (5.0%), g5=289 (16.1%), g6=251 (14.0%), g7=236 (13.2%)

### Metodo hdbscan
- Amostras: 1793 | ativos: 41 | grupos: 1
- Troca de grupo entre dias: 0.000
- Novidade media: 1.000 | novidade p99: 1.000
- Distribuicao: g-1=1793 (100.0%)

## Simulador temporal (antes e depois da correcao)
- Antes da correcao, um modelo mostrava erro quase zero no horizonte de 1 dia (irreal).
- Depois da correcao, os numeros ficaram plausiveis.
### Alvo return
- h=1: antes knn_phase (erro 0.00000049, ganho 1.000) | depois markov_phase (erro 0.01736551, ganho 0.311)
- h=5: antes markov_phase (erro 0.01731678, ganho 0.337) | depois markov_phase (erro 0.01732074, ganho 0.337)
- h=20: antes markov_phase (erro 0.01754295, ganho 0.296) | depois markov_phase (erro 0.01754630, ganho 0.295)

### Alvo volatility
- h=1: antes knn_phase (erro 0.00000011, ganho 1.000) | depois persist (erro 0.00086235, ganho 0.000)
- h=5: antes knn_phase (erro 0.00248508, ganho 0.156) | depois persist (erro 0.00294583, ganho 0.000)
- h=20: antes markov_phase (erro 0.00653413, ganho 0.158) | depois markov_phase (erro 0.00657975, ganho 0.152)

## Verdades e limites
- O motor e bom para defesa de risco, nao para prometer retorno maior sempre.
- Em universo menor, o bloqueio precisa acontecer e aconteceu.
- O agrupamento global existe, mas ainda troca de estado rapido demais para decisao diaria sem filtro extra.
- O run oficial com universo grande segue sendo a base mais confiavel para comunicar para fora.
