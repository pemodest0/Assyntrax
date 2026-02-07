import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const asset = searchParams.get("asset");
  if (!asset) {
    return NextResponse.json({ error: "missing_asset" }, { status: 400 });
  }
  const target = path.join(repoRoot(), "data", "realestate", "normalized", `${asset}.csv`);
  try {
    const text = await fs.readFile(target, "utf-8");
    const lines = text.trim().split("\n");
    const rows = lines.slice(1).map((line) => {
      const [date, value] = line.split(",");
      return { date, value: value ? Number(value) : null };
    });
    return NextResponse.json(rows);
  } catch {
    return NextResponse.json({ error: "series_not_found" }, { status: 404 });
  }
}
