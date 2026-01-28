export default function HomePage() {
  return (
    <div className="py-12">
      <div className="rounded-3xl border border-zinc-800 bg-zinc-950/50 p-10 backdrop-blur">
        <div className="text-xs uppercase text-zinc-400">Regime &amp; Risk Engine</div>
        <h1 className="mt-4 text-5xl font-semibold tracking-tight">
          Diagnóstico de regimes e risco para decisões mais seguras
        </h1>
        <p className="mt-4 text-zinc-300 max-w-3xl">
          Não prometemos “prever preço”. Nosso produto detecta mudanças de estado: volatilidade
          alta/baixa, instabilidade e transições de regime. Forecast entra apenas como diagnóstico,
          sempre comparado ao baseline.
        </p>
        <div className="mt-6 flex gap-3">
          <a
            className="rounded-xl bg-zinc-100 text-black px-4 py-2 font-medium hover:bg-white transition"
            href="/app/dashboard"
          >
            Open App
          </a>
          <a
            className="rounded-xl border border-zinc-800 px-4 py-2 text-zinc-200 hover:border-zinc-600 transition"
            href="/methods"
          >
            Métodos
          </a>
        </div>
      </div>
    </div>
  );
}
