import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { readValidatedUniverse } from "@/lib/server/validated";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

function parseCsv(text: string) {
  const lines = text.trim().split("\n");
  const header = (lines.shift()?.split(",") || []).map((h) => h.trim());
  return lines.map((line) => {
    const parts = line.split(",");
    const row: Record<string, string> = {};
    header.forEach((h, idx) => {
      row[h] = (parts[idx] || "").trim();
    });
    return row;
  });
}

function std(values: number[]) {
  if (!values.length) return 0;
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const varSum = values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length;
  return Math.sqrt(varSum);
}

function quantile(values: number[], q: number) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  }
  return sorted[base];
}

function computeRegime(vol: number, q1: number, q2: number) {
  if (vol <= q1) return "STABLE";
  if (vol <= q2) return "TRANSITION";
  return "UNSTABLE";
}

function computeConfidence(vol: number, minVol: number, maxVol: number) {
  if (!Number.isFinite(vol) || maxVol <= minVol) return 0.6;
  const rel = (vol - minVol) / (maxVol - minVol);
  const conf = 0.6 + 0.3 * Math.abs(rel - 0.5) * 2;
  return Math.max(0.55, Math.min(0.9, conf));
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const tf = searchParams.get("tf") || "weekly";
  try {
    const validated = await readValidatedUniverse(tf);
    if (Array.isArray(validated) && validated.length) {
      return NextResponse.json(validated);
    }
  } catch {
    // fallback to legacy path
  }
  const file = tf === "daily" ? "universe_daily.json" : "universe_weekly.json";
  const target = path.join(repoRoot(), "results", "latest_graph", file);
  try {
    const text = await fs.readFile(target, "utf-8");
    return NextResponse.json(JSON.parse(text));
  } catch {
    // fallback from asset_groups.csv + price data
    try {
      const groupsCsv = await fs.readFile(path.join(repoRoot(), "data", "asset_groups.csv"), "utf-8");
      const groups = parseCsv(groupsCsv);
      const out: Array<Record<string, unknown>> = [];
      for (const row of groups) {
        const asset = row.asset;
        const group = row.group;
        try {
          const priceFile = path.join(repoRoot(), "data", "raw", "finance", "yfinance_daily", `${asset}.csv`);
          const raw = await fs.readFile(priceFile, "utf-8");
          const rows = parseCsv(raw);
          const returns = rows.map((r) => Number(r.r)).filter((v) => Number.isFinite(v));
          const window = 20;
          const volSeries: number[] = [];
          for (let i = window; i < returns.length; i++) {
            const slice = returns.slice(i - window, i);
            volSeries.push(std(slice));
          }
          const q1 = quantile(volSeries, 0.33);
          const q2 = quantile(volSeries, 0.66);
          const minVol = Math.min(...volSeries, q1);
          const maxVol = Math.max(...volSeries, q2);
          const lastVol = volSeries[volSeries.length - 1] ?? 0;
          const regime = computeRegime(lastVol, q1, q2);
          const confidence = computeConfidence(lastVol, minVol, maxVol);
          out.push({
            asset,
            group,
            state: { label: regime },
            metrics: { confidence },
          });
        } catch {
          out.push({ asset, group, state: { label: "TRANSITION" }, metrics: { confidence: 0.6 } });
        }
      }
      return NextResponse.json(out);
    } catch {
      return NextResponse.json({ error: "graph_universe_not_found" }, { status: 404 });
    }
  }
}
