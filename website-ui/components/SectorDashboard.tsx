"use client";

import { useEffect, useMemo, useState } from "react";
import DashboardFilters from "@/components/DashboardFilters";
import RegimeChart from "@/components/RegimeChart";

type Domain = "finance" | "energy" | "realestate";

type SeriesPoint = {
  date: string;
  price: number | null;
  confidence: number;
  regime: string;
  volume?: number | null;
};

type UniverseAsset = {
  asset: string;
  group?: string;
};

type AssetRow = {
  asset: string;
  group?: string;
  startDate?: string;
  endDate?: string;
  period: string;
  priceToday: number | null;
  pricePrev: number | null;
  changeAbs: number | null;
  changePct: number | null;
  ret5d: number | null;
  vol20d: number | null;
  volume: number | null;
  retH1: number | null;
  retH5: number | null;
  retH10: number | null;
};

const MISSING = "--";

const groupLabels: Record<string, string> = {
  crypto: "Cripto",
  volatility: "Volatilidade",
  commodities_broad: "Commodities",
  energy: "Energia",
  metals: "Metais",
  bonds_rates: "Juros e Bonds",
  fx: "Moedas",
  equities_us_broad: "Acoes EUA - indice amplo",
  equities_us_sectors: "Acoes EUA - setores",
  equities_international: "Acoes internacionais",
  realestate: "Imobiliario",
};

const financeGroupFilter: Array<{ value: string; label: string }> = [
  { value: "all", label: "Todos os grupos" },
  { value: "equities_us_broad", label: "Acoes EUA - indice amplo" },
  { value: "equities_us_sectors", label: "Acoes EUA - setores" },
  { value: "equities_international", label: "Acoes internacionais" },
  { value: "commodities_broad", label: "Commodities" },
  { value: "metals", label: "Metais" },
  { value: "bonds_rates", label: "Juros e Bonds" },
  { value: "fx", label: "Cambio" },
  { value: "crypto", label: "Cripto" },
  { value: "volatility", label: "Volatilidade" },
];

const FALLBACK_UNIVERSE: UniverseAsset[] = [
  { asset: "SPY", group: "equities_us_broad" },
  { asset: "QQQ", group: "equities_us_broad" },
  { asset: "IWM", group: "equities_us_broad" },
  { asset: "TLT", group: "bonds_rates" },
  { asset: "GLD", group: "metals" },
  { asset: "BTC-USD", group: "crypto" },
];

function mean(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((acc, value) => acc + value, 0) / values.length;
}

