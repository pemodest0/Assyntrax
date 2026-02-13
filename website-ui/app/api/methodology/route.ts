import { NextResponse } from "next/server";
import {
  findLatestLabCorrRun,
  findLatestValidRun,
  readGlobalStatus,
  readLatestLabCorrCaseStudies,
  readLatestLabCorrTimeseries,
  readRiskTruthPanel,
} from "@/lib/server/data";

export async function GET() {
  const [run, globalStatus, panel, labRun, labTs, labCases] = await Promise.all([
    findLatestValidRun(),
    readGlobalStatus(),
    readRiskTruthPanel(),
    findLatestLabCorrRun(),
    readLatestLabCorrTimeseries(120),
    readLatestLabCorrCaseStudies(120),
  ]);

  return NextResponse.json({
    run_id: run?.runId || null,
    summary: run?.summary || null,
    global_status: globalStatus || { status: "unknown" },
    risk_truth_panel: panel || {
      status: "empty",
      counts: { assets: 0, validated: 0, watch: 0, inconclusive: 0 },
      entries: [],
    },
    lab_corr_macro: labRun
      ? {
          run_id: labRun.runId,
          deployment_gate: (labRun.summary?.deployment_gate || {}) as Record<string, unknown>,
          latest_state: labTs?.latest || null,
          delta_20d: labTs?.delta_20d || null,
          n_used_stats: labTs?.n_used_stats || null,
          case_studies: {
            count_valid: labCases?.count_valid ?? 0,
            dropped_rows: labCases?.dropped_rows ?? 0,
            items: labCases?.cases || [],
          },
        }
      : null,
  });
}
