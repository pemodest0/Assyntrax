"use client";

import { useEffect, useMemo, useState } from "react";
import BrMap from "@/components/BrMap";

type Point = { date: string; value: number };
type DynamicRow = {
  date: string;
  regime: string;
  microstate: "M1" | "M2" | "M3" | "UNK";
  transition: boolean;
  confidence: number;
  quality: number;
  entropy: number;
  persistence: number;
  instability_score: number;
};

type AssetMeta = {
  asset: string;
  city: string;
  state: string;
  region: string;
  source_type: string;
  source_name: string;
};

type RealEstatePayload = {
  asset: string;
  assets: string[];
  assets_meta: AssetMeta[];
  data: {
    profile: {
      n_points: number;
      coverage_years: number;
      gap_ratio: number;
      start_date: string;
      end_date: string;
      required_fields: { P: boolean; L: boolean; J: boolean; D: boolean };
      notes: string[];
    };
    series: { P: Point[]; L: Point[]; J: Point[]; D: Point[] };
  };
  dynamic: { m: number; tau: number; rows: DynamicRow[] };
  operational: {
    status: "validated" | "watch" | "inconclusive";
    explanation: string;
    adequacy_ok: boolean;
    thresholds: Record<string, number>;
    latest: DynamicRow | null;
  };
};

const palette: Record<string, string> = {
  STABLE: "#34d399",
  TRANSITION: "#fbbf24",
  UNSTABLE: "#fb7185",
};

const REGION_ORDER = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Desconhecida"];

function fallbackMetaFromAsset(asset: string): AssetMeta {
  const city = asset
    .replace(/^FipeZap_/i, "")
    .replace(/_Total$/i, "")
    .replace(/_/g, " ");
  return {
    asset,
    city,
    state: "NA",
    region: "Desconhecida",
    source_type: "fallback",
    source_name: "asset_name",
  };
}

function formatPct(v: number | null | undefined) {
  if (v == null || Number.isNaN(v)) return "--";
  return `${(v * 100).toFixed(2)}%`;
}

function formatRegime(regime?: string) {
  if (!regime) return "--";
  if (regime === "STABLE") return "Estável";
  if (regime === "TRANSITION") return "Transição";
  if (regime === "UNSTABLE") return "Instável";
  return regime;
}

function getOperationalRule(status?: string, regime?: string) {
  if (status === "validated" && regime === "STABLE") {
    return "Projeções condicionais permitidas dentro do regime atual.";
  }
  if (status === "watch") {
    return "Regime em observação: evitar extrapolações e reduzir agressividade.";
  }
  return "Somente diagnóstico: ação operacional bloqueada por baixa estrutura.";
}

function computeForecast(
  series: Point[],
  regime: string | undefined,
  horizonDays: 1 | 5 | 10,
  allowForecast: boolean
) {
  if (!allowForecast) return null;
  const latest = series.at(-1)?.value;
  if (!Number.isFinite(latest)) return null;
  const drift = regime === "STABLE" ? 0.004 : regime === "TRANSITION" ? 0.001 : -0.003;
  return {
    p50: (latest as number) * (1 + drift * horizonDays),
  };
}

