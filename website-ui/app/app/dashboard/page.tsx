import Link from "next/link";

const cards = [
  { href: "/ativos", title: "Ativos", desc: "Diagnóstico por ativo com regime, confiança e alertas." },
  { href: "/setores", title: "Setores", desc: "Visão por setor e agrupamentos temáticos." },
  { href: "/benchmark", title: "Benchmark", desc: "Validação, métricas e comparações oficiais." },
  { href: "/api-docs", title: "API", desc: "Documentação técnica e exemplos de uso." },
  { href: "/sobre", title: "Metodologia", desc: "Como o motor detecta regimes e evita overfit." },
];

export default function DashboardHome() {
  return (
    <div className="p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Painel Principal</h1>
        <p className="text-sm text-zinc-400">
          Acesse os módulos do diagnóstico de regimes e validações do Assyntrax.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {cards.map((c) => (
          <Link
            key={c.href}
            href={c.href}
            className="rounded-2xl border border-zinc-800 bg-black/40 p-5 hover:bg-zinc-900/60 transition"
          >
            <div className="text-lg font-semibold">{c.title}</div>
            <div className="mt-2 text-sm text-zinc-400">{c.desc}</div>
            <div className="mt-4 text-xs text-emerald-300">Abrir →</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
