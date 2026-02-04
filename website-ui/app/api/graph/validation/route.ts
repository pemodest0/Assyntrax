import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

async function readJson(target: string) {
  const text = await fs.readFile(target, "utf-8");
  return JSON.parse(text);
}

export async function GET() {
  const base = path.join(repoRoot(), "results");
  const spectralPath = path.join(base, "graph_validation", "summary.json");
  const pccaPath = path.join(base, "graph_validation_pcca", "summary.json");
  try {
    const [spectral, pcca] = await Promise.all([readJson(spectralPath), readJson(pccaPath)]);
    return NextResponse.json({ spectral, pcca });
  } catch {
    return NextResponse.json({ error: "validation_not_found" }, { status: 404 });
  }
}
