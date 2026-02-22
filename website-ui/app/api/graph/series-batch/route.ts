import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { resultsRoot } from "@/lib/server/results";

function parseCsv(text: string) {
  const lines = text.trim().split("\n");
  const header = (lines.shift()?.split(",") || []).map((h) => h.trim());
  return lines.map((line) => {
    const parts = line.split(",").map((p) => p.trim());
    const row: Record<string, string> = {};
    header.forEach((h, idx) => {
      row[h] = parts[idx];
    });
    return row;
  });
}

function pickNumber(row: Record<string, string>, keys: string[]) {
  for (const key of keys) {
    const raw = row[key];
    const n = Number(raw);
    if (Number.isFinite(n)) return n;
  }
  return null;
}

function toWeeklyIndices(dates: string[]) {
  const out: number[] = [];
  let lastKey = "";
  for (let i = 0; i < dates.length; i += 1) {
    const d = dates[i];
    const dt = new Date(d + "T00:00:00Z");
    const year = dt.getUTCFullYear();
    const week = Math.ceil(((dt.getTime() - Date.UTC(year, 0, 1)) / 86400000 + 1) / 7);
    const key = `${year}-W${week}`;
    if (key !== lastKey) {
      out.push(i);
      lastKey = key;
    } else {
      out[out.length - 1] = i;
    }
  }
  return out;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const assetsParam = searchParams.get("assets");
  const tf = searchParams.get("tf") || "weekly";
  const limitParam = searchParams.get("limit");
  const stepParam = searchParams.get("step");
  const limit = limitParam ? Math.max(1, Number(limitParam)) : 0;
  const step = stepParam ? Math.max(1, Number(stepParam)) : 1;
  if (!assetsParam) {
    return NextResponse.json({ error: "missing_assets" }, { status: 400 });
  }
  const assets = assetsParam.split(",").map((s) => s.trim()).filter(Boolean);
  const out: Record<
    string,
    { date: string; confidence: number; regime: string; price: number | null; volume: number | null }[]
  > = {};

  await Promise.all(
    assets.map(async (asset) => {
      try {
        out[asset] = await loadFallbackSeries(asset, tf, limit, step);
      } catch {
        out[asset] = [];
      }
    })
  );

  return NextResponse.json(out);
}
