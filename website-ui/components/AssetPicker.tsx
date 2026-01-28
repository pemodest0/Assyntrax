"use client";

import { useEffect, useMemo, useState } from "react";
import { useAsset } from "@/lib/asset-context";

export default function AssetPicker() {
  const { asset, setAsset, timeframe, setTimeframe } = useAsset();
  const [options, setOptions] = useState<string[]>([]);
  const [tfMap, setTfMap] = useState<Record<string, string[]>>({});

  useEffect(() => {
    fetch("/api/assets")
      .then((r) => r.json())
      .then((data) => {
        const files: string[] = data.files || [];
        const map: Record<string, string[]> = {};
        for (const f of files) {
          const m = f.match(/^(.+?)_(daily|weekly)\.json$/);
          if (!m) continue;
          const a = m[1];
          const tf = m[2];
          if (!map[a]) map[a] = [];
          if (!map[a].includes(tf)) map[a].push(tf);
        }
        const assets = Object.keys(map).sort();
        if (assets.length) {
          setOptions(assets);
          setTfMap(map);
          if (!assets.includes(asset)) setAsset(assets[0]);
          const preferred = map[asset] || [];
          if (!preferred.includes(timeframe) && preferred.length) {
            setTimeframe(preferred.includes("weekly") ? "weekly" : "daily");
          }
        }
      })
      .catch(() => {
        setOptions(["SPY", "QQQ", "GLD"]);
      });
  }, [asset, setAsset]);

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 px-4 py-3 text-sm shadow-lg backdrop-blur">
      <label className="block text-xs text-zinc-500 uppercase tracking-wide">Asset</label>
      <select
        value={asset}
        onChange={(e) => setAsset(e.target.value)}
        className="mt-1 w-44 bg-transparent outline-none text-zinc-100"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
      <label className="mt-3 block text-xs text-zinc-500 uppercase tracking-wide">Timeframe</label>
      <select
        value={timeframe}
        onChange={(e) => setTimeframe(e.target.value)}
        className="mt-1 w-44 bg-transparent outline-none text-zinc-100"
      >
        <option value="daily" disabled={tfMap[asset] && !tfMap[asset]?.includes("daily")}>
          daily
        </option>
        <option value="weekly" disabled={tfMap[asset] && !tfMap[asset]?.includes("weekly")}>
          weekly
        </option>
      </select>
    </div>
  );
}
