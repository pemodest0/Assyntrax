# Guia do Engine

## Pacote oficial
Use `engine/` para novos codigos.

## Contrato minimo por ativo
- `run_id`
- `asset`
- `domain`
- `status` (`validated|watch|inconclusive`)
- `regime`
- `confidence`
- `quality`
- `reason`
- `data_adequacy`

## Consumo esperado
- Scripts de ops escrevem snapshots.
- API do `website-ui` le ultimo run valido.
- UI mostra acao apenas para `validated/watch`.

## Compatibilidade
- `spa/` e `graph_engine/` continuam disponiveis como wrappers.
- Migracao de codigo novo deve ser feita somente para `engine.*`.
