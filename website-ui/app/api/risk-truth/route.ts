import { NextResponse } from "next/server";
import { readRiskTruthPanel } from "@/lib/server/data";

export async function GET() {
  const panel = await readRiskTruthPanel();
  return NextResponse.json(panel);
}

