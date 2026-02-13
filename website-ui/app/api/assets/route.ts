import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { listLatestFiles, readLatestFile, readLatestSnapshot, readRiskTruthPanel } from "@/lib/server/data";
import { readAssetStatusMap } from "@/lib/server/validated";

function inferDomain(group?: string) {
  const g = (group || "").toLowerCase();
  if (g.includes("realestate") || g.includes("imob")) return "realestate";
  if (g.includes("energy") || g.includes("carga")) return "energy";
  if (g) return "finance";
  return "finance";
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
  const warnings = Array.isArray(record.warnings) ? record.warnings.map((w) => String(w)) : [];
  const inferredRegime =
    String(record.regime_label || record.regime || regimeFromState || "").toUpperCase() ||
    (warnings.includes("REGIME_INSTAVEL") ? "UNSTABLE" : "TRANSITION");
  const baseConfidence =
    Number(
      record.confidence ??
        (record.metrics as Record<string, unknown> | undefined)?.confidence ??
        record.forecast_confidence ??
        (record.state as Record<string, unknown> | undefined)?.confidence ??
        0
    ) || 0;
  const mase = Number(record.mase_6m ?? Number.NaN);
  const baseQuality =
    Number(record.quality ?? (record.metrics as Record<string, unknown> | undefined)?.quality ?? Number.NaN);
  const quality = Number.isFinite(baseQuality) ? baseQuality : Number.isFinite(mase) ? Math.max(0, Math.min(1, 1 - mase * 0.25)) : 0.5;
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
    regime: inferredRegime,
    confidence: baseConfidence,
    quality,
    instability_score: Number(record.instability_score ?? 0),
    status: signalStatus,
    signal_status: signalStatus,
    reason: String(record.reason || record.warning_reason || ""),
    risk_truth_status: (riskTruthStatus || fallbackRiskStatus || "unknown").toLowerCase(),
    group: String(record.group || ""),
  };
}

function parseJsonl(text: string): Record<string, unknown>[] {
  const out: Record<string, unknown>[] = [];
  for (const line of text.split(/\r?\n/)) {
    const raw = line.trim();
    if (!raw) continue;
    try {
      out.push(JSON.parse(raw));
    } catch {
      // ignore malformed lines
    }
  }
  return out;
}

async function readPublicLatestRecords() {
  const candidates = [
    path.join(process.cwd(), "public", "data", "latest", "api_records.jsonl"),
    path.join(process.cwd(), "public", "data", "latest", "api_records.csv"),
  ];

  for (const filePath of candidates) {
    try {
      const text = await fs.readFile(filePath, "utf-8");
      if (filePath.endsWith(".jsonl")) {
        const rows = parseJsonl(text);
        if (rows.length) return rows;
      } else {
        const lines = text.split(/\r?\n/).filter(Boolean);
        if (lines.length < 2) continue;
        const header = lines[0].split(",").map((h) => h.trim());
        const rows: Record<string, unknown>[] = [];
        for (const line of lines.slice(1)) {
          const cols = line.split(",");
          const row: Record<string, unknown> = {};
          header.forEach((h, idx) => {
            row[h] = (cols[idx] || "").trim();
          });
          if (String(row.asset || "").trim()) rows.push(row);
        }
        if (rows.length) return rows;
      }
    } catch {
      // try next file candidate
    }
  }

  return [] as Record<string, unknown>[];
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
    const fallbackRows = await readPublicLatestRecords();
    if (!fallbackRows.length) {
      return NextResponse.json({ error: "no_valid_run" }, { status: 503 });
    }

    const normalizedFallback = fallbackRows
      .map((r: Record<string, unknown>) => normalizeRecord(r))
      .filter((r) => (domain ? r.domain === domain : true))
      .filter((r) => {
        const rt = String(r.risk_truth_status || "unknown").toLowerCase();
        if (rt === "unknown") return includeInconclusive || allowed.has("watch");
        if (rt === "inconclusive") return includeInconclusive;
        return allowed.has(rt);
      });

    const dedupFallback = new Map<string, (typeof normalizedFallback)[number]>();
    for (const row of normalizedFallback) {
      const key = `${row.asset}__${row.domain}`;
      const prev = dedupFallback.get(key);
      if (!prev || String(row.timestamp || "") >= String(prev.timestamp || "")) {
        dedupFallback.set(key, row);
      }
    }
    const records = Array.from(dedupFallback.values()).sort((a, b) => a.asset.localeCompare(b.asset));
    return NextResponse.json({
      run_id: "public_latest",
      summary: { source: "public_latest" },
      records,
    });
  }
  const truthMap = new Map<string, string>(
    Array.isArray(riskTruth?.entries) ? riskTruth.entries.map((e: Record<string, unknown>) => [String(e.asset_id || ""), String(e.risk_truth_status || "unknown")]) : []
  );

  const normalized = (Array.isArray(snap.records) ? snap.records : [])
    .map((r: Record<string, unknown>) => normalizeRecord(r, truthMap.get(String(r.asset || ""))))
    .filter((r) => (domain ? r.domain === domain : true))
    .filter((r) => {
      const rt = String(r.risk_truth_status || "unknown").toLowerCase();
      if (rt === "unknown") return includeInconclusive || allowed.has("watch");
      if (rt === "inconclusive") return includeInconclusive;
      return allowed.has(rt);
    });

  const dedup = new Map<string, (typeof normalized)[number]>();
  for (const row of normalized) {
    const key = `${row.asset}__${row.domain}`;
    const prev = dedup.get(key);
    if (!prev || String(row.timestamp || "") >= String(prev.timestamp || "")) {
      dedup.set(key, row);
    }
  }
  const records = Array.from(dedup.values()).sort((a, b) => a.asset.localeCompare(b.asset));

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
