import { promises as fs } from "fs";
import path from "path";
import { readAssetStatusMap } from "@/lib/server/validated";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export function dataDirs() {
  const root = repoRoot();
  return {
    latest: process.env.DATA_DIR || path.join(root, "results", "latest"),
    publicLatest: path.join(process.cwd(), "public", "data", "latest"),
    results: path.join(root, "results"),
  };
}

export async function listLatestFiles() {
  const { latest, publicLatest } = dataDirs();
  let dir = latest;
  try {
    await fs.access(dir);
  } catch {
    dir = publicLatest;
  }
  const files = await fs.readdir(dir);
  return files.filter((f) => f.endsWith(".json"));
}

export async function readLatestFile(file: string) {
  const { latest, publicLatest } = dataDirs();
  let dir = latest;
  try {
    await fs.access(dir);
  } catch {
    dir = publicLatest;
  }
  const target = path.join(dir, file);
  try {
    const text = await fs.readFile(target, "utf-8");
    return JSON.parse(text);
  } catch {
    const fallback = dir === latest ? path.join(publicLatest, file) : path.join(latest, file);
    const text = await fs.readFile(fallback, "utf-8");
    return JSON.parse(text);
  }
}

export async function findLatestApiRecords() {
  const { results } = dataDirs();
  const snapshotsRoot = path.join(results, "ops", "snapshots");
  try {
    const runDirs = await fs.readdir(snapshotsRoot, { withFileTypes: true });
    const snapCandidates: { path: string; mtime: number }[] = [];
    for (const ent of runDirs) {
      if (!ent.isDirectory()) continue;
      const p = path.join(snapshotsRoot, ent.name, "api_snapshot.jsonl");
      try {
        const stat = await fs.stat(p);
        snapCandidates.push({ path: p, mtime: stat.mtimeMs });
      } catch {
        // ignore
      }
    }
    snapCandidates.sort((a, b) => b.mtime - a.mtime);
    if (snapCandidates.length) return snapCandidates[0].path;
  } catch {
    // ignore and fallback to legacy search
  }

  const entries = await fs.readdir(results, { withFileTypes: true });
  const candidates: { path: string; mtime: number }[] = [];
  for (const ent of entries) {
    if (!ent.isDirectory()) continue;
    const p = path.join(results, ent.name, "api_records.jsonl");
    try {
      const stat = await fs.stat(p);
      candidates.push({ path: p, mtime: stat.mtimeMs });
    } catch {
      // ignore
    }
  }
  candidates.sort((a, b) => b.mtime - a.mtime);
  return candidates.length ? candidates[0].path : null;
}

function sanitizeJsonLine(line: string) {
  return line
    .replace(/\bNaN\b/g, "null")
    .replace(/\bInfinity\b/g, "null")
    .replace(/\b-Infinity\b/g, "null");
}

function parseJsonLine(line: string): Record<string, unknown> {
  try {
    return JSON.parse(line);
  } catch {
    const fixed = sanitizeJsonLine(line);
    return JSON.parse(fixed);
  }
}

export async function readJsonl(pathFile: string): Promise<Record<string, unknown>[]> {
  const text = await fs.readFile(pathFile, "utf-8");
  const out: Record<string, unknown>[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    try {
      out.push(parseJsonLine(line));
    } catch {
      // ignore malformed line instead of breaking entire snapshot read
    }
  }
  return out;
}

function repairMojibake(value: string) {
  return value
    .replace(/ÃƒÂ§/g, "ç")
    .replace(/ÃƒÂ£/g, "ã")
    .replace(/ÃƒÂ¡/g, "á")
    .replace(/ÃƒÂ©/g, "é")
    .replace(/ÃƒÂª/g, "ê")
    .replace(/ÃƒÂ­/g, "í")
    .replace(/ÃƒÂ³/g, "ó")
    .replace(/ÃƒÂ´/g, "ô")
    .replace(/ÃƒÂº/g, "ú")
    .replace(/Ãƒâ€°/g, "É")
    .replace(/Ãƒâ€œ/g, "Ó")
    .replace(/Ãƒ/g, "à")
    .replace(/Ã‚/g, "");
}

