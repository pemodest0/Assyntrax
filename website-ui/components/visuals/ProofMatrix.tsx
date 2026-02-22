"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

type MethodologyPayload = {
  run_id?: string | null;
  summary?: { deployment_gate?: { blocked?: boolean } } | null;
  global_status?: { status?: string } | null;
  risk_truth_panel?: {
    counts?: { assets?: number; validated?: number; watch?: number; inconclusive?: number };
  } | null;
};

function toNum(value: unknown, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export default function ProofMatrix() {
  const [data, setData] = useState<MethodologyPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetch("/api/methodology", { cache: "no-store" });
        if (!res.ok) throw new Error("methodology_fetch_failed");
        const payload = (await res.json()) as MethodologyPayload;
        if (!active) return;
        setData(payload);
      } catch {
        if (!active) return;
        setError(true);
      } finally {
        if (!active) return;
        setLoading(false);
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  const cards = useMemo(() => {
    const counts = data?.risk_truth_panel?.counts || {};
    const assets = toNum(counts.assets, 0);
    const validated = toNum(counts.validated, 0);
    const watch = toNum(counts.watch, 0);
    const inconclusive = toNum(counts.inconclusive, 0);
    const gateBlocked = data?.summary?.deployment_gate?.blocked;
    const globalStatus = String(data?.global_status?.status || "unknown").toUpperCase();
    return [
      {
        label: "RUN_ID",
        value: String(data?.run_id || "n/a"),
        note: "Snapshot published",
        help: "Identifier of the run currently exposed by the site.",
      },
      {
        label: "STATUS",
        value: globalStatus,
        note: "Global gate",
        help: "Operational status loaded from methodology artifacts.",
      },
      {
        label: "VALIDATED",
        value: `${validated}/${assets}`,
        note: "Risk panel",
        help: "Validated assets over total assets in risk_truth_panel.",
      },
      {
        label: "WATCH+INC",
        value: `${watch + inconclusive}`,
        note: "Monitoring",
        help: "Watch and inconclusive assets currently under monitoring.",
      },
      {
        label: "DEPLOY",
        value: gateBlocked == null ? "n/a" : gateBlocked ? "BLOCKED" : "OPEN",
        note: "Deployment gate",
        help: "Deployment lock state from run summary.",
      },
    ];
  }, [data]);

  return (
    <motion.div
      className="rounded-3xl border border-zinc-800 bg-zinc-950/70 p-6"
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Auditable evidence</div>
      <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
        {cards.map((m) => (
          <div
            key={m.label}
            className="group rounded-2xl border border-zinc-800 bg-black/60 p-4 transition hover:-translate-y-1 hover:border-zinc-600"
          >
            <div className="text-xs text-zinc-500">{m.note}</div>
            <div className="mt-2 text-2xl font-semibold text-zinc-100">{m.value}</div>
            <div className="mt-1 flex items-center gap-2">
              <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">{m.label}</div>
              <span
                className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-zinc-700 text-[10px] text-zinc-400"
                title={m.help}
              >
                ?
              </span>
            </div>
            <div className="mt-2 hidden rounded-lg border border-zinc-800 bg-zinc-950/90 p-2 text-[11px] text-zinc-300 group-hover:block">
              {m.help}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 text-xs text-zinc-500">
        {loading ? "Loading auditable artifacts..." : null}
        {!loading && error ? "Failed to load /api/methodology." : null}
        {!loading && !error ? "Numbers are sourced from run and risk panel artifacts." : null}
      </div>
    </motion.div>
  );
}
