# Oferta Comercial - Motor de Risco Estrutural

## O que e
Servico de leitura de risco de mercado para apoiar decisao de carteira.

Ele nao tenta acertar o dia exato da crise.
Ele ajuda a detectar piora estrutural para entrar em modo cautela mais cedo.
Saida comercial padrao: interpretacao estatistica e suporte quantitativo (sem recomendacao de investimento).

## O que entregamos hoje
- Leitura diaria por setor: verde, amarelo, vermelho.
- Sinal em duas camadas: rapido e confirmado.
- Regra anti-ruido com espacamento minimo entre alertas (menos flicker).
- Ranking de setores com maior fragilidade no curto prazo.
- Historico por setor com tendencia de melhora ou piora.
- Monitor de drift do proprio motor para evitar degradacao silenciosa.
- Alerta quando setor sai de verde.
- Relatorio simples para comite.
- Plano de acao por setor com faixa numerica de risco e hedge sugerido.

## Estado atual (real e auditavel)
- Perfil de producao congelado em `config/sector_alerts_profile.json`.
- Perfil aplicado no pipeline diario via `scripts/ops/run_daily_sector_alerts.py`.
- Ultimo run validado: `results/event_study_sectors/20260220T041951Z`.
- Comparador de modos (util vs agressivo): `results/dual_mode_compare/20260220T060852Z/summary.json`.
- Hiper simulacao grande (21 rodadas): `results/hyper_sector_search/20260220T014134Z`.
- Revalidacao mensal automatica:
  - `results/monthly_revalidation/20260220T024324Z/summary.json`
  - decisao: manter baseline (nao promover nova configuracao).

## Numero que importa (resumo)
No perfil refinado atual:
- recall drawdown em 10 dias: 0,39
- recall drawdown em 20 dias: 0,67
- recall retorno extremo em 10 dias: 0,50
- falso alerta drawdown em 10 dias: 8,10 dias por ano
- precisao drawdown em 10 dias: 0,139

Leitura simples:
- melhoramos reducao de falso alerta sem destruir detecao.
- ainda existe erro e variacao por periodo.
- modo agressivo aumenta acerto em janela longa, mas piora muito falso alerta.

## Atualizacao pratica (1, 2 e 3 executados)
Run consolidado:
- `results/followup_123/20260220T170102Z/summary.json`

### 1) Politica conservadora em teste continuo
- arquivo diario: `results/followup_123/20260220T170102Z/policy_conservative_continuous_daily.csv`
- resumo: `results/followup_123/20260220T170102Z/report_step1_policy_continuous.txt`
- l10: recall=0,833 | precisao=0,143 | falso alerta=3,45 dias/ano | antecedencia media=7,8 dias
- cobertura macro valida: 1753/1989 dias
- limite atual: ultimo dia macro valido foi 2025-03-04 (arquivo vai ate 2026-01-28, mas com universo insuficiente apos essa data)

### 2) Triagem dos 123 ativos de sinal fraco
- triagem completa: `results/followup_123/20260220T170102Z/weak_signal_triage.csv`
- top prioridade: `results/followup_123/20260220T170102Z/weak_signal_top20_priority.csv`
- quebra por motivo:
  - misto_revisar: 47
  - sinal_fraco_modelo: 44
  - mercado_estrutural_forte: 20
  - mercado_estrutural_moderado: 12
- problema de dados detectado: 0

### 3) Diagnostico final por setor
- tabela geral: `results/followup_123/20260220T170102Z/sector_diagnostic_table.csv`
- resumo texto: `results/followup_123/20260220T170102Z/report_step3_sector_diagnosis.txt`
- setores principais mais fragilizados: energy, real_estate, consumer_discretionary, utilities, consumer_staples
- setores principais mais estaveis: technology, health_care, utilities, financials, industrials

## Teste por periodos (robustez)
Walkforward anual mais recente:
- `results/walkforward_sector_stability/20260220T044621Z/summary.json`
- 6 anos avaliados (2020 a 2025)
- taxa de passagem de gate: 6 em 6 (100%)

