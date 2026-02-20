import ProductMock from "@/components/visuals/ProductMock";
import SignalWeave from "@/components/visuals/SignalWeave";
import ProofMatrix from "@/components/visuals/ProofMatrix";

export default function ProductPage() {
  return (
    <div className="space-y-16">
      <section className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
        <div className="space-y-4">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Produto</div>
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
            Estrutura, métricas e decisão em um fluxo único
          </h1>
          <p className="text-zinc-300 max-w-3xl text-lg">
            O Eigen Engine combina diagnóstico de regime, risco estrutural e forecast condicional com
            rastreabilidade operacional. O foco é reduzir erro de decisão, não adivinhar preço.
          </p>
        </div>
        <SignalWeave />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-10 items-center">
        <div className="space-y-4">
          <h2 className="text-3xl font-semibold">Dashboard operacional</h2>
          <p className="text-zinc-300 text-lg">
            Leitura de regime com confiança, qualidade, status de gate e motivo explícito de uso.
            Quando o sistema está inconclusivo, a ação fica bloqueada em modo diagnóstico.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-zinc-300">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
              Estado atual: o que mudou no sistema hoje.
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
              Regra operacional: o que evitar para não forçar decisão frágil.
            </div>
          </div>
        </div>
        <ProductMock />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr] gap-10 items-center">
        <ProofMatrix />
        <div className="space-y-4">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">API e integração</div>
          <h2 className="text-3xl font-semibold">Saídas prontas para produção</h2>
          <p className="text-zinc-300 text-lg">
            Respostas em JSON com regime, confiança, qualidade, status, motivo e run_id para auditoria.
            Integração direta com BI, alertas e sistemas internos.
          </p>
          <pre className="rounded-2xl border border-zinc-800 bg-black/60 p-4 text-xs text-zinc-200 overflow-x-auto">
{`{
  "regime": "transition",
  "confidence": 0.84,
  "quality": 0.78,
  "status": "watch",
  "reason": "transição persistente",
  "run_id": "20260210_xxx"
}`}
          </pre>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Setores de aplicação</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="Finanças">
            Regime diário para ativos líquidos. Útil para reduzir overtrading, evitar extrapolação em
            transição e bloquear ação quando a estrutura degrada.
          </Card>
          <Card title="Imobiliário">
            Diagnóstico por cidade e estado com preço, liquidez, juros e crédito. Separa expansão,
            maturação, estagnação e estresse local com explicação operacional.
          </Card>
          <Card title="Energia e infraestrutura">
            Leitura de estabilidade em séries de carga, custo e risco operacional, com alerta para
            mudança estrutural antes de ajuste tático.
          </Card>
          <Card title="Operações e risco institucional">
            Base para comitês e governança: status validado/observação/inconclusivo, motivo do gate
            e trilha de decisão por execução.
          </Card>
        </div>
      </section>

      <section className="rounded-[28px] border border-zinc-800 bg-zinc-950/60 p-8 space-y-5">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Oferta ativa</div>
        <h2 className="text-3xl font-semibold">Piloto em 30 dias com criterio claro</h2>
        <p className="text-zinc-300 text-lg">
          Posicionamento atual: monitor de risco estrutural para modo cautela. Nao e previsao de dia exato de crash.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-zinc-300">
          <div className="rounded-2xl border border-zinc-800 bg-black/30 p-5">
            <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">1. Kickoff</div>
            <div className="mt-2">Alinhar setores, horario de entrega e regra de acao por nivel.</div>
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-black/30 p-5">
            <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">2. Operacao diaria</div>
            <div className="mt-2">Sinal por setor, alerta de saida de verde e resumo semanal de uso real.</div>
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-black/30 p-5">
            <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">3. Fechamento</div>
            <div className="mt-2">Decisao objetiva: manter monitor mensal, ajustar parametros ou encerrar.</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-3 text-sm">
          <a
            className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500"
            href="https://github.com/pemodest0/Assyntrax/blob/main/docs/OFERTA_COMERCIAL_MOTOR.md"
            target="_blank"
            rel="noreferrer"
          >
            Oferta comercial
          </a>
          <a
            className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500"
            href="https://github.com/pemodest0/Assyntrax/blob/main/docs/PILOTO_30D_PLAYBOOK.md"
            target="_blank"
            rel="noreferrer"
          >
            Playbook 30 dias
          </a>
          <a
            className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500"
            href="https://github.com/pemodest0/Assyntrax/blob/main/docs/PACOTE_VENDA_CHECKLIST.md"
            target="_blank"
            rel="noreferrer"
          >
            Checklist de venda
          </a>
        </div>
      </section>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
      <div className="text-lg font-semibold">{title}</div>
      <div className="mt-3 text-sm text-zinc-300">{children}</div>
    </div>
  );
}
