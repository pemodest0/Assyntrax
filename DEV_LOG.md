# DEV_LOG — Stochastic Process Analyzer (SPA)

Registro diario do desenvolvimento tecnico do projeto.
Este arquivo e cronologico e nao normativo.
Decisoes finais e escopo congelado devem estar em AGENT_MEMORY.md.

---

## 2026-01-21

### Objetivo do dia
- Transformar o relatório em case de portfólio.

### O que foi feito
- Texto passou a ser narrativo, direto e confiante.
- Estrutura do PDF reorganizada como apresentação: capa, problema, método, visão do Brasil, comparação e detalhes.

### O que foi mudado
- Atualizado `spa/report.py` para tom de portfólio e narrativa profissional.

### Ideias / insights do momento
- Comunicação clara aumenta a percepção de valor do produto.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Relatório com linguagem de produto/demo e apresentação consistente.

---
## 2026-01-21

### Objetivo do dia
- Refinar o relatório com mapa por 4 regiões e sem heatmap.

### O que foi feito
- Dissolução das UFs em 4 regiões grandes (N, NE, SE/CO, S) usando GeoJSON real.
- Remoção do heatmap do relatório e expansão para mais páginas com detalhes por subsistema.
- Geração de placar por subsistema para inspeção.

### O que foi mudado
- Atualizado `spa/report.py` para mapa dissolvido e relatório completo.
- Atualizado `spa/run.py` para gerar `placar_subsistemas.json`.

### Ideias / insights do momento
- Mapa por regiões reduz ruído visual e melhora compreensão.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Relatório mais completo com mapa real por regiões.

---
## 2026-01-20

### Objetivo do dia
- Reestruturar o relatório com mapa por 4 regiões e mais conteúdo.

### O que foi feito
- Mapa com regiões dissolvidas (N, NE, SE/CO, S) usando GeoJSON real.
- Remoção completa do heatmap e expansão do relatório para várias páginas.
- Placar por subsistema com médias, meses de pico/vale e variabilidade.

### O que foi mudado
- Atualizado `spa/report.py` para mapa real por região e nova estrutura de páginas.
- Atualizado `spa/run.py` para gerar `placar_subsistemas.json`.

### Ideias / insights do momento
- Visual limpo e hierárquico melhora compreensão executiva.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Relatório com mapa real por regiões e narrativa completa.

---
## 2026-01-20

### Objetivo do dia
- Substituir o mapa inventado por geometria real do Brasil.

### O que foi feito
- Adicionado GeoJSON real de estados e mapeamento para regiões do ONS.
- Mapa agora usa geometria real com cores por demanda média.

### O que foi mudado
- Atualizado `spa/report.py` para ler `data/geo/br_uf.geojson` e gerar `mapa_brasil.png`.

### Ideias / insights do momento
- Usar geometrias reais melhora confiança visual.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Mapa com base geográfica real, nível relatório profissional.

---
## 2026-01-20

### Objetivo do dia
- Redefinir o relatório para visualização global simples.

### O que foi feito
- Mapa do Brasil com regiões reais e cor por demanda média anual.
- Heatmap único do Brasil por região e mês.

### O que foi mudado
- Atualizado `spa/report.py` para usar apenas mapa e heatmap global como visuais principais.

### Ideias / insights do momento
- Visual direto ajuda a leitura não técnica.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Relatório com dois visuais principais e síntese clara.

---
## 2026-01-20

### Objetivo do dia
- Reorganizar o relatório para priorizar visualização hierárquica.

### O que foi feito
- Mapa esquemático do Brasil por subsistema e heatmaps anuais.
- Relatório passa a começar pelo panorama nacional e depois detalha o tempo.

### O que foi mudado
- Atualizado `spa/report.py` com mapa, heatmaps e nova ordem de páginas.

### Ideias / insights do momento
- Visual hierárquico facilita leitura para não técnicos.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Relatório com foco visual e hierarquia clara de informação.

---
## 2026-01-20

### Objetivo do dia
- Tornar o método explícito: análise por subsistema, comparação e síntese.

### O que foi feito
- Pipeline reorganizado para analisar cada subsistema separadamente.
- Comparação entre subsistemas e síntese do sistema sem soma cega.

### O que foi mudado
- Atualizado `spa/run.py` para gerar `summary_<subsistema>.json` e `summary_system.json`.
- Atualizado `spa/report.py` para relatório com visão geral, comparação e detalhes por subsistema.

### Ideias / insights do momento
- Priorizar a leitura individual antes de consolidar o sistema.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Método individual → comparação → síntese aplicado no pipeline.

---
## 2026-01-20

### Objetivo do dia
- Tornar explícito como as regiões do ONS entram na análise.

