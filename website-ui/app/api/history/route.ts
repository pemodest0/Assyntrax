import { NextResponse } from "next/server";
import { findLatestApiRecords, readJsonlWithValidationGate } from "@/lib/server/data";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const asset = searchParams.get("asset");
  const timeframe = searchParams.get("timeframe");
  const limit = parseInt(searchParams.get("limit") || "500", 10);
  const apiPath = await findLatestApiRecords();
  if (!apiPath) {
    return NextResponse.json({ error: "no_valid_run" }, { status: 503 });
  }
  const records = await readJsonlWithValidationGate(apiPath);
  let filtered = records;
  if (asset) filtered = filtered.filter((r) => r.asset === asset);
  if (timeframe) filtered = filtered.filter((r) => r.timeframe === timeframe);
  const sliced = filtered.slice(-limit);
  return NextResponse.json({ records: sliced });
}
