# Piloto 30 Dias - Playbook

## Objetivo
Validar utilidade do motor em ambiente real de decisao, sem promessa de retorno.

## Escopo
- Universo: setores do cliente (ou universo padrao 470 ativos).
- Frequencia: leitura diaria + resumo semanal.
- Duracao: 30 dias corridos.

## Entregas
1. Sinal diario por setor (`verde`, `amarelo`, `vermelho`).
2. Ranking diario de fragilidade setorial.
3. Alerta de mudanca de nivel (saida de verde).
4. Relatorio semanal de 1 pagina.
5. Fechamento final com comparacao inicial vs final.

## Rotina de execucao
1. Dia 0: kickoff e alinhamento de regra de acao.
2. Dias 1-30:
- roda pipeline diario
- envia snapshot do dia
- registra decisoes tomadas
3. Toda semana:
- revisar sinais acionados
- revisar falso alerta e utilidade pratica
4. Dia 30:
- consolidar resultado
- recomendacao: manter, ajustar ou encerrar.

## Critero de sucesso do piloto
1. Disciplina operacional:
- 100% de dias com atualizacao entregue no horario combinado.
2. Qualidade de sinal:
- falso alerta anualizado <= 12 dias/ano (modo util).
3. Uso pratico:
- time do cliente confirma utilidade em decisao de risco setorial.
4. Transparencia:
- todas as mudancas e limites documentados.

## Regra de acao sugerida
- `verde`: manter risco base.
- `amarelo`: reduzir risco setorial em 10%-20%.
- `vermelho`: reduzir risco setorial em 20%-40% e reforcar protecao.

## Sinais de bloqueio (nao operar)
1. pipeline sem atualizar por 1 dia util.
2. falha de contrato de dados.
3. drift do motor em nivel `block`.

## Arquivos usados no piloto
- `results/event_study_sectors/latest_run.json`
- `results/event_study_sectors/alerts/latest_alert.json`
- `results/event_study_sectors/drift/latest_drift.json`
- `results/event_study_sectors/health/latest_health.json`

## Resultado final esperado
- decisao objetiva: continuar com monitor mensal, ajustar parametros, ou encerrar.