### O que foi feito
- Detecção automática das regiões presentes no arquivo.
- Texto narrativo explicando agregação/selecão e suas limitações.

### O que foi mudado
- Atualizado `spa/run.py` para registrar regiões e modo de análise no summary.
- Atualizado `spa/report.py` com seção “Como as regiões foram tratadas”.

### Ideias / insights do momento
- Sugerir análise por região quando houver suspeita local.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Relatório transparente sobre o tratamento das regiões.

---
## 2026-01-20

### Objetivo do dia
- Tornar o relatório narrativo e claro para pessoas não técnicas.

### O que foi feito
- Textos em português correto, com explicação do dado e do período analisado.
- Seções narrativas para situação atual, mudanças recentes e previsão curta.

### O que foi mudado
- Atualizado `spa/run.py` para incluir período, explicações e textos longos no summary.
- Atualizado `spa/report.py` para relatório em 2 páginas com narrativa completa.

### Ideias / insights do momento
- Manter o foco em clareza antes de qualquer aprofundamento técnico.

### Dificuldades / dúvidas
- Nenhuma.

### Entregável mínimo do dia
- Relatório legível, explicativo e com período analisado explícito.

---
## 2026-01-20

### Objetivo do dia
- Corrigir sobreposicao de texto no PDF.

### O que foi feito
- Ajuste de layout com blocos de texto unicos e espacos reservados.

### O que foi mudado
- Atualizado `spa/report.py` para usar `wrap=True` e layout vertical organizado.

### Ideias / insights do momento
- Evitar varios `text()` pequenos para blocos longos.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- PDF legivel sem sobreposicao.

---
## 2026-01-20

### Objetivo do dia
- Fazer o relatorio explicar o dado antes de analisar.

### O que foi feito
- Texto simples explicando o que o numero significa.
- Comparacao com o normal recente e deteccao simples de mudanca.
- Previsao curta explicada com limite claro.

### O que foi mudado
- Atualizado `spa/run.py` com bloco "o_que_e_esse_numero" e comparacoes simples.
- Atualizado `spa/report.py` com paginas focadas em entendimento e visual.
- Mantida previsao simples e saida em `forecast.csv`.

### Ideias / insights do momento
- Reforcar a explicacao com exemplos de subsistema quando usar selecao.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Relatorio e summary explicaveis para leigos, em portugues simples.

---
## 2026-01-20

### Objetivo do dia
- Simplificar a saida e adicionar limpeza, previsao e relatorio claro.

### O que foi feito
- Nomes simples no summary e no relatorio.
- Limpeza opcional com controle de picos, preenchimento e duplicados.
- Previsao simples de curto prazo com saida em CSV.

### O que foi mudado
- Atualizado `spa/preprocess.py` com limpeza e contagem de ajustes.
- Criado `spa/forecast.py` para previsao simples.
- Atualizado `spa/run.py` com novos argumentos e summary em portugues simples.
- Atualizado `spa/report.py` com relatorio em 2 paginas e texto claro.

### Ideias / insights do momento
- Ajustar mensagens de observacoes conforme novos casos reais.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Pipeline explicavel, previsao simples e relatorio limpo via `--pdf`.

---
## 2026-01-20

### Objetivo do dia
- Ajustar politica de artefatos e evitar PDFs por padrao.

### O que foi feito
- Remocao de PDFs e graficos antigos em `results/`.
- PDF agora so gera com flag explicita.

### O que foi mudado
- Atualizado `spa/run.py` para gerar PDF apenas com `--pdf`.
- Atualizado `tests/test_smoke.py` para explicitar `--pdf`.

### Ideias / insights do momento
- Manter artefatos apenas quando aprovados.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Politica de artefatos aplicada e pipeline sem PDF por padrao.

---
## 2026-01-20

### Objetivo do dia
- Corrigir ingestao de CSVs ONS para evitar mistura por timestamp.

### O que foi feito
- Adaptador ONS para normalizar series por soma ou selecao de subsistema.
- CLI com flags para normalizacao ONS e filtros.

### O que foi mudado
- Criado `spa/adapters/ons.py` e `spa/adapters/__init__.py`.
- Atualizado `spa/preprocess.py` para normalizar ONS quando `--source ONS` ou colunas tipicas.
- Atualizado `spa/run.py` com `--source`, `--ons-mode` e `--ons-filter`.
- Atualizado `README.md` com uso de `--ons-mode` e exemplo real.

### Ideias / insights do momento
- Validar filtros por subsistema com dados diarios e horarios.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Normalizacao ONS antes de features e diagnosticos.

---

## 2026-01-20

### Objetivo do dia
- Iniciar vertical slice do SPA para energia com pipeline minimo e suporte ONS.

