"use client";

import { useEffect, useMemo, useState } from "react";
import DashboardFilters from "@/components/DashboardFilters";
import RegimeChart from "@/components/RegimeChart";

type Domain = "finance" | "energy" | "realestate";
type StatusTab = "validated" | "watch" | "inconclusive";

type SeriesPoint = {
  date: string;
  price: number | null;
  confidence: number;
  regime: string;
};

type UniverseAsset = {
  asset: string;
  group?: string;
  domain?: string;
  state?: { label?: string };
  metrics?: { confidence?: number; quality?: number };
  confidence?: number;
  quality?: number;
  signal_status?: string;
  reason?: string;
  risk_truth_status?: string;
};

type ForecastPoint = {
  y_pred?: number;
};

const regimeColor: Record<string, string> = {
  STABLE: "text-emerald-300",
  TRANSITION: "text-amber-300",
  UNSTABLE: "text-rose-300",
  INCONCLUSIVE: "text-zinc-400",
};

const groupLabels: Record<string, string> = {
  crypto: "Cripto",
  volatility: "Volatilidade",
  commodities_broad: "Commodities",
  energy: "Energia",
  metals: "Metais",
  bonds_rates: "Juros e Bonds",
  fx: "Moedas",
  equities_us_broad: "Ações EUA - índice amplo",
  equities_us_sectors: "Ações EUA - setores",
  equities_international: "Ações internacionais",
  realestate: "Imobiliário",
};

const financeGroupFilter: Array<{ value: string; label: string }> = [
  { value: "all", label: "Todos os grupos" },
  { value: "equities_us_broad", label: "Ações EUA - índice amplo" },
  { value: "equities_us_sectors", label: "Ações EUA - setores" },
  { value: "equities_international", label: "Ações internacionais" },
  { value: "commodities_broad", label: "Commodities" },
  { value: "metals", label: "Metais" },
  { value: "bonds_rates", label: "Juros e Bonds" },
  { value: "fx", label: "Câmbio" },
  { value: "crypto", label: "Cripto" },
  { value: "volatility", label: "Volatilidade" },
];

function normalizeRegime(label?: string) {
  if (!label) return "TRANSITION";
  if (label === "NOISY") return "UNSTABLE";
  if (label === "STABLE" || label === "TRANSITION" || label === "UNSTABLE" || label === "INCONCLUSIVE") return label;
  return "TRANSITION";
}

function mean(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((acc, value) => acc + value, 0) / values.length;
}

