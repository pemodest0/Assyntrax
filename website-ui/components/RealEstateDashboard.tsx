"use client";

import { useEffect, useMemo, useState } from "react";

type SeriesPoint = { date: string; value: number | null };
type RegimePoint = { date: string; regime: string; confidence: number };

type RqaInfo = { rqa?: { det?: number; lam?: number; tt?: number } };
type ForecastByRegime = Record<string, { by_regime: Record<string, any> }>;

const palette: Record<string, string> = {
  STABLE: "#34d399",
  TRANSITION: "#fbbf24",
  UNSTABLE: "#fb7185",
};

const CITY_MAP = [
  { asset: "FipeZap_São_Paulo_Total", state: "SP", city: "São Paulo", region: "Sudeste", x: 245, y: 235 },
  { asset: "FipeZap_Rio_de_Janeiro_Total", state: "RJ", city: "Rio de Janeiro", region: "Sudeste", x: 268, y: 235 },
  { asset: "FipeZap_Belo_Horizonte_Total", state: "MG", city: "Belo Horizonte", region: "Sudeste", x: 250, y: 215 },
  { asset: "FipeZap_Porto_Alegre_Total", state: "RS", city: "Porto Alegre", region: "Sul", x: 225, y: 310 },
  { asset: "FipeZap_Brasília_Total", state: "DF", city: "Brasília", region: "Centro-Oeste", x: 215, y: 195 },
];

const REGION_ORDER = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"];
const REGION_COLORS: Record<string, string> = {
  Norte: "#0ea5e9",
  Nordeste: "#f59e0b",
  "Centro-Oeste": "#10b981",
  Sudeste: "#a855f7",
  Sul: "#f43f5e",
};
const REGION_STATES: Record<string, string[]> = {
  Norte: ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
  Nordeste: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
  "Centro-Oeste": ["DF", "GO", "MS", "MT"],
  Sudeste: ["ES", "MG", "RJ", "SP"],
  Sul: ["PR", "RS", "SC"],
};

const HERO_IMAGES = [
  "/visuals/realestate-tiles.svg",
  "/visuals/realestate-skyline.svg",
];

function formatPct(v?: number) {
  if (v == null || Number.isNaN(v)) return "--";
  return `${(v * 100).toFixed(2)}%`;
}

function formatDateLabel(date: string, mode: "mensal" | "anual" | "diario") {
  if (!date) return "";
  if (mode === "anual") return date.slice(0, 4);
  if (mode === "mensal") return date.slice(0, 7);
  return date;
}

