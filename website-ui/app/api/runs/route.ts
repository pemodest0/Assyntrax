import { NextResponse } from "next/server";
import { readIndex } from "@/lib/server/results";

export async function GET() {
  try {
    const index = await readIndex();
    const runs = index?.runs || {};
    return NextResponse.json({ runs });
  } catch {
    return NextResponse.json({ error: "results_index_not_found" }, { status: 404 });
  }
}
