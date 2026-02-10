import { NextResponse } from "next/server";
import { listLatestFiles, readLatestFile, readLatestSnapshot, readRiskTruthPanel } from "@/lib/server/data";
import { readAssetStatusMap } from "@/lib/server/validated";

function inferDomain(group?: string) {
  const g = (group || "").toLowerCase();
  if (g.includes("realestate") || g.includes("imob")) return "realestate";
  if (g.includes("energy") || g.includes("carga")) return "energy";
  if (g) return "finance";
  return "unknown";
}

function normalizeDomain(value?: string, group?: string) {
  const raw = (value || "").toLowerCase().trim();
  if (!raw) return inferDomain(group);
  if (raw.includes("realestate") || raw.includes("real_estate") || raw.includes("imob")) {
    return "realestate";
  }
  if (raw.includes("energy") || raw.includes("logistics") || raw.includes("carga")) {
    return "energy";
  }
  if (raw.includes("fin") || raw.includes("equit") || raw.includes("crypto")) {
    return "finance";
  }
  return inferDomain(group);
}

function normalizeRecord(record: Record<string, unknown>, riskTruthStatus?: string) {
  const regimeFromState = (record.state as Record<string, unknown> | undefined)?.label;
  const signalStatus = String(record.status || record.signal_status || "unknown").toLowerCase();
  const fallbackRiskStatus =
    signalStatus === "validated" || signalStatus === "watch" || signalStatus === "inconclusive"
      ? signalStatus
      : "unknown";
  return {
    asset: String(record.asset || ""),
    domain: normalizeDomain(String(record.domain || ""), String(record.group || "")),
    timestamp: String(record.timestamp || ""),
    run_id: String(record.run_id || ""),
    data_adequacy: String(record.data_adequacy || "unknown"),
    source_type: String(record.source_type || "proxy"),
    regime: String(record.regime_label || record.regime || regimeFromState || "unknown"),
    confidence: Number(record.confidence ?? (record.metrics as Record<string, unknown> | undefined)?.confidence ?? 0),
    quality: Number(record.quality ?? (record.metrics as Record<string, unknown> | undefined)?.quality ?? 0),
    instability_score: Number(record.instability_score ?? 0),
    status: signalStatus,
    signal_status: signalStatus,
    reason: String(record.reason || record.warning_reason || ""),
    risk_truth_status: (riskTruthStatus || fallbackRiskStatus || "unknown").toLowerCase(),
    group: String(record.group || ""),
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const file = searchParams.get("file");
  if (file) {
    try {
      const data = await readLatestFile(file);
      const m = file.match(/^(.+?)_(daily|weekly)\.json$/i);
      if (m) {
        try {
          const statusMap = await readAssetStatusMap();
          const key = `${m[1]}__${m[2].toLowerCase()}`;
          const gate = statusMap[key];
          if (gate && (gate.status || "").toLowerCase() !== "validated") {
            return NextResponse.json({
              ...data,
              signal_status: "inconclusive",
              regime_label: "INCONCLUSIVE",
              action: "DIAGNOSTICO_INCONCLUSIVO",
              gate_reason: gate.reason || "gate_not_validated",
            });
          }
        } catch {
          // no validated map, keep legacy payload
        }
      }
      return NextResponse.json(data);
    } catch {
      return NextResponse.json({ error: "file_not_found", file }, { status: 404 });
    }
  }

  const domain = (searchParams.get("domain") || "").toLowerCase();
  const statusParam = searchParams.get("status") || "validated,watch";
  const includeInconclusive = searchParams.get("include_inconclusive") === "1";
  const allowedStatus = statusParam
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  const allowed = new Set(allowedStatus.length ? allowedStatus : ["validated", "watch"]);

  const [snap, riskTruth] = await Promise.all([readLatestSnapshot(), readRiskTruthPanel()]);
  if (!snap) {
    return NextResponse.json({ error: "no_valid_run" }, { status: 503 });
  }
  const truthMap = new Map<string, string>(
    Array.isArray(riskTruth?.entries) ? riskTruth.entries.map((e: Record<string, unknown>) => [String(e.asset_id || ""), String(e.risk_truth_status || "unknown")]) : []
  );

  const records = (Array.isArray(snap.records) ? snap.records : [])
    .map((r: Record<string, unknown>) => normalizeRecord(r, truthMap.get(String(r.asset || ""))))
    .filter((r) => (domain ? r.domain === domain : true))
    .filter((r) => {
      const rt = String(r.risk_truth_status || "unknown").toLowerCase();
      if (rt === "unknown") return includeInconclusive || allowed.has("watch");
      if (rt === "inconclusive") return includeInconclusive;
      return allowed.has(rt);
    });

  if (!records.length) {
    const files = await listLatestFiles();
    return NextResponse.json({ files, records: [], run_id: snap.runId, summary: snap.summary });
  }

  return NextResponse.json({
    run_id: snap.runId,
    summary: snap.summary,
    records,
  });
}