export default function RealEstateDashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [regionFilter, setRegionFilter] = useState("Sudeste");
  const [stateFilter, setStateFilter] = useState("SP");
  const [cityFilter, setCityFilter] = useState("São Paulo");
  const [series, setSeries] = useState<SeriesPoint[]>([]);
  const [regimes, setRegimes] = useState<RegimePoint[]>([]);
  const [viewMode, setViewMode] = useState<"mensal" | "anual" | "diario">("mensal");
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const selectedAsset = useMemo(() => {
    const match = CITY_MAP.find((c) => c.state === stateFilter && c.city === cityFilter);
    return match?.asset || CITY_MAP[0].asset;
  }, [stateFilter, cityFilter]);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/realestate/summary");
        if (!res.ok) return;
        const data = await res.json();
        setSummary(data);
      } catch {
        setSummary(null);
      }
    };
    load();
  }, []);

  useEffect(() => {
    const loadSeries = async () => {
      try {
        const res = await fetch(`/api/realestate/series?asset=${encodeURIComponent(selectedAsset)}`);
        const data = await res.json();
        setSeries(Array.isArray(data) ? data : []);
      } catch {
        setSeries([]);
      }
    };
    loadSeries();
  }, [selectedAsset]);

  useEffect(() => {
    const loadRegimes = async () => {
      try {
        const base = selectedAsset.toUpperCase().replace(/\s+/g, "_");
        const res = await fetch(
          `/api/files/realestate/assets/${base}_monthly_regimes.csv`
        );
        if (!res.ok) {
          setRegimes([]);
          return;
        }
        const text = await res.text();
        const lines = text.trim().split("\n").slice(1);
        const parsed = lines.map((line) => {
          const [date, regime, confidence] = line.split(",");
          return { date, regime, confidence: Number(confidence) };
        });
        setRegimes(parsed);
      } catch {
        setRegimes([]);
      }
    };
    loadRegimes();
  }, [selectedAsset]);

  const rqa: RqaInfo | null = summary?.rqa?.[selectedAsset.toUpperCase()] || null;
  const forecast: ForecastByRegime | null =
    summary?.forecast?.[selectedAsset.toUpperCase()] || null;

  const displaySeries = useMemo(() => {
    if (!series.length) return [];
    if (viewMode === "diario") {
      return series;
    }
    if (viewMode === "anual") {
      const byYear: Record<string, SeriesPoint> = {};
      for (const p of series) {
        const year = p.date.slice(0, 4);
        byYear[year] = p;
      }
      return Object.values(byYear);
    }
    return series;
  }, [series, viewMode]);

  const chart = useMemo(() => {
    if (!displaySeries.length) return null;
    const width = 1400;
    const height = 700;
    const pad = 90;
    const yVals = displaySeries.map((d) => d.value).filter((v) => v != null) as number[];
    if (!yVals.length) return null;
    const ymin = Math.min(...yVals);
    const ymax = Math.max(...yVals);
    const scaleX = (i: number, total: number) =>
      pad + (i / Math.max(1, total - 1)) * (width - pad * 2);
    const scaleY = (v: number) =>
      height - pad - ((v - ymin) / Math.max(1e-6, ymax - ymin)) * (height - pad * 2);
    return { width, height, pad, scaleX, scaleY, ymin, ymax };
  }, [displaySeries]);

  const states = REGION_STATES[regionFilter] || [];
  const cities = CITY_MAP.filter((c) => c.state === stateFilter).map((c) => c.city);

  const statusColor = (assetKey: string) => {
    const key = assetKey.toUpperCase();
    const det = summary?.rqa?.[key]?.rqa?.det ?? 0;
    const lam = summary?.rqa?.[key]?.rqa?.lam ?? 0;
    if (det > 0.85 && lam > 0.8) return palette.STABLE;
    if (det > 0.6) return palette.TRANSITION;
    return palette.UNSTABLE;
  };

  const regimeAt = (idx: number | null) => {
    if (idx == null || !regimes.length || !displaySeries.length) return null;
    const mapped = Math.round((idx / Math.max(1, displaySeries.length - 1)) * (regimes.length - 1));
    return regimes[Math.max(0, Math.min(regimes.length - 1, mapped))] || null;
  };

  const insight = useMemo(() => {
    const det = rqa?.rqa?.det ?? 0;
    const lam = rqa?.rqa?.lam ?? 0;
    if (det > 0.9 && lam > 0.8) {
      return "Estrutura forte e lenta: ideal para decisões de longo prazo.";
    }
    if (det > 0.7 && lam < 0.5) {
      return "Estrutura estável com mobilidade: janela boa para projeções.";
    }
    return "Estrutura instável: use apenas diagnóstico, sem projeção agressiva.";
  }, [rqa]);

  return (
    <div className="p-6 space-y-6">
      <header className="space-y-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Setor Imobiliário</h1>
            <p className="text-sm text-zinc-400">
              Diagnóstico de regimes para preços residenciais: estrutura, travamento de liquidez e
              janela de previsão válida.
            </p>
          </div>
          <div className="flex gap-3">
            {HERO_IMAGES.map((src) => (
              <img
                key={src}
                src={src}
                alt="Fachadas residenciais"
                className="h-24 w-40 rounded-xl object-cover border border-zinc-800"
              />
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-black/40 p-4 text-sm text-zinc-300">
          <div className="font-semibold text-zinc-100">Guia rápido</div>
          <div className="mt-2 grid gap-2 lg:grid-cols-3">
            <div title="DET alto indica repetição de padrão e previsibilidade estrutural.">
              <span className="font-semibold">DET</span> → mede estrutura do regime.
            </div>
            <div title="LAM alto indica preço “travado” por longos períodos.">
              <span className="font-semibold">LAM</span> → mede travamento de liquidez.
            </div>
            <div title="TT é o tempo médio em que o mercado fica preso em um estado.">
              <span className="font-semibold">TT</span> → mede persistência do regime.
            </div>
          </div>
          <div className="mt-3 text-xs text-zinc-400">
            Dica: selecione uma região, depois estado e cidade. O gráfico mostra o preço com
            faixas de regime (estável, transição, instável) e a tabela resume a leitura.
          </div>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-4 space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
            <div className="text-xs text-zinc-500 mb-2">Filtro geográfico</div>
            <div className="space-y-3">
              <label className="text-xs text-zinc-400" title="Escolha a macro-região do Brasil.">
                Região
              </label>
              <select
                className="w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm"
                value={regionFilter}
                onChange={(e) => {
                  const reg = e.target.value;
                  setRegionFilter(reg);
                  const fallback = CITY_MAP.find((c) => c.region === reg);
                  setStateFilter(fallback?.state || "SP");
                  setCityFilter(fallback?.city || "São Paulo");
                }}
              >
                {REGION_ORDER.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
              <label className="text-xs text-zinc-400" title="Selecione o estado da região.">
                Estado
              </label>
              <select
                className="w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm"
                value={stateFilter}
                onChange={(e) => {
                  setStateFilter(e.target.value);
                  setCityFilter(CITY_MAP.find((c) => c.state === e.target.value)?.city || "");
                }}
              >
                {states.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <label className="text-xs text-zinc-400" title="Selecione a cidade monitorada.">
                Cidade
              </label>
              <select
                className="w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm"
                value={cityFilter}
                onChange={(e) => setCityFilter(e.target.value)}
              >
                {cities.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
            <div className="text-xs text-zinc-500 mb-2">Mapa do Brasil (regiões)</div>
            <svg viewBox="0 0 420 520" className="w-full h-96">
              <path
                d="M150 40 L210 28 L285 52 L340 90 L365 150 L350 210 L378 270 L350 335 L300 390 L250 372 L220 405 L175 392 L125 350 L105 300 L85 250 L60 210 L78 150 L105 95 Z"
                fill="#0b0b0f"
                stroke="#52525b"
                strokeWidth="2.5"
              />
              {REGION_ORDER.map((region) => {
                const isActive = regionFilter === region;
                return (
                  <text
                    key={region}
                    x={18}
                    y={30 + REGION_ORDER.indexOf(region) * 22}
                    fill={isActive ? "#e5e7eb" : "#71717a"}
                    fontSize="11"
                  >
                    {region}
                  </text>
                );
              })}
              {CITY_MAP.map((c) => (
                <g key={c.asset}>
                  <circle
                    cx={c.x}
                    cy={c.y}
                    r={7}
                    fill={REGION_COLORS[c.region] || statusColor(c.asset)}
                    stroke={c.city === cityFilter ? "#fff" : "#0f0f0f"}
                    strokeWidth={c.city === cityFilter ? 2 : 1}
                    onClick={() => {
                      setRegionFilter(c.region);
                      setStateFilter(c.state);
                      setCityFilter(c.city);
                    }}
                  />
                  <title>{`${c.city} • ${c.state} (${c.region})`}</title>
                </g>
              ))}
            </svg>
            <div className="mt-2 flex flex-wrap gap-3 text-xs text-zinc-400">
              {REGION_ORDER.map((region) => (
                <span key={region} className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ background: REGION_COLORS[region] }} />
                  {region}
                </span>
              ))}
            </div>
            <div className="mt-2 text-xs text-zinc-400">
              Clique em um ponto para selecionar a cidade.
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
            <div className="text-xs text-zinc-500 mb-2">Sinais do motor</div>
            <div className="text-sm text-zinc-200">{insight}</div>
            <div className="mt-3 text-xs text-zinc-400">
              DET = estrutura | LAM = travamento | TT = tempo preso
            </div>
            <div className="mt-2 text-xs text-zinc-500">
              Passe o mouse sobre as métricas para ver a interpretação detalhada.
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-black/40 p-4 grid grid-cols-3 gap-3 text-center">
            <div title="Determinismo: percentual de recorrências que seguem padrão.">
              <div className="text-xs text-zinc-500">DET</div>
              <div className="text-lg font-semibold">{formatPct(rqa?.rqa?.det)}</div>
            </div>
            <div title="Laminaridade: indica tempo em que o preço fica “travado”.">
              <div className="text-xs text-zinc-500">LAM</div>
              <div className="text-lg font-semibold">{formatPct(rqa?.rqa?.lam)}</div>
            </div>
            <div title="Trapping Time: tempo médio de permanência no regime.">
              <div className="text-xs text-zinc-500">TT</div>
              <div className="text-lg font-semibold">{rqa?.rqa?.tt?.toFixed(1) ?? "--"}</div>
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-8">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div
                className="text-xs text-zinc-500 mb-3"
                title="Linha azul = preço médio; faixas de fundo = regimes."
              >
                Preço (FipeZap Total) — valores em R$
              </div>
              <div className="flex items-center gap-2 text-xs text-zinc-400">
                <label className="text-xs text-zinc-500" title="Escolha o nível de agregação temporal.">
                  Visão
                </label>
                <select
                  className="rounded-lg border border-zinc-700 bg-black/30 px-2 py-1 text-xs"
                  value={viewMode}
                  onChange={(e) => setViewMode(e.target.value as "mensal" | "anual" | "diario")}
                >
                  <option value="mensal">Mensal</option>
                  <option value="anual">Anual</option>
                  <option value="diario">Diário</option>
                </select>
              </div>
              <div className="flex items-center gap-3 text-xs text-zinc-400">
                <span className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-sky-400" />
                  Preço médio
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ background: palette.STABLE }} />
                  Estável
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ background: palette.TRANSITION }} />
                  Transição
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ background: palette.UNSTABLE }} />
                  Instável
                </span>
              </div>
            </div>
            {chart ? (
              <div className="relative">
                <svg
                  width={chart.width}
                  height={chart.height}
                  className="w-full"
                  onMouseLeave={() => setHoverIndex(null)}
                  onMouseMove={(e) => {
                    const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const idx = Math.round(
                      ((x - chart.pad) / Math.max(1, rect.width - chart.pad * 2)) *
                        (displaySeries.length - 1)
                    );
                    if (idx >= 0 && idx < displaySeries.length) {
                      setHoverIndex(idx);
                    } else {
                      setHoverIndex(null);
                    }
                  }}
                >
                  <rect x={0} y={0} width={chart.width} height={chart.height} fill="transparent" />

                {regimes.length > 1 &&
                  regimes.map((r, i) => {
                    if (i === regimes.length - 1) return null;
                    const x0 = chart.scaleX(i, regimes.length);
                    const x1 = chart.scaleX(i + 1, regimes.length);
                    const color = palette[r.regime] || "#3f3f46";
                    return (
                      <rect
                        key={`${r.date}-${i}`}
                        x={x0}
                        y={chart.pad}
                        width={x1 - x0}
                        height={chart.height - chart.pad * 2}
                        fill={color}
                        opacity={0.12}
                      />
                    );
                  })}

                <polyline
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  points={displaySeries
                    .map((p, i) => {
                      if (p.value == null) return null;
                      return `${chart.scaleX(i, displaySeries.length)},${chart.scaleY(p.value)}`;
                    })
                    .filter(Boolean)
                    .join(" ")}
                />

                {[0, 0.25, 0.5, 0.75, 1].map((p) => {
                  const y = chart.pad + (1 - p) * (chart.height - chart.pad * 2);
                  const value = chart.ymin + p * (chart.ymax - chart.ymin);
                  return (
                    <g key={`y-${p}`}>
                      <line
                        x1={chart.pad}
                        y1={y}
                        x2={chart.width - chart.pad}
                        y2={y}
                        stroke="#1f2937"
                        strokeDasharray="4 6"
                      />
                      <text x={chart.pad - 8} y={y + 4} fill="#9ca3af" fontSize="10" textAnchor="end">
                        {value.toFixed(0)}
                      </text>
                    </g>
                  );
                })}

                {[0, 0.25, 0.5, 0.75, 1].map((p) => {
                  const idx = Math.round(p * (displaySeries.length - 1));
                  const x = chart.scaleX(idx, displaySeries.length);
                  const label = formatDateLabel(displaySeries[idx]?.date ?? "", viewMode);
                  return (
                    <g key={`x-${p}`}>
                      <line x1={x} y1={chart.height - chart.pad} x2={x} y2={chart.height - chart.pad + 6} stroke="#3f3f46" />
                      <text x={x} y={chart.height - chart.pad + 20} fill="#9ca3af" fontSize="10" textAnchor="middle">
                        {label}
                      </text>
                    </g>
                  );
                })}

                <text
                  x={chart.pad}
                  y={chart.pad - 18}
                  fill="#9ca3af"
                  fontSize="11"
                >
                  Preço (R$)
                </text>
                <text
                  x={chart.width - chart.pad}
                  y={chart.height - chart.pad + 40}
                  fill="#9ca3af"
                  fontSize="11"
                  textAnchor="end"
                >
                  Datas
                </text>
              </svg>
                {hoverIndex != null && displaySeries[hoverIndex] && (
                  <div className="absolute right-6 top-6 rounded-lg border border-zinc-700 bg-black/80 px-3 py-2 text-xs text-zinc-200">
                    <div className="font-semibold">
                      {formatDateLabel(displaySeries[hoverIndex].date, viewMode)}
                    </div>
                    <div>Preço: R$ {displaySeries[hoverIndex].value?.toFixed(0) ?? "--"}</div>
                    {regimeAt(hoverIndex) && (
                      <div className="mt-1">
                        Regime: {regimeAt(hoverIndex)?.regime ?? "--"} • Conf.{" "}
                        {regimeAt(hoverIndex)?.confidence?.toFixed(2) ?? "--"}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-zinc-400">Sem dados carregados.</div>
            )}
          </div>

          <div className="mt-4 rounded-xl border border-zinc-800 bg-black/40 p-4">
            <div className="text-xs text-zinc-500 mb-2">
              Projeção (baseline por regime)
            </div>
            {forecast ? (
              <div className="text-xs text-zinc-300 space-y-2">
                {Object.entries(forecast).map(([h, data]) => (
                  <div key={h} className="flex items-center justify-between">
                    <span>Horizonte {h} meses</span>
                    <span className="text-zinc-400">
                      {Object.keys(data.by_regime || {}).length
                        ? `${Object.keys(data.by_regime || {}).length} regimes avaliados`
                        : "sem regimes suficientes"}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-zinc-400">Sem projeção disponível.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