function std(values: number[]) {
  if (values.length < 2) return 0;
  const avg = mean(values);
  const variance = values.reduce((acc, value) => acc + (value - avg) ** 2, 0) / values.length;
  return Math.sqrt(variance);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function formatNumber(value: number | null | undefined, digits = 2) {
  if (!isFiniteNumber(value)) return MISSING;
  return value.toFixed(digits);
}

function formatPercent(value: number | null | undefined, digits = 2) {
  if (!isFiniteNumber(value)) return MISSING;
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(digits)}%`;
}

function computeReturn(points: Array<SeriesPoint & { price: number }>, horizonBars: number) {
  if (points.length <= horizonBars) return null;
  const last = points[points.length - 1];
  const ref = points[points.length - 1 - horizonBars];
  if (!isFiniteNumber(last?.price) || !isFiniteNumber(ref?.price) || ref.price === 0) return null;
  return (last.price - ref.price) / ref.price;
}

export default function SectorDashboard({
  title,
  showTable = true,
  initialDomain = "finance",
}: {
  title: string;
  showTable?: boolean;
  initialDomain?: Domain;
}) {
  const [timeframe, setTimeframe] = useState("daily");
  const [groupFilter, setGroupFilter] = useState("all");
  const [rangePreset, setRangePreset] = useState("180d");
  const [normalize, setNormalize] = useState(false);
  const [showRegimeBands, setShowRegimeBands] = useState(true);
  const [smoothing, setSmoothing] = useState<"none" | "ema_short" | "ema_long">("none");
  const [summaryHorizon, setSummaryHorizon] = useState<1 | 5 | 10>(5);

  const [universe, setUniverse] = useState<UniverseAsset[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [seriesByAsset, setSeriesByAsset] = useState<Record<string, SeriesPoint[]>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadUniverse = async () => {
      try {
        let data: UniverseAsset[] = [];
        const assetsQueries = [
          `/api/assets?domain=${encodeURIComponent(initialDomain)}&status=${encodeURIComponent("validated,watch")}&include_inconclusive=1`,
          `/api/assets?domain=${encodeURIComponent(initialDomain)}&status=${encodeURIComponent("validated,watch")}&include_inconclusive=0`,
        ];

        for (const query of assetsQueries) {
          const res = await fetch(query);
          if (!res.ok) continue;
          const assetsJson = await res.json();
          const parsed = Array.isArray(assetsJson?.records) ? (assetsJson.records as UniverseAsset[]) : [];
          if (parsed.length) {
            data = parsed;
            break;
          }
        }

        if (!data.length) {
          const fallbackRes = await fetch(`/api/graph/universe?tf=${encodeURIComponent(timeframe)}`);
          if (fallbackRes.ok) {
            const fallbackJson = await fallbackRes.json();
            const parsedFallback = Array.isArray(fallbackJson)
              ? (fallbackJson as UniverseAsset[])
              : Array.isArray(fallbackJson?.records)
              ? (fallbackJson.records as UniverseAsset[])
              : [];
            data = parsedFallback.filter((row) => typeof row?.asset === "string" && row.asset.length > 0);
          }
        }

        const byGroupRaw = groupFilter === "all" ? data : data.filter((r) => (r.group || "") === groupFilter);
        const byGroup = byGroupRaw.length ? byGroupRaw : FALLBACK_UNIVERSE;

        setUniverse(byGroup);
        setSelected((prev) => {
          const scoped = byGroup.map((u) => u.asset);
          const keep = prev.filter((asset) => scoped.includes(asset));
          if (keep.length) return keep;
          return scoped.slice(0, 6).length ? scoped.slice(0, 6) : FALLBACK_UNIVERSE.map((u) => u.asset);
        });
      } catch {
        setUniverse(FALLBACK_UNIVERSE);
        setSelected(FALLBACK_UNIVERSE.map((u) => u.asset));
      }
    };

    loadUniverse();
  }, [initialDomain, groupFilter, timeframe]);

  useEffect(() => {
    const loadSeries = async () => {
      if (!selected.length) {
        setSeriesByAsset({});
        return;
      }

      setLoading(true);
      try {
        const seriesRes = await fetch(`/api/graph/series-batch?assets=${selected.join(",")}&tf=${timeframe}&limit=2000`);
        if (!seriesRes.ok) {
          setSeriesByAsset({});
          return;
        }
        const seriesJson = await seriesRes.json();
        setSeriesByAsset(seriesJson || {});
      } finally {
        setLoading(false);
      }
    };

    loadSeries();
  }, [selected, timeframe]);

  const tableRows = useMemo<AssetRow[]>(() => {
    const rows = selected.map((asset) => {
      const series = seriesByAsset[asset] || [];
      const rowMeta = universe.find((u) => u.asset === asset);
      const pricedPoints = series.filter((p): p is SeriesPoint & { price: number } => isFiniteNumber(p.price));

      const first = pricedPoints[0];
      const last = pricedPoints[pricedPoints.length - 1];
      const prev = pricedPoints.length >= 2 ? pricedPoints[pricedPoints.length - 2] : undefined;
      const point5 = pricedPoints.length >= 6 ? pricedPoints[pricedPoints.length - 6] : undefined;

      const priceToday = last?.price ?? null;
      const pricePrev = prev?.price ?? null;
      const changeAbs = isFiniteNumber(priceToday) && isFiniteNumber(pricePrev) ? priceToday - pricePrev : null;
      const changePct = isFiniteNumber(changeAbs) && isFiniteNumber(pricePrev) && pricePrev !== 0 ? changeAbs / pricePrev : null;
      const ret5d =
        isFiniteNumber(priceToday) && isFiniteNumber(point5?.price) && point5.price !== 0 ? (priceToday - point5.price) / point5.price : null;

      const returns = [] as number[];
      for (let i = 1; i < pricedPoints.length; i += 1) {
        const p0 = pricedPoints[i - 1]?.price;
        const p1 = pricedPoints[i]?.price;
        if (!isFiniteNumber(p0) || !isFiniteNumber(p1) || p0 === 0) continue;
        returns.push((p1 - p0) / p0);
      }
      const vol20d = returns.length >= 20 ? std(returns.slice(-20)) : null;
      const volume = isFiniteNumber(last?.volume) ? last.volume : null;

      return {
        asset,
        group: groupLabels[rowMeta?.group || ""] || rowMeta?.group || "",
        startDate: first?.date,
        endDate: last?.date,
        period: first && last ? `${first.date} -> ${last.date}` : MISSING,
        priceToday,
        pricePrev,
        changeAbs,
        changePct,
        ret5d,
        vol20d,
        volume,
        retH1: computeReturn(pricedPoints, 1),
        retH5: computeReturn(pricedPoints, 5),
        retH10: computeReturn(pricedPoints, 10),
      };
    });

    return rows.sort((a, b) => {
      const aScore = isFiniteNumber(a.changePct) ? Math.abs(a.changePct) : -1;
      const bScore = isFiniteNumber(b.changePct) ? Math.abs(b.changePct) : -1;
      return bScore - aScore;
    });
  }, [selected, seriesByAsset, universe]);

  const metrics = useMemo(() => {
    const allSeriesPoints = selected.flatMap((asset) => seriesByAsset[asset] || []);
    const absChanges = tableRows.map((row) => row.changePct).filter(isFiniteNumber).map((value) => Math.abs(value));
    const vols = tableRows.map((row) => row.vol20d).filter(isFiniteNumber);
    const lastPrices = tableRows.map((row) => row.priceToday).filter(isFiniteNumber);

    return {
      sampleSize: allSeriesPoints.length,
      avgAbsChange: mean(absChanges),
      avgVol20d: mean(vols),
      avgPrice: mean(lastPrices),
    };
  }, [selected, seriesByAsset, tableRows]);

  const summary = useMemo(() => {
    const withDaily = tableRows.filter((row) => isFiniteNumber(row.changePct));
    const topGain = [...withDaily].sort((a, b) => (b.changePct || 0) - (a.changePct || 0))[0];
    const topDrop = [...withDaily].sort((a, b) => (a.changePct || 0) - (b.changePct || 0))[0];

    const horizonKey = summaryHorizon === 1 ? "retH1" : summaryHorizon === 5 ? "retH5" : "retH10";
    const withHorizon = tableRows.filter((row) => isFiniteNumber(row[horizonKey] as number | null));
    const topGainH = [...withHorizon].sort((a, b) => ((b[horizonKey] as number) || 0) - ((a[horizonKey] as number) || 0))[0];
    const topDropH = [...withHorizon].sort((a, b) => ((a[horizonKey] as number) || 0) - ((b[horizonKey] as number) || 0))[0];

    const starts = tableRows.map((row) => row.startDate).filter((value): value is string => Boolean(value));
    const ends = tableRows.map((row) => row.endDate).filter((value): value is string => Boolean(value));
    const periodStart = starts.length ? starts.sort()[0] : null;
    const periodEnd = ends.length ? ends.sort()[ends.length - 1] : null;

    const avgVol20d = mean(tableRows.map((row) => row.vol20d).filter(isFiniteNumber));

    return {
      period: periodStart && periodEnd ? `${periodStart} -> ${periodEnd}` : MISSING,
      topGain,
      topDrop,
      topGainH,
      topDropH,
      avgVol20d: isFiniteNumber(avgVol20d) && avgVol20d > 0 ? avgVol20d : null,
    };
  }, [tableRows, summaryHorizon]);

  const sectors =
    initialDomain === "finance"
      ? financeGroupFilter
      : initialDomain === "energy"
      ? [
          { value: "all", label: "Todos os grupos" },
          { value: "energy", label: "Energia" },
        ]
      : [{ value: "all", label: "Todos os grupos imobiliarios" }];

  return (
    <div className="p-4 md:p-5 space-y-4 md:space-y-5">
      <div className="space-y-2">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">{title}</div>
        <h1 className="text-2xl font-semibold">Painel financeiro por ativo</h1>
        <p className="text-sm text-zinc-400">Leitura direta de preco e variacao com base nas series carregadas.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card label="Ativos" value={String(selected.length)} helper="Ativos selecionados no painel." />
        <Card label="Amostras" value={String(metrics.sampleSize)} helper="Total de pontos carregados no grafico." />
        <Card label="|Delta %| medio" value={formatPercent(metrics.avgAbsChange)} helper="Media da variacao absoluta diaria." />
        <Card label="Vol media 20d" value={formatPercent(metrics.avgVol20d)} helper="Desvio padrao dos retornos diarios (janela 20)." />
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 space-y-4">
        <DashboardFilters
          assets={universe}
          selected={selected}
          onSelectedChange={setSelected}
          sector={groupFilter}
          onSectorChange={setGroupFilter}
          sectors={sectors}
          timeframe={timeframe}
          onTimeframeChange={setTimeframe}
          rangePreset={rangePreset}
          onRangePresetChange={setRangePreset}
          normalize={normalize}
          onNormalizeChange={setNormalize}
          showRegimeBands={showRegimeBands}
          onShowRegimeBandsChange={setShowRegimeBands}
          regimeBandsLabel="Destaques"
          regimeBandsTitle="Exibir ou ocultar destaques de fundo no grafico"
          smoothing={smoothing}
          onSmoothingChange={setSmoothing}
        />
        <p className="text-xs text-zinc-500">Grafico: eixo X = tempo, eixo Y = preco (ou indice base 100 se normalizado).</p>

        {loading ? <div className="text-sm text-zinc-500">Carregando series...</div> : null}

        <RegimeChart
          data={seriesByAsset}
          selected={selected}
          normalize={normalize}
          showRegimeBands={showRegimeBands}
          smoothing={smoothing}
          rangePreset={rangePreset}
          tooltipMode="price_only"
        />
      </div>

      {showTable ? (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4 md:gap-5">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
            <div className="flex items-center justify-between">
              <div className="text-sm uppercase tracking-widest text-zinc-400">Tabela por ativo</div>
              <div className="text-xs text-zinc-500" title="Metricas derivadas da serie exibida">
                Valores em unidade de preco do ativo
              </div>
            </div>
            <div className="mt-3 overflow-auto">
              <table className="w-full text-xs">
                <thead className="text-zinc-500 uppercase">
                  <tr>
                    <th className="text-left py-2">Ativo</th>
                    <th className="text-left py-2">Setor</th>
                    <th className="text-left py-2">Periodo</th>
                    <th className="text-left py-2">Preco hoje</th>
                    <th className="text-left py-2">Preco ontem</th>
                    <th className="text-left py-2">Delta abs</th>
                    <th className="text-left py-2">Delta %</th>
                    <th className="text-left py-2">Ret 5D</th>
                    <th className="text-left py-2">Vol 20D</th>
                    <th className="text-left py-2">Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row) => {
                    const deltaTone = !isFiniteNumber(row.changePct)
                      ? "text-zinc-300"
                      : row.changePct > 0
                      ? "text-emerald-300"
                      : row.changePct < 0
                      ? "text-rose-300"
                      : "text-zinc-300";

                    return (
                      <tr key={row.asset} className="border-t border-zinc-800/70 text-zinc-300">
                        <td className="py-2">{row.asset}</td>
                        <td className="py-2 text-zinc-400">{row.group || MISSING}</td>
                        <td className="py-2 text-zinc-400">{row.period}</td>
                        <td className="py-2">{formatNumber(row.priceToday)}</td>
                        <td className="py-2">{formatNumber(row.pricePrev)}</td>
                        <td className="py-2">{formatNumber(row.changeAbs)}</td>
                        <td className={`py-2 ${deltaTone}`}>{formatPercent(row.changePct)}</td>
                        <td className="py-2">{formatPercent(row.ret5d)}</td>
                        <td className="py-2">{formatPercent(row.vol20d)}</td>
                        <td className="py-2">{isFiniteNumber(row.volume) ? row.volume.toLocaleString("en-US") : MISSING}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 space-y-3">
            <div className="text-sm uppercase tracking-widest text-zinc-400">Resumo</div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-zinc-400" title="Horizonte visual de retorno em barras">
                Horizonte:
              </span>
              {[1, 5, 10].map((h) => (
                <button
                  key={h}
                  className={`rounded-md border px-2 py-1 ${
                    summaryHorizon === h ? "border-cyan-400 text-cyan-300" : "border-zinc-700 text-zinc-300"
                  }`}
                  onClick={() => setSummaryHorizon(h as 1 | 5 | 10)}
                  title={`Retorno visual em ${h} barra(s)`}
                >
                  h{h}
                </button>
              ))}
            </div>
            <div className="text-xs text-zinc-300">Amostras no grafico: {metrics.sampleSize}</div>
            <div className="text-xs text-zinc-300">Ativos selecionados: {selected.length}</div>
            <div className="text-xs text-zinc-300">Periodo exibido: {summary.period}</div>
            <div className="text-xs text-zinc-300">
              Maior alta do dia: {summary.topGain ? `${summary.topGain.asset} (${formatPercent(summary.topGain.changePct)})` : MISSING}
            </div>
            <div className="text-xs text-zinc-300">
              Maior queda do dia: {summary.topDrop ? `${summary.topDrop.asset} (${formatPercent(summary.topDrop.changePct)})` : MISSING}
            </div>
            <div className="text-xs text-zinc-300">
              Maior alta H{summaryHorizon}: {summary.topGainH ? `${summary.topGainH.asset} (${formatPercent(summary.topGainH[summaryHorizon === 1 ? "retH1" : summaryHorizon === 5 ? "retH5" : "retH10"] as number)})` : MISSING}
            </div>
            <div className="text-xs text-zinc-300">
              Maior queda H{summaryHorizon}: {summary.topDropH ? `${summary.topDropH.asset} (${formatPercent(summary.topDropH[summaryHorizon === 1 ? "retH1" : summaryHorizon === 5 ? "retH5" : "retH10"] as number)})` : MISSING}
            </div>
            <div className="text-xs text-zinc-300">
              Volatilidade media (20d): {summary.avgVol20d != null ? formatPercent(summary.avgVol20d) : MISSING}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Card({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3 md:p-4" title={helper}>
      <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">{label}</div>
      <div className="mt-1 text-lg md:text-xl font-semibold text-zinc-100">{value}</div>
      <div className="mt-1 text-[11px] text-zinc-500">{helper}</div>
    </div>
  );
}
