# Pacote de Prova do Motor (3 paginas)

## Pagina 1 - O que o motor faz e limite real

### O que faz
- Le o comportamento diario de setores usando os 470 ativos.
- Marca cada setor em `verde`, `amarelo` ou `vermelho`.
- Entrega alerta para entrar em modo cautela antes de estresse maior.

### O que nao faz
- Nao acerta o dia exato do choque.
- Nao promete retorno.
- Nao substitui decisao humana.

### Regra simples de uso
- `verde`: manter risco base.
- `amarelo`: reduzir risco parcial.
- `vermelho`: reduzir risco forte e proteger carteira.

## Pagina 2 - Como provamos que funciona

### Protocolo
- Eventos definidos de forma automatica (`ret_tail`, `drawdown20`, `vol_spike20`, `stress_combo`).
- Tudo causal (sem usar futuro).
- Comparacao contra baselines simples e baseline aleatorio.
- Repeticao por setores e por janelas (`1, 5, 10, 20` dias).

### Arquivos de prova
- Script principal: `scripts/bench/event_study_validate_sectors.py`
- Hiper simulacao: `scripts/bench/hyper_simulate_sector_alerts.py`
- Estabilidade anual: `scripts/bench/walkforward_sector_stability.py`
- Perfil congelado: `config/sector_alerts_profile.json`

### Saidas auditaveis
- `results/event_study_sectors/latest_run.json`
- `results/event_study_sectors/<run_id>/sector_metrics_summary.csv`
- `results/event_study_sectors/<run_id>/sector_alert_levels_latest.csv`
- `results/event_study_sectors/<run_id>/weekly_compare.json`
- `results/event_study_sectors/drift/latest_drift.json`

## Pagina 3 - Estado atual e proximo passo de venda

### Estado atual
- Pipeline diario rodando com perfil congelado.
- Revalidacao mensal automatica com decisao de promover ou manter baseline.
- Painel com leitura por setor, comparacao semanal e drift do motor.

### Como vender hoje
- Vender como monitor de risco estrutural.
- Fechar piloto de 30 dias com regra objetiva de sucesso.
- Mostrar historico real e limite do produto sem exagero.

### Proximo passo tecnico
1. Aumentar taxa de passagem no walkforward anual.
2. Reduzir falso alerta mantendo detecao em `L=10` e `L=20`.
3. Consolidar relatorio executivo semanal de 1 pagina para cliente final.
