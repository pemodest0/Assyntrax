# Resultado Esperado e Visão de Negócio

Este documento define como o veredito do Motor de Analise de Serie Temporal deve ser comunicado e
posicionado como produto. O foco é honestidade metodológica e utilidade prática.

## 1) Resultado esperado

Ao final da bateria de testes, o motor deve emitir um veredito objetivo sobre
previsibilidade, com horizonte de validade e estabilidade ao longo do tempo.

## 0) Ideia principal (produto)
- Regime -> confianca -> forecast (opcional)
- Filtro de estrutura, nao promessa de prever mercado
- Sempre mostrar quando falha e por que

Exemplo de declaração:

> “Após uma bateria extensiva de testes, concluímos que a série X apresenta
> previsibilidade apenas em horizontes muito curtos. Modelos simples superaram
> a persistência em previsões de 1 dia. Para horizontes acima de 1 semana, o
> erro converge para níveis de aleatoriedade. Recomendação: use apenas nowcasting
> e evite previsões de médio/longo prazo.”

## 2) Valor de negócio

- Evita investimento em previsões onde não há sinal.
- Direciona esforço para estratégias compatíveis (gestão de risco, hedging).
- Constrói credibilidade ao não prometer o impossível.

## 3) Se houver previsibilidade

Caso o sistema apresente sinais consistentes:

- O motor quantifica o ganho vs baseline.
- Define horizonte útil (ex.: até 1 mês).
- Recomenda evolução para modelos mais sofisticados, se justificável.

Exemplo:

> “Série Y apresenta Hurst 0.75 (persistência), e o modelo superou a baseline
> em 5% com estabilidade. Há potencial preditivo real em horizontes de até 1 mês.”

## 4) Entrega de produto

O veredito será entregue como:

1. **Relatório geral (`overview.md`)**  
   Explica configurações testadas, resultados por ativo e conclusões.

2. **Tabela completa (`overview.csv`)**  
   Registro auditável de todos os resultados.

3. **Veredito estruturado (`temporal_verdict.json`)**  
   Saída programática para integração futura.

## 5) Princípios de integridade

- Se o modelo falhar, o veredito dirá “falhou”.
- Sem ajustes ad hoc para “parecer bom”.
- Preferimos subestimar a previsibilidade a inflar resultados.

## Anti-enganacao (sempre)
- Comparar com baseline
- Mostrar metricas e alertas
- Expor quando nao ha estrutura

## 6) Próximos passos

Após validação técnica:

- README institucional (com resultados resumidos).
- Whitepaper técnico (metodologia e evidências).
- Pitch para investidores com foco em rigor e credibilidade.