export default function RealEstateDashboard() {
  const [payload, setPayload] = useState<RealEstatePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regionFilter, setRegionFilter] = useState("Sudeste");
  const [stateFilter, setStateFilter] = useState("SP");
  const [assetFilter, setAssetFilter] = useState<string>("");
  const [horizonDays, setHorizonDays] = useState<1 | 5 | 10>(5);
  const [viewMode, setViewMode] = useState<"mensal" | "anual" | "diario">("mensal");
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      setLoading(true);
      try {
        const query = assetFilter ? `?asset=${encodeURIComponent(assetFilter)}` : "";
        const res = await fetch(`/api/realestate/asset${query}`, {
          signal: controller.signal,
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as { error?: string; reason?: string };
          throw new Error(
            `Falha ao carregar imobiliário (${res.status}). ${body.reason || body.error || "Sem base imobiliária disponível."}`
          );
        }
        const data = (await res.json()) as RealEstatePayload;
        setPayload(data);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setPayload(null);
        setError(err instanceof Error ? err.message : "Erro desconhecido.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    void run();
    return () => controller.abort();
  }, [assetFilter]);

  const assetsMeta = useMemo(() => {
    const raw = payload?.assets_meta || [];
    if (raw.length > 0) {
      return raw.map((m) => ({
        asset: m.asset,
        city: m.city || fallbackMetaFromAsset(m.asset).city,
        state: m.state || "NA",
        region: m.region || "Desconhecida",
        source_type: m.source_type || "fallback",
        source_name: m.source_name || "asset_name",
      }));
    }
    return (payload?.assets || []).map((asset) => fallbackMetaFromAsset(asset));
  }, [payload?.assets_meta, payload?.assets]);

  const regionOptions = useMemo(() => {
    const unique = Array.from(new Set(assetsMeta.map((m) => m.region)));
    return REGION_ORDER.filter((r) => unique.includes(r)).concat(
      unique.filter((r) => !REGION_ORDER.includes(r))
    );
  }, [assetsMeta]);

  const statesByRegion = useMemo(() => {
    const filtered = assetsMeta.filter((m) => m.region === regionFilter);
    return Array.from(new Set(filtered.map((m) => m.state))).sort();
  }, [assetsMeta, regionFilter]);

  const assetsByState = useMemo(() => {
    return assetsMeta.filter((m) => m.state === stateFilter).sort((a, b) => a.city.localeCompare(b.city));
  }, [assetsMeta, stateFilter]);

  useEffect(() => {
    if (!assetsMeta.length) return;
    if (!regionOptions.includes(regionFilter)) {
      setRegionFilter(regionOptions[0] || "Desconhecida");
      return;
    }
    if (!statesByRegion.includes(stateFilter)) {
      setStateFilter(statesByRegion[0] || assetsMeta[0].state);
      return;
    }
    const current = assetsByState.find((m) => m.asset === assetFilter);
    if (!current) {
      setAssetFilter(assetsByState[0]?.asset || assetsMeta[0].asset);
    }
  }, [assetsMeta, assetsByState, assetFilter, regionFilter, regionOptions, stateFilter, statesByRegion]);

  const currentMeta = useMemo(() => {
    return assetsMeta.find((m) => m.asset === (payload?.asset || assetFilter)) || null;
  }, [assetsMeta, assetFilter, payload?.asset]);

  const profile = payload?.data.profile;
  const P = useMemo(() => payload?.data.series.P || [], [payload?.data.series.P]);
  const L = useMemo(() => payload?.data.series.L || [], [payload?.data.series.L]);
  const J = useMemo(() => payload?.data.series.J || [], [payload?.data.series.J]);
  const rows = useMemo(() => payload?.dynamic.rows || [], [payload?.dynamic.rows]);
  const latest = payload?.operational.latest || null;

  const displaySeries = useMemo(() => {
    if (!P.length) return [];
    if (viewMode === "diario") return P;
    if (viewMode === "anual") {
      const byYear = new Map<string, Point>();
      for (const p of P) byYear.set(p.date.slice(0, 4), p);
      return Array.from(byYear.values());
    }
    return P;
  }, [P, viewMode]);

  const chart = useMemo(() => {
    if (!displaySeries.length) return null;
    const width = 1400;
    const height = 860;
    const pad = 90;
    const yVals = displaySeries.map((d) => d.value).filter((v) => Number.isFinite(v));
    if (!yVals.length) return null;
    const ymin = Math.min(...yVals);
    const ymax = Math.max(...yVals);
    const scaleX = (i: number, total: number) => pad + (i / Math.max(1, total - 1)) * (width - pad * 2);
    const scaleY = (v: number) => height - pad - ((v - ymin) / Math.max(1e-6, ymax - ymin)) * (height - pad * 2);
    return { width, height, pad, scaleX, scaleY, ymin, ymax };
  }, [displaySeries]);

  const rowByDisplayIndex = (idx: number) => {
    if (!rows.length || !displaySeries.length) return null;
    const mapped = Math.round((idx / Math.max(1, displaySeries.length - 1)) * (rows.length - 1));
    return rows[Math.max(0, Math.min(rows.length - 1, mapped))] || null;
  };

  const allowForecast = payload?.operational.status !== "inconclusive" && !!latest?.regime;
  const forecast = computeForecast(P, latest?.regime, horizonDays, allowForecast);
  const periodInfo = profile ? `${profile.start_date} ate ${profile.end_date}` : "--";

  const onSelectUF = (uf: string) => {
    setStateFilter(uf);
    const firstByUf = assetsMeta.find((m) => m.state === uf);
    if (firstByUf) {
      setRegionFilter(firstByUf.region);
      setAssetFilter(firstByUf.asset);
    }
  };

  if (loading) {
    return <div className="p-6 text-sm text-zinc-400">Carregando setor imobiliário...</div>;
  }

  if (error || !payload) {
    return (
      <div className="p-6 space-y-3">
        <div className="text-sm text-rose-300">Falha ao carregar setor imobiliário: {error || "sem dados."}</div>
        <div className="text-xs text-zinc-400">
          Ação sugerida: verifique `data/realestate` e `public/data/realestate` com arquivos de cidade, estado e região.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">Setor Imobiliário</h1>
        <p className="text-sm text-zinc-300 leading-relaxed">
          Modelo em 3 camadas: dados (P/L/J/D), dinâmica de regime e operação com gate auditável.
        </p>
      </header>

      <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
        <div className="text-xs uppercase tracking-wide text-zinc-500">O que muda hoje</div>
        <div className="mt-2 grid gap-3 md:grid-cols-4">
          <div
            className="rounded-lg border border-zinc-700 bg-zinc-950/50 p-3"
            title="Status final do gate: validated, watch ou inconclusive."
          >
            <div className="text-[11px] text-zinc-400">Status operacional</div>
            <div className="mt-1 text-base font-semibold text-zinc-100">{payload?.operational.status || "--"}</div>
          </div>
          <div
            className="rounded-lg border border-zinc-700 bg-zinc-950/50 p-3"
            title="Regime dominante no último ponto disponível para o ativo selecionado."
          >
            <div className="text-[11px] text-zinc-400">Regime atual</div>
            <div className="mt-1 text-base font-semibold text-zinc-100">{formatRegime(latest?.regime)}</div>
          </div>
          <div
            className="rounded-lg border border-zinc-700 bg-zinc-950/50 p-3"
            title="Confiança e qualidade medem consistência estrutural da leitura."
          >
            <div className="text-[11px] text-zinc-400">Confiabilidade</div>
            <div className="mt-1 text-base font-semibold text-zinc-100">
              C {latest?.confidence?.toFixed(2) ?? "--"} | Q {latest?.quality?.toFixed(2) ?? "--"}
            </div>
          </div>
          <div
            className="rounded-lg border border-zinc-700 bg-zinc-950/50 p-3"
            title="Leitura operacional sugerida para reduzir erro em regime instável."
          >
            <div className="text-[11px] text-zinc-400">Regra do dia</div>
            <div className="mt-1 text-sm text-zinc-200">{getOperationalRule(payload?.operational.status, latest?.regime)}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-4 space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
            <div className="text-xs text-zinc-500 mb-2">Filtro geográfico</div>
            <div className="mb-3 text-[11px] text-zinc-400 leading-relaxed">
              Passo 1: região. Passo 2: estado. Passo 3: cidade.
            </div>
            <div className="space-y-3">
              <label className="text-xs text-zinc-400">Região</label>
              <select
                className="w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm"
                value={regionFilter}
                aria-label="Selecionar região"
                onChange={(e) => {
                  const region = e.target.value;
                  setRegionFilter(region);
                  const nextState = Array.from(new Set(assetsMeta.filter((m) => m.region === region).map((m) => m.state))).sort()[0];
                  if (nextState) onSelectUF(nextState);
                }}
              >
                {regionOptions.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>

              <label className="text-xs text-zinc-400">Estado</label>
              <select
                className="w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm"
                value={stateFilter}
                aria-label="Selecionar estado"
                onChange={(e) => onSelectUF(e.target.value)}
              >
                {statesByRegion.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>

              <label className="text-xs text-zinc-400">Cidade/ativo</label>
              <select
                className="w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm"
                value={payload?.asset || assetFilter}
                aria-label="Selecionar cidade ou ativo"
                onChange={(e) => setAssetFilter(e.target.value)}
              >
                {assetsByState.map((m) => (
                  <option key={m.asset} value={m.asset}>
                    {m.city}
                  </option>
                ))}
              </select>
              <div className="rounded-lg border border-zinc-700 bg-zinc-950/40 p-2 text-xs text-zinc-400">
                Fonte: {currentMeta?.source_type || "--"} / {currentMeta?.source_name || "--"}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
            <div className="text-xs text-zinc-500 mb-2">Mapa político do Brasil por estados</div>
            <BrMap selectedUF={stateFilter} onSelectUF={onSelectUF} />
            <div className="mt-2 text-[11px] text-zinc-500">
              Clique no estado para filtrar ativos da UF e atualizar a lista de cidades.
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
            <div className="text-xs text-zinc-500 mb-3">Gate operacional</div>
            <div className="space-y-1 text-sm text-zinc-200">
              <div title="validated: sinal operacional; watch: monitorar; inconclusive: somente diagnóstico">
                Status: {payload?.operational.status || "--"}
              </div>
              <div title="Confere se série possui tamanho, frequência e cobertura mínima para o modelo">
                Adequação de dados: {payload?.operational.adequacy_ok ? "ok" : "falhou"}
              </div>
              <div>Instability score: {latest?.instability_score?.toFixed(3) ?? "--"}</div>
              <div className="text-zinc-400">{payload?.operational.explanation || "--"}</div>
            </div>
            <div className="mt-2 text-[11px] text-zinc-500">
              Quando o gate está inconclusive, as projeções p50 são bloqueadas para evitar uso indevido.
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-8 space-y-4">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-5">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div className="text-xs text-zinc-500">
                Preço médio (P) com bandas de regime - camada dinâmica (m={payload?.dynamic.m ?? "-"}, tau={payload?.dynamic.tau ?? "-"})
              </div>
              <div className="flex items-center gap-2 text-xs text-zinc-400">
                <label>Visão</label>
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
            </div>

            {chart ? (
              <div className="relative">
                <svg
                  width={chart.width}
                  height={chart.height}
                  className="w-full"
                  role="img"
                  aria-label="Série de preço médio com faixas de regime do ativo imobiliário selecionado"
                  onMouseLeave={() => setHoverIndex(null)}
                  onMouseMove={(e) => {
                    const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const idx = Math.round(
                      ((x - chart.pad) / Math.max(1, rect.width - chart.pad * 2)) * (displaySeries.length - 1)
                    );
                    setHoverIndex(idx >= 0 && idx < displaySeries.length ? idx : null);
                  }}
                >
                  <rect x={0} y={0} width={chart.width} height={chart.height} fill="transparent" />

                  {rows.length > 1 &&
                    rows.map((r, i) => {
                      if (i === rows.length - 1) return null;
                      const x0 = chart.scaleX(i, rows.length);
                      const x1 = chart.scaleX(i + 1, rows.length);
                      return (
                        <rect
                          key={`${r.date}-${i}`}
                          x={x0}
                          y={chart.pad}
                          width={x1 - x0}
                          height={chart.height - chart.pad * 2}
                          fill={palette[r.regime] || "#3f3f46"}
                          opacity={0.13}
                        />
                      );
                    })}

                  <polyline
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth={2.2}
                    points={displaySeries
                      .map((p, i) => `${chart.scaleX(i, displaySeries.length)},${chart.scaleY(p.value)}`)
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
                </svg>

                {hoverIndex != null && displaySeries[hoverIndex] && (
                  <div className="absolute right-6 top-6 rounded-lg border border-zinc-700 bg-black/80 px-3 py-2 text-xs text-zinc-200">
                    <div className="font-semibold">{displaySeries[hoverIndex].date}</div>
                    <div>Preço: R$ {displaySeries[hoverIndex].value.toFixed(0)}</div>
                    {rowByDisplayIndex(hoverIndex) && (
                      <div>
                        Regime: {formatRegime(rowByDisplayIndex(hoverIndex)?.regime)} | Confiança{" "}
                        {rowByDisplayIndex(hoverIndex)?.confidence.toFixed(2)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-zinc-400">Sem dados para este ativo. Escolha outra cidade ou estado.</div>
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
              <div className="text-xs text-zinc-500 mb-2">Camada de dados e perfil</div>
              <div className="grid grid-cols-2 gap-2 text-sm text-zinc-200">
                <div className="text-zinc-400">Ativo</div>
                <div>{payload?.asset || "--"}</div>
                <div className="text-zinc-400">Cidade</div>
                <div>{currentMeta?.city || "--"}</div>
                <div className="text-zinc-400">Periodo analisado</div>
                <div>{periodInfo}</div>
                <div className="text-zinc-400">Pontos</div>
                <div>{profile?.n_points ?? "--"}</div>
                <div className="text-zinc-400">Cobertura (anos)</div>
                <div>{profile?.coverage_years ?? "--"}</div>
                <div className="text-zinc-400">Gap ratio</div>
                <div>{profile?.gap_ratio ?? "--"}</div>
                <div className="text-zinc-400" title="L(t): proxy de liquidez (atividade/estoque)">
                  L(t) (liquidez)
                </div>
                <div>{formatPct(L.at(-1)?.value)}</div>
                <div className="text-zinc-400" title="J(t): juros/crédito; impacta custo de financiamento">
                  J(t) (juros)
                </div>
                <div>{J.at(-1)?.value != null ? J.at(-1)?.value.toFixed(2) : "N/D"}</div>
                <div className="text-zinc-400" title="D(t): desconto pedido x fechamento, quando disponível">
                  D(t) (desconto médio)
                </div>
                <div>{payload?.data.series.D.length ? formatPct(payload.data.series.D.at(-1)?.value) : "N/D"}</div>
                <div className="text-zinc-400">Disponibilidade P/L/J/D</div>
                <div>
                  P {profile?.required_fields.P ? "ok" : "off"} | L {profile?.required_fields.L ? "ok" : "off"} | J{" "}
                  {profile?.required_fields.J ? "ok" : "off"} | D {profile?.required_fields.D ? "ok" : "off"}
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-xs text-zinc-500">Camada operacional</div>
                <select
                  className="rounded-lg border border-zinc-700 bg-black/30 px-2 py-1 text-xs"
                  value={horizonDays}
                  onChange={(e) => setHorizonDays(Number(e.target.value) as 1 | 5 | 10)}
                >
                  <option value={1}>1 dia</option>
                  <option value={5}>5 dias</option>
                  <option value={10}>10 dias</option>
                </select>
              </div>
                <div className="space-y-1 text-sm text-zinc-200">
                <div>Regime atual: {formatRegime(latest?.regime)}</div>
                <div>Confiança: {latest?.confidence?.toFixed(2) ?? "--"}</div>
                <div>Qualidade: {latest?.quality?.toFixed(2) ?? "--"}</div>
                <div>Entropia: {latest?.entropy?.toFixed(2) ?? "--"}</div>
                <div>Persistência de regime: {latest?.persistence ?? "--"} dias</div>
                <div title="p50 condicional ao regime. Se gate inconclusive, fica indisponível.">
                  Forecast p50 ({horizonDays}d): R$ {forecast?.p50?.toFixed(0) ?? "N/D"}
                </div>
                <div>Instability score: {latest?.instability_score?.toFixed(3) ?? "--"}</div>
                <div className="text-zinc-400">{payload?.operational.explanation || "--"}</div>
                {!allowForecast && (
                  <div className="text-amber-400">Somente diagnóstico: projeções bloqueadas por gate inconclusivo.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
