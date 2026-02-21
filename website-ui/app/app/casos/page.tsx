import { DOMAIN_LABELS, STORY_CASES } from "@/lib/story/cases";
import { readLatestSnapshot, readRiskTruthPanel } from "@/lib/server/data";

type Domain = "finance" | "macro" | "realestate";

function domainCount(entries: Record<string, unknown>[], domain: Domain) {
  return entries.filter((entry) => {
    const asset = String(entry.asset_id || "");
    const row = String(entry.domain || "");
    if (row) return row === domain;
    if (domain === "finance") return asset.includes("USD") || asset.includes("SPY") || asset.includes("QQQ");
    if (domain === "realestate") return asset.includes("FIPEZAP") || asset.includes("IMOB");
    if (domain === "macro") return asset.includes("DGS") || asset.includes("DX");
    return false;
  }).length;
}

export default async function CasosPage() {
  const [snap, panel] = await Promise.all([readLatestSnapshot(), readRiskTruthPanel()]);
  const entries = Array.isArray(panel?.entries) ? (panel.entries as Record<string, unknown>[]) : [];

  return (
    <div className="p-5 md:p-6 lg:p-8 space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5">
        <p className="text-xs tracking-[0.14em] uppercase text-zinc-500">Nível 1 - Storyline</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Casos reais de transição de regime</h1>
        <p className="mt-3 text-sm text-zinc-300">
          Esta página mostra uso operacional do motor como radar de risco. Os textos são narrativos, mas o status exibido
          vem da execução válida mais recente e do painel de verdade de risco.
        </p>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          {(["finance", "macro", "realestate"] as Domain[]).map((domain) => (
            <div key={domain} className="rounded-xl border border-zinc-800 bg-black/30 p-3">
              <div className="text-zinc-400">{DOMAIN_LABELS[domain]}</div>
              <div className="text-xl font-semibold mt-1">{domainCount(entries, domain)}</div>
              <div className="text-xs text-zinc-500 mt-1">ativos com classificação no painel</div>
            </div>
          ))}
        </div>
        <div className="mt-4 text-xs text-zinc-500">execução de referência: {snap?.runId || "indisponível"}</div>
      </section>

      <section className="space-y-4">
        {STORY_CASES.map((item) => (
          <article key={item.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-full border border-zinc-700 px-2 py-1 text-zinc-300">{DOMAIN_LABELS[item.domain]}</span>
              <span className="rounded-full border border-zinc-700 px-2 py-1 text-zinc-400">{item.period}</span>
            </div>
            <h2 className="mt-3 text-lg md:text-xl font-semibold text-zinc-100">{item.title}</h2>
            <div className="mt-3 space-y-2 text-sm text-zinc-300">
              <p><span className="text-zinc-400">Contexto:</span> {item.why_matters}</p>
              <p><span className="text-zinc-400">Evento:</span> {item.what_happened}</p>
              <p><span className="text-zinc-400">Leitura do motor:</span> {item.motor_reading}</p>
              <p><span className="text-zinc-400">Uso prático:</span> {item.operational_use}</p>
              <p><span className="text-zinc-400">Limite:</span> {item.risk_limit}</p>
            </div>
            <div className="mt-4">
              <h3 className="text-xs tracking-[0.12em] uppercase text-zinc-500">Fontes</h3>
              <ul className="mt-2 space-y-1 text-sm">
                {item.sources.map((src) => (
                  <li key={`${item.id}-${src.url}`} className="text-zinc-300">
                    [{src.level}] {src.title} -{" "}
                    <a className="text-emerald-300 hover:text-emerald-200 underline underline-offset-2" href={src.url} target="_blank" rel="noreferrer">
                      link
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
