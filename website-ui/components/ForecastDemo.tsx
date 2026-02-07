"use client";

import { useEffect, useMemo, useState } from "react";

type SeriesPoint = {
  date: string;
  price: number | null;
  confidence: number;
  regime: string;
};

type ForecastPoint = {
  date: string;
  model: string;
  y_pred: number;
  y_true?: number;
  regime?: string;
};

type UniverseAsset = {
  asset: string;
  group?: string;
  state?: { label?: string };
  metrics?: { confidence?: number };
};

const palette: Record<string, string> = {
  STABLE: "#34d399",
  TRANSITION: "#fbbf24",
  UNSTABLE: "#fb7185",
  NOISY: "#94a3b8",
};

const assetColors = [
  "#38bdf8",
  "#22c55e",
  "#f97316",
  "#a855f7",
  "#facc15",
  "#14b8a6",
  "#f472b6",
  "#e879f9",
  "#60a5fa",
  "#fb7185",
];

const groupLabels: Record<string, string> = {
  crypto: "Cripto",
  volatility: "Volatilidade",
  commodities_broad: "Commodities",
  energy: "Energia",
  metals: "Metais",
  bonds_rates: "Juros/Bonds",
  fx: "Moedas",
  equities_us: "Ações EUA",
  equities_global: "Ações Globais",
  realestate: "Imobiliário",
  industrials: "Indústria",
  consumer: "Consumo",
  tech: "Tecnologia",
  health: "Saúde",
  utilities: "Utilities",
  financials: "Financeiro",
};

const horizonsByTf: Record<string, number[]> = {
  daily: [1, 5, 20, 252],
  weekly: [1, 4, 12, 52],
};

function formatPct(v: number | null | undefined) {
  if (v == null || Number.isNaN(v)) return "--";
  return `${(v * 100).toFixed(2)}%`;
}

