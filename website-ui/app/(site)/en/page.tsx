export default function HomePageEN() {
  return (
    <div className="py-10 space-y-16">
      <section className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-10 backdrop-blur">
          <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">
            Regime &amp; Risk Engine
          </div>
          <h1 className="mt-5 text-5xl font-semibold tracking-tight">
            Forecasting With Regime Awareness
          </h1>
          <p className="mt-4 text-zinc-300 max-w-2xl">
            We detect regime shifts and risk states in complex systems — then show forecasts only
            when the system is structurally reliable. Predict less. Predict better.
          </p>
          <div className="mt-5 text-sm text-zinc-300 max-w-2xl">
            <span className="text-zinc-200 font-semibold">Prediction with discipline:</span> we do not
            just predict — we say when prediction makes sense.
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <a
              className="rounded-xl bg-zinc-100 text-black px-4 py-2 font-medium hover:bg-white transition"
              href="/ativos"
            >
              Open App &rarr;
            </a>
            <a
              className="rounded-xl border border-zinc-800 px-4 py-2 text-zinc-200 hover:border-zinc-600 transition"
              href="/en/methods"
            >
              Methods
            </a>
          </div>
          <div className="mt-5 text-xs text-zinc-500">
            Forecasts are conditional. When structure breaks, we say so.
          </div>
        </div>
        <div className="relative h-[420px] rounded-3xl border border-zinc-800 overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(120,120,150,0.35),rgba(0,0,0,0.9))]" />
          <div className="absolute inset-0 bg-[url('/assets/hero/hero.png')] bg-cover bg-center opacity-80" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
          <div className="absolute bottom-6 left-6 text-xs uppercase tracking-[0.2em] text-zinc-300">
            Assyntrax Labs
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/50 p-8">
          <div className="text-sm uppercase text-zinc-400">The Problem</div>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            Markets don't fail because of noise.
          </h2>
          <p className="mt-4 text-zinc-300">
            They fail because regimes change. Most models assume stationarity. Reality does not.
          </p>
        </div>
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/50 p-8">
          <div className="text-sm uppercase text-zinc-400">Promise</div>
          <p className="mt-3 text-zinc-300">
            Forecasts when regimes are stable. Explicit warnings when they are not. No hype. No
            blind extrapolation.
          </p>
        </div>
      </section>

      <section className="space-y-6">
        <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">What we do</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FeatureCard title="Regime & Risk Detection">
            Detects volatility regimes, instability and transitions using robust statistical and
            dynamical signatures.
          </FeatureCard>
          <FeatureCard title="Confidence & Stability">
            Every output is paired with confidence, health flags and explicit usage warnings.
          </FeatureCard>
          <FeatureCard title="Forecast (as diagnostic)">
            Forecast exists only as diagnostic context, always compared to naive baselines.
          </FeatureCard>
        </div>
      </section>

      <section className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="text-sm uppercase text-zinc-400">Ready to explore</div>
          <h3 className="mt-3 text-3xl font-semibold tracking-tight">
            Open the Dashboard
          </h3>
          <p className="mt-2 text-zinc-300">
            Decision support built on regime awareness and risk diagnostics.
          </p>
        </div>
        <a
          className="rounded-xl bg-zinc-100 text-black px-6 py-3 font-medium hover:bg-white transition"
          href="/ativos"
        >
          Open the Dashboard &rarr;
        </a>
      </section>
    </div>
  );
}

function FeatureCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
      <div className="text-lg font-semibold">{title}</div>
      <div className="mt-3 text-sm text-zinc-300">{children}</div>
    </div>
  );
}
