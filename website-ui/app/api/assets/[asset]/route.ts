import { NextResponse } from "next/server";
import { readLatestSnapshot, readRiskTruthPanel } from "@/lib/server/data";

export async function GET(_: Request, context: { params: Promise<{ asset: string }> }) {
  const params = await context.params;
  const asset = decodeURIComponent(params.asset || "");
  const snap = await readLatestSnapshot();
  if (!snap) {
    return NextResponse.json({ error: "no_valid_run" }, { status: 503 });
  }

  const riskTruth = await readRiskTruthPanel();
  const riskEntry = Array.isArray(riskTruth?.entries)
    ? riskTruth.entries.find((e: Record<string, unknown>) => String(e.asset_id || "") === asset)
    : null;

  const row = (Array.isArray(snap.records) ? snap.records : []).find(
    (r: Record<string, unknown>) => String(r.asset || "") === asset
  );
  if (!row) {
    return NextResponse.json({ error: "asset_not_found", asset }, { status: 404 });
  }

  const state = (row.state as Record<string, unknown> | undefined)?.label;
  const normalized = {
    run_id: snap.runId,
    asset,
    domain: String(row.domain || "unknown"),
    timestamp: String(row.timestamp || ""),
    data_adequacy: String(row.data_adequacy || "unknown"),
    source_type: String(row.source_type || "proxy"),
    regime: String(row.regime_label || row.regime || state || "unknown"),
    confidence: Number(row.confidence ?? (row.metrics as Record<string, unknown> | undefined)?.confidence ?? 0),
    quality: Number(row.quality ?? (row.metrics as Record<string, unknown> | undefined)?.quality ?? 0),
    instability_score: Number(row.instability_score ?? 0),
    status: String(row.status || row.signal_status || "unknown"),
    signal_status: String(row.status || row.signal_status || "unknown"),
    reason: String(row.reason || row.warning_reason || ""),
    risk_truth_status: String((riskEntry as Record<string, unknown> | null)?.risk_truth_status || "unknown"),
    risk_truth_entry: riskEntry || null,
    summary: snap.summary,
  };
  return NextResponse.json(normalized);
}
