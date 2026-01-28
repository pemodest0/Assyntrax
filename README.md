# Stochastic Process Analyzer (SPA) — Energia

SPA e um produto demo tecnico para analisar series temporais reais (tempo + metrica)
como processos estocasticos efetivos em tempo discreto. Nesta fase, o foco e energia
com uma vertical slice minima (sem drift/difusao).

## Estrutura

- `spa/` pipeline principal do motor (IO, preprocess, features, diagnosticos, relatorio).
- `spa/engine/` motor de regimes (antigo `temporal_engine/`).
- `scripts/` organizado por area:
  - `scripts/data/` ingestao e checagens de dados
  - `scripts/finance/` pipelines financeiros
  - `scripts/sim/` simulacoes e sinteticos
  - `scripts/bench/` benchmarks e avaliacao
  - `scripts/report/` geracao de relatorios/figuras
  - `scripts/engine/` execucoes do motor
  - `scripts/maintenance/` limpeza/manutencao
  - `scripts/lab/` experimentos locais
  - `scripts/utils/` utilitarios comuns
- `data/raw/` dados brutos baixados.
- `tests/` testes simples (opcionais).

## Baixar dados do ONS

Exemplo (curva de carga horaria 2024):

```bash
python scripts/data/fetch_datasets.py --source ONS --dataset ons_curva_carga_horaria --year 2024
```

O CSV sera salvo em `data/raw/ONS/ons_curva_carga_horaria/`.

## Rodar o SPA em CSV real

Alguns CSVs do ONS possuem multiplos registros por timestamp (ex: por subsistema).
Use `--source ONS` com `--ons-mode` para normalizar a serie 1D antes das features.

Modo `sum` agrega por timestamp (carga total). Modo `select` filtra um subsistema
com `--ons-filter`.

Exemplo real (CARGA_ENERGIA_2025.csv, soma por timestamp):

```bash
python -m spa.run \
  --source ONS \
  --input data/raw/ONS/ons_carga_diaria/CARGA_ENERGIA_2025.csv \
  --time-col din_instante \
  --value-col val_cargaenergiamwmed \
  --ons-mode sum \
  --outdir results/ons_2025
```

Exemplo real (selecionar subsistema SE/CO):

```bash
python -m spa.run \
  --source ONS \
  --input data/raw/ONS/ons_carga_diaria/CARGA_ENERGIA_2025.csv \
  --time-col din_instante \
  --value-col val_cargaenergiamwmed \
  --ons-mode select \
  --ons-filter subsistema=SE/CO \
  --outdir results/ons_2025_seco
```

Exemplo (carga diaria 2025):

```bash
python -m spa.run \
  --source ONS \
  --dataset ons_carga_diaria \
  --year 2025 \
  --time-col din_instante \
  --value-col val_cargaenergiamwmed \
  --ons-mode sum \
  --outdir results/ons_2025
```

Saidas:

- `processed.csv`
- `summary.json`
- `report.pdf`

## Rodar em um CSV local

```bash
python -m spa.run \
  --input path/para/arquivo.csv \
  --time-col sua_coluna_tempo \
  --value-col sua_coluna_valor \
  --outdir results/minha_serie
```

## Testar o website localmente

Alguns navegadores bloqueiam `fetch()` em `file://`. Para testar o dashboard:

```bash
cd website
python -m http.server 8000
```

Depois abra `http://localhost:8000/index.html`.

## Gerar atrator 3D e horizonte de previsibilidade

Os JSONs sao gerados a partir de `results/_tmp/processed_*.csv` e ficam em `website/assets/spa_energy/`.

Teste rapido:

```bash
python -m pytest tests/test_predictability.py
```

## Gerar dados do Lorenz Lab

Gera os JSONs usados na pagina `website/lab_lorenz.html`:

```bash
python scripts/sim/lab_generate_lorenz.py
```

## Gerar figuras em PNG (energia)

Gera figuras em `results/_figs/energy/`:

```bash
python scripts/report/generate_figures.py
```

## Diagnostico visual por subsistema (fase/embedding)

Exemplo com ONS (carga diaria):

```bash
python -m spa.diagnostics_phase \
  --input data/external/ONS/carga-energia/raw.csv \
  --time-col din_instante \
  --value-col val_cargaenergiamwmed \
  --group-col nom_subsistema \
  --tau 4 \
  --m 4 \
  --k 10 \
  --outdir results/phase
```
