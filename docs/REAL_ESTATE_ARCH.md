# Assyntrax + Mercado Imobiliario (Brasil)

Este documento converte a pesquisa enviada em um plano pratico de implementacao
apoiado no que ja existe no repo. As equacoes sao mantidas em formato LaTeX.

## 1) Dados recomendados
Fontes citadas e como encaixar:
- FipeZap (preco de oferta): usar como serie principal por cidade/bairro.
- IVAR (FGV): serie complementar (contratos reais).
- SBPE/ABECIP (credito): series auxiliares para CRQA e regime.
- Selic/BCB: forca exogena (parametro de transicao).

Sugestao de armazenamento:
```
data/raw/realestate/
  fipezap_sp.csv
  fipezap_rj.csv
  ivar_sp.csv
  sbpe_credito.csv
  selic.csv
```

## 2) Equacoes (copiadas)

### 2.1 Embedding de Takens
$$
s_n = (x_n, x_{n-\tau}, x_{n-2\tau}, \dots, x_{n-(m-1)\tau})
$$

### 2.2 Fokker-Planck (drift/difusao)
$$
\frac{\partial P}{\partial t} = -\frac{\partial}{\partial x}[D^{(1)}(x)P]
 + \frac{\partial^2}{\partial x^2}[D^{(2)}(x)P]
$$

### 2.3 Recurrence Plot
$$
R_{i,j} = \Theta(\epsilon - \|\vec{s}_i - \vec{s}_j\|)
$$

### 2.4 Transfer Entropy
$$
TE_{X \to Y} = \sum P(y_{t+1}, y_t^{(k)}, x_t^{(l)}) \log
\frac{P(y_{t+1} | y_t^{(k)}, x_t^{(l)})}{P(y_{t+1} | y_t^{(k)})}
$$

### 2.5 HMM (transicao)
$$
P(S_{t+1} = j | S_t = i) = a_{ij}
$$

### 2.6 Von Neumann Graph Entropy (VNGE)
$$
E_{vne} = - \mathrm{Tr}(\rho \ln \rho) = -\sum_i \lambda_i \ln \lambda_i
$$

## 3) Como implementar com o que ja existe

### 3.1 Embedding e parametros (tau, m)
Ja existe:
- `graph_engine/embedding.py`
  - AMI para tau
  - Cao/FNN para m
  - `takens_embed`

Acao:
- Usar `estimate_embedding_params(series)` nas series FipeZap/IVAR.

### 3.2 RQA (DET/LAM/TT)
Ja existe:
- `graph_engine/diagnostics.py` -> `_rqa_metrics`
Acao:
- Aplicar em janelas deslizantes (por cidade).

### 3.3 Regimes por microestado + HMM
Ja existe:
- `graph_engine/microstates.py` (HDBSCAN + HMM smoothing)
- `graph_engine/labels.py` (smoothing de labels)

Acao:
- Rodar `run_graph_regime_universe.py` com series imobiliarias.
- Usar `--micro-method hdbscan_hmm --micro-smooth hmm`.

### 3.4 Drift/Difusao (Kramers-Moyal)
Nao existe completo ainda.
Sugestao:
- Criar script `scripts/realestate/run_km_drift_diffusion.py`
- Usar bibliotecas `kramersmoyal` ou implementar estimador simples
  com momentos condicionais.

### 3.5 Entropia de grafo e TE
Parcial:
- Estruturas de grafos ja existem em `graph_engine`.
Sugestao:
- Criar `scripts/realestate/build_te_graph.py` para TE entre cidades.
- Calcular VNGE via espectro do Laplaciano (NetworkX).

## 4) Pipeline proposto (Fase 1)

1. Normalizar series (FipeZap/IVAR/SBPE/Selic).
2. Calcular tau/m (AMI + Cao).
3. Embedding + microestados (HDBSCAN+HMM).
4. RQA em janelas (DET/LAM/TT).
5. Regimes finais + labels para decisao.

## 5) Proximos passos tecnicos
- Implementar ingestao (fetch) de FipeZap/IVAR/SBPE.
- Adicionar rotina de CRQA entre preco e credito.
- Adicionar TE para redes entre cidades.

Este documento serve como ponte entre a teoria e o core atual do repo.
