export default function ProductPage() {
  return (
    <div className="space-y-10">
      <div className="space-y-3">
        <h1 className="text-4xl font-semibold tracking-tight">O que você recebe</h1>
        <p className="text-zinc-300 max-w-3xl">
          Inteligência de decisão que prioriza consciência de regime e diagnósticos de risco.
        </p>
      </div>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Dashboard">
          Regime de risco (alto/baixo). Estabilidade. Confiança. Alertas de saúde do sistema.
          Contexto histórico de performance. Feito para decisão, não especulação.
        </Card>
        <Card title="API">
          Saídas estruturadas. Agnóstico a ativo. Consciente de timeframe. Pronto para produção.
          <pre className="mt-4 rounded-xl border border-zinc-800 bg-black/60 p-4 text-xs text-zinc-200 overflow-x-auto">
{`{
  "risk_regime": "HIGH_VOL",
  "confidence": 0.93,
  "regime_state": "UNSTABLE",
  "warnings": ["DIRECTION_WEAK"]
}`}
          </pre>
        </Card>
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
