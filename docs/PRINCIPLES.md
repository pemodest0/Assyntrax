# Principles / Princípios

## Português (PT-BR)
### Por quê
A Assyntrax existe para separar estrutura de ruído. O produto não é um oráculo de preço; é um oráculo de regime e confiança que indica quando há estrutura e quando não há.

### Cinco regras de ouro (gating)
1) Regime primeiro: nunca mostrar forecast sem rótulo de regime.
2) Confiança em seguida: se a confiança estiver abaixo do limiar, marcar “NÃO CONFIAR”.
3) Sempre comparar com baseline: mostrar MASE/dir_acc vs naïve.
4) Expor falhas: quando o modelo falhar, a UI precisa dizer.
5) Explicar o bloqueio: mostrar por que o forecast foi vetado (regime instável, direção fraca, sem estrutura).

### Quando funciona vs quando não funciona
Funciona:
- Regime estável, estrutura repetível, confiança acima do limiar.
- Forecast supera o baseline em walk-forward.

Não funciona:
- Regime instável ou em transição por longos períodos.
- Confiança baixa ou direção fraca.

### O motor como oráculo
O motor é um oráculo de confiança + regime (não de preço). Ele decide se o sistema está estruturado o suficiente para permitir forecast ou ação.

### Bloco anti-enganção
- Sempre mostrar baselines e métricas.
- Sempre mostrar quando falha.
- Nunca esconder sinais fracos.

## English (EN)
### Why
Assyntrax exists to separate structure from noise. The product is not a price oracle; it is a regime and confidence oracle that tells when structure exists and when it does not.

### Five rules of gold (gating)
1) Regime first: never show a forecast without a regime label.
2) Confidence next: if confidence is below threshold, label “DO NOT TRUST”.
3) Always compare to baseline: show MASE/dir_acc vs naive.
4) Expose failure: when the model fails, the UI must say it.
5) Explain the warning: show why a forecast is gated (regime unstable, direction weak, no structure).

### When it works vs when it does not
Works:
- Stable regime, repeatable structure, confidence above threshold.
- Forecast beats naive baseline in walk-forward.

Does not work:
- Regime unstable or transitional for long stretches.
- Confidence low or direction weak.

### The motor as oracle
The motor is an oracle of confidence + regime (not price). It decides if the system is structured enough to allow forecast or action.

### Anti-deception block
- Always show baselines and metrics.
- Always show when it fails.
- Never hide weak signals.
