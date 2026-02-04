import { NextResponse } from "next/server";
import { readIndex } from "@/lib/server/results";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const asset = searchParams.get("asset");
  const run = searchParams.get("run");
  const freq = searchParams.get("freq");
  const tag = searchParams.get("tag");
  const type = searchParams.get("type");

  try {
    const index = await readIndex();
    let files = Array.isArray(index?.files) ? index.files : [];
    if (asset) files = files.filter((f) => f.asset === asset);
    if (run) files = files.filter((f) => f.run_id === run);
    if (freq) files = files.filter((f) => (f.freq || "unknown") === freq);
    if (tag) files = files.filter((f) => (f.tags || []).includes(tag));
    if (type) files = files.filter((f) => f.artifact_type === type);
    return NextResponse.json({ files });
  } catch {
    return NextResponse.json({ error: "results_index_not_found" }, { status: 404 });
  }
}
