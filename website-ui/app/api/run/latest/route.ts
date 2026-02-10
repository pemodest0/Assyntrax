import { NextResponse } from "next/server";
import { findLatestValidRun, readGlobalVerdict } from "@/lib/server/data";

export async function GET() {
  const [run, verdict] = await Promise.all([findLatestValidRun(), readGlobalVerdict()]);
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
    global_verdict_status: verdict?.status || "unknown",
  });
}

