"use client";

import { useEffect, useMemo, useState } from "react";

type AlertLevelRow = {
  sector: string;
  date: string;
  n_assets: number;
  alert_level: string;
  sector_score: number | null;
  share_unstable: number | null;
  share_transition: number | null;
  mean_confidence: number | null;
  score_delta_5d?: number | null;
  level_changes_30d?: number;
  action_recommended?: string;
  exposure_range?: string;
  action_tier?: string;
  risk_budget_min?: number | null;
  risk_budget_max?: number | null;
  hedge_min?: number | null;
  hedge_max?: number | null;
  action_priority?: number | null;
  action_reason?: string;
  confidence_band?: "alta" | "media" | "baixa";
  confidence_reason?: string;
};

type RankRow = {
  sector: string;
  drawdown_recall_l5: number | null;
  drawdown_precision_l5: number | null;
  drawdown_false_alarm_l5: number | null;
  drawdown_p_vs_random_l5: number | null;
  ret_tail_recall_l5: number | null;
  ret_tail_precision_l5: number | null;
  composite_score: number | null;
  n_assets_median_test: number | null;
};

type EligibilityRow = {
  sector: string;
  eligible: boolean;
  reason: string;
  n_days_cal: number;
  n_days_test: number;
  n_assets_median_test: number | null;
};

type Payload = {
  status: string;
  run_id: string;
  source?: string;
  generated_at: string;
  lookback_days?: number;
  counts: { verde: number; amarelo: number; vermelho: number };
  levels: AlertLevelRow[];
  ranking: RankRow[];
  eligibility: EligibilityRow[];
  timeline?: Array<{ sector: string; date: string; alert_level: string; sector_score: number | null }>;
  weekly_compare?: {
    reference_run_id: string | null;
    summary: Record<string, unknown>;
    rows: Array<{
      sector: string;
      n_assets: number;
      level_now: string;
      level_prev_week: string | null;
      score_now: number | null;
      score_prev_week: number | null;
      delta_score_week: number | null;
      trend: string;
      changed: boolean;
    }>;
  };
  notification?: {
    run_id: string;
    n_exited_green: number;
    exited_green: string[];
  };
  drift?: {
    level: string;
    score: number | null;
    reasons: string[];
  };
  summary_simple?: {
    short_state: string;
    top_warning_sectors: string[];
  };
  data_quality?: {
    sectors_total: number;
    sectors_eligible: number;
    sectors_ineligible: number;
    assets_in_eligible_sectors: number;
    assets_in_ineligible_sectors: number;
    most_common_ineligible_reason: string;
  };
  limits?: {
    what_it_does: string;
    what_it_does_not: string;
    methodological_limits: string[];
  };
};

function pct(v: number | null | undefined, d = 1) {
  if (v == null || !Number.isFinite(v)) return "--";
  return `${(v * 100).toFixed(d)}%`;
}

function num(v: number | null | undefined, d = 3) {
  if (v == null || !Number.isFinite(v)) return "--";
  return v.toFixed(d);
}

function pctRange(minV: number | null | undefined, maxV: number | null | undefined, d = 0) {
  if (minV == null || maxV == null || !Number.isFinite(minV) || !Number.isFinite(maxV)) return "--";
  return `${(minV * 100).toFixed(d)}% a ${(maxV * 100).toFixed(d)}%`;
}

function levelBadge(level: string) {
  const key = String(level || "").toLowerCase();
  if (key === "vermelho") return "bg-rose-950/40 border-rose-700/50 text-rose-200";
  if (key === "amarelo") return "bg-amber-950/40 border-amber-700/50 text-amber-200";
  return "bg-emerald-950/40 border-emerald-700/50 text-emerald-200";
}

function trendTone(trend: string) {
  if (trend === "piorou") return "text-rose-300";
  if (trend === "melhorou") return "text-emerald-300";
  return "text-zinc-300";
}

function confidenceTone(band: string | undefined) {
  if (band === "alta") return "text-emerald-300";
  if (band === "media") return "text-amber-300";
  return "text-rose-300";
}

