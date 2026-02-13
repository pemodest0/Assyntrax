import { NextResponse } from "next/server";
import {
  findLatestLabCorrRun,
  readLatestLabCorrActionPlaybook,
  readLatestLabCorrEraEvaluation,
  readLatestLabCorrOperationalAlerts,
  readLatestLabCorrCaseStudies,
  readLatestLabCorrTimeseries,
  readLatestLabCorrUiViewModel,
} from "@/lib/server/data";

const SCHEMA_VERSION = "lab_corr_api_v1";

function emptyContract(windowValue: number) {
  return {
    schema_version: SCHEMA_VERSION,
    generated_at_utc: new Date().toISOString(),
    window: Math.trunc(windowValue),
    run: { id: "", dir: "", status: "missing" },
    metrics: {
      period: { start: "", end: "" },
      latest_state: null,
      delta_20d: null,
      n_used_stats: null,
    },
    alerts: {
      operational: {
        latest_date: "",
        latest_events: [],
        n_events_total: 0,
        n_events_last_60d: 0,
        event_counts: {},
        latest_event_rows: [],
      },
    },
    era_evaluation: { count: 0, items: [] },
    case_studies: { count_raw: 0, count_valid: 0, dropped_rows: 0, items: [] },
    playbook: { count: 0, latest: null, items_recent: [] },
    view_model: null,
    summary: null,
    summary_compact: "",
    contract_checks: { case_rows_dropped: 0, has_view_model: false },
    timeseries: [],
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const windowParam = Number(searchParams.get("window") || "120");
  const includeRows = searchParams.get("include_rows") === "1";

  if (!Number.isFinite(windowParam) || windowParam <= 0) {
    return NextResponse.json(
      {
        ...emptyContract(120),
        run: { id: "", dir: "", status: "error" },
        error: "invalid_window",
      },
      { status: 400 }
    );
  }

  const [run, ts, cases, opAlerts, eraEval, playbook, viewModel] = await Promise.all([
    findLatestLabCorrRun(),
    readLatestLabCorrTimeseries(windowParam),
    readLatestLabCorrCaseStudies(windowParam),
    readLatestLabCorrOperationalAlerts(windowParam),
    readLatestLabCorrEraEvaluation(windowParam),
    readLatestLabCorrActionPlaybook(windowParam),
    readLatestLabCorrUiViewModel(windowParam),
  ]);

  if (!run) {
    return NextResponse.json(
      {
        ...emptyContract(windowParam),
        run: { id: "", dir: "", status: "missing" },
        error: "no_valid_lab_run",
        message: "Nenhum run valido de lab_corr_macro foi encontrado.",
      },
      { status: 503 }
    );
  }

  const playbookRows = Array.isArray(playbook) ? playbook : [];
  const latestPlaybook = playbookRows.length ? playbookRows[playbookRows.length - 1] : null;
  const payload = {
    schema_version: SCHEMA_VERSION,
    generated_at_utc: new Date().toISOString(),
    window: Math.trunc(windowParam),
    run: { id: run.runId, dir: run.runDir, status: "ok" },
    metrics: {
      period: ts ? { start: ts.start, end: ts.end } : { start: "", end: "" },
      latest_state: ts?.latest || null,
      delta_20d: ts?.delta_20d || null,
      n_used_stats: ts?.n_used_stats || null,
    },
    alerts: {
      operational: opAlerts,
    },
    era_evaluation: {
      count: Array.isArray(eraEval) ? eraEval.length : 0,
      items: Array.isArray(eraEval) ? eraEval : [],
    },
    case_studies: {
      count_raw: cases?.count_raw ?? 0,
      count_valid: cases?.count_valid ?? 0,
      dropped_rows: cases?.dropped_rows ?? 0,
      items: cases?.cases || [],
    },
    playbook: {
      count: playbookRows.length,
      latest: latestPlaybook,
      items_recent: playbookRows.slice(-30),
    },
    view_model: viewModel || null,
    summary: run.summary,
    summary_compact: run.summaryCompact || "",
    contract_checks: {
      case_rows_dropped: cases?.dropped_rows ?? 0,
      has_view_model: Boolean(viewModel && typeof viewModel === "object"),
    },
    timeseries: includeRows ? ts?.rows || [] : [],
  };

  return NextResponse.json(payload);
}