### O que foi feito
- Estrutura inicial do pacote `spa/` com IO, preprocessamento, features, diagnosticos e relatorio.
- CLI minima para rodar o pipeline em CSV local ou datasets ONS ja baixados.
- Downloader de datasets com configuracao de fontes.
- Demo sintetica e teste de fumaça.

### O que foi mudado
- Criados `spa/__init__.py`, `spa/io.py`, `spa/preprocess.py`, `spa/features.py`, `spa/diagnostics.py`, `spa/report.py`, `spa/run.py`.
- Criado `scripts/fetch_datasets.py` e `data_sources.json`.
- Criados `examples/energy_demo.py`, `tests/test_smoke.py`, `README.md`.
- Ajuste em `spa/io.py` para leitura com delimitador inferido (CSV do ONS).
- Ajuste em `spa/preprocess.py` para `ffill` sem warning.
- Ajuste em `spa/preprocess.py` para ignorar deltas zero no `dt`.

### Ideias / insights do momento
- Validar heuristicas de diagnostico com mais series reais antes de ajustar thresholds.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Pipeline minimo executando e pronto para CSVs do ONS.

---

---

## 2026-01-21

### Objetivo do dia
- Integrar serie historica e previsao 2025 no website do case SPA.

### O que foi feito
- Geracao de series reais 2000-2024 e previsoes 2025 por subsistema.
- Dashboard interativo no site com controles, KPIs, graficos e mapa por subsistema.
- Downloads consolidados com JSON/CSV/PDF/ZIP em assets.

### O que foi mudado
- Atualizados `website/case_spa_energy.html`, `website/index.html`, `website/portfolio.html`, `website/sobre.html`, `website/contato.html`.
- Atualizado `website/script.js` para consumir `manifest.json` e `series_full.json`.
- Atualizado `website/styles_modern.css` para layout do dashboard.
- Criados `website/assets/spa_energy/series_full.json`, `metrics_2024.json`, CSVs e `spa_energy_outputs.zip`.
- Atualizado `website/assets/spa_energy/manifest.json`.
- Atualizado `README.md` com nota de teste via http.server.

### Ideias / insights do momento
- Separar real vs previsao melhora entendimento e confianca.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Site com dashboard interativo e downloads consistentes.

---

## 2026-01-21

### Objetivo do dia
- Criar resumo do motor e ajustar a area do dashboard no site.

### O que foi feito
- Gerado PDF separado com resumo do motor, metodos e confianca.
- KPI de confianca adicionado ao dashboard, baseado no MAPE 2024.
- Ajustado texto do dashboard para destacar retorno do motor e previsao 2025.

### O que foi mudado
- Criado `website/assets/spa_energy/engine_summary.pdf` e atualizado ZIP.
- Atualizados `website/case_spa_energy.html` e `website/script.js`.
- Atualizado `AGENT_MEMORY.md` com novo arquivo.

### Ideias / insights do momento
- Confianca explicita melhora leitura de previsao para nao tecnicos.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- PDF de resumo do motor e dashboard com confianca 2025.

---

## 2026-01-21

### Objetivo do dia
- Gerar series 10 anos a partir de processed_* e atualizar o dashboard.

### O que foi feito
- Criado series_10y.json com agregacoes diaria, mensal e anual (2016-2024).
- Dashboard atualizado para usar series_10y.json, com selecao de resolucao e ano do mapa.
- Downloads e manifest atualizados para incluir series_10y.json.

### O que foi mudado
- Criado `website/assets/spa_energy/series_10y.json`.
- Atualizados `website/case_spa_energy.html`, `website/script.js`, `website/assets/spa_energy/manifest.json`.

### Ideias / insights do momento
- Separar resolucoes melhora leitura da tendencia de longo prazo.

### Dificuldades / duvidas
- Processed_* inicia em 2016, sem dados 2015.

### Entregavel minimo do dia
- Dashboard com serie 10 anos e mapa por ano.

---

## 2026-01-21

### Objetivo do dia
- Exibir confianca por subsistema e previsao 2025 com selecao de modelo.

### O que foi feito
- Gerados forecasts 2025 por kNN e LSTM e metricas por subsistema.
- Dashboard com grafico de confianca (1 - MAPE) e selecao de modelo.
- Linha de previsao 2025 adicionada ao grafico principal.

### O que foi mudado
- Criados `website/assets/spa_energy/forecast_2025_knn.json`, `forecast_2025_lstm.json`, `metrics_models.json`.
- Atualizados `website/case_spa_energy.html`, `website/script.js`, `website/styles_modern.css`.
- Atualizado `website/assets/spa_energy/manifest.json` e `spa_energy_outputs.zip`.

### Ideias / insights do momento
- Comparar modelos aumenta transparencia do motor.

### Dificuldades / duvidas
- Series processed_* iniciam em 2016.

