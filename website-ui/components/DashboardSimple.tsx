"use client";

import { useEffect, useMemo, useState } from "react";
import { nameForAsset } from "@/lib/assetNames";

const labelPt: Record<string, string> = {
  STABLE: "Estável",
  TRANSITION: "Transição",
  UNSTABLE: "Instável",
  NOISY: "Ruidoso",
};

const regimeColor: Record<string, string> = {
  STABLE: "#10b981",
  TRANSITION: "#f59e0b",
  UNSTABLE: "#ef4444",
  NOISY: "#94a3b8",
};

type GraphRecord = {
  asset: string;
  timeframe?: string;
  state?: { label?: string; confidence?: number };
  quality?: { score?: number };
  recommendation?: string;
  alerts?: string[];
};

type SeriesPoint = { date: string; confidence: number; regime: string; price?: number | null };

type SeriesMap = Record<string, SeriesPoint[]>;

const categories: Record<string, string[]> = {
  all: [],
  finance: ["SPY", "QQQ", "DIA", "IWM", "VTI", "VT", "RSP", "XLF", "LQD", "HYG", "SHY", "IEF", "TLT", "TIP", "VIX", "^VIX"],
  commodities: ["GLD", "SLV", "USO", "DBC", "DBA", "XLE", "XOP", "XLB"],
  fx: ["UUP", "FXE", "FXY"],
  crypto: ["BTC-USD", "ETH-USD"],
};

const categoryLabels: Record<string, string> = {
  all: "Todos",
  finance: "Finanças",
  commodities: "Commodities",
  fx: "Moedas",
  crypto: "Cripto",
};

function useUniverseByTf(tf: "daily" | "weekly") {
  const [data, setData] = useState<GraphRecord[]>([]);
  useEffect(() => {
    fetch(`/api/graph/universe?tf=${tf}`)
      .then((r) => r.json())
      .then((j) => setData(Array.isArray(j) ? j : []))
      .catch(() => setData([]));
  }, [tf]);
  return data;
}

