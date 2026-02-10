import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { resultsRoot } from "@/lib/server/results";

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

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const sector = (searchParams.get("sector") || "all").toLowerCase();
  const tf = searchParams.get("tf") || "weekly";
  const file = path.join(resultsRoot(), "latest_graph", `universe_${tf}.json`);
  try {
    const raw = await fs.readFile(file, "utf-8");
    const data = JSON.parse(raw);
    if (sector === "all") return NextResponse.json(data);
    const filtered = (Array.isArray(data) ? data : []).filter(
      (r: Record<string, unknown>) => String(r.group || "").toLowerCase() === sector
    );
    return NextResponse.json(filtered);
  } catch {
    try {
      const groupsCsv = await fs.readFile(path.join(repoRoot(), "data", "asset_groups.csv"), "utf-8");
      const rows = parseCsv(groupsCsv);
      const filtered = sector === "all" ? rows : rows.filter((r) => (r.group || "").toLowerCase() === sector);
      return NextResponse.json(filtered.map((r) => ({ asset: r.asset, group: r.group })));
    } catch {
      return NextResponse.json({ error: "not_found" }, { status: 404 });
    }
  }
}
