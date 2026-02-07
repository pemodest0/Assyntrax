import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

async function readJson(rel: string) {
  const target = path.join(repoRoot(), rel);
  const text = await fs.readFile(target, "utf-8");
  return JSON.parse(text);
}

export async function GET() {
  try {
    const universe = await readJson("results/realestate/realestate_universe.json");
    const rqa = await readJson("results/realestate/rqa/rqa_summary.json");
    const forecast = await readJson(
      "results/realestate/forecast_by_regime/forecast_by_regime_summary.json"
    );
    return NextResponse.json({ universe, rqa, forecast });
  } catch {
    return NextResponse.json({ error: "realestate_summary_not_found" }, { status: 404 });
  }
}
