# AGENT_MEMORY — Stochastic Process Analyzer (SPA)

## Projeto
Nome: Stochastic Process Analyzer (SPA)

Objetivo:
Analisar series temporais reais (tempo + metrica) como processos estocasticos
efetivos em tempo discreto. Nesta fase, o foco e a vertical de ENERGIA.

---

## Escopo atual (congelado)
- Series temporais 1D
- Pipeline minimo: leitura, preprocessamento, features, diagnosticos e relatorio
- Dados reais do ONS via CSV (download e normalizacao)
- Stack enxuta: numpy, scipy, pandas, matplotlib
- Saidas: CSV processado, JSON de resumo, PDF simples

---

## Restricoes importantes
- Nao implementar drift/difusao fisica ainda
- Evitar overengineering e dependencias extras
- Codigo simples, legivel e reutilizavel

---

## Nota sobre DEV_LOG
DEV_LOG.md e historico e nao normativo.

---

## Website / Dashboard (SPA Energy Visual Intelligence)
- Dashboard principal em `website/case_spa_energy.html` com controles de subsistema, resolucao e periodo.
- Toggle de previsao 2025 com linha tracejada e marcador de inicio de 2025.
- Mapa estilizado por subsistema (N, NE, SE/CO, S) com clique para selecionar.
- Dados e downloads em `website/assets/spa_energy/`:
  - `series_full.json` (series diaria/mensal/anual, real 2000-2024 + previsao 2025).
  - `metrics_2024.json` (MAE/RMSE/MAPE por subsistema e Brasil).
  - `daily_2000_2024.csv`, `monthly_2000_2024.csv`, `annual_2000_2024.csv`.
  - `forecast_2025_daily.csv`, `forecast_2025_monthly.csv`, `forecast_2025_annual.csv`.
  - `report.pdf`, `engine_summary.pdf`, `spa_energy_outputs.zip`.
  - `manifest.json` com paths e metadados.
  - `forecast_2025_knn.json`, `forecast_2025_lstm.json`, `metrics_models.json`.
  - `attractor_{res}_{sub}.json` (atrator 3D por embedding Takens).
  - `predictability_{res}_{sub}.json` (erro vs horizonte h em 2024).

---

## Website / Lorenz Lab (validacao do motor)
- Pagina `website/lab_lorenz.html` para explorar embedding e previsibilidade em sistema caotico.
- Dados em `website/assets/lab_lorenz/`:
  - `lorenz_true.json` (t, x, y, z) e `lorenz_observed.json` (t, obs = x).
  - `data_bundle_lorenz.js` para abrir via `file://` sem CORS.

---

## Repo cleanup (commit)
- Objetivo: reduzir o repo ao motor SPA e preparar para commit.
- Pastas a manter: `spa/`, `scripts/` (apenas utilitarios do motor), `experiments/`, `data/`, `tests/`, `config/`.
- Pastas candidatas a remocao: `website/`, `results/`, `dados/`, `legado/`, `api/`, `venv/`.
- Scripts de limpeza: `scripts/cleanup_repo.ps1` e `scripts/cleanup_repo.sh`.