### Entregavel minimo do dia
- Dashboard com confianca por subsistema e previsao 2025 por modelo.

---

## 2026-01-21

### Objetivo do dia
- Adicionar atrator 3D e horizonte de previsibilidade no motor e no dashboard.

### O que foi feito
- Gerados JSONs de atrator 3D por subsistema e resolucao.
- Gerados JSONs de horizonte de previsibilidade (h vs erro) para 2024.
- Dashboard atualizado com visualizacoes interativas de atrator e previsibilidade.

### O que foi mudado
- Criados `website/assets/spa_energy/attractor_*.json` e `predictability_*.json`.
- Atualizados `website/case_spa_energy.html`, `website/script.js`, `website/styles_modern.css`.
- Atualizados `manifest.json` e `spa_energy_outputs.zip`.
- Criado `tests/test_predictability.py` e atualizado `README.md`.
- Atualizado `AGENT_MEMORY.md`.

### Ideias / insights do momento
- Atrator 3D facilita leitura de padroes dinamicos sem jargao.

### Dificuldades / duvidas
- Processed_* inicia em 2016, sem dados 2015.

### Entregavel minimo do dia
- Dashboard com atrator 3D e horizonte de previsibilidade.


## 2026-01-21

### Objetivo do dia
- Criar o Lorenz Lab como laboratorio visual para validar o motor.

### O que foi feito
- Geracao de dados do sistema de Lorenz (true e observado) em JSON.
- Nova pagina `lab_lorenz.html` com controles de tau, m, k, horizonte e proje??o.
- Graficos Plotly: atrator real, atrator reconstruido, serie real vs prevista e erro vs horizonte.
- Integracao no site com link de navegacao e card no portfolio.

### O que foi mudado
- Criados `scripts/lab_generate_lorenz.py`, `website/lab_lorenz.html`, `website/lab_lorenz.js`.
- Criados `website/assets/lab_lorenz/lorenz_true.json`, `lorenz_observed.json`, `data_bundle_lorenz.js`.
- Atualizados `website/index.html`, `website/portfolio.html`, `website/sobre.html`, `website/contato.html`.
- Atualizado `README.md` com comando de geracao do Lorenz Lab.

### Ideias / insights do momento
- O Lorenz Lab torna visivel o limite do modelo local em dinamicas caoticas.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Pagina Lorenz Lab funcional com controles e plots interativos.

---


## 2026-01-21

### Objetivo do dia
- Pausar o site interativo e gerar PNGs para validacao rapida.

### O que foi feito
- Script de figuras para comparar real vs previsto e erros anuais por subsistema.
- Tabelas e embeddings em PNG para inspecao no VS Code.
- Script de limpeza para apagar `results/_figs/` com flag.

### O que foi mudado
- Criados `scripts/generate_figures.py` e `scripts/clean_figs.py`.
- Atualizado `README.md` com comando de geracao de figuras.

### Ideias / insights do momento
- PNGs simples aceleram a revisao visual sem depender do site.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Figuras salvas em `results/_figs/energy/`.

---


## 2026-01-21

### Objetivo do dia
- Criar runner padrao para benchmarks em PNG/CSV sem site.

### O que foi feito
- Runner `lab_run.py` para yfinance e energia com Takens+kNN.
- Modulo compartilhado `spa/models/takens_knn.py`.
- Scripts de suporte para yfinance (fetch/load) e limpeza de tmp.

### O que foi mudado
- Criados `scripts/lab_run.py`, `scripts/yf_fetch_or_load.py`, `scripts/clean_tmp.py`.
- Criado `spa/models/takens_knn.py`.
- Atualizado `scripts/yf_chaos_benchmark.py` (bias e outdir) e `scripts/generate_figures.py` (backend).

### Ideias / insights do momento
- Runner unico facilita rodar e sair sem precisar do site.

### Dificuldades / duvidas
- Nenhuma.

### Entregavel minimo do dia
- Resultados em `results/_figs/{domain}/` com resumo em `_summary/benchmark_summary.csv`.

---

## 2026-01-22

### Objetivo do dia
- Preparar o repo para commit com limpeza e estrutura minima do motor.

### O que foi feito
- Atualizado `.gitignore` para ignorar caches e resultados locais.
- Criados scripts de limpeza para Windows e macOS.

### O que foi mudado
- Atualizado `.gitignore`.
- Criados `scripts/cleanup_repo.ps1` e `scripts/cleanup_repo.sh`.
- Atualizado `AGENT_MEMORY.md` com politica de limpeza.

### Ideias / insights do momento
- Cleanup deve focar em manter apenas o motor e dados essenciais.

### Dificuldades / duvidas
- Remocao de pastas grandes depende de confirmacao explicita.

### Entregavel minimo do dia
- Scripts de limpeza prontos e politica registrada.
