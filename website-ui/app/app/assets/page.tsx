"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

type UniverseRecord = {
  asset: string;
  group: string;
  timeframe: "daily" | "weekly";
  asof: string;
  risk: { label: string; p: number };
  state: { label: string; confidence: number };
  predictability: { score: number; label: string };
  forecast_diag: { mase: number; dir_acc: number; alerts?: string[] };
  alerts?: string[];
};

export default function AssetsPage() {
  const [tf, setTf] = useState<"daily" | "weekly">("weekly");
  const [records, setRecords] = useState<UniverseRecord[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch(`/data/latest/universe_${tf}.json`)
      .then((r) => r.json())
      .then((j) => setRecords(Array.isArray(j) ? j : []))
      .catch(() => setRecords([]));
  }, [tf]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return records;
    return records.filter((r) => r.asset.toLowerCase().includes(q));
  }, [records, search]);

  return (
    <div className="p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Assets</div>
          <div className="text-sm text-zinc-400 mt-1">Explore asset pages and diagnostics.</div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-xl border border-zinc-800 bg-black/40 p-1">
            <button
              onClick={() => setTf("weekly")}
              className={`px-3 py-1.5 rounded-lg text-sm transition ${
                tf === "weekly" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Weekly
            </button>
            <button
              onClick={() => setTf("daily")}
              className={`px-3 py-1.5 rounded-lg text-sm transition ${
                tf === "daily" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Daily
            </button>
          </div>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search ticker"
            className="rounded-xl border border-zinc-800 bg-black/40 px-3 py-2 text-sm outline-none"
          />
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((r) => (
          <Link
            key={`${r.asset}-${r.timeframe}`}
            href={`/app/assets/${r.asset}`}
            className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-4 hover:border-zinc-600 transition"
          >
            <div className="text-lg font-semibold">{r.asset}</div>
            <div className="text-xs text-zinc-400">{r.group}</div>
            <div className="mt-3 text-sm text-zinc-300">
              State: {r.state.label} ({Math.round(r.state.confidence * 100)}%)
            </div>
            <div className="text-sm text-zinc-300">Risk: {r.risk.label}</div>
            <div className="text-xs text-zinc-500 mt-2">As of {r.asof}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