export default function DashboardSimple() {
  const [timeframe, setTimeframe] = useState<"daily" | "weekly">("weekly");
  const [periodDays, setPeriodDays] = useState<number>(365);
  const [assetSearch, setAssetSearch] = useState<string>("");
  const universe = useUniverseByTf(timeframe);
  const [category, setCategory] = useState("all");
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [seriesMap, setSeriesMap] = useState<SeriesMap>({});

  const tableAssets = useMemo(() => {
    const list = categories[category] || [];
    const base = category === "all" ? universe : universe.filter((u) => list.includes(u.asset));
    const needle = assetSearch.trim().toLowerCase();
    if (!needle) return base;
    return base.filter((u) => `${u.asset} ${nameForAsset(u.asset)}`.toLowerCase().includes(needle));
  }, [universe, category, assetSearch]);
  const effectiveSelectedAssets = useMemo(() => {
    if (selectedAssets.length) return selectedAssets;
    return tableAssets.slice(0, 3).map((r) => r.asset);
  }, [selectedAssets, tableAssets]);

  useEffect(() => {
    if (!effectiveSelectedAssets.length) return;
    const assets = effectiveSelectedAssets.slice(0, 3).join(",");
    const limit = timeframe === "daily" ? Math.max(60, Math.min(1500, periodDays)) : Math.max(20, Math.min(400, Math.round(periodDays / 5)));
    const step = timeframe === "daily" ? 1 : 2;
    fetch(`/api/graph/series-batch?assets=${encodeURIComponent(assets)}&tf=${timeframe}&limit=${limit}&step=${step}`)
      .then((r) => r.json())
      .then((j) => setSeriesMap(j || {}))
      .catch(() => setSeriesMap({}));
  }, [effectiveSelectedAssets, timeframe, periodDays]);

  return (
    <div className="p-6 space-y-6">
      <section className="rounded-3xl border border-zinc-800 bg-zinc-950/70 p-6">
        <div className="flex flex-wrap items-center gap-3">
          <div className="text-sm font-semibold text-zinc-100">Dashboard de Regimes</div>
          <div className="ml-auto flex flex-wrap gap-2">
            <select
              className="rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-xs text-zinc-200"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {Object.keys(categories).map((key) => (
                <option key={key} value={key}>
                  {categoryLabels[key] || key}
                </option>
              ))}
            </select>
            <select
              className="rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-xs text-zinc-200"
              value={timeframe}
              onChange={(e) => setTimeframe((e.target.value as "daily" | "weekly") || "weekly")}
            >
              <option value="weekly">Semanal</option>
              <option value="daily">Diário</option>
            </select>
            <select
              className="rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-xs text-zinc-200"
              value={periodDays}
              onChange={(e) => setPeriodDays(Number(e.target.value) || 365)}
            >
              <option value={90}>90d</option>
              <option value={180}>180d</option>
              <option value={365}>365d</option>
              <option value={730}>730d</option>
            </select>
            <input
              value={assetSearch}
              onChange={(e) => setAssetSearch(e.target.value)}
              placeholder="filtrar ativo"
              className="rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-xs text-zinc-200"
            />
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-zinc-800 bg-zinc-950/70 p-6">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-stretch">
          <div className="w-full h-[70vh] min-h-[520px]">
            <SimpleChart assets={effectiveSelectedAssets.slice(0, 3)} seriesMap={seriesMap} />
          </div>
          <div className="space-y-4">
            <div className="rounded-2xl border border-zinc-800 bg-black/40 p-4">
              <div className="text-xs text-zinc-500">Ativos (até 3)</div>
              <select
                multiple
                className="mt-2 w-full rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-xs text-zinc-200 min-h-[140px]"
                value={effectiveSelectedAssets}
                onChange={(e) => {
                  const options = Array.from(e.target.selectedOptions).map((o) => o.value);
                  setSelectedAssets(options);
                }}
              >
                {tableAssets.map((a) => (
                  <option key={a.asset} value={a.asset}>
                    {a.asset} — {nameForAsset(a.asset)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-zinc-800 bg-zinc-950/70 p-6">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Tabela principal</div>
        <div className="mt-4">
          <table className="min-w-full text-xs">
            <thead className="text-zinc-500">
              <tr>
                <th className="px-3 py-2 text-left">Ativo</th>
                <th className="px-3 py-2 text-left">Nome</th>
                <th className="px-3 py-2 text-left">Regime</th>
                <th className="px-3 py-2 text-left">Confiança</th>
                <th className="px-3 py-2 text-left">Qualidade</th>
              </tr>
            </thead>
            <tbody>
              {tableAssets.map((r) => {
                const conf = r.state?.confidence ?? 0;
                const quality = r.quality?.score ?? 0;
                return (
                  <tr key={r.asset} className="border-t border-zinc-800">
                    <td className="px-3 py-2 text-zinc-200 font-semibold">{r.asset}</td>
                    <td className="px-3 py-2 text-zinc-400">{nameForAsset(r.asset)}</td>
                    <td className="px-3 py-2 text-zinc-200">
                      {labelPt[r.state?.label || ""] ?? r.state?.label ?? "--"}
                    </td>
                    <td className="px-3 py-2 text-zinc-200">{conf.toFixed(2)}</td>
                    <td className="px-3 py-2 text-zinc-200">{quality.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function SimpleChart({ assets, seriesMap }: { assets: string[]; seriesMap: SeriesMap }) {
  const width = 1400;
  const height = 700;
  const padding = 60;
  const palette = ["#60a5fa", "#34d399", "#f97316"]; 

  const series = assets.map((a, i) => ({
    asset: a,
    data: seriesMap[a] || [],
    color: palette[i % palette.length],
  }));

  const maxLen = Math.max(0, ...series.map((s) => s.data.length));
  const values = series.flatMap((s) => s.data.map((d) => d.confidence));
  if (!maxLen || !values.length) {
    return <div className="text-xs text-zinc-500">Sem dados para exibir.</div>;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(0.05, max - min);
  const scaleX = (x: number) => padding + (x / Math.max(1, maxLen - 1)) * (width - padding * 2);
  const scaleY = (y: number) => height - padding - ((y - min) / range) * (height - padding * 2);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
      <rect x="0" y="0" width={width} height={height} rx="18" fill="rgba(8,8,8,0.92)" />
      {series.map((s) => {
        const path = s.data.map((d, i) => `${i === 0 ? "M" : "L"} ${scaleX(i)} ${scaleY(d.confidence)}`).join(" ");
        return (
          <g key={s.asset}>
            <path d={path} stroke={s.color} strokeWidth="2.4" fill="none" />
            {s.data.filter((_, i) => i % 4 === 0).map((d, i) => (
              <circle
                key={`${s.asset}-${i}`}
                cx={scaleX(i * 4)}
                cy={scaleY(d.confidence)}
                r={2.2}
                fill={regimeColor[d.regime] || s.color}
              />
            ))}
          </g>
        );
      })}
    </svg>
  );
}
