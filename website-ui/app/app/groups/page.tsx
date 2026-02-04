"use client";

import { useEffect, useMemo, useState } from "react";

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

type GroupRow = {
  group: string;
  n: number;
  avgRisk: number;
  avgConfidence: number;
  avgPredictability: number;
  avgMase: number;
};

export default function GroupsPage() {
  const [tf, setTf] = useState<"daily" | "weekly">("weekly");
  const [records, setRecords] = useState<UniverseRecord[]>([]);

  useEffect(() => {
    fetch(`/data/latest/universe_${tf}.json`)
      .then((r) => r.json())
      .then((j) => setRecords(Array.isArray(j) ? j : []))
      .catch(() => setRecords([]));
  }, [tf]);

  const groups = useMemo(() => {
    const map = new Map<string, UniverseRecord[]>();
    for (const r of records) {
      if (!map.has(r.group)) map.set(r.group, []);
      map.get(r.group)!.push(r);
    }
    const rows: GroupRow[] = [];
    for (const [group, items] of map.entries()) {
      const n = items.length;
      const avgRisk = items.reduce((s, r) => s + r.risk.p, 0) / n;
      const avgConfidence = items.reduce((s, r) => s + r.state.confidence, 0) / n;
      const avgPredictability = items.reduce((s, r) => s + r.predictability.score, 0) / n;
      const avgMase = items.reduce((s, r) => s + r.forecast_diag.mase, 0) / n;
      rows.push({ group, n, avgRisk, avgConfidence, avgPredictability, avgMase });
    }
    return rows.sort((a, b) => b.avgPredictability - a.avgPredictability);
  }, [records]);

  return (
    <div className="p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Groups / Rankings</div>
          <div className="text-sm text-zinc-400 mt-1">Compare groups by confidence and predictability.</div>
        </div>
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
      </div>

      <div className="mt-6 rounded-2xl border border-zinc-800 bg-black/30 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-black/60 text-zinc-400">
              <tr>
                <th className="px-4 py-3 text-left">Group</th>
                <th className="px-4 py-3 text-left">Assets</th>
                <th className="px-4 py-3 text-left">Avg risk</th>
                <th className="px-4 py-3 text-left">Avg confidence</th>
                <th className="px-4 py-3 text-left">Predictability</th>
                <th className="px-4 py-3 text-left">Avg MASE</th>
              </tr>
            </thead>
            <tbody>
              {groups.map((g) => (
                <tr key={g.group} className="border-t border-zinc-800">
                  <td className="px-4 py-3 font-medium">{g.group}</td>
                  <td className="px-4 py-3">{g.n}</td>
                  <td className="px-4 py-3">{g.avgRisk.toFixed(2)}</td>
                  <td className="px-4 py-3">{Math.round(g.avgConfidence * 100)}%</td>
                  <td className="px-4 py-3">{Math.round(g.avgPredictability)}</td>
                  <td className="px-4 py-3">{g.avgMase.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
