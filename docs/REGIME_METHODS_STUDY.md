# Métodos para detecção de regimes dinâmicos

Este documento consolida o estudo conceitual do motor de regimes baseado em
dinâmica não-linear e modelos de Markov. Ele serve como base teórica para a
implementação da via paralela `graph_engine/`.

## 1. Reconstrução de espaço de fase (Takens)

O teorema de Takens garante que, para um sistema determinístico suave com
atrator de dimensão d, um vetor de atraso com dimensão M > 2d é difeomorfo ao
atrator original. Em termos práticos, isso significa que amostras sucessivas
da série podem reconstruir topologicamente a dinâmica original.

**Limitações práticas:** o teorema vale idealmente sem ruído. Em dados reais,
o ruído distorce a geometria do espaço reconstruído. Estudos clássicos apontam
que, com ruído significativo ou alta dimensionalidade caótica, a reconstrução
se degrada e a série se torna efetivamente aleatória.

**Parâmetros críticos:**
- Atraso τ: recomendado via autocorrelação ou informação mútua.
- Dimensão M: recomendado via vizinhos falsos (FNN) ou heurísticas.

---

## 2. Agrupamento em microestados

Após o embedding, os pontos no espaço de fase são agrupados em microestados
discretos. Em Markov State Models (MSM), isso é feito por clusterização
geométrica (K-means, k-centers). Cada microestado representa uma região local
da dinâmica.

**Objetivo:** discretizar a trajetória contínua em uma sequência simbólica
de microestados.

---

## 3. Matriz de transição e métricas de rede

Da sequência de microestados, constrói-se a matriz de transição P (Markov)
entre estados. Cada elemento T_ij representa a probabilidade de transitar de
i para j em um passo de tempo.

**Métricas principais:**
- Stay_prob = T_ii
- Escape_prob = 1 - T_ii
- LCC ratio: proporção no maior componente conectado
- Entropia: reflete imprevisibilidade
- Cobertura: fração de estados visitados
- Fração de baixo grau: nós com grau <= 1

---

## 4. Clustering espectral e estados metastáveis

A análise espectral de P revela regimes metastáveis. Em sistemas multiestáveis,
P é quase blocodiagonal, com autovalores próximos de 1 correspondendo a
regimes lentos.

Métodos como PCCA+ ou clustering espectral são usados para agrupar microestados
em macrostados (regimes).

---

## 5. Classificação de regimes

Com as métricas calculadas, cada estado é rotulado:

- **ESTÁVEL:** stay_prob alto, escape baixo, baixa entropia.
- **TRANSIÇÃO:** métricas intermediárias, ponte entre regimes.
- **INSTÁVEL:** escape alto + sinais de estiramento/entropia.
- **RUIDOSO:** baixa cobertura e baixa qualidade estrutural.

Os limiares são geralmente definidos por percentis (quantis), pois não há
patamares universais na literatura.

---

## 6. Pipeline computacional replicável

1) Pré-processar a série (normalização, limpeza).  
2) Escolher τ e M (ACF/mútua, FNN).  
3) Construir embedding Takens.  
4) Clusterizar em microestados.  
5) Construir matriz P.  
6) Calcular métricas (stay, escape, entropia, conectividade).  
7) Aplicar clustering espectral (metastável).  
8) Rotular regimes e gerar relatórios.  

---

## 7. Visualização e interface web

Recomenda-se dashboards com:
- Espaço de fase (2D/3D) colorido por regime
- Série temporal com faixas de regime
- Grafo de microestados (transições)
- Filtros por confiança/entropia

---

## Conclusão

O motor é fundamentado em dinâmica não-linear e MSM. A maior limitação é a
escolha de parâmetros (τ, M, K) e limiares de classificação. Esses valores
devem ser ajustados empiricamente para cada domínio.

