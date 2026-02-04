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

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const assetsParam = searchParams.get("assets");
  const tf = searchParams.get("tf") || "weekly";
  const limit = Number(searchParams.get("limit") || "0");
  if (!assetsParam) {
    return NextResponse.json({ error: "missing_assets" }, { status: 400 });
  }
  const assets = assetsParam.split(",").map((s) => s.trim()).filter(Boolean);
  const out: Record<string, { t: number; regime: string; confidence: number }[]> = {};
  await Promise.all(
    assets.map(async (asset) => {
      const file = path.join(resultsRoot(), "latest_graph", "assets", `${asset}_${tf}_regimes.csv`);
      try {
        const raw = await fs.readFile(file, "utf-8");
        let rows = parseCsv(raw).map((r) => ({
          t: Number(r.t),
          regime: r.regime,
          confidence: Number(r.confidence),
        }));
        if (limit && rows.length > limit) rows = rows.slice(-limit);
        out[asset] = rows;
      } catch {
        out[asset] = [];
      }
    })
  );
  return NextResponse.json(out);
}
