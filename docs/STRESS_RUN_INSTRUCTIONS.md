## Stress Test – Guia Rápido (macOS)

### 1. Pré-requisitos
- macOS com Python 3.10+ instalado (`python3 --version` para conferir).
- git (opcional) caso vá clonar o repositório.
- Recomendado: usar `venv` para isolar dependências.

### 2. Clonar ou copiar o projeto
```bash
git clone <seu-repo> quantum_walk_project
cd quantum_walk_project
```
> Se já transferiu a pasta, apenas abra um terminal em `quantum_walk_project`.

### 3. Criar ambiente virtual (opcional, mas recomendado)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar dependências
```bash
pip install -r requirements.txt
```
> Caso o arquivo `requirements.txt` esteja desatualizado, instale manualmente:  
`pip install numpy pandas matplotlib yfinance`

### 5. Rodar a bateria de stress
O script `analysis/stress_pipeline.py` automatiza todos os testes descritos:
```bash
python analysis/stress_pipeline.py --domains all --noise-levels 0.0,0.01,0.02,0.05
```
- Resultados são salvos em `results_stress/`:
  - `stress_summary.csv`: tabela com ΔMAE, Δdir, Δα, etc.
  - `stress_performance.png`: gráficos de ΔMAE/Δα versus ruído.
  - `stress_report.md`: resumo textual.
  - Subpastas (`robustness`, `financial`, `noise`, `shuffle`) por domínio.

### 6. Verificar hipóteses de falha
Abra `results_stress/stress_report.md` para ver:
- Robustez (percentual de combinações em que Hadamard vence).
- Inversões de Δα.
- Comparação com p-valores DM (carregados automaticamente de `analysis/make_report.py`).

### 7. Recomendações
- Para repetir algum domínio isolado:  
  `python analysis/stress_pipeline.py --domains SPY`
- Ajustar níveis de ruído:  
  `--noise-levels 0.0,0.01,0.03,0.05,0.1`
- Se precisar rodar apenas a grade de robustez:  
  `python run_robustness_grid.py --symbol SPY --bins-list ... --window-list ... --noise-list ... --outdir results_custom/SPY`

### 8. Dicas macOS
- Use `python3`/`pip3` se o alias `python` apontar para Python 2.
- Para abrir os gráficos: `open results_stress/stress_performance.png`.
- Para acompanhar logs em tempo real: `tail -f results_stress/<domínio>/financial/run.log` (se desejar salvar stdout).

### 9. Limpeza
- Para rodar novamente do zero:  
  `rm -rf results_stress tmp`
- Reative o ambiente virtual sempre que abrir nova sessão:  
  `source .venv/bin/activate`

Pronto! Com esses passos você consegue reproduzir a bateria completa no macOS e validar onde o modelo mantém (ou perde) vantagem.
