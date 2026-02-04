export default function MethodsPageEN() {
  return (
    <div className="space-y-12">
      <div className="space-y-3">
        <h1 className="text-4xl font-semibold tracking-tight">Methods &amp; Philosophy</h1>
        <p className="text-zinc-300 max-w-3xl">
          We diagnose system state. Forecasting without regime awareness is blind extrapolation.
          Each topic includes a lay view, formalism, and practical use.
        </p>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-300">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">Topics</div>
        <div className="mt-3 flex flex-wrap gap-3">
          <a href="#regimes" className="underline">Regimes</a>
          <a href="#embedding" className="underline">Embedding</a>
          <a href="#microstates" className="underline">Microstates</a>
          <a href="#graphs" className="underline">Graphs</a>
          <a href="#metrics" className="underline">Metrics</a>
          <a href="#forecast" className="underline">Conditional forecast</a>
          <a href="#validation" className="underline">Validation</a>
        </div>
      </div>

      <Section id="regimes" title="Regimes">
        <SplitCard title="Lay view" content="A regime is the system's state: stable, transition, unstable, or noisy." />
        <SplitCard title="Formal" content={<CodeBlock code={`regime_t in {STABLE, TRANSITION, UNSTABLE, NOISY}`} />} />
        <SplitCard title="Use" content="Stable regimes allow forecasts; unstable regimes block them." />
      </Section>

      <Section id="embedding" title="Embedding (Takens)">
        <SplitCard title="Lay view" content="We reconstruct phase space to reveal geometry and stability." />
        <SplitCard
          title="Formal"
          content={
            <>
              <p>Delay embedding:</p>
              <CodeBlock code={`X_t = [x_t, x_{t-tau}, x_{t-2*tau}, ..., x_{t-(m-1)*tau}]`} />
              <p className="mt-3">tau via AMI/ACF, m via Cao/FNN.</p>
            </>
          }
        />
        <SplitCard title="Use" content="Highlights transitions and hidden structure." />
      </Section>

      <Section id="microstates" title="Microstates">
        <SplitCard title="Lay view" content="We cluster the phase space into local states." />
        <SplitCard title="Formal" content={<CodeBlock code={`state_t = argmin_k || X_t - c_k ||`} />} />
        <SplitCard title="Use" content="Enables transition counting and graph construction." />
      </Section>

      <Section id="graphs" title="Graphs & Markov">
        <SplitCard title="Lay view" content="We track transitions between microstates." />
        <SplitCard
          title="Formal"
          content={
            <>
              <p>Transition matrix:</p>
              <CodeBlock code={`P_{ij} = count(i->j) / sum_j count(i->j)`} />
              <p className="mt-3">Markov entropy:</p>
              <CodeBlock code={`H = -sum_i pi_i * sum_j P_{ij} log P_{ij}`} />
            </>
          }
        />
        <SplitCard title="Use" content="Connectivity and entropy indicate stability and risk." />
      </Section>

      <Section id="metrics" title="Metrics">
        <SplitCard title="Lay view" content="We measure confidence, escape risk, and graph quality." />
        <SplitCard
          title="Formal"
          content={
            <>
              <CodeBlock code={`conf_t = sum_{j in regime} P_{ij}`} />
              <CodeBlock code={`escape_t = 1 - conf_t`} />
            </>
          }
        />
        <SplitCard title="Use" content="Forecasts are shown only under strong structure." />
      </Section>

      <Section id="forecast" title="Conditional forecast">
        <SplitCard title="Lay view" content="We show forecasts only when regimes are stable and quality is high." />
        <SplitCard title="Formal" content={<CodeBlock code={`forecast_visible = (state == STABLE) && (quality >= q*)`} />} />
        <SplitCard title="Use" content="If the signal is weak, we block and warn." />
      </Section>

      <Section id="validation" title="Validation (no makeup)">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="Walk-forward only">
            No leakage. Baselines included. Metrics: ROC-AUC, F1, MASE, Directional Accuracy.
          </Card>
          <Card title="Explicit warnings">
            Weak signals are labeled DIRECAO_FRACA or REGIME_INSTAVEL.
          </Card>
        </div>
      </Section>
    </div>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="space-y-4">
      <h2 className="text-2xl font-semibold">{title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{children}</div>
    </section>
  );
}

function SplitCard({ title, content }: { title: string; content: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">{title}</div>
      <div className="mt-3 text-sm text-zinc-300">{content}</div>
    </div>
  );
}

function CodeBlock({ code }: { code: string }) {
  return (
    <pre className="mt-3 rounded-xl border border-zinc-800 bg-black/60 p-4 text-xs text-zinc-200 overflow-x-auto">
      {code}
    </pre>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="text-lg font-semibold">{title}</div>
      <div className="mt-2 text-sm text-zinc-300">{children}</div>
    </div>
  );
}
