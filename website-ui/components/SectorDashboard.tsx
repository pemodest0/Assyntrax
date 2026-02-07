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
};

const assetColors = [
  "#38bdf8",
  "#22c55e",
  "#f97316",
  "#a855f7",
  "#facc15",
  "#14b8a6",
  "#f472b6",
  "#60a5fa",
  "#fb7185",
  "#e879f9",
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

const assetNames: Record<string, string> = {
  SPY: "S&P 500",
  QQQ: "Nasdaq 100",
  DIA: "Dow Jones",
  IWM: "Russell 2000",
  GLD: "Ouro",
  SLV: "Prata",
  USO: "Petróleo",
  TLT: "Treasury 20Y",
  IEF: "Treasury 7-10Y",
  SHY: "Treasury 1-3Y",
  LQD: "IG Bonds",
  HYG: "High Yield",
  TIP: "TIPS",
  UUP: "Dólar DXY",
  FXE: "Euro",
  FXY: "Iene",
  BTC: "Bitcoin",
  "BTC-USD": "Bitcoin",
  "ETH-USD": "Ethereum",
  VIX: "Volatilidade",
  "^VIX": "Volatilidade",
  XLK: "Tecnologia",
  XLF: "Financeiro",
  XLE: "Energia",
  XLV: "Saúde",
  XLY: "Consumo",
  XLP: "Consumo Básico",
  XLU: "Utilities",
  XLI: "Indústria",
  XLB: "Materiais",
  XLRE: "Imobiliário",
  XOP: "Energia",
  EEM: "Mercados Emergentes",
  EFA: "Mercados Globais",
  EWJ: "Japão",
  EWZ: "Brasil",
  VT: "Ações Globais",
  VTI: "Total Market",
};

const horizonsByTf: Record<string, number[]> = {
  daily: [1, 5, 20, 252],
  weekly: [1, 4, 12, 52],
};

function formatPct(v: number | null | undefined) {
  if (v == null || Number.isNaN(v)) return "--";
  return `${(v * 100).toFixed(2)}%`;
}

function cleanRegime(label?: string) {
  if (!label) return "TRANSITION";
  if (label === "NOISY") return "UNSTABLE";
  if (label === "STABLE" || label === "TRANSITION" || label === "UNSTABLE") return label;
  return "TRANSITION";
}

function formatAxisDate(date?: string, tf?: string) {
  if (!date) return "";
  if (tf === "weekly") return date.slice(0, 7);
  if (tf === "daily") return date.slice(0, 7);
  return date.slice(0, 10);
}

export default function SectorDashboard({
  title,
  showTable = true,
}: {
  title: string;
  showTable?: boolean;
}) {
  const [timeframe, setTimeframe] = useState("daily");
  const [horizon, setHorizon] = useState(1);
  const [universe, setUniverse] = useState<UniverseAsset[]>([]);
  const [sectorFilter, setSectorFilter] = useState("all");
  const [sortKey, setSortKey] = useState("confidence");
  const [sortDir, setSortDir] = useState<"desc" | "asc">("desc");
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
    if (!universe.length) return;
    const filtered = universe.filter((u) => sectorFilter === "all" || u.group === sectorFilter);
    const keep = selected.filter((a) => filtered.find((u) => u.asset === a));
    if (keep.length) {
      setSelected(keep);
    } else if (filtered.length) {
      setSelected(filtered.slice(0, 3).map((u) => u.asset));
    }
  }, [sectorFilter, universe]);

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
    const base = [...filteredUniverse].sort((a, b) => getScore(b) - getScore(a));
    return sortDir === "desc" ? base : base.reverse();
  }, [filteredUniverse, sortKey, sortDir, seriesByAsset, forecastByAsset]);

  const selection = useMemo(() => {
    const valid = selected.filter((a) => universe.find((u) => u.asset === a));
    return valid.slice(0, 10);
  }, [selected, universe]);

  const focusAsset = selection[0];

  const chart = useMemo(() => {
    if (!selection.length) return null;
    const merged = selection.flatMap((a) => seriesByAsset[a] || []);
    if (!merged.length) return null;
    const width = 1600;
    const height = 900;
    const pad = 96;
    const yVals = merged.map((d) => (d.price == null ? NaN : d.price)).filter((v) => Number.isFinite(v)) as number[];
    const ymin = Math.min(...yVals);
    const ymax = Math.max(...yVals);
    const scaleX = (i: number, total: number) => pad + (i / Math.max(1, total - 1)) * (width - pad * 2);
    const scaleY = (v: number) =>
      height - pad - ((v - ymin) / Math.max(1e-6, ymax - ymin)) * (height - pad * 2);
    const yTicks = 5;
    const xTicks = 6;
    return { width, height, pad, scaleX, scaleY, ymin, ymax, yTicks, xTicks };
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
      const regime = cleanRegime(last?.regime ?? u.state?.label);
      let suggestion = "Aguardar";
      if (conf != null && (regime === "UNSTABLE" || conf < 0.45)) suggestion = "Não operar";
      if (conf != null && regime === "STABLE" && conf >= 0.6) suggestion = "Aplicar";
      return {
        asset: u.asset,
        name: assetNames[u.asset] || "",
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
          <div className="text-sm text-zinc-400 uppercase tracking-[0.2em]">{title}</div>
          <h1 className="text-2xl font-semibold">Regimes por setor com projeção integrada</h1>
          <p className="text-sm text-zinc-400 max-w-3xl">
            Selecione setor e ativos. O gráfico exibe preços com regiões de regime e a tabela resume a projeção
            por horizonte.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <select
            value={timeframe}
            onChange={(e) => {
              setTimeframe(e.target.value);
              setHorizon(horizonsByTf[e.target.value][0]);
            }}
            title="Escolha a frequência (diário ou semanal)."
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          >
            <option value="daily">Diário</option>
            <option value="weekly">Semanal</option>
          </select>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            title="Horizonte de projeção em passos."
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
            title="Filtre por setor."
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
            title="Ordene pelo critério selecionado."
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          >
            <option value="confidence">Confiança</option>
            <option value="price">Preço</option>
            <option value="forecast">Projeção</option>
          </select>
          <button
            onClick={() => setSortDir(sortDir === "desc" ? "asc" : "desc")}
            title="Alterna ordem de classificação."
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          >
            {sortDir === "desc" ? "Maior → menor" : "Menor → maior"}
          </button>
        </div>
      </div>

      <div className="space-y-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6 min-h-[70vh]">
          <div className="flex items-center justify-between">
            <div className="text-sm uppercase tracking-widest text-zinc-400">Gráfico principal</div>
            <div className="text-xs text-zinc-500">{loading ? "Carregando..." : "Últimos 120 pontos"}</div>
          </div>
          <div className="mt-2 grid gap-2 text-[11px] text-zinc-500">
            <div>
              Guia rápido: áreas coloridas = regime do ativo referência · linhas = preço dos ativos selecionados · linha
              cinza = confiança (escala).
            </div>
            <div>
              Passe o mouse nos rótulos e opções para ver explicações rápidas.
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-zinc-400">
            {["STABLE", "TRANSITION", "UNSTABLE"].map((r) => (
              <span
                key={r}
                className="inline-flex items-center gap-2"
                title={`Regime ${r}: cor de fundo do gráfico.`}
              >
                <span className="h-2 w-2 rounded-full" style={{ background: palette[r] }} />
                {r === "STABLE" ? "Estável" : r === "TRANSITION" ? "Transição" : "Instável"}
              </span>
            ))}
            <span className="inline-flex items-center gap-2" title="Linha de confiança do ativo principal.">
              <span className="h-2 w-2 rounded-full bg-zinc-300" />
              Confiança (escala)
            </span>
          </div>
          <div className="mt-4">
            {chart && focusAsset ? (
              <svg
                viewBox={`0 0 ${chart.width} ${chart.height}`}
                className="w-full h-[72vh] min-h-[520px]"
              >
                <title>
                  Gráfico principal: preços dos ativos selecionados, com faixas de regime e linha de confiança.
                </title>
                <rect
                  x="0"
                  y="0"
                  width={chart.width}
                  height={chart.height}
                  rx="24"
                  fill="rgba(8,8,10,0.85)"
                />
                {Array.from({ length: chart.yTicks }).map((_, i) => {
                  const v = chart.ymin + ((chart.ymax - chart.ymin) / (chart.yTicks - 1)) * i;
                  const y = chart.scaleY(v);
                  return (
                    <g key={`y-${i}`}>
                      <line
                        x1={chart.pad}
                        y1={y}
                        x2={chart.width - chart.pad}
                        y2={y}
                        stroke="rgba(148,163,184,0.15)"
                      />
                      <text
                        x={chart.pad - 12}
                        y={y + 4}
                        textAnchor="end"
                        fontSize="12"
                        fill="rgba(148,163,184,0.8)"
                      >
                        US$ {v.toFixed(2)}
                      </text>
                    </g>
                  );
                })}
                {Array.from({ length: chart.xTicks }).map((_, i) => {
                  const idx = Math.round((i / (chart.xTicks - 1)) * (seriesByAsset[focusAsset]?.length - 1 || 0));
                  const x = chart.scaleX(idx, seriesByAsset[focusAsset]?.length || 1);
                  return (
                    <g key={`x-${i}`}>
                      <line
                        x1={x}
                        y1={chart.pad}
                        x2={x}
                        y2={chart.height - chart.pad}
                        stroke="rgba(148,163,184,0.12)"
                      />
                      <text
                        x={x}
                        y={chart.height - chart.pad + 20}
                        textAnchor="middle"
                        fontSize="12"
                        fill="rgba(148,163,184,0.8)"
                      >
                        {formatAxisDate(seriesByAsset[focusAsset]?.[idx]?.date, timeframe)}
                      </text>
                    </g>
                  );
                })}
                {(seriesByAsset[focusAsset] || []).map((d, idx, arr) => {
                  if (idx === 0) return null;
                  const prev = arr[idx - 1];
                  if (!prev?.regime) return null;
                  const x0 = chart.scaleX(idx - 1, arr.length);
                  const x1 = chart.scaleX(idx, arr.length);
                  const color = palette[cleanRegime(prev.regime)] || "#94a3b8";
                  return (
                    <rect
                      key={`${focusAsset}-${idx}`}
                      x={x0}
                      y={chart.pad}
                      width={Math.max(1, x1 - x0)}
                      height={chart.height - chart.pad * 2}
                      fill={color}
                      opacity="0.12"
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
                  return <path key={assetName} d={path} stroke={color} strokeWidth="3" fill="none" />;
                })}
                {(seriesByAsset[focusAsset] || []).length ? (
                  <path
                    d={(seriesByAsset[focusAsset] || [])
                      .map((d, i) => {
                        if (d.confidence == null) return "";
                        const scaled =
                          chart.ymin + (chart.ymax - chart.ymin) * Math.max(0, Math.min(1, d.confidence));
                        return `${i === 0 ? "M" : "L"} ${chart.scaleX(i, seriesByAsset[focusAsset].length)} ${chart.scaleY(scaled)}`;
                      })
                      .join(" ")}
                    stroke="rgba(226,232,240,0.7)"
                    strokeWidth="2"
                    fill="none"
                  />
                ) : null}
                <text
                  x={20}
                  y={chart.height / 2}
                  textAnchor="middle"
                  fontSize="12"
                  fill="rgba(226,232,240,0.85)"
                  transform={`rotate(-90, 20, ${chart.height / 2})`}
                >
                  Preço (US$)
                </text>
                <text
                  x={chart.width / 2}
                  y={chart.height - 18}
                  textAnchor="middle"
                  fontSize="12"
                  fill="rgba(226,232,240,0.85)"
                >
                  Datas (dias / meses / anos)
                </text>
              </svg>
            ) : (
              <div className="text-sm text-zinc-500">Selecione ativos para visualizar.</div>
            )}
          </div>
          <div className="mt-4 flex flex-wrap gap-3 text-xs text-zinc-400">
            {selection.map((a, idx) => (
              <span key={a} className="inline-flex items-center gap-2" title="Série de preço do ativo.">
                <span className="h-2 w-2 rounded-full" style={{ background: assetColors[idx % assetColors.length] }} />
                {a}
              </span>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[280px_1fr] gap-4">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
            <div className="text-xs uppercase tracking-widest text-zinc-400">Ativos</div>
            <div className="mt-2 text-[11px] text-zinc-500">
              Dica: selecione até 10 ativos. O primeiro é a referência das áreas de regime.
            </div>
            <div className="mt-4 max-h-[420px] overflow-auto space-y-1 text-[11px] text-zinc-300">
              {sortedUniverse.slice(0, 40).map((u) => (
                <label key={u.asset} className="flex items-center gap-2" title="Selecionar ativo para o gráfico.">
                  <input
                    type="checkbox"
                    checked={selection.includes(u.asset)}
                    onChange={() => toggleAsset(u.asset)}
                    className="h-2.5 w-2.5 accent-cyan-400"
                  />
                  <span className="w-11">{u.asset}</span>
                  <span className="text-zinc-500">
                    {assetNames[u.asset] || groupLabels[u.group || ""] || u.group || ""}
                  </span>
                </label>
              ))}
            </div>
            <div className="mt-3 text-[11px] text-zinc-500">Use os filtros acima para reduzir a lista.</div>
          </div>

          {showTable && (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
              <div className="text-sm uppercase tracking-widest text-zinc-400">Tabela por ativo</div>
              <div className="mt-4 grid grid-cols-1 gap-2 text-xs text-zinc-300">
                <div className="grid grid-cols-7 gap-3 text-[11px] uppercase text-zinc-500">
                  <span title="Ativo selecionado">Ativo</span>
                  <span title="Setor ou grupo do ativo">Setor</span>
                  <span title="Regime atual">Regime</span>
                  <span title="Confiança média do regime">Conf.</span>
                  <span title="Preço atual">Preço</span>
                  <span title="Projeção para o horizonte selecionado">Projeção h={horizon}</span>
                  <span title="Sugestão do motor">Ação</span>
                </div>
                {rows
                  .filter((r) => selection.includes(r.asset))
                  .map((r) => (
                    <div
                      key={r.asset}
                      className="grid grid-cols-7 gap-3 items-center border-b border-zinc-800/60 py-2"
                    >
                      <span>
                        {r.asset} {r.name ? `— ${r.name}` : ""}
                      </span>
                      <span className="text-zinc-400">{r.group}</span>
                      <span style={{ color: palette[r.regime] || "#e5e7eb" }}>{r.regime}</span>
                      <span>{r.confidence != null ? r.confidence.toFixed(2) : "--"}</span>
                      <span>{r.priceNow != null ? `US$ ${r.priceNow.toFixed(2)}` : "--"}</span>
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
          )}
        </div>
      </div>
    </div>
  );
}
