import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export async function GET() {
  const target = path.join(repoRoot(), "results", "latest_graph", "sanity_summary.json");
  try {
    const text = await fs.readFile(target, "utf-8");
    return NextResponse.json(JSON.parse(text));
  } catch {
    return NextResponse.json({ error: "sanity_summary_not_found" }, { status: 404 });
  }
}
