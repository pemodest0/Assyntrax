import { NextResponse } from "next/server";
import { findLatestLabCorrRun, findLatestValidRun, readGlobalStatus, readLatestLabCorrTimeseries } from "@/lib/server/data";

export async function GET() {
  const [run, globalStatus, labRun, labTs] = await Promise.all([
    findLatestValidRun(),
    readGlobalStatus(),
    findLatestLabCorrRun(),
    readLatestLabCorrTimeseries(120),
  ]);
  if (!run) {
    return NextResponse.json(
      {
        error: "no_valid_run",
        message: "Nenhum run valido encontrado (status ok + deployment gate liberado).",
      },
      { status: 503 }
    );
  }

  return NextResponse.json({
    run_id: run.runId,
    summary: run.summary,
    global_status: globalStatus?.status || "unknown",
    lab_corr_macro: labRun
      ? {
          run_id: labRun.runId,
          latest_state: labTs?.latest || null,
          delta_20d: labTs?.delta_20d || null,
          deployment_gate: (labRun.summary?.deployment_gate || {}) as Record<string, unknown>,
        }
      : null,
  });
}

