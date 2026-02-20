import Link from "next/link";
import {
  findLatestLabCorrRun,
  readLatestLabCorrActionPlaybook,
  readLatestLabCorrBacktestSummary,
  readLatestLabCorrCaseStudies,
  readLatestLabCorrEraEvaluation,
  readLatestLabCorrOperationalAlerts,
  readLatestLabCorrTimeseries,
} from "@/lib/server/data";

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function fmtPct(value: number | null, digits = 2) {
  if (value == null || !Number.isFinite(value)) return "--";
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(digits)}%`;
}

function fmtNum(value: number | null, digits = 3) {
  if (value == null || !Number.isFinite(value)) return "--";
  return value.toFixed(digits);
}

export default async function DashboardHome() {
  const [labRun, ts, cases, opAlerts, eraEval, playbook, bt] = await Promise.all([
    findLatestLabCorrRun(),
    readLatestLabCorrTimeseries(120),
    readLatestLabCorrCaseStudies(120),
    readLatestLabCorrOperationalAlerts(120),
    readLatestLabCorrEraEvaluation(120),
    readLatestLabCorrActionPlaybook(120),
    readLatestLabCorrBacktestSummary(120),
  ]);

  const gate = ((labRun?.summary?.deployment_gate || {}) as Record<string, unknown>) || {};
  const gateBlocked = gate?.blocked === true;
  const latest = ts?.latest || null;
  const delta20 = ts?.delta_20d || null;
  const latestEvents = Array.isArray((opAlerts as Record<string, unknown>)?.latest_events)
    ? ((opAlerts as Record<string, unknown>).latest_events as unknown[]).map((x) => String(x))
    : [];
  const opLast60 = toNumber((opAlerts as Record<string, unknown>)?.n_events_last_60d) ?? 0;

  const btObj = (bt || {}) as Record<string, unknown>;
  const s = ((btObj.strategy || {}) as Record<string, unknown>) || {};
  const b = ((btObj.benchmark || {}) as Record<string, unknown>) || {};
  const sAnn = toNumber(s.ann_return);
  const bAnn = toNumber(b.ann_return);
  const sMdd = toNumber(s.max_drawdown);
  const bMdd = toNumber(b.max_drawdown);
  const alphaAnn = sAnn != null && bAnn != null ? sAnn - bAnn : null;
  const ddImprovement = sMdd != null && bMdd != null ? Math.abs(bMdd) - Math.abs(sMdd) : null;
  const modeLabel = alphaAnn != null && alphaAnn > 0.02 ? "Alpha" : "Protection";

  const playRows = Array.isArray(playbook) ? (playbook as Record<string, unknown>[]) : [];
  const latestPlay = playRows.length ? playRows[playRows.length - 1] : null;
  const eraRows = Array.isArray(eraEval) ? (eraEval as Record<string, unknown>[]) : [];
  const caseRows = cases?.cases || [];

  return (
    <div className="p-5 md:p-6 lg:p-8 space-y-6 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.10),transparent_40%),radial-gradient(circle_at_top_left,rgba(56,189,248,0.12),transparent_42%)]">
      <section className="rounded-2xl border border-cyan-800/40 bg-gradient-to-br from-zinc-950 via-zinc-950 to-cyan-950/30 p-5 md:p-6">
        <p className="text-xs uppercase tracking-[0.16em] text-zinc-500">Control Center</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Operational Dashboard</h1>
        <p className="mt-3 text-sm md:text-base text-zinc-300 max-w-3xl">
          Regime engine with explicit trade-off: when alpha is weak but drawdown improves, the system is in protection mode.
        </p>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          <HeroKpi label="Run" value={labRun?.runId || "unavailable"} tone="neutral" />
          <HeroKpi label="Gate" value={gateBlocked ? "blocked" : "ok"} tone={gateBlocked ? "danger" : "good"} />
          <HeroKpi label="Mode" value={modeLabel} tone={modeLabel === "Alpha" ? "good" : "warn"} />
          <HeroKpi
            label="Regime / Action"
            value={`${String(latestPlay?.regime || "--")} / ${String(latestPlay?.action_code || "--")}`}
            tone="neutral"
          />
        </div>

        <div className="mt-3 text-xs text-zinc-400">
          signal_tier: <span className="text-zinc-200">{String(latestPlay?.signal_tier || "--")}</span> | latest events:{" "}
          <span className="text-zinc-200">{latestEvents.length ? latestEvents.join(", ") : "none"}</span>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <DomainCard
          title="Finance"
          text="Regime reading for liquid assets with structural-risk focus and actionable playbook."
          href="/app/finance"
          cta="Open Finance"
        />
        <DomainCard
          title="Real Estate"
          text="City/UF cycle diagnostics with price, liquidity, rates and transition handling."
          href="/app/real-estate"
          cta="Open Real Estate"
        />
      </section>

      <section className="grid grid-cols-1 md:grid-cols-1 gap-4">
        <DomainCard
          title="Setores"
          text="Niveis verde, amarelo e vermelho por setor, com ranking de antecipacao de estresse em 5 dias."
          href="/app/setores"
          cta="Open Sectors"
        />
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/55 p-5 space-y-3">
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">Macro Lab T120</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <MetricCard
            title="Current state"
            line1={latest ? `${latest.date} | N=${latest.N_used}` : "--"}
            line2={`p1=${fmtNum(toNumber(latest?.p1), 4)} | deff=${fmtNum(toNumber(latest?.deff), 2)}`}
          />
          <MetricCard
            title="Delta 20d"
            line1={`dp1=${fmtNum(toNumber(delta20?.p1), 4)}`}
            line2={`ddeff=${fmtNum(toNumber(delta20?.deff), 3)}`}
          />
          <MetricCard
            title="Operational alerts"
            line1={latestEvents.length ? latestEvents.join(", ") : "none"}
            line2={`events in 60d: ${fmtNum(opLast60, 0)}`}
          />
        </div>
      </section>

      <section className="rounded-2xl border border-amber-800/40 bg-gradient-to-br from-zinc-950 to-amber-950/20 p-5 space-y-3">
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">Motor mode</p>
        <div className="text-sm">
          <span className="text-zinc-400">Reading:</span>{" "}
          <span className={modeLabel === "Alpha" ? "text-emerald-300" : "text-amber-300"}>{modeLabel}</span>
        </div>
        <div className="text-sm text-zinc-300">annual alpha vs benchmark: {fmtPct(alphaAnn, 2)}</div>
        <div className="text-sm text-zinc-300">drawdown improvement: {fmtPct(ddImprovement, 2)}</div>
        <div className="text-xs text-zinc-500">
          If annual alpha is low/negative and drawdown improves, the engine is operating as risk protection.
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/55 p-5 space-y-3">
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">Playbook now</p>
        {latestPlay ? (
          <>
            <div className="text-sm text-zinc-300">
              {String(latestPlay.date || "--")} | regime={String(latestPlay.regime || "--")} | action={" "}
              <span className="text-zinc-100">{String(latestPlay.action_code || "--")}</span>
            </div>
            <div className="text-sm text-zinc-300">
              signal={String(latestPlay.signal_tier || "--")} ({fmtNum(toNumber(latestPlay.signal_reliability), 3)}) | tradeoff={" "}
              {String(latestPlay.tradeoff_label || "--")}
            </div>
          </>
        ) : (
          <div className="text-sm text-zinc-400">No playbook available.</div>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/55 p-5 space-y-3">
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">Case studies</p>
        {caseRows.length ? (
          <div className="space-y-2 text-sm text-zinc-300">
            {caseRows.slice(0, 3).map((row) => (
              <div key={`${row.case_regime}-${row.date}`} className="rounded-lg border border-zinc-800 bg-black/30 p-3">
                <div className="text-zinc-100">
                  {String(row.case_regime).toUpperCase()} | {String(row.date)}
                </div>
                <div>alpha={fmtPct(toNumber(row.alpha_cum), 2)} | dd_improvement={fmtPct(toNumber(row.dd_improvement), 2)}</div>
                <div className="text-zinc-400">{String(row.honest_verdict || "--")}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-zinc-400">No case studies available.</div>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/55 p-5 space-y-3">
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">Era comparison</p>
        {eraRows.length ? (
          <div className="space-y-2 text-sm text-zinc-300">
            {eraRows.map((row) => (
              <div key={String(row.era)} className="rounded-lg border border-zinc-800 bg-black/30 p-3">
                <div className="text-zinc-100">{String(row.era)}</div>
                <div>
                  p1_mean={fmtNum(toNumber(row.p1_mean), 3)} | deff_mean={fmtNum(toNumber(row.deff_mean), 2)} | alpha_ann={" "}
                  {fmtPct(toNumber(row.alpha_ann_return), 2)} | dd_improvement={fmtPct(toNumber(row.dd_improvement), 2)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-zinc-400">No era evaluation available.</div>
        )}
      </section>
    </div>
  );
}

function DomainCard({
  title,
  text,
  href,
  cta,
}: {
  title: string;
  text: string;
  href: string;
  cta: string;
}) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/55 p-5">
      <h2 className="text-xl font-semibold text-zinc-100">{title}</h2>
      <p className="mt-2 text-sm text-zinc-300">{text}</p>
      <Link
        href={href}
        className="inline-flex mt-4 rounded-xl border border-zinc-700 px-3 py-2 text-sm text-zinc-100 hover:border-zinc-500 transition"
      >
        {cta}
      </Link>
    </div>
  );
}

function HeroKpi({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "good" | "warn" | "danger" | "neutral";
}) {
  const toneCls =
    tone === "good"
      ? "border-emerald-700/50 bg-emerald-950/20 text-emerald-200"
      : tone === "warn"
      ? "border-amber-700/50 bg-amber-950/20 text-amber-200"
      : tone === "danger"
      ? "border-rose-700/50 bg-rose-950/20 text-rose-200"
      : "border-zinc-700/60 bg-zinc-900/40 text-zinc-200";
  return (
    <div className={`rounded-xl border p-3 ${toneCls}`}>
      <div className="text-[11px] uppercase tracking-[0.14em] opacity-80">{label}</div>
      <div className="mt-1 text-sm font-semibold break-all">{value}</div>
    </div>
  );
}

function MetricCard({
  title,
  line1,
  line2,
}: {
  title: string;
  line1: string;
  line2: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-black/30 p-3">
      <div className="text-zinc-400">{title}</div>
      <div className="text-zinc-100 mt-1 break-words">{line1}</div>
      <div className="text-zinc-300 mt-1">{line2}</div>
    </div>
  );
}
