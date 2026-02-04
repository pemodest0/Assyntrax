export default function HomePage() {
  return (
    <div className="py-10 space-y-16">
      <section className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-10 backdrop-blur">
          <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">
            Motor de Regime e Risco
          </div>
          <h1 className="mt-5 text-5xl font-semibold tracking-tight">
            Previsão com consciência de regime
          </h1>
          <p className="mt-4 text-zinc-300 max-w-2xl">
            Detectamos mudanças de regime e estados de risco — e só então mostramos previsão quando
            há estrutura confiável. Prever menos. Prever melhor.
          </p>
          <div className="mt-5 text-sm text-zinc-300 max-w-2xl">
            <span className="text-zinc-200 font-semibold">Previsão com disciplina:</span> não é só
            prever — é dizer quando faz sentido prever.
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <a
              className="rounded-xl bg-zinc-100 text-black px-4 py-2 font-medium hover:bg-white transition"
              href="/ativos"
            >
              Abrir App &rarr;
            </a>
            <a
              className="rounded-xl border border-zinc-800 px-4 py-2 text-zinc-200 hover:border-zinc-600 transition"
              href="/methods"
            >
              Métodos
            </a>
          </div>
          <div className="mt-5 text-xs text-zinc-500">
            Forecast é condicional. Se não há estrutura, o sistema avisa.
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
          <div className="text-sm uppercase text-zinc-400">O problema</div>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            Mercados não falham por ruído.
          </h2>
          <p className="mt-4 text-zinc-300">
            Falham porque regimes mudam. A maioria dos modelos assume estacionariedade. A realidade
            não.
          </p>
        </div>
        <div className="rounded-3xl border border-zinc-800 bg-zinc-950/50 p-8">
          <div className="text-sm uppercase text-zinc-400">Promessa</div>
          <p className="mt-3 text-zinc-300">
            Previsão apenas quando o regime é estável. Alertas claros quando o sinal não é confiável.
          </p>
        </div>
      </section>

      <section className="space-y-6">
        <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">O que fazemos</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FeatureCard title="Detecção de Regime e Risco">
            Detecta regimes de volatilidade, instabilidade e transições com assinaturas estatísticas
            e dinâmicas robustas.
          </FeatureCard>
          <FeatureCard title="Confiança e Estabilidade">
            Toda saída vem com confiança, sinais de saúde e alertas de uso explícitos.
          </FeatureCard>
          <FeatureCard title="Forecast (como diagnóstico)">
            Forecast existe apenas como contexto diagnóstico, sempre comparado a baselines simples.
          </FeatureCard>
        </div>
      </section>

      <section className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="text-sm uppercase text-zinc-400">Pronto para explorar</div>
          <h3 className="mt-3 text-3xl font-semibold tracking-tight">
            Abrir o Dashboard
          </h3>
          <p className="mt-2 text-zinc-300">
            Suporte à decisão baseado em consciência de regime e diagnósticos de risco.
          </p>
        </div>
        <a
          className="rounded-xl bg-zinc-100 text-black px-6 py-3 font-medium hover:bg-white transition"
          href="/ativos"
        >
          Abrir o Dashboard &rarr;
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
