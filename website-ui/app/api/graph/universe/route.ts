import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const tf = searchParams.get("tf") || "weekly";
  const file = tf === "daily" ? "universe_daily.json" : "universe_weekly.json";
  const target = path.join(repoRoot(), "results", "latest_graph", file);
  try {
    const text = await fs.readFile(target, "utf-8");
    return NextResponse.json(JSON.parse(text));
  } catch {
    return NextResponse.json({ error: "graph_universe_not_found" }, { status: 404 });
  }
}
