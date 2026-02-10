"use client";

import { useEffect, useMemo, useState } from "react";

type IndexFile = {
  rel_path: string;
  filename: string;
  mtime_iso: string;
  run_id: string;
  asset: string;
  freq?: string;
  artifact_type: string;
  tags?: string[];
};

type IndexPayload = {
  files: IndexFile[];
  assets?: string[];
};

const PLOT_NAMES = new Set([
  "embedding_2d.png",
  "timeline_regime.png",
  "transition_matrix.png",
]);

export default function RecentDiagnostics() {
  const [index, setIndex] = useState<IndexPayload | null>(null);
  const [asset, setAsset] = useState("");
  const [since, setSince] = useState("");
  const [freq, setFreq] = useState("weekly");

  useEffect(() => {
    fetch("/api/index")
      .then((r) => r.json())
      .then((j) => setIndex(j))
      .catch(() => setIndex(null));
  }, []);

  const items = useMemo(() => {
    const files = index?.files || [];
    return files
      .filter((f) => f.artifact_type === "image")
      .filter((f) => f.rel_path.includes("latest_graph/assets"))
      .filter((f) => PLOT_NAMES.has(f.filename))
      .filter((f) => (freq ? (f.freq || "weekly") === freq : true))
      .filter((f) => (asset ? f.asset === asset : true))
      .filter((f) => {
        if (!since) return true;
        return f.mtime_iso?.slice(0, 10) >= since;
      })
      .sort((a, b) => (a.mtime_iso < b.mtime_iso ? 1 : -1))
      .slice(0, 9);
  }, [index, asset, since, freq]);

  const assetList = useMemo(() => {
    const files = index?.files || [];
    const set = new Set<string>();
    for (const f of files) {
      if (f.rel_path.includes("latest_graph/assets")) set.add(f.asset);
    }
    return Array.from(set).sort();
  }, [index]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">
          Recent Diagnostics
        </div>
        <div className="flex flex-wrap gap-2 ml-auto">
          <select
            className="rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-xs"
            value={freq}
            onChange={(e) => setFreq(e.target.value)}
          >
            <option value="weekly">Weekly</option>
            <option value="daily">Daily</option>
          </select>
          <select
            className="rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-xs"
            value={asset}
            onChange={(e) => setAsset(e.target.value)}
          >
            <option value="">All assets</option>
            {assetList.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
          <input
            className="rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-xs"
            type="date"
            value={since}
            onChange={(e) => setSince(e.target.value)}
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items.map((item) => (
          <div
            key={item.rel_path}
            className="rounded-2xl border border-zinc-800 bg-zinc-950/70 overflow-hidden"
          >
            <div
              className="h-48 bg-cover bg-center"
              style={{ backgroundImage: `url(/api/files/${item.rel_path})` }}
            />
            <div className="px-4 py-3 text-xs text-zinc-300">
              <div className="font-semibold">{item.asset} · {item.freq || "weekly"}</div>
              <div className="text-zinc-500">{item.filename.replace(".png", "")}</div>
              <div className="text-zinc-600">{item.mtime_iso?.slice(0, 10)}</div>
            </div>
          </div>
        ))}
        {!items.length && (
          <div className="col-span-full rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6 text-sm text-zinc-400">
            Nenhum plot encontrado. Rode o Graph Engine para gerar
            <span className="text-zinc-200"> embedding_2d / timeline_regime / transition_matrix</span>.
          </div>
        )}
      </div>
      <div className="text-xs text-zinc-500">
        O que você está vendo: mapas do embedding, linha temporal do regime e matriz de transição.
      </div>
    </div>
  );
}
