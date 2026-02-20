import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { resultsRoot } from "@/lib/server/results";

const CONTRACT_VERSION = "sector_alerts_v2";

type CsvRow = Record<string, string>;

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

type TimelineRow = {
  sector: string;
  date: string;
  alert_level: string;
  sector_score: number | null;
};

type WeeklyCompareRow = {
  sector: string;
  n_assets: number;
  level_now: string;
  level_prev_week: string | null;
  score_now: number | null;
  score_prev_week: number | null;
  delta_score_week: number | null;
  trend: string;
  changed: boolean;
};

type DriftPayload = {
  drift_level?: string;
  drift_score?: number | null;
  reasons?: string[];
};

function toNum(value: string | undefined): number | null {
  if (typeof value !== "string") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function actionByLevel(level: string) {
  const key = String(level || "").toLowerCase();
  if (key === "vermelho") {
    return "Cautela alta: reduzir exposicao, reforcar protecao e evitar novas posicoes agressivas.";
  }
  if (key === "amarelo") {
    return "Atencao: reduzir risco tatico e apertar limites de perda.";
  }
  return "Operacao normal: manter exposicao base e monitorar.";
}

function exposureRangeByLevel(level: string) {
  const key = String(level || "").toLowerCase();
  if (key === "vermelho") return "reduzir 40% a 70% do risco";
  if (key === "amarelo") return "reduzir 15% a 35% do risco";
  return "manter risco base (0% a 10% de ajuste)";
}

function pctRange(minV: number | null | undefined, maxV: number | null | undefined, digits = 0) {
  if (minV == null || maxV == null || !Number.isFinite(minV) || !Number.isFinite(maxV)) return "";
  return `${(minV * 100).toFixed(digits)}% a ${(maxV * 100).toFixed(digits)}%`;
}

function confidenceBand(v: number | null | undefined): "alta" | "media" | "baixa" {
  if (v == null || !Number.isFinite(v)) return "baixa";
  if (v >= 0.62) return "alta";
  if (v >= 0.46) return "media";
  return "baixa";
}

function confidenceReason(
  row: AlertLevelRow,
  trend: { score_delta_5d: number | null; level_changes_30d: number } | undefined
) {
  const band = confidenceBand(row.mean_confidence);
  const changes = trend?.level_changes_30d ?? 0;
  const unstable = row.share_unstable ?? 0;
  const transition = row.share_transition ?? 0;

  if (changes >= 7) {
    return "troca de nivel muito frequente nas ultimas semanas";
  }
  if (band === "baixa") {
    return "confianca media baixa no conjunto de ativos do setor";
  }
  if (unstable >= 0.35 || transition >= 0.50) {
    return "muitos ativos em mudanca de regime, sinal mais fragil";
  }
  if (band === "alta" && changes <= 2) {
    return "sinal consistente e com poucas viradas recentes";
  }
  return "sinal razoavel, mas precisa monitorar a persistencia";
}

function parseCsvLine(line: string): string[] {
  const out: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === "\"") {
      if (inQuotes && line[i + 1] === "\"") {
        current += "\"";
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (ch === "," && !inQuotes) {
      out.push(current);
      current = "";
      continue;
    }
    current += ch;
  }
  out.push(current);
  return out;
}

function parseCsv(text: string): CsvRow[] {
  const lines = text
    .replace(/^\uFEFF/, "")
    .split("\n")
    .map((x) => x.trim())
    .filter(Boolean);
  if (!lines.length) return [];
  const header = parseCsvLine(lines[0]).map((h) => h.trim());
  const rows: CsvRow[] = [];
  for (const line of lines.slice(1)) {
    const parts = parseCsvLine(line);
    const row: CsvRow = {};
    header.forEach((h, idx) => {
      row[h] = (parts[idx] || "").trim();
    });
    rows.push(row);
  }
  return rows;
}

function isAuthorized(request: Request) {
  const raw = process.env.ASSYNTRAX_API_KEYS || "";
  const keys = raw
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
  if (!keys.length) return true;
  const fromHeader = request.headers.get("x-assyntrax-key") || "";
  const { searchParams } = new URL(request.url);
  const fromQuery = searchParams.get("key") || "";
  const provided = (fromHeader || fromQuery).trim();
  return keys.includes(provided);
}

async function findLatestSectorRun() {
  const root = resultsRoot();
  const base = path.join(root, "event_study_sectors");
  const entries = await fs.readdir(base, { withFileTypes: true });
  const dirs = entries
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
    .sort()
    .reverse();

  for (const runId of dirs) {
    const runDir = path.join(base, runId);
    const levelsPath = path.join(runDir, "sector_alert_levels_latest.csv");
    const rankPath = path.join(runDir, "sector_rank_l5.csv");
    try {
      await Promise.all([fs.access(levelsPath), fs.access(rankPath)]);
      return { runId, runDir, levelsPath, rankPath };
    } catch {
      // keep scanning older runs
    }
  }
  return null;
}

export async function GET(request: Request) {
  try {
    if (!isAuthorized(request)) {
      return NextResponse.json({ error: "unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const days = Math.max(10, Math.min(180, Number(searchParams.get("days") || 60)));

    const run = await findLatestSectorRun();
    if (!run) {
      return NextResponse.json({ error: "no_sector_run" }, { status: 404 });
    }

    const alertsRoot = path.join(resultsRoot(), "event_study_sectors");
    const latestRunMetaPath = path.join(alertsRoot, "latest_run.json");
    const latestAlertPath = path.join(alertsRoot, "alerts", "latest_alert.json");
    const latestDriftPath = path.join(alertsRoot, "drift", "latest_drift.json");
    const [levelsText, rankText, reportText, eligibilityText, signalsText, latestRunMetaText, latestAlertText, latestDriftText] = await Promise.all([
      fs.readFile(run.levelsPath, "utf-8"),
      fs.readFile(run.rankPath, "utf-8"),
      fs.readFile(path.join(run.runDir, "report_sector_event_study.txt"), "utf-8").catch(() => ""),
      fs.readFile(path.join(run.runDir, "sector_eligibility.csv"), "utf-8").catch(() => ""),
      fs.readFile(path.join(run.runDir, "sector_daily_signals.csv"), "utf-8").catch(() => ""),
      fs.readFile(latestRunMetaPath, "utf-8").catch(() => ""),
      fs.readFile(latestAlertPath, "utf-8").catch(() => ""),
      fs.readFile(latestDriftPath, "utf-8").catch(() => ""),
    ]);

    const levelsRows = parseCsv(levelsText);
    const rankRows = parseCsv(rankText);
    const eligibilityRows = parseCsv(eligibilityText);
    const signalsRows = parseCsv(signalsText);
    const latestRunMeta = latestRunMetaText ? (JSON.parse(latestRunMetaText) as Record<string, unknown>) : {};
    const latestAlert = latestAlertText ? (JSON.parse(latestAlertText) as Record<string, unknown>) : {};
    const latestDrift = latestDriftText ? (JSON.parse(latestDriftText) as DriftPayload) : {};

    const levelsBase: AlertLevelRow[] = levelsRows.map((r) => ({
      sector: r.sector || "unknown",
      date: r.date || "",
      n_assets: Number(r.n_assets || 0),
      alert_level: (r.alert_level || "verde").toLowerCase(),
      sector_score: toNum(r.sector_score),
      share_unstable: toNum(r.share_unstable),
      share_transition: toNum(r.share_transition),
      mean_confidence: toNum(r.mean_confidence),
      action_tier: r.action_tier || "",
      risk_budget_min: toNum(r.risk_budget_min),
      risk_budget_max: toNum(r.risk_budget_max),
      hedge_min: toNum(r.hedge_min),
      hedge_max: toNum(r.hedge_max),
      action_priority: toNum(r.action_priority),
      action_reason: r.action_reason || "",
    }));

    const ranking: RankRow[] = rankRows.map((r) => ({
      sector: r.sector || "unknown",
      drawdown_recall_l5: toNum(r.drawdown_recall_l5),
      drawdown_precision_l5: toNum(r.drawdown_precision_l5),
      drawdown_false_alarm_l5: toNum(r.drawdown_false_alarm_l5),
      drawdown_p_vs_random_l5: toNum(r.drawdown_p_vs_random_l5),
      ret_tail_recall_l5: toNum(r.ret_tail_recall_l5),
      ret_tail_precision_l5: toNum(r.ret_tail_precision_l5),
      composite_score: toNum(r.composite_score),
      n_assets_median_test: toNum(r.n_assets_median_test),
    }));

    const eligibility = eligibilityRows.map((r) => ({
      sector: r.sector || "unknown",
      eligible: String(r.eligible || "").toLowerCase() === "true",
      reason: r.reason || "",
      n_days_cal: Number(r.n_days_cal || 0),
      n_days_test: Number(r.n_days_test || 0),
      n_assets_median_test: toNum(r.n_assets_median_test),
    }));

    const eligibleSet = new Set(
      eligibility.filter((x) => x.eligible).map((x) => x.sector)
    );

    const timelineRaw: TimelineRow[] = signalsRows
      .map((r) => ({
        sector: r.sector || "unknown",
        date: r.date || "",
        alert_level: String(r.alert_level || "verde").toLowerCase(),
        sector_score: toNum(r.sector_score),
      }))
      .filter((r) => r.date && (eligibleSet.size === 0 || eligibleSet.has(r.sector)));

    const bySector = new Map<string, TimelineRow[]>();
    for (const row of timelineRaw) {
      const arr = bySector.get(row.sector) || [];
      arr.push(row);
      bySector.set(row.sector, arr);
    }
    const timeline: TimelineRow[] = [];
    const trendBySector = new Map<string, { score_delta_5d: number | null; level_changes_30d: number }>();
    for (const [sector, rows] of bySector.entries()) {
      const sorted = [...rows].sort((a, b) => a.date.localeCompare(b.date));
      const tail = sorted.slice(-days);
      timeline.push(...tail);

      const tail30 = sorted.slice(-30);
      let changes = 0;
      for (let i = 1; i < tail30.length; i += 1) {
        if (tail30[i].alert_level !== tail30[i - 1].alert_level) changes += 1;
      }
      const last = sorted[sorted.length - 1];
      const ref = sorted[Math.max(0, sorted.length - 6)];
      const delta = last?.sector_score != null && ref?.sector_score != null ? last.sector_score - ref.sector_score : null;
      trendBySector.set(sector, { score_delta_5d: delta, level_changes_30d: changes });
    }

    const levels: AlertLevelRow[] = levelsBase.map((row) => {
      const t = trendBySector.get(row.sector);
      const band = confidenceBand(row.mean_confidence);
      return {
        ...row,
        score_delta_5d: t?.score_delta_5d ?? null,
        level_changes_30d: t?.level_changes_30d ?? 0,
        action_recommended: row.action_reason || actionByLevel(row.alert_level),
        exposure_range:
          pctRange(row.risk_budget_min, row.risk_budget_max, 0) ||
          exposureRangeByLevel(row.alert_level),
        confidence_band: band,
        confidence_reason: confidenceReason(row, t),
      };
    });

    let weeklyCompare: { reference_run_id: string | null; summary: Record<string, unknown>; rows: WeeklyCompareRow[] } = {
      reference_run_id: null,
      summary: {},
      rows: [],
    };
    const weeklyPathFromMeta = String(latestRunMeta.weekly_compare_file || "");
    const weeklyPath = weeklyPathFromMeta || path.join(run.runDir, "weekly_compare.json");
    try {
      const t = await fs.readFile(weeklyPath, "utf-8");
      const j = JSON.parse(t) as Record<string, unknown>;
      weeklyCompare = {
        reference_run_id: (j.reference_run_id as string) || null,
        summary: (j.summary as Record<string, unknown>) || {},
        rows: ((j.rows as WeeklyCompareRow[]) || []).filter((x) => eligibleSet.has(String(x.sector || ""))),
      };
    } catch {
      weeklyCompare = { reference_run_id: null, summary: {}, rows: [] };
    }

    const counts = levels.reduce(
      (acc, row) => {
        const key = row.alert_level === "vermelho" || row.alert_level === "amarelo" ? row.alert_level : "verde";
        acc[key] += 1;
        return acc;
      },
      { verde: 0, amarelo: 0, vermelho: 0 }
    );

    return NextResponse.json({
      status: "ok",
      contract_version: CONTRACT_VERSION,
      run_id: run.runId,
      generated_at: new Date().toISOString(),
      lookback_days: days,
      counts,
      levels,
      ranking,
      eligibility,
      timeline,
      weekly_compare: weeklyCompare,
      notification: {
        run_id: String(latestAlert.run_id || ""),
        n_exited_green: Number(latestAlert.n_exited_green || 0),
        exited_green: Array.isArray(latestAlert.exited_green) ? latestAlert.exited_green : [],
      },
      drift: {
        level: String(latestDrift.drift_level || "unknown"),
        score: typeof latestDrift.drift_score === "number" ? latestDrift.drift_score : null,
        reasons: Array.isArray(latestDrift.reasons) ? latestDrift.reasons.slice(0, 4) : [],
      },
      report_excerpt: reportText.split("\n").slice(0, 40).join("\n"),
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: "sector_alerts_failed",
        message: error instanceof Error ? error.message : "unknown_error",
      },
      { status: 500 }
    );
  }
}
