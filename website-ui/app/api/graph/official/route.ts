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

export async function GET() {
  const file = path.join(resultsRoot(), "official_regimes", "official_regimes.csv");
  try {
    const raw = await fs.readFile(file, "utf-8");
    const rows = parseCsv(raw)
      .filter((r) => r.date)
      .slice(-260)
      .map((r) => ({
        date: r.date,
        VIX: r.VIX ? Number(r.VIX) : undefined,
        NFCI: r.NFCI ? Number(r.NFCI) : undefined,
        USREC: r.USREC ? Number(r.USREC) : undefined,
      }));
    return NextResponse.json(rows);
  } catch (err: any) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }
}