Nota metodologica:
- Em anos sem evento de drawdown no recorte, o gate usa disciplina de alerta (falso alerta) em vez de recall, para nao punir janela sem amostra de evento.

Leitura simples:
- no gate adaptativo, o motor passou em 6 de 6 janelas anuais no recorte atual.
- ainda assim, o formato correto de venda continua piloto com acompanhamento, por causa do tradeoff acerto x ruido.

## Para que serve na pratica
- Reduzir exposicao quando sinais de risco aumentam.
- Priorizar setores para revisao de carteira.
- Definir quando entrar em modo cautela.
- Dar base objetiva para conversa de risco com cliente.

## Para que NAO serve
- Nao e promessa de retorno.
- Nao e ferramenta para "adivinhar crash".
- Nao substitui gestao humana.

## Forma correta de vender agora
### Piloto assistido (recomendado)
- Duracao: 30 dias
- Entrega diaria + resumo semanal
- Revisao de sinal e ajuste de regra junto com cliente

Preco sugerido: R$ 3.000 a R$ 8.000 por piloto.

Material pronto para iniciar:
- `docs/PILOTO_30D_PLAYBOOK.md`
- `docs/PACOTE_VENDA_CHECKLIST.md`

### Monitor mensal
- Atualizacao diaria automatica
- Alertas e leitura por setor
- Relatorio executivo semanal

Preco sugerido: R$ 5.000 a R$ 12.000 por mes.

## Roteiro de venda (curto)
1. Mostrar painel setorial e historico real.
2. Mostrar limite honesto: nao preve dia exato.
3. Mostrar utilidade: modo cautela e ajuste de risco.
4. Fechar piloto de 30 dias com criterio objetivo de avaliacao.

## Criterio de evolucao para "venda forte"
Para subir de patamar comercial, o motor precisa:
- melhorar estabilidade no walkforward (mais anos passando gate),
- manter falso alerta baixo,
- manter recall de drawdown em 10 dias acima de 0,35.

## Material de prova curto
- Ver `docs/MOTOR_PROVA_3P.md`.

## Kit comercial pronto
- Proposta curta: `docs/venda/PROPOSTA_CURTA.md`
- Pacotes (3 niveis): `docs/venda/PACOTES_ENTREGA_3_NIVEIS.md`
- Relatorio executivo (1 pagina): `docs/venda/RELATORIO_EXECUTIVO_1_PAGINA.md`
- Estudo de caso real: `docs/venda/ESTUDO_DE_CASO_REAL_SETOR.md`
- Guia de demo para reuniao: `docs/venda/DEMO_REUNIAO_GUIA.md`

## Atualizacao tecnica recente (frentes 1 e 2)
### Frente 1 - cobertura de dados
- Run macro promovido: `results/lab_corr_macro/20260220T174540Z`
- Cobertura valida ate 2026-02-12 em T60, T120 e T252.
- Deployment gate liberado e `latest_release.json` atualizado.

### Frente 2 - prova de antecipacao
- Consolidado multi-politica: `results/event_study_proof/20260220T184728Z`
- Melhor politica no protocolo atual: `regime_entry`.
- Resultado honesto: sinal operacional forte, sem evidencia estatistica forte contra baseline aleatorio no criterio principal.

## Atualizacao de produto no site e painel
- Dashboard principal simplificado com leitura direta do estado do motor.
- Filtros operacionais adicionados: `ativo`, `setor`, `janela` e `periodo`.
- Resumo por setor com risco medio, confianca e plano de acao.
- Historico de mudancas de estado no periodo filtrado.
- Bloco "por que alerta" com explicacao humana do evento.
- Bloco de limites do motor (faz e nao faz) com linguagem simples.
- Bloco de qualidade de dados com status de checks e falhas.
- Nova tela de operacao (`/app/operacao`) com gate de publicacao e relatorio diario.
- Nova tela de venda (`/app/venda`) com pacotes e material de reuniao.
