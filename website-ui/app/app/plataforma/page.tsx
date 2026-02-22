import { readPlatformDbRelease, readPlatformDbSnapshot } from "@/lib/server/data";

function toNum(v: unknown, fallback = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export default async function PlataformaPage() {
  const [snapshot, release] = await Promise.all([readPlatformDbSnapshot(), readPlatformDbRelease()]);
  const snap = (snapshot || {}) as Record<string, unknown>;
  const counts = ((snap.counts || {}) as Record<string, unknown>) || {};
  const run = ((snap.run || {}) as Record<string, unknown>) || {};
  const copilot = ((snap.copilot || {}) as Record<string, unknown>) || {};
  const domains = Array.isArray(snap.domains) ? (snap.domains as Record<string, unknown>[]) : [];
  const signalStatus = Array.isArray(snap.signal_status) ? (snap.signal_status as Record<string, unknown>[]) : [];

  return (
    <div className="p-5 md:p-6 lg:p-8 space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5">
        <p className="text-xs tracking-[0.14em] uppercase text-zinc-500">Plataforma</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Executavel + Banco + Site</h1>
        <p className="mt-3 text-sm text-zinc-300">
          Estado do banco operacional indexado pelo pipeline diario. Fonte: `results/platform/latest_db_snapshot.json`.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        <Card title="Run indexado" value={String(snap.run_id || "--")} />
        <Card title="Runs totais" value={String(toNum(counts.runs_total, 0))} />
        <Card title="Rows do run" value={String(toNum(counts.asset_rows_for_run, 0))} />
        <Card title="Copiloto publicavel" value={copilot.publishable === true ? "sim" : "nao"} />
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-4">
          <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Run</div>
          <div className="mt-2 text-sm text-zinc-300">status: {String(run.status || "--")}</div>
          <div className="mt-1 text-sm text-zinc-300">gate_blocked: {String(Boolean(run.gate_blocked))}</div>
          <div className="mt-1 text-sm text-zinc-300">
            validated/watch/inconclusive: {toNum(run.validated_signals, 0)}/{toNum(run.watch_signals, 0)}/
            {toNum(run.inconclusive_signals, 0)}
          </div>
          <div className="mt-1 text-sm text-zinc-300">validated_ratio: {toNum(run.validated_ratio, 0).toFixed(3)}</div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-4">
          <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Copiloto</div>
          <div className="mt-2 text-sm text-zinc-300">row_exists: {String(copilot.row_exists === true)}</div>
          <div className="mt-1 text-sm text-zinc-300">publishable: {String(copilot.publishable === true)}</div>
          <div className="mt-1 text-sm text-zinc-300">risk: {String(copilot.risk_structural ?? "--")}</div>
          <div className="mt-1 text-sm text-zinc-300">confidence: {String(copilot.confidence ?? "--")}</div>
          <div className="mt-1 text-sm text-zinc-300">risk_level: {String(copilot.risk_level || "--")}</div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-4">
          <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Dominios</div>
          <ul className="mt-2 space-y-1 text-sm text-zinc-300">
            {domains.length ? (
              domains.map((d, idx) => (
                <li key={`d-${idx}`}>
                  {String(d.domain || "--")}: {String(d.count || 0)}
                </li>
              ))
            ) : (
              <li>Sem dados.</li>
            )}
          </ul>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-4">
          <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Signal Status</div>
          <ul className="mt-2 space-y-1 text-sm text-zinc-300">
            {signalStatus.length ? (
              signalStatus.map((s, idx) => (
                <li key={`s-${idx}`}>
                  {String(s.status || "--")}: {String(s.count || 0)}
                </li>
              ))
            ) : (
              <li>Sem dados.</li>
            )}
          </ul>
        </div>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-4 text-xs text-zinc-400">
        db_path: {String(snap.db_path || "--")} | release atualizado em:{" "}
        {String((release as Record<string, unknown>)?.updated_at_utc || "--")}
      </section>
    </div>
  );
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
      <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">{title}</div>
      <div className="mt-2 text-lg font-semibold text-zinc-100">{value}</div>
    </div>
  );
}