export default function ForecastDemo() {
  const [timeframe, setTimeframe] = useState("daily");
  const [horizon, setHorizon] = useState(1);
  const [universe, setUniverse] = useState<UniverseAsset[]>([]);
  const [sectorFilter, setSectorFilter] = useState("all");
  const [sortKey, setSortKey] = useState("confidence");
  const [selected, setSelected] = useState<string[]>([]);
  const [seriesByAsset, setSeriesByAsset] = useState<Record<string, SeriesPoint[]>>({});
  const [forecastByAsset, setForecastByAsset] = useState<Record<string, ForecastPoint | null>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadUniverse = async () => {
      try {
        const res = await fetch(`/api/graph/universe?tf=${timeframe}`);
        const data = await res.json();
        if (Array.isArray(data)) {
          setUniverse(data);
          if (!selected.length) {
            const first = data.slice(0, 3).map((d) => d.asset);
            setSelected(first);
          }
        }
      } catch {
        setUniverse([]);
      }
    };
    loadUniverse();
  }, [timeframe]);

  useEffect(() => {
    if (!selected.length) return;
    const load = async () => {
      setLoading(true);
      try {
        const seriesRes = await fetch(
          `/api/graph/series-batch?assets=${selected.join(",")}&tf=${timeframe}&limit=120`
        );
        const seriesJson = await seriesRes.json();
        setSeriesByAsset(seriesJson || {});

        const forecasts: Record<string, ForecastPoint | null> = {};
        await Promise.all(
          selected.map(async (asset) => {
            try {
              const forecastRes = await fetch(
                `/api/files/forecast_suite/${asset}/${timeframe}/${asset}_${timeframe}_log_return_h${horizon}.json`
              );
              if (!forecastRes.ok) {
                forecasts[asset] = null;
                return;
              }
              const forecastJson = await forecastRes.json();
              const predictions: ForecastPoint[] = forecastJson?.predictions ?? [];
              const preferred = predictions.filter((p) =>
                ["auto_best_ens", "auto_best", "auto_sector", "ridge"].includes(p.model)
              );
              const pickModel =
                preferred.find((p) => p.model === "auto_best_ens")?.model ||
                preferred.find((p) => p.model === "auto_best")?.model ||
                preferred.find((p) => p.model === "auto_sector")?.model ||
                "ridge";
              const filtered = predictions.filter((p) => p.model === pickModel);
              forecasts[asset] = filtered.length ? filtered[filtered.length - 1] : null;
            } catch {
              forecasts[asset] = null;
            }
          })
        );
        setForecastByAsset(forecasts);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [selected, timeframe, horizon]);

  const filteredUniverse = useMemo(() => {
    return universe.filter((u) => sectorFilter === "all" || u.group === sectorFilter);
  }, [universe, sectorFilter]);

  const sortedUniverse = useMemo(() => {
    const getScore = (u: UniverseAsset) => {
      const series = seriesByAsset[u.asset] || [];
      const last = series[series.length - 1];
      if (sortKey === "price") return last?.price ?? 0;
      if (sortKey === "forecast") return forecastByAsset[u.asset]?.y_pred ?? 0;
      return u.metrics?.confidence ?? last?.confidence ?? 0;
    };
    return [...filteredUniverse].sort((a, b) => getScore(b) - getScore(a));
  }, [filteredUniverse, sortKey, seriesByAsset, forecastByAsset]);

  const selection = useMemo(() => {
    const valid = selected.filter((a) => universe.find((u) => u.asset === a));
    return valid.slice(0, 10);
  }, [selected, universe]);

  const focusAsset = selection[0];

  const chart = useMemo(() => {
    if (!selection.length) return null;
    const merged = selection.flatMap((a) => seriesByAsset[a] || []);
    if (!merged.length) return null;
    const width = 980;
    const height = 360;
    const pad = 46;
    const yVals = merged.map((d) => (d.price == null ? NaN : d.price)).filter((v) => Number.isFinite(v)) as number[];
    const ymin = Math.min(...yVals);
    const ymax = Math.max(...yVals);
    const scaleX = (i: number, total: number) => pad + (i / Math.max(1, total - 1)) * (width - pad * 2);
    const scaleY = (v: number) =>
      height - pad - ((v - ymin) / Math.max(1e-6, ymax - ymin)) * (height - pad * 2);
    return { width, height, pad, scaleX, scaleY, ymin, ymax };
  }, [selection, seriesByAsset]);

  const rows = useMemo(() => {
    return sortedUniverse.map((u) => {
      const series = seriesByAsset[u.asset] || [];
      const last = series[series.length - 1];
      const forecast = forecastByAsset[u.asset];
      const priceNow = last?.price ?? null;
      const forecastReturn = forecast?.y_pred ?? null;
      const forecastPrice =
        priceNow != null && forecastReturn != null ? priceNow * Math.exp(forecastReturn) : null;
      const conf = last?.confidence ?? u.metrics?.confidence ?? null;
      const regime = last?.regime ?? u.state?.label ?? "--";
      let suggestion = "Aguardar";
      if (conf != null && (regime === "NOISY" || regime === "UNSTABLE" || conf < 0.45)) suggestion = "Não operar";
      if (conf != null && regime === "STABLE" && conf >= 0.6) suggestion = "Aplicar";
      return {
        asset: u.asset,
        group: groupLabels[u.group || ""] || u.group || "Outros",
        regime,
        confidence: conf,
        priceNow,
        forecastReturn,
        forecastPrice,
        suggestion,
      };
    });
  }, [sortedUniverse, seriesByAsset, forecastByAsset]);

  const toggleAsset = (asset: string) => {
    setSelected((prev) => {
      if (prev.includes(asset)) return prev.filter((a) => a !== asset);
      if (prev.length >= 10) return prev;
      return [...prev, asset];
    });
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-sm text-zinc-400 uppercase tracking-[0.2em]">Demo Forecast + Regimes</div>
          <h1 className="text-2xl font-semibold">Visão multi-ativos com regimes e forecast</h1>
          <p className="text-sm text-zinc-400 max-w-3xl">
            Selecione ativos, horizonte e setor. O gráfico pinta regiões de regime e o forecast mostra o cenário
            provável para cada ativo.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <select
            value={timeframe}
            onChange={(e) => {
              setTimeframe(e.target.value);
              setHorizon(horizonsByTf[e.target.value][0]);
            }}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          >
            <option value="daily">Diário</option>
            <option value="weekly">Semanal</option>
          </select>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          >
            {horizonsByTf[timeframe].map((h) => (
              <option key={h} value={h}>
                Horizonte h={h}
              </option>
            ))}
          </select>
          <select
            value={sectorFilter}
            onChange={(e) => setSectorFilter(e.target.value)}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          >
            <option value="all">Todos os setores</option>
            {Array.from(new Set(universe.map((u) => u.group).filter(Boolean))).map((g) => (
              <option key={g} value={g as string}>
                {groupLabels[g as string] || g}
              </option>
            ))}
          </select>
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value)}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          >
            <option value="confidence">Ordenar por confiança</option>
            <option value="price">Ordenar por valor atual</option>
            <option value="forecast">Ordenar por forecast</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
          <div className="text-xs uppercase tracking-widest text-zinc-400">Ativos disponíveis</div>
          <div className="mt-4 max-h-72 overflow-auto space-y-2 text-xs text-zinc-300">
            {sortedUniverse.slice(0, 40).map((u) => (
              <label key={u.asset} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selection.includes(u.asset)}
                  onChange={() => toggleAsset(u.asset)}
                />
                <span className="w-10">{u.asset}</span>
                <span className="text-zinc-500">{groupLabels[u.group || ""] || u.group || "Outros"}</span>
              </label>
            ))}
          </div>
          <div className="mt-3 text-[11px] text-zinc-500">Selecione até 10 ativos.</div>
        </div>

        <div className="xl:col-span-2 rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
          <div className="flex items-center justify-between">
            <div className="text-sm uppercase tracking-widest text-zinc-400">Gráfico principal</div>
            <div className="text-xs text-zinc-500">{loading ? "Carregando..." : "Dados recentes"}</div>
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-zinc-400">
            {["STABLE", "TRANSITION", "UNSTABLE", "NOISY"].map((r) => (
              <span key={r} className="inline-flex items-center gap-2">
                <span className="h-2 w-2 rounded-full" style={{ background: palette[r] }} />
                {r}
              </span>
            ))}
          </div>
          <div className="mt-4">
            {chart && focusAsset ? (
              <svg viewBox={`0 0 ${chart.width} ${chart.height}`} className="w-full h-[360px]">
                <rect
                  x="0"
                  y="0"
                  width={chart.width}
                  height={chart.height}
                  rx="20"
                  fill="rgba(10,10,10,0.75)"
                />
                {(seriesByAsset[focusAsset] || []).map((d, idx, arr) => {
                  if (idx === 0) return null;
                  const prev = arr[idx - 1];
                  if (!prev?.regime) return null;
                  const x0 = chart.scaleX(idx - 1, arr.length);
                  const x1 = chart.scaleX(idx, arr.length);
                  const color = palette[prev.regime] || "#94a3b8";
                  return (
                    <rect
                      key={`${focusAsset}-${idx}`}
                      x={x0}
                      y={chart.pad}
                      width={Math.max(1, x1 - x0)}
                      height={chart.height - chart.pad * 2}
                      fill={color}
                      opacity="0.08"
                    />
                  );
                })}
                {selection.map((assetName, idx) => {
                  const data = seriesByAsset[assetName] || [];
                  if (!data.length) return null;
                  const color = assetColors[idx % assetColors.length];
                  const path = data
                    .map((d, i) => {
                      if (d.price == null) return "";
                      return `${i === 0 ? "M" : "L"} ${chart.scaleX(i, data.length)} ${chart.scaleY(d.price)}`;
                    })
                    .join(" ");
                  return <path key={assetName} d={path} stroke={color} strokeWidth="2" fill="none" />;
                })}
              </svg>
            ) : (
              <div className="text-sm text-zinc-500">Selecione ativos para visualizar.</div>
            )}
          </div>
          <div className="mt-4 flex flex-wrap gap-3 text-xs text-zinc-400">
            {selection.map((a, idx) => (
              <span key={a} className="inline-flex items-center gap-2">
                <span className="h-2 w-2 rounded-full" style={{ background: assetColors[idx % assetColors.length] }} />
                {a}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
        <div className="text-sm uppercase tracking-widest text-zinc-400">Tabela de decisão por ativo</div>
        <div className="mt-4 grid grid-cols-1 gap-2 text-xs text-zinc-300">
          <div className="grid grid-cols-7 gap-3 text-[11px] uppercase text-zinc-500">
            <span>Ativo</span>
            <span>Setor</span>
            <span>Regime</span>
            <span>Confiança</span>
            <span>Preço atual</span>
            <span>Forecast</span>
            <span>Ação</span>
          </div>
          {rows.slice(0, 30).map((r) => (
            <div key={r.asset} className="grid grid-cols-7 gap-3 items-center border-b border-zinc-800/60 py-2">
              <span>{r.asset}</span>
              <span className="text-zinc-400">{r.group}</span>
              <span style={{ color: palette[r.regime] || "#e5e7eb" }}>{r.regime}</span>
              <span>{r.confidence != null ? r.confidence.toFixed(2) : "--"}</span>
              <span>{r.priceNow != null ? r.priceNow.toFixed(2) : "--"}</span>
              <span>{formatPct(r.forecastReturn)}</span>
              <span
                className={
                  r.suggestion === "Aplicar"
                    ? "text-emerald-300"
                    : r.suggestion === "Não operar"
                    ? "text-rose-300"
                    : "text-amber-300"
                }
              >
                {r.suggestion}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
