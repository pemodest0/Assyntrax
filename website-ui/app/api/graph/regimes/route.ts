import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { resultsRoot } from "@/lib/server/results";

function parseCsv(text: string) {
  const lines = text.trim().split("\n");
  const header = lines.shift()?.split(",") || [];
  return lines.map((line) => {
    const parts = line.split(",");
    const row: Record<string, string> = {};
    header.forEach((h, idx) => {
      row[h] = parts[idx];
    });
    return row;
  });
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const asset = searchParams.get("asset");
  const tf = searchParams.get("tf") || "weekly";
  if (!asset) {
    return NextResponse.json({ error: "missing_asset" }, { status: 400 });
  }
  const file = path.join(resultsRoot(), "latest_graph", "assets", `${asset}_${tf}_regimes.csv`);
  try {
    const raw = await fs.readFile(file, "utf-8");
    const rows = parseCsv(raw).map((r) => ({
      t: Number(r.t),
      regime: r.regime,
      confidence: Number(r.confidence),
    }));
    return NextResponse.json(rows);
  } catch (err: any) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }
}
