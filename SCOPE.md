# Escopo Delimitado (Fase Atual)

Este documento define explicitamente o que **não** será feito agora. O objetivo é
manter o projeto focado no núcleo analítico, evitando custos, inconsistências e
complexidade desnecessária.

## Fora do escopo (por enquanto)

1. **Downloads repetitivos / dependência online constante**  
   O mecanismo deve operar com dados locais já baixados. Nada de puxar Yahoo Finance
   automaticamente em cada execução. Cache e dados locais são obrigatórios.

2. **Misturar coleta de dados com simulação**  
   Scripts de simulação/análise assumem que os dados já existem. Coleta e análise
   devem permanecer separadas.

3. **Dashboards ou interfaces gráficas**  
   Não serão criadas UIs web ou dashboards interativos neste estágio. Apenas outputs
   analíticos (arquivos e gráficos estáticos) são permitidos.

4. **Modelos de Deep Learning (LSTM/Transformers)**  
   Não serão incorporados nesta fase. O foco é em métodos interpretáveis e análise
   de previsibilidade fundamental.

5. **Promessas de previsões de longo prazo**  
   O código e a comunicação devem evitar qualquer promessa irreal. Se a incerteza
   domina após X passos, isso deve ser dito claramente.

6. **Gráficos redundantes**  
   Evitar gerar dezenas de figuras por ativo. Priorizar 2–3 gráficos essenciais
   (ex.: real vs previsto e erro vs horizonte). Outros gráficos só se agregarem
   explicação clara, idealmente como anexo opcional.

## Diretriz geral

Foco no essencial: rodar testes corretamente, evitar vazamento de informação e
produzir um veredito claro. Expansões podem ser consideradas depois que o núcleo
estiver validado.
