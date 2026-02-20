# Contrato API - Setores

Endpoint:
- `GET /api/sectors/alerts`

Versao:
- `contract_version = sector_alerts_v2`

Autenticacao opcional:
- Se `ASSYNTRAX_API_KEYS` estiver definida no servidor (lista separada por virgula),
  a requisicao deve enviar `x-assyntrax-key`.

Parametros:
- `days` (opcional): janela de historico para timeline (min 10, max 180).

Campos principais de resposta:
- `status`
- `contract_version`
- `run_id`
- `generated_at`
- `lookback_days`
- `counts` (`verde`, `amarelo`, `vermelho`)
- `levels[]`
  - `confidence_band`
  - `confidence_reason`
  - `action_tier`
  - `risk_budget_min`
  - `risk_budget_max`
  - `hedge_min`
  - `hedge_max`
  - `action_priority`
  - `action_reason`
- `ranking[]`
- `eligibility[]`
- `timeline[]`
- `weekly_compare`
- `notification`
- `drift`

Uso recomendado:
- Frontend institucional deve validar `contract_version` antes de consumir campos novos.
- Integracao externa deve tratar `status!=ok` e `error`.
