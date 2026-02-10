export default function ContactPageEN() {
  return (
    <div className="space-y-10">
      <div className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-8 items-center">
        <div className="space-y-3">
          <h1 className="text-4xl font-semibold tracking-tight">Contact</h1>
          <p className="text-zinc-300 max-w-3xl">
            Interested in collaboration, research, or integration? Tell us your use case and data
            coverage.
          </p>
          <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4 text-sm text-zinc-300">
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Quick guide</div>
            <ul className="mt-2 space-y-2">
              <li>- Share the asset list or sector scope.</li>
              <li>- Mention the timeframes you need.</li>
              <li>- Describe how you intend to consume the output (API/UI).</li>
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
          <a className="hover:text-white" href="https://github.com/pemodest0/Assyntrax">
            GitHub
          </a>
          <a className="hover:text-white" href="https://www.linkedin.com/in/pedro-henrique-gesualdo-modesto-39a135272/">
            LinkedIn
          </a>
          <a className="hover:text-white" href="https://pemodest0.github.io/">
            Portfolio
          </a>
        </div>
      </div>
    </div>
  );
}
