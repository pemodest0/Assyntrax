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
            Estrutura, métricas e decisão em um só fluxo
          </h1>
          <p className="text-zinc-300 max-w-3xl text-lg">
            A Assyntrax entrega diagnóstico acionável de regimes, saúde estrutural e forecast
            condicional — com rastreabilidade, alertas e contexto técnico.
          </p>
        </div>
        <SignalWeave />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-10 items-center">
        <div className="space-y-4">
          <h2 className="text-3xl font-semibold">Dashboard de decisão</h2>
          <p className="text-zinc-300 text-lg">
            Regime, confiança, qualidade e alertas em tempo real. Sem magia, com critérios claros.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-zinc-300">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
              Diagnóstico antes de previsão.
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
              Alertas explícitos de uso e risco.
            </div>
          </div>
        </div>
        <ProductMock />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr] gap-10 items-center">
        <ProofMatrix />
        <div className="space-y-4">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">API &amp; integração</div>
          <h2 className="text-3xl font-semibold">Saídas prontas para produção</h2>
          <p className="text-zinc-300 text-lg">
            Respostas em JSON com regime, confiança, métricas e sinais de alerta. Integração direta
            com BI, alertas e pipelines internos.
          </p>
          <pre className="rounded-2xl border border-zinc-800 bg-black/60 p-4 text-xs text-zinc-200 overflow-x-auto">
{`{
  "risk_regime": "HIGH_VOL",
  "confidence": 0.93,
  "regime_state": "UNSTABLE",
  "warnings": ["DIRECTION_WEAK"]
}`}
          </pre>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Para quem</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="Equipes de risco">Consciência de regime para controle de exposição.</Card>
          <Card title="Gestores de portfólio">Decisão contextual sob mudança de volatilidade.</Card>
          <Card title="Pesquisa quant">Diagnósticos para validar sinais e baselines.</Card>
          <Card title="Decisão sob incerteza">Saídas transparentes e alertas explícitos.</Card>
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