function computeFallbackForecast(
  lastPrice: number | null | undefined,
  regime: string,
  confidence: number,
  horizon: 1 | 5 | 10
) {
  if (!Number.isFinite(lastPrice)) return null;
  const safePrice = Number(lastPrice);
  const driftByRegime: Record<string, number> = {
    STABLE: 0.0016,
    TRANSITION: 0.0004,
    UNSTABLE: -0.0008,
    INCONCLUSIVE: 0,
  };
  const confidenceWeight = Math.max(0.2, Math.min(1, confidence || 0));
  const drift = (driftByRegime[regime] ?? 0) * confidenceWeight;
  return safePrice * (1 + drift * horizon);
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
  const [statusTab, setStatusTab] = useState<StatusTab>("validated");
  const [showInconclusive, setShowInconclusive] = useState(false);
  const [rangePreset, setRangePreset] = useState("180d");
  const [normalize, setNormalize] = useState(false);
  const [showRegimeBands, setShowRegimeBands] = useState(true);
  const [smoothing, setSmoothing] = useState<"none" | "ema_short" | "ema_long">("none");
  const [summaryHorizon, setSummaryHorizon] = useState<1 | 5 | 10>(5);

  const [universe, setUniverse] = useState<UniverseAsset[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [seriesByAsset, setSeriesByAsset] = useState<Record<string, SeriesPoint[]>>({});
  const [forecastByAsset, setForecastByAsset] = useState<Record<string, Record<number, ForecastPoint | null>>>({});
  const [loading, setLoading] = useState(false);
  const [runMeta, setRunMeta] = useState<{ run_id?: string; global_verdict_status?: string } | null>(null);
  const [runSummary, setRunSummary] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const loadUniverse = async () => {
      const statuses = statusTab === "inconclusive" ? "inconclusive" : "validated,watch";
      const includeInconclusive = showInconclusive || statusTab === "inconclusive" ? 1 : 0;
      const [runRes, assetsRes] = await Promise.all([
        fetch("/api/run/latest"),
        fetch(
          `/api/assets?domain=${encodeURIComponent(initialDomain)}&status=${encodeURIComponent(
            statuses
          )}&include_inconclusive=${includeInconclusive}`
        ),
      ]);

      if (runRes.ok) {
        const runJson = await runRes.json();
        setRunMeta({ run_id: runJson?.run_id, global_verdict_status: runJson?.global_verdict_status });
        setRunSummary((runJson?.summary as Record<string, unknown>) || null);
      } else {
        setRunMeta(null);
        setRunSummary(null);
      }

      const assetsJson = await assetsRes.json();
      const data = Array.isArray(assetsJson?.records) ? (assetsJson.records as UniverseAsset[]) : [];
      const byGroup = groupFilter === "all" ? data : data.filter((r) => (r.group || "") === groupFilter);
      setUniverse(byGroup);
      setSelected((prev) => {
        const approved = byGroup.filter((u) => (u.risk_truth_status || "validated") === "validated");
        const preferred = approved.length ? approved : byGroup;
        const keep = prev.filter((asset) => preferred.some((u) => u.asset === asset));
        if (keep.length) return keep;
        return preferred.slice(0, 4).map((u) => u.asset);
      });
    };
    loadUniverse();
  }, [initialDomain, statusTab, showInconclusive, groupFilter]);

  useEffect(() => {
    if (!universe.length) return;
    const scoped = universe.map((u) => u.asset);
    setSelected((prev) => {
      const kept = prev.filter((a) => scoped.includes(a));
      if (kept.length) return kept;
      return scoped.slice(0, 6);
    });
  }, [universe]);

  useEffect(() => {
    const loadSeries = async () => {
      if (!selected.length) {
        setSeriesByAsset({});
        setForecastByAsset({});
        return;
      }
      setLoading(true);
      try {
        const seriesRes = await fetch(`/api/graph/series-batch?assets=${selected.join(",")}&tf=${timeframe}&limit=2000`);
        const seriesJson = await seriesRes.json();
        setSeriesByAsset(seriesJson || {});

        const forecasts: Record<string, Record<number, ForecastPoint | null>> = {};
        await Promise.all(
          selected.map(async (asset) => {
            forecasts[asset] = { 1: null, 5: null, 10: null };
            await Promise.all(
              [1, 5, 10].map(async (h) => {
                try {
                  const f = await fetch(`/api/files/forecast_suite/${asset}/${timeframe}/${asset}_${timeframe}_log_return_h${h}.json`);
                  if (!f.ok) {
                    forecasts[asset][h] = null;
                    return;
                  }
                  const j = await f.json();
                  const preds = Array.isArray(j?.predictions) ? j.predictions : [];
                  forecasts[asset][h] = preds.length ? preds[preds.length - 1] : null;
                } catch {
                  forecasts[asset][h] = null;
                }
              })
            );
          })
        );
        setForecastByAsset(forecasts);
      } finally {
        setLoading(false);
      }
    };
    loadSeries();
  }, [selected, timeframe]);

  const metrics = useMemo(() => {
    const activeSeries = selected.flatMap((asset) => seriesByAsset[asset] || []);
    const lastPoints = selected
      .map((asset) => (seriesByAsset[asset] || [])[Math.max(0, (seriesByAsset[asset] || []).length - 1)])
      .filter(Boolean) as SeriesPoint[];
    const avgConf = mean(lastPoints.map((point) => point.confidence || 0));
    const unstableCount = lastPoints.filter((point) => normalizeRegime(point.regime) === "UNSTABLE").length;
    const dominant = (() => {
      const counts: Record<string, number> = {};
      lastPoints.forEach((point) => {
        const regime = normalizeRegime(point.regime);
        counts[regime] = (counts[regime] || 0) + 1;
      });
      return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || "TRANSITION";
    })();
    return {
      state: dominant,
      confidence: avgConf,
      quality: Math.max(0, Math.min(1, avgConf * 0.9)),
      alerts: unstableCount,
      sampleSize: activeSeries.length,
    };
  }, [selected, seriesByAsset]);

  const tableRows = useMemo(() => {
    return selected.map((asset) => {
      const series = seriesByAsset[asset] || [];
      const last = series[series.length - 1];
      const first = series[0];
      const confidence = last?.confidence ?? 0;
      const regime = normalizeRegime(last?.regime);
      const rowMeta = universe.find((u) => u.asset === asset);
      const validationStatus = rowMeta?.risk_truth_status || rowMeta?.signal_status || "validated";
      const validationReason = rowMeta?.reason || "";
      const lastRegimeIndex = series.length - 1;
      let streak = 0;
      for (let i = lastRegimeIndex; i >= 0; i -= 1) {
        if (normalizeRegime(series[i]?.regime) === regime) streak += 1;
        else break;
      }
      const regimeDurationDays = timeframe === "weekly" ? streak * 7 : streak;
      const h1Raw = forecastByAsset[asset]?.[1]?.y_pred;
      const h5Raw = forecastByAsset[asset]?.[5]?.y_pred;
      const h10Raw = forecastByAsset[asset]?.[10]?.y_pred;
      const h1 = h1Raw != null ? (last?.price || 0) * (1 + h1Raw) : computeFallbackForecast(last?.price, regime, confidence, 1);
      const h5 = h5Raw != null ? (last?.price || 0) * (1 + h5Raw) : computeFallbackForecast(last?.price, regime, confidence, 5);
      const h10 = h10Raw != null ? (last?.price || 0) * (1 + h10Raw) : computeFallbackForecast(last?.price, regime, confidence, 10);
      const projSelected = summaryHorizon === 1 ? h1 : summaryHorizon === 5 ? h5 : h10;

      let action = "Aguardar";
      if (regime === "STABLE" && confidence >= 0.6) action = "Aplicar";
      if (regime === "UNSTABLE" || confidence < 0.45) action = "Não operar";
      if (validationStatus !== "validated") action = "Diagnóstico inconclusivo";
      return {
        asset,
        group: groupLabels[rowMeta?.group || ""] || rowMeta?.group || "",
        regime: validationStatus !== "validated" ? "INCONCLUSIVE" : regime,
        confidence,
        quality: rowMeta?.quality ?? rowMeta?.metrics?.quality,
        period: first && last ? `${first.date} -> ${last.date}` : "--",
        regimeDurationDays,
        price: last?.price,
        projSelected,
        h1,
        h5,
        h10,
        action,
        validationReason,
      };
    });
  }, [selected, seriesByAsset, forecastByAsset, universe, summaryHorizon, timeframe]);

  const sectors =
    initialDomain === "finance"
      ? financeGroupFilter
      : initialDomain === "energy"
      ? [
          { value: "all", label: "Todos os grupos" },
          { value: "energy", label: "Energia" },
        ]
      : [{ value: "all", label: "Todos os grupos imobiliários" }];

  return (
    <div className="p-4 md:p-5 space-y-4 md:space-y-5">
      <div className="space-y-2">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">{title}</div>
        <h1 className="text-2xl font-semibold">Regimes por setor com projeção integrada</h1>
        <p className="text-sm text-zinc-400">Leitura estrutural do mercado com contexto operacional e forecast condicional.</p>
        {runMeta?.global_verdict_status && String(runMeta.global_verdict_status).toLowerCase() !== "pass" ? (
          <div className="rounded-lg border border-rose-500/40 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">
            Global gate FAIL: sinais não acionáveis.
          </div>
        ) : null}
        {runSummary && (runSummary?.deployment_gate as Record<string, unknown> | undefined)?.blocked === true ? (
          <div className="rounded-lg border border-amber-500/40 bg-amber-950/40 px-3 py-2 text-xs text-amber-200">
            Deployment gate BLOCKED: exibindo dados em modo diagnóstico.
          </div>
        ) : null}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {(["validated", "watch", "inconclusive"] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusTab(status)}
              className={`rounded-md border px-2 py-1 ${
                statusTab === status ? "border-cyan-400 text-cyan-300" : "border-zinc-700 text-zinc-400"
              }`}
              title={
                status === "validated"
                  ? "Sinal apto para leitura operacional"
                  : status === "watch"
                  ? "Sinal em observação por risco de mudança de regime"
                  : "Sem estrutura suficiente para ação"
              }
            >
              {status}
            </button>
          ))}
          <label className="ml-2 inline-flex items-center gap-2 text-zinc-400">
            <input
              type="checkbox"
              checked={showInconclusive}
              onChange={(e) => setShowInconclusive(e.target.checked)}
              className="h-3 w-3 accent-cyan-400"
            />
            Mostrar inconclusivos
          </label>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card
          label="Estado"
          value={metrics.state}
          helper="Estado dominante no conjunto de ativos selecionado."
          tone={metrics.state}
        />
        <Card
          label="Confiança"
          value={`${(metrics.confidence * 100).toFixed(1)}%`}
          helper="Consistência da inferência estrutural no período."
        />
        <Card
          label="Qualidade"
          value={`${(metrics.quality * 100).toFixed(1)}%`}
          helper="Saúde do sinal após filtros de ruído e validação."
        />
        <Card
          label="Alertas"
          value={String(metrics.alerts)}
          helper="Contagem de ativos em estado instável no recorte atual."
        />
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
          smoothing={smoothing}
          onSmoothingChange={setSmoothing}
        />
        <p className="text-xs text-zinc-500">
          Gráfico: eixo X = tempo, eixo Y = preço (ou índice base 100 se normalizado). Passe o mouse para ver data, regime, confiança e valor.
        </p>

        {loading ? <div className="text-sm text-zinc-500">Carregando séries...</div> : null}

        <RegimeChart
          data={seriesByAsset}
          selected={selected}
          normalize={normalize}
          showRegimeBands={showRegimeBands}
          smoothing={smoothing}
          rangePreset={rangePreset}
        />
      </div>

      {showTable ? (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4 md:gap-5">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
            <div className="flex items-center justify-between">
              <div className="text-sm uppercase tracking-widest text-zinc-400">Tabela por ativo</div>
              <div className="text-xs text-zinc-500" title="Projeções p50 para horizontes h1, h5 e h10">
                Valores em unidade de preço do ativo
              </div>
            </div>
            <div className="mt-3 overflow-auto">
              <table className="w-full text-xs">
                <thead className="text-zinc-500 uppercase">
                  <tr>
                    <th className="text-left py-2">Ativo</th>
                    <th className="text-left py-2">Setor</th>
                    <th className="text-left py-2">Período</th>
                    <th className="text-left py-2">Regime</th>
                    <th className="text-left py-2" title="Dias consecutivos no regime atual">Duração</th>
                    <th className="text-left py-2">Conf.</th>
                    <th className="text-left py-2">Qual.</th>
                    <th className="text-left py-2" title="Preço em unidade local do ativo">Preço</th>
                    <th className="text-left py-2">Proj. h{summaryHorizon}</th>
                    <th className="text-left py-2">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row) => (
                    <tr key={row.asset} className="border-t border-zinc-800/70 text-zinc-300">
                      <td className="py-2">{row.asset}</td>
                      <td className="py-2 text-zinc-400">{row.group || "-"}</td>
                      <td className="py-2 text-zinc-400">{row.period}</td>
                      <td className={`py-2 ${regimeColor[row.regime] || "text-zinc-300"}`}>{row.regime}</td>
                      <td className="py-2 text-zinc-400">{row.regimeDurationDays}d</td>
                      <td className="py-2">{(row.confidence * 100).toFixed(1)}%</td>
                      <td className="py-2">{row.quality != null ? `${(row.quality * 100).toFixed(1)}%` : "--"}</td>
                      <td className="py-2">{row.price != null ? row.price.toFixed(2) : "--"}</td>
                      <td className="py-2">{row.projSelected != null ? row.projSelected.toFixed(2) : "--"}</td>
                      <td className="py-2" title={row.validationReason || ""}>
                        {row.action}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 space-y-3">
            <div className="text-sm uppercase tracking-widest text-zinc-400">Resumo</div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-zinc-400" title="Horizonte da projeção condicional p50">
                Horizonte:
              </span>
              {[1, 5, 10].map((h) => (
                <button
                  key={h}
                  className={`rounded-md border px-2 py-1 ${
                    summaryHorizon === h ? "border-cyan-400 text-cyan-300" : "border-zinc-700 text-zinc-300"
                  }`}
                  onClick={() => setSummaryHorizon(h as 1 | 5 | 10)}
                  title={`Projeção condicional em ${h} dia(s)`}
                >
                  h{h}
                </button>
              ))}
            </div>
            <div className="text-xs text-zinc-300">Amostras no gráfico: {metrics.sampleSize}</div>
            <div className="text-xs text-zinc-300">Ativos selecionados: {selected.length}</div>
            <div className="text-xs text-zinc-300">Regime dominante: {metrics.state}</div>
            <div className="text-xs text-zinc-300">Confiança média: {(metrics.confidence * 100).toFixed(1)}%</div>
            <div className="text-xs text-zinc-500">
              h1/h5/h10: projeção condicional. Quando não houver arquivo de forecast, usa fallback conservador por regime + confiança.
            </div>
            {tableRows.slice(0, 4).map((row) => (
              <div key={row.asset} className="rounded-lg border border-zinc-800 p-2 text-xs">
                <div className="font-medium text-zinc-200">{row.asset}</div>
                <div className="text-zinc-400">{row.period}</div>
                <div className="text-zinc-300">
                  {row.regime} por ~{row.regimeDurationDays}d
                </div>
                <div className="text-zinc-400">
                  h1: {row.h1 != null ? row.h1.toFixed(2) : "--"} | h5: {row.h5 != null ? row.h5.toFixed(2) : "--"} | h10:{" "}
                  {row.h10 != null ? row.h10.toFixed(2) : "--"}
                </div>
              </div>
            ))}
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
  tone,
}: {
  label: string;
  value: string;
  helper: string;
  tone?: string;
}) {
  const color =
    tone === "STABLE"
      ? "text-emerald-300"
      : tone === "UNSTABLE"
      ? "text-rose-300"
      : tone === "TRANSITION"
      ? "text-amber-300"
      : "text-zinc-100";
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3 md:p-4" title={helper}>
      <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">{label}</div>
      <div className={`mt-1 text-lg md:text-xl font-semibold ${color}`}>{value}</div>
      <div className="mt-1 text-[11px] text-zinc-500">{helper}</div>
    </div>
  );
}
