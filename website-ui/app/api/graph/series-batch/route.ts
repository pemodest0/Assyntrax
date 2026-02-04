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

function toWeeklyDates(dates: string[]) {
  const out: string[] = [];
  let lastKey = "";
  for (const d of dates) {
    const dt = new Date(d + "T00:00:00Z");
    const year = dt.getUTCFullYear();
    const week = Math.ceil(((dt.getTime() - Date.UTC(year, 0, 1)) / 86400000 + 1) / 7);
    const key = `${year}-W${week}`;
    if (key !== lastKey) {
      out.push(d);
      lastKey = key;
    } else {
      out[out.length - 1] = d;
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
        const alignedDates = tf === "weekly" ? toWeeklyDates(dates) : dates;

        const total = regRows.length;
        const n = limit ? Math.min(limit, total) : total;
        const sliceDates = alignedDates.slice(-n);
        const sliceRegs = regRows.slice(-n);
        const slicePrices = priceRows.slice(-n);
        const series = sliceRegs
          .filter((_, idx) => idx % step === 0)
          .map((r, i) => ({
            date: sliceDates[i] || "",
            confidence: Number(r.confidence),
            regime: r.regime,
            price: Number(slicePrices[i]?.price ?? NaN) || null,
          }));
        out[asset] = series;
      } catch {
        out[asset] = [];
      }
    })
  );

  return NextResponse.json(out);
}
