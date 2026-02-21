import Link from "next/link";

const sectors = [
  { id: "finance", label: "Finanças" },
];

export default function DashboardLayout({
  children,
  active,
}: {
  children: React.ReactNode;
  active?: string;
}) {
  return (
    <div className="min-h-[calc(100vh-2rem)] grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6">
      <aside className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold tracking-tight">Assyntrax</div>
            <div className="text-xs text-zinc-400">Dashboard de regime</div>
          </div>
          <span className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">Live</span>
        </div>
        <nav className="mt-6 space-y-2 text-sm">
          <Link
            href="/app/dashboard"
            className="block rounded-2xl border border-zinc-800 bg-black/40 px-3 py-2 text-zinc-200 hover:border-cyan-400/50 transition"
          >
            Visão geral
          </Link>
          {sectors.map((s) => (
            <Link
              key={s.id}
              href={`/app/dashboard?sector=${s.id}`}
              className={`block rounded-2xl border px-3 py-2 transition ${
                active === s.id
                  ? "border-cyan-400/60 bg-cyan-950/30 text-cyan-100"
                  : "border-zinc-800 bg-black/40 text-zinc-300 hover:border-cyan-400/50"
              }`}
            >
              {s.label}
            </Link>
          ))}
        </nav>
        <div className="mt-6 border-t border-zinc-800 pt-4 text-xs text-zinc-400">
          <div className="flex items-center justify-between">
            <span>Voltar</span>
            <Link className="underline hover:text-zinc-200" href="/app/dashboard">
              Dashboard
            </Link>
          </div>
        </div>
      </aside>

      <main className="space-y-6">{children}</main>
    </div>
  );
}
