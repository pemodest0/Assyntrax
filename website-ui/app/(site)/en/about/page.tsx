export default function AboutPageEN() {
  return (
    <div className="space-y-10">
      <div className="space-y-3">
        <h1 className="text-4xl font-semibold tracking-tight">Why Assyntrax Exists</h1>
        <p className="text-zinc-300 max-w-3xl">
          Problem: markets change regimes while traditional models keep predicting as if nothing
          changed. Solution: diagnose state before forecasting.
        </p>
      </div>

      <section className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-8">
        <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">What we do differently</div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <ValueCard title="Conditional forecast">
            We show forecasts only when regimes are stable.
          </ValueCard>
          <ValueCard title="Diagnosis first">
            State, confidence and quality before any projection.
          </ValueCard>
          <ValueCard title="Full transparency">
            Explicit warnings, reasons and metrics.
          </ValueCard>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-8">
          <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">Story</div>
          <p className="mt-3 text-zinc-300">
            The project started from a real pain: predictors fail precisely when regimes change.
            We shifted focus to structure and disciplined forecasting.
          </p>
          <p className="mt-3 text-zinc-300">
            The engine evolved into a full pipeline: embedding, microstates, graphs and metastable
            regimes, with quality and explicit alerts.
          </p>
        </div>
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-8">
          <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">Future</div>
          <ul className="mt-3 space-y-3 text-zinc-300">
            <li>• Global multi-asset diagnostics API.</li>
            <li>• Sector agents (finance, logistics, real estate).</li>
            <li>• Broader geographic coverage and official benchmarks.</li>
          </ul>
        </div>
      </section>

      <section className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-8">
        <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">Product phases</div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-zinc-300">
          <TimelineItem title="Phase 1" text="Base engine + real-series diagnostics." />
          <TimelineItem title="Phase 2" text="Graph engine + multi-asset hypertests." />
          <TimelineItem title="Phase 3" text="Decision dashboard + API." />
          <TimelineItem title="Phase 4" text="Global expansion by sector." />
        </div>
      </section>
    </div>
  );
}

function ValueCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 text-sm text-zinc-300">
      <div className="text-lg font-semibold">{title}</div>
      <div className="mt-2">{children}</div>
    </div>
  );
}

function TimelineItem({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">{title}</div>
      <div className="mt-2 text-zinc-300">{text}</div>
    </div>
  );
}
