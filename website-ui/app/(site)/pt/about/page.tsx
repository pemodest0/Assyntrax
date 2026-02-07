import OriginPulse from "@/components/visuals/OriginPulse";

export default function AboutPage() {
  return (
    <div className="space-y-16">
      <section className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
        <div className="space-y-4">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Sobre</div>
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
            Por que a Assyntrax existe
          </h1>
          <p className="text-zinc-300 max-w-3xl text-lg">
            Mercados mudam de regime e modelos tradicionais continuam prevendo como se nada tivesse
            mudado. A Assyntrax nasceu para diagnosticar estrutura antes de qualquer projeção.
          </p>
        </div>
        <OriginPulse />
      </section>

      <section className="rounded-[32px] border border-zinc-800 bg-zinc-950/60 p-10 hero-noise">
        <div className="text-sm uppercase tracking-[0.3em] text-zinc-400">
          O que fazemos diferente
        </div>
        <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          <ValueCard title="Forecast condicional">
            Previsão só aparece quando o regime é estável.
          </ValueCard>
          <ValueCard title="Diagnóstico primeiro">
            Estado, confiança e qualidade antes de qualquer projeção.
          </ValueCard>
          <ValueCard title="Transparência total">
            Alertas, motivos e métricas explícitas.
          </ValueCard>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-[28px] border border-zinc-800 bg-zinc-950/60 p-8">
          <div className="text-sm uppercase tracking-[0.3em] text-zinc-400">História</div>
          <p className="mt-3 text-zinc-300">
            O projeto nasceu de um problema real: previsores falham quando o regime muda. O foco
            virou identificar estrutura e disciplinar o uso de previsão.
          </p>
          <p className="mt-3 text-zinc-300">
            O motor evoluiu para um pipeline completo: embedding, microestados, grafos e regimes
            metastáveis, com qualidade e alertas explícitos.
          </p>
        </div>
        <div className="rounded-[28px] border border-zinc-800 bg-zinc-950/60 p-8">
          <div className="text-sm uppercase tracking-[0.3em] text-zinc-400">Futuro</div>
          <ul className="mt-3 space-y-3 text-zinc-300">
            <li>• API global de diagnóstico multiativos.</li>
            <li>• Agentes setoriais (financeiro, logística, imobiliário).</li>
            <li>• Expandir cobertura geográfica e dados oficiais.</li>
          </ul>
        </div>
      </section>

      <section className="rounded-[32px] border border-zinc-800 bg-zinc-950/60 p-10">
        <div className="text-sm uppercase tracking-[0.3em] text-zinc-400">Fases do produto</div>
        <div className="mt-5 grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-zinc-300">
          <TimelineItem title="Fase 1" text="Motor base + diagnóstico em séries reais." />
          <TimelineItem title="Fase 2" text="Graph Engine + hiper-testes multi-ativos." />
          <TimelineItem title="Fase 3" text="API e dashboard de decisão." />
          <TimelineItem title="Fase 4" text="Expansão global e setorial." />
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
