import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { resultsRoot } from "@/lib/server/results";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const asset = searchParams.get("asset");
  const tf = searchParams.get("tf") || "weekly";
  if (!asset) {
    return NextResponse.json({ error: "missing_asset" }, { status: 400 });
  }
  const file = path.join(resultsRoot(), "latest_graph", "assets", `${asset}_${tf}.json`);
  try {
    const raw = await fs.readFile(file, "utf-8");
    return NextResponse.json(JSON.parse(raw));
  } catch (err: any) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }
}
