"use client";

import { useEffect, useMemo, useState } from "react";
import DashboardFilters from "@/components/DashboardFilters";
import RegimeChart from "@/components/RegimeChart";

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
  validation?: { status?: string; reasons?: string[] };
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
  bonds_rates: "Juros/Bonds",
  fx: "Moedas",
  equities_us_broad: "Equities US Broad",
  equities_us_sectors: "Equities US Setores",
  equities_international: "Equities Internacionais",
  realestate: "Imobiliário",
};

function cleanRegime(label?: string) {
  if (!label) return "TRANSITION";
  if (label === "NOISY") return "UNSTABLE";
  if (label === "STABLE" || label === "TRANSITION" || label === "UNSTABLE" || label === "INCONCLUSIVE") return label;
  return "TRANSITION";
}

function mean(nums: number[]) {
  if (!nums.length) return 0;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

export default function SectorDashboard({
  title,
  showTable = true,
  initialDomain = "finance",
}: {
  title: string;
  showTable?: boolean;
  initialDomain?: "finance" | "energy" | "realestate";
}) {
  const [timeframe, setTimeframe] = useState("daily");
  const [sector, setSector] = useState(initialDomain);
  const [statusTab, setStatusTab] = useState<"validated" | "watch" | "inconclusive">("validated");
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
  const [riskTruthCounts, setRiskTruthCounts] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    const loadUniverse = async () => {
      const statuses = statusTab === "inconclusive" ? "inconclusive" : "validated,watch";
      const includeInconclusive = showInconclusive || statusTab === "inconclusive" ? 1 : 0;
      const [runRes, riskRes, assetsRes] = await Promise.all([
        fetch("/api/run/latest"),
        fetch("/api/risk-truth"),
        fetch(
          `/api/assets?domain=${encodeURIComponent(sector)}&status=${encodeURIComponent(
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

      if (riskRes.ok) {
        const riskJson = await riskRes.json();
        setRiskTruthCounts((riskJson?.counts as Record<string, number>) || null);
      } else {
        setRiskTruthCounts(null);
      }

      const assetsJson = await assetsRes.json();
      const data = assetsJson?.records;
      if (!Array.isArray(data)) {
        setUniverse([]);
        setSelected([]);
        return;
      }
      setUniverse(data);
      setSelected((prev) => {
        const approved = data.filter((u: UniverseAsset) => (u.risk_truth_status || "validated") === "validated");
        const preferred = approved.length ? approved : data;
        const valid = prev.filter((a) => preferred.find((u: UniverseAsset) => u.asset === a));
        return valid.length ? valid : preferred.slice(0, 4).map((u: UniverseAsset) => u.asset);
      });
    };
    loadUniverse();
  }, [timeframe, sector, statusTab, showInconclusive]);

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
            try {
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
            } catch {
              forecasts[asset] = { 1: null, 5: null, 10: null };
            }
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
    const activeSeries = selected.flatMap((a) => seriesByAsset[a] || []);
    const lastPoints = selected.map((a) => (seriesByAsset[a] || [])[Math.max(0, (seriesByAsset[a] || []).length - 1)]).filter(Boolean) as SeriesPoint[];
    const avgConf = mean(lastPoints.map((p) => p.confidence || 0));
    const unstableCount = lastPoints.filter((p) => cleanRegime(p.regime) === "UNSTABLE").length;
    const dominantRegime = (() => {
      const counts: Record<string, number> = {};
      lastPoints.forEach((p) => {
        const r = cleanRegime(p.regime);
        counts[r] = (counts[r] || 0) + 1;
      });
      return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || "TRANSITION";
    })();
    return {
      state: dominantRegime,
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
      const conf = last?.confidence ?? 0;
      const regime = cleanRegime(last?.regime);
      const rowMeta = universe.find((u) => u.asset === asset);
      const vStatus = rowMeta?.risk_truth_status || rowMeta?.signal_status || "validated";
      const vReason = rowMeta?.reason || "";
      const ret = forecastByAsset[asset]?.[summaryHorizon]?.y_pred;
      const lastRegimeIdx = series.length - 1;
      let streak = 0;
      for (let i = lastRegimeIdx; i >= 0; i -= 1) {
        if (cleanRegime(series[i]?.regime) === regime) streak += 1;
        else break;
      }
      const regimeDurationDays = timeframe === "weekly" ? streak * 7 : streak;
      let action = "Aguardar";
      if (regime === "STABLE" && conf >= 0.6) action = "Aplicar";
      if (regime === "UNSTABLE" || conf < 0.45) action = "Nao operar";
      if (vStatus !== "validated") action = "Diagnóstico inconclusivo";
      return {
        asset,
        group: groupLabels[rowMeta?.group || ""] || rowMeta?.group || "",
        regime: vStatus !== "validated" ? "INCONCLUSIVE" : regime,
        confidence: conf,
        quality: rowMeta?.quality ?? rowMeta?.metrics?.quality,
        period: first && last ? `${first.date} -> ${last.date}` : "--",
        regimeDurationDays,
        price: last?.price,
        forecast: ret,
        action,
        validationStatus: vStatus,
        validationReason: vReason,
      };
    });
  }, [selected, seriesByAsset, forecastByAsset, universe, summaryHorizon, timeframe]);

  return (
    <div className="p-4 md:p-5 space-y-4 md:space-y-5">
      <div className="space-y-2">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">{title}</div>
        <h1 className="text-2xl font-semibold">Regimes por setor com projeção integrada</h1>
        <p className="text-sm text-zinc-400">Leitura estrutural do mercado com confiança e forecast condicional.</p>
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
        <div className="flex flex-wrap gap-2 text-xs text-zinc-400">
          <span>Run: {runMeta?.run_id || "--"}</span>
          <span>Validados: {riskTruthCounts?.validated ?? "--"}</span>
          <span>Watch: {riskTruthCounts?.watch ?? "--"}</span>
          <span>Inconclusivos: {riskTruthCounts?.inconclusive ?? "--"}</span>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {(["validated", "watch", "inconclusive"] as const).map((k) => (
            <button
              key={k}
              onClick={() => setStatusTab(k)}
              className={`rounded-md border px-2 py-1 ${
                statusTab === k ? "border-cyan-400 text-cyan-300" : "border-zinc-700 text-zinc-400"
              }`}
            >
              {k}
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
        <Card label="Estado" value={metrics.state} tone={metrics.state} />
        <Card label="Confiança" value={`${(metrics.confidence * 100).toFixed(1)}%`} />
        <Card label="Qualidade" value={`${(metrics.quality * 100).toFixed(1)}%`} />
        <Card label="Alertas" value={String(metrics.alerts)} />
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 space-y-4">
        <DashboardFilters
          assets={universe}
          selected={selected}
          onSelectedChange={setSelected}
          sector={sector}
          onSectorChange={(value: string) => setSector(value as "finance" | "energy" | "realestate")}
          sectors={[
            { value: "finance", label: "Finance / Trading" },
            { value: "energy", label: "Macro / Operacoes" },
            { value: "realestate", label: "Imobiliário" },
          ]}
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

        {loading ? <div className="text-sm text-zinc-500">Carregando series...</div> : null}

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
            <div className="text-sm uppercase tracking-widest text-zinc-400">Tabela por ativo</div>
            <div className="mt-3 overflow-auto">
              <table className="w-full text-xs">
                <thead className="text-zinc-500 uppercase">
                  <tr>
                    <th className="text-left py-2">Ativo</th>
                    <th className="text-left py-2">Setor</th>
                    <th className="text-left py-2">Periodo</th>
                    <th className="text-left py-2">Regime</th>
                    <th className="text-left py-2">Duração</th>
                    <th className="text-left py-2">Conf.</th>
                    <th className="text-left py-2">Qual.</th>
                    <th className="text-left py-2">Preco</th>
                    <th className="text-left py-2">Proj. h{summaryHorizon}</th>
                    <th className="text-left py-2">Acao</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((r) => (
                    <tr key={r.asset} className="border-t border-zinc-800/70 text-zinc-300">
                      <td className="py-2">{r.asset}</td>
                      <td className="py-2 text-zinc-400">{r.group || "-"}</td>
                      <td className="py-2 text-zinc-400">{r.period}</td>
                      <td className={`py-2 ${regimeColor[r.regime] || "text-zinc-300"}`}>{r.regime}</td>
                      <td className="py-2 text-zinc-400">{r.regimeDurationDays}d</td>
                      <td className="py-2">{(r.confidence * 100).toFixed(1)}%</td>
                      <td className="py-2">{r.quality != null ? `${(r.quality * 100).toFixed(1)}%` : "--"}</td>
                      <td className="py-2">{r.price != null ? r.price.toFixed(2) : "--"}</td>
                      <td className="py-2">{r.forecast != null ? `${(r.forecast * 100).toFixed(2)}%` : "--"}</td>
                      <td className="py-2" title={r.validationReason || ""}>{r.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 space-y-3">
            <div className="text-sm uppercase tracking-widest text-zinc-400">Resumo</div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-zinc-400">Horizonte:</span>
              {[1, 5, 10].map((h) => (
                <button
                  key={h}
                  className={`rounded-md border px-2 py-1 ${summaryHorizon === h ? "border-cyan-400 text-cyan-300" : "border-zinc-700 text-zinc-300"}`}
                  onClick={() => setSummaryHorizon(h as 1 | 5 | 10)}
                >
                  h{h}
                </button>
              ))}
            </div>
            <div className="text-xs text-zinc-300">Amostras no chart: {metrics.sampleSize}</div>
            <div className="text-xs text-zinc-300">Ativos selecionados: {selected.length}</div>
            <div className="text-xs text-zinc-300">Regime dominante: {metrics.state}</div>
            <div className="text-xs text-zinc-300">Confiança média: {(metrics.confidence * 100).toFixed(1)}%</div>
            {tableRows.slice(0, 3).map((r) => (
              <div key={r.asset} className="rounded-lg border border-zinc-800 p-2 text-xs">
                <div className="font-medium text-zinc-200">{r.asset}</div>
                <div className="text-zinc-400">{r.period}</div>
                <div className="text-zinc-300">
                  {r.regime} por ~{r.regimeDurationDays}d • h{summaryHorizon}: {r.forecast != null ? `${(r.forecast * 100).toFixed(2)}%` : "--"}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Card({ label, value, tone }: { label: string; value: string; tone?: string }) {
  const color = tone === "STABLE" ? "text-emerald-300" : tone === "UNSTABLE" ? "text-rose-300" : tone === "TRANSITION" ? "text-amber-300" : "text-zinc-100";
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3 md:p-4">
      <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">{label}</div>
      <div className={`mt-1 text-lg md:text-xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}
