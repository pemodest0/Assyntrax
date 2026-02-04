import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const asset = searchParams.get("asset");
  const tf = searchParams.get("tf") || "daily";
  const target = searchParams.get("target") || "close";
  const horizon = searchParams.get("horizon") || "1";
  if (!asset) {
    return NextResponse.json({ error: "missing_asset" }, { status: 400 });
  }
  const targetPath = path.join(
    repoRoot(),
    "results",
    "latest_graph",
    "forecast_backtest",
    asset,
    tf,
    `${asset}_${tf}_${target}_h${horizon}.json`
  );
  try {
    const text = await fs.readFile(targetPath, "utf-8");
    return NextResponse.json(JSON.parse(text));
  } catch {
    return NextResponse.json({ error: "backtest_not_found" }, { status: 404 });
  }
}
