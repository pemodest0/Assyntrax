import { NextResponse } from "next/server";
import { findLatestValidRun, readGlobalVerdict, readRiskTruthPanel } from "@/lib/server/data";

export async function GET() {
  const [run, verdict, panel] = await Promise.all([
    findLatestValidRun(),
    readGlobalVerdict(),
    readRiskTruthPanel(),
  ]);

  return NextResponse.json({
    run_id: run?.runId || null,
    summary: run?.summary || null,
    global_verdict: verdict || { status: "unknown" },
    risk_truth_panel: panel || {
      status: "empty",
      counts: { assets: 0, validated: 0, watch: 0, inconclusive: 0 },
      entries: [],
    },
  });
}
