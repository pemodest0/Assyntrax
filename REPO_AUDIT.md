# REPO_AUDIT

Inventario rapido do repositorio (nao altera nada).

## Pastas principais (topo)
- `.git/`: metadados do git.
- `api/`: backend/API (conteudo nao auditado em detalhe).
- `config/`: configuracoes do pipeline (ex.: safe_mode).
- `dados/`: datasets legados e configuracoes antigas.
- `data/`: dados atuais do SPA (raw/processed, geo).
- `examples/`: demos de uso do SPA.
- `experiments/`: scripts de backtest e estudos.
- `legado/`: resultados e artefatos antigos.
- `results/`: saidas atuais (tmp, figs, bench, walkforward).
- `scripts/`: utilitarios e runners.
- `spa/`: codigo principal do produto SPA.
- `tests/`: testes de fumaça e previsibilidade.
- `venv/`: ambiente virtual (nao versionar).
- `website/`: site/portfolio e assets.
- `n sei c pode exluir/`: pasta sem contexto (verificar manualmente).

## Arquivos de produto (codigo fonte)
- `spa/` (core).
- `experiments/`, `scripts/` (execucao e pesquisa).
- `tests/`.
- `website/` (HTML/CSS/JS).

## Dados e artefatos
- Dados brutos/legados: `dados/`, `data/raw/`.
- Dados processados: `data/processed/`, `results/_tmp/`.
- Artefatos de execucao: `results/` (figs, walkforward, bench).
- Assets do site: `website/assets/`.
- Cache local: `data/yfinance_cache/`, `results/_tmp/`, `venv/`.

## Lixo/temporario (nao versionar)
- `venv/`
- `results/_tmp/`
- `results/_figs/`
- `results/walkforward/`
- `data/yfinance_cache/`
- `scripts/__pycache__/`, `spa/__pycache__/`

## Duplicatas e possiveis redundancias
- Muitos scripts no `scripts/` parecem sobrepostos (varias rotinas de backtest/forecast).
- `dados/` e `data/` coexistem com funcoes parecidas (legado vs atual).
- `results/` contem artefatos duplicados de runs anteriores (ex.: forecasts/PNGs em `_tmp`).
- `website/` contem paginas antigas (`produtos.html`, `bot.html`) que nao sao mais foco.
- `data/raw/ONS/ons_carga_diaria/` tem anos individuais + agregados.
- `website/assets/spa_energy/br_uf.geojson` duplica `data/geo/br_uf.geojson`.

## Mudancas recentes (git status)
Existe grande volume de arquivos marcados como deletados/modificados (provavel reestrutura antiga).
Tambem ha muitos arquivos nao rastreados (incluindo `results/`, `data/`, `website/assets/`, `venv/`).
Isso sugere um repo com historico legado + muitos artefatos locais.

## O que nao deveria ir para commit
- `venv/`
- `results/**`
- `data/yfinance_cache/**`
- `results/_tmp/**`
- PNGs/ZIPs grandes e caches
- `__pycache__/`

## Candidatos claros a exclusao (sujeito a confirmacao)
- `venv/`
- `results/_tmp/`
- `results/_figs/`
- `results/walkforward/`
- `results/bench_finance/`, `results/phase/`, `results/market_data_*`, `results/gpt_reports/`
- `data/yfinance_cache/`
- `results/_lab/ons_samples/`
- `website/assets/spa_energy/ons_2016_2025.zip` (se for apenas bundle intermediario)
- `website/bot.html`, `website/bot.js`, `website/produtos.html`
- `n sei c pode exluir/`

## Itens para decisao (nao apagar sem OK)
- `dados/` (legado grande; pode mover para `legado/` ou excluir)
- `legado/` (manter historico ou remover)
- `data/raw/ONS/ons_carga_diaria/*.csv` (manter apenas agregado?)
- `website/assets/spa_energy/report.pdf` e `engine_summary.pdf`
- `author.png`

## Recomendacoes (sem executar)
1) Definir politica clara de `results/` e `data/` no `.gitignore` (incluir `venv/`).
2) Consolidar dados ONS (manter um arquivo agregado e remover anos individuais).
3) Mover/arquivar legados antigos para `legado/` e manter o core em `spa/`.
4) Padronizar pipelines ativos em `experiments/` e remover scripts redundantes.
5) Limpar `website/` deixando apenas as paginas do portfolio atual.
6) Revisar `n sei c pode exluir/` e decidir destino.
7) Usar `scripts/cleanup_repo.ps1` ou `scripts/cleanup_repo.sh` para limpeza segura.
6) Revisar a pasta `n sei c pode exluir/` e decidir destino.
