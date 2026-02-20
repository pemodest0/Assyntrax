# Rulebook de Acao - Motor de Risco

## Objetivo
Definir resposta pratica para cada nivel de alerta.

## Niveis
- `verde`: risco estrutural baixo.
- `amarelo`: risco subindo, precisa atencao.
- `vermelho`: risco alto, prioridade de defesa.

## Acoes por nivel
### Verde
- manter exposicao normal.
- revisar apenas rotina semanal.

### Amarelo
- reduzir exposicao em 10% a 20%.
- cortar aumento de risco novo.
- revisar setores que mais pioraram.

### Vermelho
- reduzir exposicao em 20% a 40%.
- pausar novas posicoes de risco alto.
- priorizar caixa e ativos defensivos.

## Regra de persistencia (evitar ruido)
- agir forte apenas se nivel ficar 2 dias seguidos.
- se voltar para verde por 3 dias seguidos, normalizar gradualmente.

## Regra por setor
- setor em vermelho: reduzir peso desse setor primeiro.
- setor em amarelo: reduzir incremental e monitorar 5 dias.

## Escalonamento
- 1 setor vermelho: ajuste setorial local.
- 2 a 3 setores vermelhos: ajuste de carteira inteira moderado.
- 4+ setores vermelhos: modo defesa de carteira.

## Janela de revisao
- diario: checar mudanca de nivel.
- semanal: revisar resultado das decisoes.
- mensal: revalidar perfil do motor.

## Limite operacional
- se o motor ficar 3 dias sem atualizar, nao usar sinal.
- se contrato de dados falhar, manter ultima postura conservadora.
