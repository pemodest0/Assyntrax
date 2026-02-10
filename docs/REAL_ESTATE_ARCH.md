# Arquitetura Imobiliario (Atual)

## Camadas
1. Dados
- `P(t)`: preco medio m2
- `L(t)`: proxy de liquidez
- `J(t)`: juros
- `D(t)`: desconto medio (quando disponivel)

2. Dinamica
- embedding (`m`, `tau`)
- microestados e transicoes
- entropia e persistencia

3. Operacional
- gate `validated/watch/inconclusive`
- explicacao auditavel por ativo

## Regras
- Data adequacy obrigatorio antes do diagnostico.
- Sinal sem adequacao vira `inconclusive`.
- Fonte deve ser marcada como `official` ou `proxy` no payload.

## Saidas minimas
- `summary.json`
- `regimes.csv`
- `alerts.csv`
- `api_snapshot.jsonl`
