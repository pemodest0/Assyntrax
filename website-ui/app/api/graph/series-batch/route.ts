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

function normalizeRegime(raw: unknown, warnings?: string[]) {
  const r = String(raw || "").toUpperCase();
  if (r === "STABLE" || r === "TRANSITION" || r === "UNSTABLE" || r === "INCONCLUSIVE") return r;
  if (warnings?.includes("REGIME_INSTAVEL")) return "UNSTABLE";
  return "TRANSITION";
}

async function loadBundledSeries(asset: string, tf: string, limit: number, step: number) {
  const bundled = path.join(process.cwd(), "public", "data", "latest", "api_records.jsonl");
  const raw = await fs.readFile(bundled, "utf-8");
  const rows = raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line) as Record<string, unknown>;
      } catch {
        return null;
      }
    })
    .filter((row): row is Record<string, unknown> => row !== null)
    .filter((row) => String(row.asset || "") === asset)
    .filter((row) => {
      const rowTf = String(row.timeframe || "").toLowerCase();
      if (!rowTf) return true;
      return rowTf === tf.toLowerCase() || (tf.toLowerCase() === "weekly" && rowTf === "daily");
    });

  const horizons = Array.from(new Set(rows.map((row) => Number(row.horizon)).filter((h) => Number.isFinite(h) && h > 0))).sort((a, b) => a - b);
  const preferredHorizon = horizons[0];
  const scoped = Number.isFinite(preferredHorizon) ? rows.filter((row) => Number(row.horizon) === preferredHorizon) : rows;

  const byDate = new Map<string, { date: string; confidence: number; regime: string; price: number | null }>();
  for (const row of scoped) {
    const date = String(row.timestamp || "").slice(0, 10);
    if (!date) continue;
    const warnings = Array.isArray(row.warnings) ? row.warnings.map((w) => String(w)) : [];
    byDate.set(date, {
      date,
      confidence: Number(row.forecast_confidence ?? row.regime_confidence ?? 0.5) || 0.5,
      regime: normalizeRegime(row.regime_label, warnings),
      price: null,
    });
  }

  const series = Array.from(byDate.values()).sort((a, b) => a.date.localeCompare(b.date));
  const total = series.length;
  const n = limit ? Math.min(limit, total) : total;
  return series.slice(-n).filter((_, idx) => idx % step === 0);
}

async function resolvePriceFile(asset: string) {
  const candidates = [
    path.join(resultsRoot(), "..", "data", "raw", "finance", "yfinance_daily", `${asset}.csv`),
    path.join(process.cwd(), "public", "data", "raw", "finance", "yfinance_daily", `${asset}.csv`),
  ];
  for (const candidate of candidates) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {
      // keep trying
    }
  }
  throw new Error("price_file_not_found");
}

async function loadFallbackSeries(asset: string, tf: string, limit: number, step: number) {
  const priceFile = await resolvePriceFile(asset);
  const rawPrice = await fs.readFile(priceFile, "utf-8");
  const priceRows = parseCsv(rawPrice);
  const dates = priceRows.map((r) => r.date).filter(Boolean);
  const returns = priceRows.map((r) => Number(r.r)).filter((v) => Number.isFinite(v));

  const window = 20;
  const volSeries: number[] = [];
  for (let i = window; i < returns.length; i += 1) {
    const slice = returns.slice(i - window, i);
    volSeries.push(std(slice));
  }

  const q1 = quantile(volSeries, 0.33);
  const q2 = quantile(volSeries, 0.66);
  const minVol = Math.min(...volSeries, q1);
  const maxVol = Math.max(...volSeries, q2);

  const seriesRaw = priceRows.map((row, idx) => {
    const vol = volSeries[idx - window] ?? volSeries[volSeries.length - 1] ?? 0;
    const regime = computeRegime(vol, q1, q2);
    const confidence = computeConfidence(vol, minVol, maxVol);
    return {
      date: row.date,
      confidence,
      regime,
      price: Number(row.price ?? NaN) || null,
    };
  });

  let indices: number[] = [];
  if (tf === "weekly") {
    indices = toWeeklyIndices(dates);
  } else {
    indices = seriesRaw.map((_, idx) => idx);
  }

  const sliced = indices.map((i) => seriesRaw[i]).filter((r) => r && r.date);
  const total = sliced.length;
  const n = limit ? Math.min(limit, total) : total;
  return sliced.slice(-n).filter((_, idx) => idx % step === 0);
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
    { date: string; confidence: number; regime: string; price: number | null }[]
  > = {};

  await Promise.all(
    assets.map(async (asset) => {
      try {
        const regimesFile = path.join(resultsRoot(), "latest_graph", "assets", `${asset}_${tf}_regimes.csv`);
        const rawReg = await fs.readFile(regimesFile, "utf-8");
        const regRows = parseCsv(rawReg);

        const priceFile = path.join(resultsRoot(), "..", "data", "raw", "finance", "yfinance_daily", `${asset}.csv`);
        const rawPrice = await fs.readFile(priceFile, "utf-8");
        const priceRows = parseCsv(rawPrice);
        const dates = priceRows.map((r) => r.date).filter(Boolean);
        const indices = tf === "weekly" ? toWeeklyIndices(dates) : priceRows.map((_, idx) => idx);

        const total = regRows.length;
        const n = limit ? Math.min(limit, total) : total;
        const sliceRegs = regRows.slice(-n);
        const sliceIdx = indices.slice(-n);
        const series = sliceRegs
          .filter((_, idx) => idx % step === 0)
          .map((r, i) => {
            const priceRow = priceRows[sliceIdx[i] ?? 0];
            return {
              date: priceRow?.date || "",
              confidence: Number(r.confidence),
              regime: r.regime,
              price: Number(priceRow?.price ?? NaN) || null,
            };
          });
        out[asset] = series;
      } catch {
        try {
          out[asset] = await loadFallbackSeries(asset, tf, limit, step);
        } catch {
          try {
            out[asset] = await loadBundledSeries(asset, tf, limit, step);
          } catch {
            out[asset] = [];
          }
        }
      }
    })
  );

  return NextResponse.json(out);
}
