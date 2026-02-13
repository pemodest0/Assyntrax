import { readGlobalStatus, readLatestSnapshot, readRiskTruthPanel } from "@/lib/server/data";

function toNum(v: unknown, fallback = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export default async function MetodologiaPage() {
  const [snap, globalStatus, panel] = await Promise.all([
    readLatestSnapshot(),
    readGlobalStatus(),
    readRiskTruthPanel(),
  ]);

  const summary = (snap?.summary || {}) as Record<string, unknown>;
  const checks = (globalStatus?.checks || {}) as Record<string, unknown>;
  const scores = (globalStatus?.scores || {}) as Record<string, unknown>;
  const counts = (panel?.counts || {}) as Record<string, unknown>;
  const entries = Array.isArray(panel?.entries) ? (panel?.entries as Record<string, unknown>[]) : [];
  const sample = entries.slice(0, 5);

  return (
    <div className="p-5 md:p-6 lg:p-8 space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5">
        <p className="text-xs tracking-[0.14em] uppercase text-zinc-500">Nível 2 - Método e auditoria</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Metodologia e evidências do run atual</h1>
        <p className="mt-3 text-sm text-zinc-300">
          Todos os números abaixo são carregados de artefatos reais do repositório: snapshot validado,
          painel de verdade de risco e status global.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        <Metric title="Global status" value={String(globalStatus?.status || "unknown").toUpperCase()} />
        <Metric title="Run id" value={String(snap?.runId || "n/a")} />
        <Metric title="Ativos no painel" value={String(toNum(counts.assets, 0))} />
        <Metric title="Validated" value={String(toNum(counts.validated, 0))} />
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
        <h2 className="text-lg font-semibold text-zinc-100">Checks globais</h2>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
          {Object.keys(checks).length ? (
            Object.entries(checks).map(([k, v]) => (
              <div key={k} className="rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300">
                <span className="text-zinc-400">{k}:</span> {String(v)}
              </div>
            ))
          ) : (
            <div className="text-zinc-400">Sem checks no status global.</div>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
        <h2 className="text-lg font-semibold text-zinc-100">Scores e contorno</h2>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
          {Object.keys(scores).length ? (
            Object.entries(scores).map(([k, v]) => (
              <div key={k} className="rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300">
                <span className="text-zinc-400">{k}:</span> {String(v)}
              </div>
            ))
          ) : (
            <div className="text-zinc-400">Sem scores no status global.</div>
          )}
          <div className="rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300">
            <span className="text-zinc-400">deployment_gate.blocked:</span>{" "}
            {String(((summary.deployment_gate as Record<string, unknown> | undefined)?.blocked ?? "n/a"))}
          </div>
          <div className="rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300">
            <span className="text-zinc-400">status:</span> {String(summary.status || "n/a")}
          </div>
          <div className="rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300">
            <span className="text-zinc-400">adaptive_thresholds_available:</span>{" "}
            {String((panel as Record<string, unknown>)?.adaptive_thresholds_available ?? "n/a")}
          </div>
          <div className="rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300">
            <span className="text-zinc-400">data_adequacy_available:</span>{" "}
            {String((panel as Record<string, unknown>)?.data_adequacy_available ?? "n/a")}
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
        <h2 className="text-lg font-semibold text-zinc-100">Amostra de auditoria por ativo</h2>
        <div className="mt-3 overflow-auto">
          <table className="w-full text-xs">
            <thead className="text-zinc-500 uppercase">
              <tr>
                <th className="text-left py-2">Ativo</th>
                <th className="text-left py-2">Status</th>
                <th className="text-left py-2">Gate reason</th>
                <th className="text-left py-2">Thr conf/qual/trans</th>
                <th className="text-left py-2">Adequação</th>
                <th className="text-left py-2">Pseudo bifurcation</th>
              </tr>
            </thead>
            <tbody>
              {sample.map((e, idx) => {
                const gates = (e.gates || {}) as Record<string, unknown>;
                const thr = (gates.thresholds || {}) as Record<string, unknown>;
                const adq = (gates.data_adequacy || {}) as Record<string, unknown>;
                const macro = (e.macro || {}) as Record<string, unknown>;
                return (
                  <tr key={`${e.asset_id || "asset"}-${idx}`} className="border-t border-zinc-800/70 text-zinc-300">
                    <td className="py-2">{String(e.asset_id || "--")}</td>
                    <td className="py-2">{String(e.risk_truth_status || "--")}</td>
                    <td className="py-2">{String(gates.status_reason || "--")}</td>
                    <td className="py-2">
                      {`${toNum(thr.thr_conf).toFixed(2)} / ${toNum(thr.thr_quality).toFixed(2)} / ${toNum(thr.thr_transition).toFixed(2)}`}
                    </td>
                    <td className="py-2">{String(adq.status || "--")} ({String(adq.n_points || "--")} pts)</td>
                    <td className="py-2">{String(Boolean(macro.pseudo_bifurcation_flag))}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!sample.length ? <div className="text-zinc-500 mt-2">Sem entries no risk_truth_panel.</div> : null}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
        <h2 className="text-lg font-semibold text-zinc-100">Caveats de uso</h2>
        <ul className="mt-3 space-y-2 text-sm text-zinc-300">
          <li>1. O motor é radar de regime e risco, não previsão garantida de preço.</li>
          <li>2. Sinal inconclusivo deve ficar em modo diagnóstico, sem ação automática.</li>
          <li>3. Backtest e replay não garantem resultado futuro.</li>
          <li>4. Custos de transação e latência podem degradar desempenho operacional.</li>
          <li>5. Decisão final exige contexto de domínio e governança de risco.</li>
        </ul>
      </section>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
      <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">{title}</div>
      <div className="mt-2 text-lg font-semibold text-zinc-100">{value}</div>
    </div>
  );
}
