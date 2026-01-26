# Metodologia Progressiva para Sistemas Dinâmicos

Este documento define um currículo de dificuldade crescente e um pipeline padronizado
para simular, analisar e rotular regimes em séries dinâmicas univariadas. O objetivo é
aplicar o mesmo processo a muitos sistemas, reduzindo erros e garantindo reprodutibilidade.

## 1) Currículo de Dificuldade

1. **Nível 0 (Linear/Quase‑linear)**  
   Ex.: oscilador harmônico, amortecimento simples.  
   Foco: periodicidade e estabilidade.
2. **Nível 1 (Não‑linear moderado)**  
   Ex.: pêndulo simples, Duffing fraco.  
   Foco: não‑linearidade suave e transições.
3. **Nível 2 (Não‑linear forçado)**  
   Ex.: Duffing forçado + amortecido.  
   Foco: regimes estáveis e transições complexas.
4. **Nível 3 (Caos clássico)**  
   Ex.: mapa logístico, Lorenz, Rössler.  
   Foco: sensibilidade às condições iniciais, atratores caóticos.
5. **Nível 4 (Séries reais)**  
   Ex.: sensores, financeiro, energia.  
   Foco: ruído, gaps, não estacionaridade.

## 2) Pipeline Padrão (Checklist)

1. **Definição do sistema e contexto**
2. **Simulação (ou carregamento)**
3. **Validação rápida**
4. **Visualizações iniciais**
5. **Embedding (m, τ) + métricas (entropia/recorrência)**
6. **Clusterização + rotulagem física**
7. **Relatórios e arquivos**
8. **Variação de parâmetros (benchmark)**
9. **Documentação dos insights**
10. **Transição para o próximo caso**

## 3) Prompts Base para o Codex

### 3.1 Definição do Sistema
```
Você agora irá analisar o sistema <NOME> descrito pela equação:
<EQUAÇÃO>. O objetivo é entender o comportamento de regimes e suas transições.
Use o pipeline padrão e explique cada etapa brevemente.
```

### 3.2 Simulação
```
Implemente em Python a simulação do sistema <NOME> com parâmetros:
<LISTA DE PARÂMETROS>. Use integração numérica (ex.: RK4 ou Euler).
Gere x(t) com N passos e Δt = <dt>.
```

### 3.3 Validação
```
Valide rapidamente a simulação verificando consistência física
(ex.: energia quase constante quando amortecimento = 0).
Relate qualquer anomalia e ajuste se necessário.
```

### 3.4 Visualização Inicial
```
Gere gráficos de x(t) e retrato de fase. Calcule métricas simples
como período ou amplitude média. Comente o comportamento.
```

### 3.5 Embedding + Métricas
```
Faça varredura de (m, τ) em intervalos definidos. Calcule entropia
e recurrence rate. Selecione o melhor par usando entropia mínima
ou contraste máximo.
```

### 3.6 Clusterização + Rotulagem
```
Padronize o embedding. Aplique HDBSCAN/KMeans.
Calcule v(t), a(t) e energia proxy. Rotule regimes com base
em média de x, v e energia. Gere summary.csv e report.md.
```

### 3.7 Benchmark Paramétrico
```
Varie um parâmetro por vez (ex.: γ = 0.2, 0.5, 1.0).
Para cada variação, refaça simulação e análise e compare resultados.
Resuma como o parâmetro afeta regimes e transições.
```

### 3.8 Documentação de Insights
```
Resuma o que foi aprendido nesta etapa: regimes detectados,
parâmetros críticos e limitações observadas.
```

### 3.9 Transição
```
Agora avance para o próximo sistema, reduzindo o nível de orientação.
Use o aprendizado anterior como referência.
```

## 4) Critérios de Avanço

- Regimes interpretáveis por pelo menos 2 métodos.
- Entropia/recorrência coerentes com o comportamento observado.
- Relatório completo gerado sem ajustes manuais.

## 5) Resultados Esperados por Sistema

- `results/<sistema>_<metodo>/labels_over_time.png`
- `results/<sistema>_<metodo>/regime_map.png`
- `results/<sistema>_<metodo>/xv_regime.png`
- `results/<sistema>_<metodo>/entropy_vs_tau.png`
- `results/<sistema>_<metodo>/recurrence_plot.png`
- `results/<sistema>_<metodo>/summary.csv`
- `results/<sistema>_<metodo>/report.md`
- `results/report_<sistema>.pdf`

## 6) Observações

- Para sistemas desconhecidos, rotular regimes genericamente (`state_0`, `state_1`, …).
- Reduzir gradualmente as dicas nos prompts para aumentar autonomia do motor.
- Reutilizar métricas e parâmetros ótimos como “memória” entre etapas.