function sanitizeEncoding<T>(input: T): T {
  if (typeof input === "string") {
    return repairMojibake(input) as T;
  }
  if (Array.isArray(input)) {
    return input.map((item) => sanitizeEncoding(item)) as T;
  }
  if (input && typeof input === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(input as Record<string, unknown>)) {
      out[k] = sanitizeEncoding(v);
    }
    return out as T;
  }
  return input;
}

export type LatestRunInfo = {
  runId: string;
  snapshotPath: string;
  summaryPath: string;
  summary: Record<string, unknown>;
};

function isRunValid(summary: Record<string, unknown>) {
  const status = String(summary?.status || "").toLowerCase();
  const gate = (summary?.deployment_gate || {}) as Record<string, unknown>;
  const blocked = gate?.blocked === true;
  return status === "ok" && !blocked;
}

export async function findLatestValidRun(): Promise<LatestRunInfo | null> {
  const { results } = dataDirs();
  const snapshotsRoot = path.join(results, "ops", "snapshots");
  let runDirs: string[] = [];
  try {
    runDirs = (await fs.readdir(snapshotsRoot, { withFileTypes: true }))
      .filter((ent) => ent.isDirectory())
      .map((ent) => ent.name)
      .sort()
      .reverse();
  } catch {
    return null;
  }

  for (const runId of runDirs) {
    const summaryPath = path.join(snapshotsRoot, runId, "summary.json");
    const snapshotPath = path.join(snapshotsRoot, runId, "api_snapshot.jsonl");
    try {
      const [summaryText, snapshotStat] = await Promise.all([
        fs.readFile(summaryPath, "utf-8"),
        fs.stat(snapshotPath),
      ]);
      if (!snapshotStat.size) continue;
      const summary = JSON.parse(summaryText) as Record<string, unknown>;
      if (!isRunValid(summary)) continue;
      return { runId, summaryPath, snapshotPath, summary };
    } catch {
      // ignore invalid run and keep scanning older runs
    }
  }
  return null;
}

export async function readLatestSnapshot() {
  const run = await findLatestValidRun();
  if (!run) return null;
  const records = await readJsonl(run.snapshotPath);
  return {
    runId: run.runId,
    summary: sanitizeEncoding(run.summary),
    records: sanitizeEncoding(records),
  };
}

export async function readRiskTruthPanel() {
  const { results } = dataDirs();
  const target = path.join(results, "validation", "risk_truth_panel.json");
  try {
    const text = await fs.readFile(target, "utf-8");
    return sanitizeEncoding(JSON.parse(text));
  } catch {
    return {
      status: "empty",
      counts: { assets: 0, validated: 0, watch: 0, inconclusive: 0 },
      entries: [],
    };
  }
}

export async function readGlobalVerdict() {
  const { results } = dataDirs();
  const target = path.join(results, "validation", "VERDICT.json");
  try {
    const text = await fs.readFile(target, "utf-8");
    return sanitizeEncoding(JSON.parse(text));
  } catch {
    return { status: "unknown", gate_checks: {} };
  }
}

export async function readJsonlWithValidationGate(pathFile: string) {
  const records = await readJsonl(pathFile);
  let statusMap: Record<string, Record<string, string>> = {};
  try {
    statusMap = await readAssetStatusMap();
  } catch {
    return records;
  }
  return records.map((record: Record<string, unknown>) => {
    const key = `${record.asset || ""}__${record.timeframe || ""}`;
    const gate = statusMap[key];
    if (!gate || (gate.status || "").toLowerCase() === "validated") {
      return record;
    }
    const reason = gate.reason || "gate_not_validated";
    const warnings = Array.isArray(record.warnings) ? [...record.warnings] : [];
    if (!warnings.includes("INCONCLUSIVE_SIGNAL")) {
      warnings.push("INCONCLUSIVE_SIGNAL");
    }
    return {
      ...record,
      signal_status: "inconclusive",
      use_forecast_bool: false,
      action: "DIAGNOSTICO_INCONCLUSIVO",
      regime_label: "INCONCLUSIVE",
      confidence_level: "LOW",
      warnings,
      gate_reason: reason,
    };
  });
}

export async function readDashboardOverview() {
  const { results } = dataDirs();
  const overviewPath = path.join(results, "dashboard", "overview.json");
  const text = await fs.readFile(overviewPath, "utf-8");
  return JSON.parse(text);
}

