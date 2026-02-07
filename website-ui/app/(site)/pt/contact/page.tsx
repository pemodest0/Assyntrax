export default function ContactPage() {
  return (
    <div className="space-y-10">
      <div className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-8 items-center">
        <div className="space-y-3">
          <h1 className="text-4xl font-semibold tracking-tight">Contato</h1>
          <p className="text-zinc-300 max-w-3xl">
            Interessado em colaboração, pesquisa ou integração? Conte o cenário, ativos e
            timeframes.
          </p>
          <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4 text-sm text-zinc-300">
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Guia rápido</div>
            <ul className="mt-2 space-y-2">
              <li>• Informe o setor ou universo de ativos.</li>
              <li>• Diga as frequências necessárias (diário/semanal).</li>
              <li>• Explique como pretende consumir as saídas (API/UI).</li>
            </ul>
          </div>
        </div>
        <div className="relative h-[260px] rounded-3xl border border-zinc-800 overflow-hidden">
          <div className="absolute inset-0 bg-[url('/visuals/hero-flow.svg')] bg-cover bg-center opacity-95 animate-drift" />
          <div className="absolute inset-0 hero-noise" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
        </div>
      </div>

      <div className="space-y-3 text-zinc-200">
        <div>
          Email:{" "}
          <a className="hover:text-white" href="mailto:contact@assyntrax.ai">
            contact@assyntrax.ai
          </a>
        </div>
        <div className="flex gap-4 text-sm">
          <a className="hover:text-white" href="https://github.com/assyntrax">
            GitHub
          </a>
          <a className="hover:text-white" href="https://www.linkedin.com/company/assyntrax/">
            LinkedIn
          </a>
        </div>
      </div>
    </div>
  );
}