export default function SectorAlertsDashboard() {
  const [data, setData] = useState<Payload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [emptyNotice, setEmptyNotice] = useState<string | null>(null);
  const [selectedSector, setSelectedSector] = useState<string>("");
  const [lookbackDays, setLookbackDays] = useState<number>(90);
  const [levelFilter, setLevelFilter] = useState<string>("all");
  const [sectorSearch, setSectorSearch] = useState<string>("");
  const [minAssets, setMinAssets] = useState<number>(0);

  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      try {
        setLoading(true);
        setEmptyNotice(null);
        const params = new URLSearchParams({
          days: String(lookbackDays),
          level: String(levelFilter),
          sector: String(sectorSearch),
          min_assets: String(minAssets),
        });
        const res = await fetch(`/api/sectors/alerts?${params.toString()}`, {
          signal: controller.signal,
          cache: "no-store",
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as { error?: string; message?: string };
          if (res.status === 404 && body.error === "no_sector_run") {
            setData(null);
            setError(null);
            setEmptyNotice("Painel setorial aguardando a primeira publicação de snapshot.");
            return;
          }
          throw new Error(
            `Erro ao consultar setores (${res.status}). ${body.message || body.error || "Snapshot setorial indisponível."}`
          );
        }
        const payload = (await res.json()) as Payload;
        if (!payload.levels?.length && !payload.ranking?.length) {
          setData(payload);
          setError(null);
          setEmptyNotice("Snapshot setorial recebido, mas ainda sem linhas elegíveis para exibição.");
          return;
        }
        setData(payload);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "erro");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    void run();
    return () => controller.abort();
  }, [lookbackDays, levelFilter, sectorSearch, minAssets]);

  const levelsSorted = useMemo(() => {
    if (!data?.levels) return [];
    const order: Record<string, number> = { vermelho: 0, amarelo: 1, verde: 2 };
    return [...data.levels].sort((a, b) => {
      const oa = order[String(a.alert_level || "").toLowerCase()] ?? 9;
      const ob = order[String(b.alert_level || "").toLowerCase()] ?? 9;
      if (oa !== ob) return oa - ob;
      return (b.sector_score || 0) - (a.sector_score || 0);
    });
  }, [data?.levels]);

  const topRanking = useMemo(() => {
    if (!data?.ranking) return [];
    return [...data.ranking]
      .filter((x) => (x.n_assets_median_test || 0) >= 10)
      .sort((a, b) => (b.drawdown_recall_l5 || 0) - (a.drawdown_recall_l5 || 0))
      .slice(0, 8);
  }, [data?.ranking]);

  const eligibleCount = useMemo(() => (data?.eligibility || []).filter((x) => x.eligible).length, [data?.eligibility]);

  useEffect(() => {
    if (!levelsSorted.length) return;
    if (selectedSector && levelsSorted.some((x) => x.sector === selectedSector)) return;
    setSelectedSector(levelsSorted[0].sector);
  }, [levelsSorted, selectedSector]);

  const selectedLevel = useMemo(
    () => levelsSorted.find((x) => x.sector === selectedSector) || null,
    [levelsSorted, selectedSector]
  );

  const selectedTimeline = useMemo(() => {
    if (!data?.timeline || !selectedSector) return [];
    return [...data.timeline]
      .filter((x) => x.sector === selectedSector)
      .sort((a, b) => b.date.localeCompare(a.date))
      .slice(0, 20);
  }, [data?.timeline, selectedSector]);

  const selectedTimeline90 = useMemo(() => {
    if (!data?.timeline || !selectedSector) return [];
    return [...data.timeline]
      .filter((x) => x.sector === selectedSector)
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-90);
  }, [data?.timeline, selectedSector]);

  const selectedChanges = useMemo(() => {
    const arr = selectedTimeline90;
    const out: Array<{ date: string; from: string; to: string }> = [];
    for (let i = 1; i < arr.length; i += 1) {
      if (arr[i].alert_level !== arr[i - 1].alert_level) {
        out.push({ date: arr[i].date, from: arr[i - 1].alert_level, to: arr[i].alert_level });
      }
    }
    return out.slice(-10).reverse();
  }, [selectedTimeline90]);

  const weeklyRows = useMemo(() => {
    return [...(data?.weekly_compare?.rows || [])].sort((a, b) => (b.delta_score_week || 0) - (a.delta_score_week || 0));
  }, [data?.weekly_compare?.rows]);

  if (loading) {
    return <div className="p-6 text-sm text-zinc-400">Carregando painel setorial...</div>;
  }

  if (emptyNotice) {
    return (
      <div className="p-6 space-y-2">
        <div className="text-sm text-zinc-200">{emptyNotice}</div>
        <div className="text-xs text-zinc-400">
          Próximo passo: execute a rotina diária para publicar o snapshot em `public/data/sectors/latest`.
        </div>
      </div>
    );
  }

  if (error || !data) {
    const lower = String(error || "").toLowerCase();
    const authIssue = lower.includes("unauthorized") || lower.includes("401");
    const noDataIssue = lower.includes("404") || lower.includes("no_sector_run");
    return (
      <div className="p-6 space-y-3">
        <div className="text-sm text-rose-300">
          Erro no painel setorial:{" "}
          {authIssue
            ? "acesso negado. libere leitura pública ou configure chave no frontend."
            : noDataIssue
            ? "snapshot setorial ainda não publicado."
            : error || "não foi possível consultar os dados agora."}
        </div>
        <div className="text-xs text-zinc-400">
          Ação sugerida: confira `results/event_study_sectors` ou o snapshot em `public/data/sectors/latest`.
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-5">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Setores</div>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-100">Radar setorial de risco</h1>
        <div className="mt-2 text-sm text-zinc-300 leading-relaxed">
          {data.summary_simple?.short_state || "Níveis por setor (verde, amarelo, vermelho) + ranking de antecipação de estresse."}
        </div>
        <div className="mt-2 text-xs text-zinc-500">
          execução: {data.run_id} | fonte: {data.source || "results"} | setores elegíveis: {eligibleCount}/{data.eligibility.length}
        </div>
        {!!data.summary_simple?.top_warning_sectors?.length && (
          <div className="mt-2 text-xs text-zinc-400">
            setores em atenção: {data.summary_simple.top_warning_sectors.join(", ")}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
        <div className="text-sm uppercase tracking-widest text-zinc-400">Piloto comercial (30 dias)</div>
        <div className="mt-2 text-sm text-zinc-300">
          Entrega diária por setor, resumo semanal e critério objetivo para avaliar continuidade do monitor mensal.
        </div>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="rounded-xl border border-zinc-800 bg-black/30 p-3">
            <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Passo 1</div>
            <div className="mt-1 text-sm text-zinc-200">Alinhar leitura estrutural por nível: verde, amarelo, vermelho.</div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-black/30 p-3">
            <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Passo 2</div>
            <div className="mt-1 text-sm text-zinc-200">Rodar o motor todo dia com alerta de mudança de nível.</div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-black/30 p-3">
            <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Passo 3</div>
            <div className="mt-1 text-sm text-zinc-200">Fechar com interpretação estatística: estável, transição ou instável.</div>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <a
            className="rounded-md border border-zinc-700 px-2 py-1 text-zinc-200 hover:border-zinc-500 hover:text-white"
            href="https://github.com/pemodest0/Assyntrax/blob/main/docs/OFERTA_COMERCIAL_MOTOR.md"
            target="_blank"
            rel="noreferrer"
          >
            Oferta comercial
          </a>
          <a
            className="rounded-md border border-zinc-700 px-2 py-1 text-zinc-200 hover:border-zinc-500 hover:text-white"
            href="https://github.com/pemodest0/Assyntrax/blob/main/docs/PILOTO_30D_PLAYBOOK.md"
            target="_blank"
            rel="noreferrer"
          >
            Playbook 30 dias
          </a>
          <a
            className="rounded-md border border-zinc-700 px-2 py-1 text-zinc-200 hover:border-zinc-500 hover:text-white"
            href="https://github.com/pemodest0/Assyntrax/blob/main/docs/PACOTE_VENDA_CHECKLIST.md"
            target="_blank"
            rel="noreferrer"
          >
            Checklist de venda
          </a>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <CountCard label="Vermelho" value={data.counts.vermelho} tone="vermelho" />
        <CountCard label="Amarelo" value={data.counts.amarelo} tone="amarelo" />
        <CountCard label="Verde" value={data.counts.verde} tone="verde" />
      </section>

      {data.notification && data.notification.n_exited_green > 0 ? (
        <section className="rounded-2xl border border-rose-700/40 bg-rose-950/20 p-4 md:p-5">
          <div className="text-sm font-semibold text-rose-200">Alerta automatico: setor saiu de verde</div>
          <div className="mt-2 text-xs text-rose-100/90">
            {data.notification.exited_green.join(", ")}
          </div>
        </section>
      ) : null}

      {data.drift ? (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
          <div className="text-sm uppercase tracking-widest text-zinc-400">Drift do motor</div>
          <div className="mt-2 text-sm text-zinc-200">
            nível: <span className={data.drift.level === "block" ? "text-rose-300" : data.drift.level === "watch" ? "text-amber-300" : "text-emerald-300"}>{data.drift.level}</span> | score: {num(data.drift.score, 2)}
          </div>
          {data.drift.reasons?.length ? (
            <div className="mt-2 text-xs text-zinc-300">{data.drift.reasons.join(" | ")}</div>
          ) : (
            <div className="mt-2 text-xs text-zinc-500">Sem desvios fortes no momento.</div>
          )}
        </section>
      ) : null}

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <div className="text-xs text-zinc-400">Janela de histórico:</div>
          {[30, 60, 90, 120].map((d) => (
            <button
              key={d}
              onClick={() => setLookbackDays(d)}
              aria-label={`Selecionar janela de ${d} dias`}
              className={`rounded-md border px-2 py-1 text-xs ${
                lookbackDays === d ? "border-cyan-400 text-cyan-300" : "border-zinc-700 text-zinc-300"
              }`}
            >
              {d}d
            </button>
          ))}
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            aria-label="Filtrar nível de alerta"
            className="ml-2 rounded-md border border-zinc-700 bg-black/30 px-2 py-1 text-xs text-zinc-200"
          >
            <option value="all">todos níveis</option>
            <option value="vermelho">vermelho</option>
            <option value="amarelo">amarelo</option>
            <option value="verde">verde</option>
          </select>
          <input
            value={sectorSearch}
            onChange={(e) => setSectorSearch(e.target.value)}
            placeholder="filtrar setor"
            aria-label="Filtrar por setor"
            className="rounded-md border border-zinc-700 bg-black/30 px-2 py-1 text-xs text-zinc-200"
          />
          <input
            value={minAssets}
            onChange={(e) => setMinAssets(Number(e.target.value) || 0)}
            type="number"
            min={0}
            step={1}
            placeholder="min ativos"
            aria-label="Mínimo de ativos por setor"
            className="w-24 rounded-md border border-zinc-700 bg-black/30 px-2 py-1 text-xs text-zinc-200"
          />
        </div>
        <div className="text-sm uppercase tracking-widest text-zinc-400">Níveis atuais por setor</div>
        <div className="mt-3 overflow-auto">
          <table className="w-full text-xs">
            <thead className="text-zinc-500 uppercase">
              <tr>
                <th className="text-left py-2">Setor</th>
                <th className="text-left py-2">Nível</th>
                <th className="text-left py-2">Score</th>
                <th className="text-left py-2">Instável</th>
                <th className="text-left py-2">Transição</th>
                <th className="text-left py-2">Confiança</th>
                <th className="text-left py-2">Faixa</th>
                <th className="text-left py-2">Delta 5d</th>
                <th className="text-left py-2">Mudanças 30d</th>
                <th className="text-left py-2">Ativos</th>
              </tr>
            </thead>
            <tbody>
              {levelsSorted.map((row) => (
                <tr key={row.sector} className="border-t border-zinc-800/70 text-zinc-300">
                  <td className="py-2">{row.sector}</td>
                  <td className="py-2">
                    <span className={`rounded-md border px-2 py-1 ${levelBadge(row.alert_level)}`}>{row.alert_level}</span>
                  </td>
                  <td className="py-2">{num(row.sector_score, 3)}</td>
                  <td className="py-2">{pct(row.share_unstable, 1)}</td>
                  <td className="py-2">{pct(row.share_transition, 1)}</td>
                  <td className="py-2">{num(row.mean_confidence, 3)}</td>
                  <td className={`py-2 ${confidenceTone(row.confidence_band)}`}>{row.confidence_band || "--"}</td>
                  <td className="py-2">{num(row.score_delta_5d, 3)}</td>
                  <td className="py-2">{row.level_changes_30d ?? 0}</td>
                  <td className="py-2">{row.n_assets}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!levelsSorted.length ? (
            <div className="mt-3 rounded-lg border border-zinc-800 bg-black/30 p-3 text-xs text-zinc-400">
              Nenhum setor encontrado com esse filtro. Ajuste nível, nome do setor ou mínimo de ativos.
            </div>
          ) : null}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
        <div className="text-sm uppercase tracking-widest text-zinc-400">Ranking de antecipação (5 dias)</div>
        <div className="mt-3 overflow-auto">
          <table className="w-full text-xs">
            <thead className="text-zinc-500 uppercase">
              <tr>
                <th className="text-left py-2">Setor</th>
                <th className="text-left py-2">Acerto</th>
                <th className="text-left py-2">Precisao</th>
                <th className="text-left py-2">Falso alerta/ano</th>
                <th className="text-left py-2">p vs aleatorio</th>
              </tr>
            </thead>
            <tbody>
              {topRanking.map((row) => (
                <tr key={row.sector} className="border-t border-zinc-800/70 text-zinc-300">
                  <td className="py-2">{row.sector}</td>
                  <td className="py-2">{pct(row.drawdown_recall_l5, 1)}</td>
                  <td className="py-2">{pct(row.drawdown_precision_l5, 1)}</td>
                  <td className="py-2">{num(row.drawdown_false_alarm_l5, 1)}</td>
                  <td className="py-2">{num(row.drawdown_p_vs_random_l5, 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 space-y-3">
          <div className="text-sm uppercase tracking-widest text-zinc-400">Setor selecionado</div>
          <select
            value={selectedSector}
            onChange={(e) => setSelectedSector(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm"
          >
            {levelsSorted.map((row) => (
              <option key={row.sector} value={row.sector}>
                {row.sector}
              </option>
            ))}
          </select>

          {selectedLevel ? (
            <div className="rounded-xl border border-zinc-800 bg-black/30 p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-zinc-300 text-sm">{selectedLevel.sector}</div>
                <span className={`rounded-md border px-2 py-1 text-xs ${levelBadge(selectedLevel.alert_level)}`}>
                  {selectedLevel.alert_level}
                </span>
              </div>
              <div className="text-xs text-zinc-400">Score: {num(selectedLevel.sector_score, 3)}</div>
              <div className="text-xs text-zinc-400">Delta 5d: {num(selectedLevel.score_delta_5d, 3)}</div>
              <div className="text-xs text-zinc-400">Mudanças 30d: {selectedLevel.level_changes_30d ?? 0}</div>
              <div className={`text-xs ${confidenceTone(selectedLevel.confidence_band)}`}>
                Confiança: {selectedLevel.confidence_band || "--"}
              </div>
              <div className="text-xs text-zinc-300">{selectedLevel.confidence_reason || "--"}</div>
              <div className="text-xs text-zinc-500">Por que alerta hoje:</div>
              <div className="text-xs text-zinc-200">{selectedLevel.action_recommended || selectedLevel.action_reason || "--"}</div>
              <div className="text-xs text-zinc-300">Faixa de referência: {selectedLevel.exposure_range || pctRange(selectedLevel.risk_budget_min, selectedLevel.risk_budget_max)}</div>
              <div className="text-xs text-zinc-300">Faixa de proteção de referência: {pctRange(selectedLevel.hedge_min, selectedLevel.hedge_max)}</div>
              <div className="text-xs text-zinc-400">Prioridade: {num(selectedLevel.action_priority, 2)}</div>
            </div>
          ) : null}

          <div className="rounded-xl border border-zinc-800 bg-black/30 p-3 space-y-2">
            <div className="text-xs uppercase tracking-[0.16em] text-zinc-400">Mudanças de nível (90d)</div>
            {selectedChanges.length ? (
              <div className="space-y-1 text-xs">
                {selectedChanges.map((x, idx) => (
                  <div key={`${x.date}-${idx}`} className="text-zinc-300">
                    {x.date}: {x.from} para {x.to}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-zinc-500">Sem mudanças recentes.</div>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
          <div className="text-sm uppercase tracking-widest text-zinc-400">Timeline do setor (90 dias)</div>
          <div className="mt-3 flex flex-wrap gap-1">
            {selectedTimeline90.map((row) => (
              <div
                key={`${row.date}-${row.sector}`}
                title={`${row.date} | ${row.alert_level} | score=${num(row.sector_score, 3)}`}
                className={`h-3 w-2 rounded-sm ${
                  row.alert_level === "vermelho"
                    ? "bg-rose-500/80"
                    : row.alert_level === "amarelo"
                    ? "bg-amber-400/80"
                    : "bg-emerald-400/80"
                }`}
              />
            ))}
          </div>
          <div className="mt-3 overflow-auto">
            <table className="w-full text-xs">
              <thead className="text-zinc-500 uppercase">
                <tr>
                  <th className="text-left py-2">Data</th>
                  <th className="text-left py-2">Nível</th>
                  <th className="text-left py-2">Score</th>
                </tr>
              </thead>
              <tbody>
                {selectedTimeline.map((row) => (
                  <tr key={`${row.sector}-${row.date}`} className="border-t border-zinc-800/70 text-zinc-300">
                    <td className="py-2">{row.date}</td>
                    <td className="py-2">
                      <span className={`rounded-md border px-2 py-1 ${levelBadge(row.alert_level)}`}>{row.alert_level}</span>
                    </td>
                    <td className="py-2">{num(row.sector_score, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
        <div className="text-sm uppercase tracking-widest text-zinc-400">Comparação semanal (site)</div>
        <div className="mt-1 text-xs text-zinc-500">
          referência: {data.weekly_compare?.reference_run_id || "--"}
        </div>
        <div className="mt-1 text-xs text-zinc-400">
          pioraram: {String(data.weekly_compare?.summary?.changed_up ?? 0)} | melhoraram:{" "}
          {String(data.weekly_compare?.summary?.changed_down ?? 0)} | sem mudança:{" "}
          {String(data.weekly_compare?.summary?.unchanged ?? 0)}
        </div>
        <div className="mt-3 overflow-auto">
          <table className="w-full text-xs">
            <thead className="text-zinc-500 uppercase">
              <tr>
                <th className="text-left py-2">Setor</th>
                <th className="text-left py-2">Nível hoje</th>
                <th className="text-left py-2">Nível semana passada</th>
                <th className="text-left py-2">Delta score</th>
                <th className="text-left py-2">Tendência</th>
              </tr>
            </thead>
            <tbody>
              {weeklyRows.map((row) => (
                <tr key={`wk-${row.sector}`} className="border-t border-zinc-800/70 text-zinc-300">
                  <td className="py-2">{row.sector}</td>
                  <td className="py-2">
                    <span className={`rounded-md border px-2 py-1 ${levelBadge(row.level_now)}`}>{row.level_now}</span>
                  </td>
                  <td className="py-2">{row.level_prev_week || "--"}</td>
                  <td className="py-2">{num(row.delta_score_week, 3)}</td>
                  <td className={`py-2 ${trendTone(row.trend)}`}>{row.trend}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
          <div className="text-sm uppercase tracking-widest text-zinc-400">Qualidade dos dados</div>
          <div className="mt-2 text-xs text-zinc-300">
            setores elegiveis: {data.data_quality?.sectors_eligible ?? "--"}/{data.data_quality?.sectors_total ?? "--"}
          </div>
          <div className="mt-1 text-xs text-zinc-300">
            ativos em setores elegiveis: {data.data_quality?.assets_in_eligible_sectors ?? "--"}
          </div>
          <div className="mt-1 text-xs text-zinc-300">
            ativos fora de elegibilidade: {data.data_quality?.assets_in_ineligible_sectors ?? "--"}
          </div>
          <div className="mt-1 text-xs text-zinc-500">
            motivo mais comum de inelegibilidade: {data.data_quality?.most_common_ineligible_reason || "none"}
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
          <div className="text-sm uppercase tracking-widest text-zinc-400">Limites do motor</div>
          <div className="mt-2 text-xs text-zinc-300">faz: {data.limits?.what_it_does || "--"}</div>
          <div className="mt-1 text-xs text-zinc-300">nao faz: {data.limits?.what_it_does_not || "--"}</div>
          <div className="mt-2 space-y-1 text-xs text-zinc-500">
            {(data.limits?.methodological_limits || []).map((x) => (
              <div key={x}>- {x}</div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function CountCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "verde" | "amarelo" | "vermelho";
}) {
  const toneCls =
    tone === "vermelho"
      ? "border-rose-700/50 bg-rose-950/30 text-rose-200"
      : tone === "amarelo"
      ? "border-amber-700/50 bg-amber-950/30 text-amber-200"
      : "border-emerald-700/50 bg-emerald-950/30 text-emerald-200";
  return (
    <div className={`rounded-xl border p-4 ${toneCls}`}>
      <div className="text-xs uppercase tracking-[0.16em] opacity-90">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}
