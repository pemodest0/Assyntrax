export default function ProductPageEN() {
  return (
    <div className="space-y-10">
      <div className="space-y-3">
        <h1 className="text-4xl font-semibold tracking-tight">What You Get</h1>
        <p className="text-zinc-300 max-w-3xl">
          Decision intelligence that prioritizes regime awareness and explicit risk diagnostics.
        </p>
      </div>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Dashboard">
          Risk regime (High / Low). Regime stability. Confidence scores. System health warnings.
          Historical performance context. Designed for decision support, not speculation.
        </Card>
        <Card title="API">
          Structured outputs. Asset-agnostic. Timeframe-aware. Production-ready.
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
        <h2 className="text-2xl font-semibold">Who it's for</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="Risk teams">Regime state awareness for exposure control.</Card>
          <Card title="Portfolio managers">Contextual decision support under volatility shifts.</Card>
          <Card title="Quant research">Diagnostics to validate signals and baselines.</Card>
          <Card title="Decision-making under uncertainty">
            Transparent outputs and explicit weakness flags.
          </Card>
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
