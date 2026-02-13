export default function ContactPage() {
  return (
    <div className="space-y-10">
      <section className="rounded-[28px] border border-zinc-800 bg-zinc-950/60 p-8 lg:p-10">
        <div className="space-y-3 max-w-3xl">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Contato</div>
          <h1 className="text-4xl font-semibold tracking-tight">Fale com a equipe da Assyntrax</h1>
          <p className="text-zinc-300">
            Descreva seu caso de uso com contexto objetivo: setor, ativos, horizonte e como a saída será usada.
            Retornaremos com um plano de avaliação técnica.
          </p>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6 space-y-4">
          <label className="text-sm text-zinc-300" htmlFor="email">
            E-mail para retorno
          </label>
          <input
            id="email"
            type="email"
            placeholder="voce@empresa.com"
            className="w-full rounded-xl border border-zinc-700 bg-black/40 px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
          />

          <label className="text-sm text-zinc-300" htmlFor="contexto">
            Contexto do pedido
          </label>
          <textarea
            id="contexto"
            rows={8}
            placeholder="Descreva o setor, os ativos, a frequência dos dados e o objetivo operacional."
            className="w-full rounded-xl border border-zinc-700 bg-black/40 px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
          />

          <div className="text-xs text-zinc-500">
            Canal de e-mail oficial da Assyntrax está em implantação. Use os links abaixo para contato direto temporário.
          </div>
        </div>

        <aside className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Links</div>
          <div className="mt-4 flex flex-col gap-3 text-sm">
            <a className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500" href="https://github.com/pemodest0/Assyntrax">
              GitHub do projeto
            </a>
            <a className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500" href="https://github.com/pemodest0">
              GitHub pessoal
            </a>
            <a className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500" href="https://www.linkedin.com/in/pedro-henrique-gesualdo-modesto-39a135272/">
              LinkedIn
            </a>
            <a className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500" href="https://pemodest0.github.io/">
              Portfólio
            </a>
          </div>
        </aside>
      </section>
    </div>
  );
}


