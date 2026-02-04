import "@/app/globals.css";
import Link from "next/link";

const nav = [
  { href: "/ativos", label: "Ativos" },
  { href: "/setores", label: "Setores" },
  { href: "/benchmark", label: "Benchmark" },
  { href: "/simulador", label: "Simulador" },
  { href: "/forecast-check", label: "Forecast Check" },
  { href: "/api-docs", label: "API" },
  { href: "/sobre", label: "Sobre" },
];

export default function ProductLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-zinc-950 to-black text-zinc-100">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          <aside className="col-span-12 lg:col-span-3">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 backdrop-blur shadow-lg p-4">
              <div className="text-lg font-semibold tracking-tight">Assyntrax</div>
              <div className="text-xs text-zinc-400">Diagnóstico de Regimes</div>
              <nav className="mt-6 space-y-1 text-sm">
                {nav.map((n) => (
                  <Link
                    key={n.href}
                    href={n.href}
                    className="block rounded-xl px-3 py-2 hover:bg-zinc-800/60 transition border border-transparent hover:border-zinc-700"
                  >
                    {n.label}
                  </Link>
                ))}
              </nav>
              <div className="mt-6 border-t border-zinc-800 pt-4 text-xs text-zinc-400">
                <Link className="underline hover:text-zinc-200" href="/">
                  Voltar ao site
                </Link>
              </div>
            </div>
          </aside>
          <main className="col-span-12 lg:col-span-9">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur shadow-lg w-full p-6">
              {children}
            </div>
            <footer className="mt-6 rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 text-xs text-zinc-400">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>© {new Date().getFullYear()} Assyntrax — Diagnóstico sem promessas de retorno.</div>
                <div className="flex items-center gap-4">
                  <Link className="hover:text-zinc-200" href="/sobre">Sobre</Link>
                  <Link className="hover:text-zinc-200" href="/contact">Contato</Link>
                  <Link className="hover:text-zinc-200" href="/policy">Política de Privacidade</Link>
                </div>
              </div>
            </footer>
          </main>
        </div>
      </div>
    </div>
  );
}
