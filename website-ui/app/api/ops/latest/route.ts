import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { resultsRoot } from "@/lib/server/results";

async function readJsonSafe(filePath: string) {
  try {
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return {};
  }
}

async function readTextSafe(filePath: string) {
  try {
    return await fs.readFile(filePath, "utf-8");
  } catch {
    return "";
  }
}

async function buildPublicFallback() {
  const base = path.join(process.cwd(), "public", "data", "lab_corr_macro", "latest");
  const publicLatestBase = path.join(process.cwd(), "public", "data", "latest");
  const [summary, summaryCompact] = await Promise.all([
    readJsonSafe(path.join(base, "summary.json")),
    readTextSafe(path.join(base, "summary_compact.txt")),
  ]);
  const predictionTruth = await readJsonSafe(path.join(publicLatestBase, "prediction_truth_daily.json"));

  const runId = String(summary.run_id || "public_latest");
  const gateObj =
    summary && typeof summary === "object" && summary.deployment_gate && typeof summary.deployment_gate === "object"
      ? (summary.deployment_gate as Record<string, unknown>)
      : {};
  const blocked = gateObj.blocked === true;
  const reasons = Array.isArray(gateObj.reasons) ? gateObj.reasons : [];
  const checks =
    summary && typeof summary === "object" && summary.checks && typeof summary.checks === "object"
      ? (summary.checks as Record<string, unknown>)
      : {};

  if (!Object.keys(summary).length && !summaryCompact.trim()) {
    return {
      status: "empty",
      run_id: "no_public_snapshot",
      run_path: "public/data/lab_corr_macro/latest",
      sanity: { status: "missing", checks: {} },
      publish_gate: { publish_allowed: false, blocked_reasons: ["snapshot_publico_ausente"] },
      history_compare: { previous_run_id: null, delta: {} },
      summary: {
        source: "public_fallback_empty",
        deployment_gate: {},
        checks: {},
        scores: {},
        metrics: {},
      },
      prediction_truth: predictionTruth,
      daily_report:
        "Sem snapshot publico de operacao. Gere um run em results/ops/runs ou publique arquivos em public/data/lab_corr_macro/latest.",
    };
  }

  return {
    status: "ok",
    run_id: runId,
    run_path: "public/data/lab_corr_macro/latest",
    sanity: { status: blocked ? "blocked" : "ok", checks },
    publish_gate: { publish_allowed: !blocked, blocked_reasons: reasons },
    history_compare: { previous_run_id: null, delta: {} },
    summary: {
      source: "public_fallback",
      deployment_gate: gateObj,
      checks,
      scores: typeof summary.scores === "object" && summary.scores ? summary.scores : {},
      metrics: typeof summary.calibration === "object" && summary.calibration ? summary.calibration : {},
    },
    prediction_truth: predictionTruth,
    daily_report:
      summaryCompact.trim() ||
      `run_id=${runId}\nstatus=${String(summary.status || "unknown")}\nsource=public_fallback\npublish_allowed=${String(!blocked)}`,
  };
}

export async function GET() {
  const root = resultsRoot();
  const latestPath = path.join(root, "ops", "runs", "latest_run.json");
  const latest = await readJsonSafe(latestPath);
  const runId = String(latest.run_id || "").trim();
  const runPath = String(latest.path || "").trim();

  if (!runId || !runPath) {
    const fallback = await buildPublicFallback();
    return NextResponse.json(fallback);
  }

  const [sanity, gate, history, summary, report] = await Promise.all([
    readJsonSafe(path.join(runPath, "sanity.json")),
    readJsonSafe(path.join(runPath, "publish_gate.json")),
    readJsonSafe(path.join(runPath, "history_compare.json")),
    readJsonSafe(path.join(runPath, "daily_master_summary.json")),
    readTextSafe(path.join(runPath, "daily_report.txt")),
  ]);
  const predictionTruth = await readJsonSafe(path.join(runPath, "prediction_truth_summary.json"));

  return NextResponse.json({
    status: "ok",
    run_id: runId,
    run_path: runPath,
    sanity,
    publish_gate: gate,
    history_compare: history,
    summary,
    prediction_truth: predictionTruth,
    daily_report: report,
  });
}
