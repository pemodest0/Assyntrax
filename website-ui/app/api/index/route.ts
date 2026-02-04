import { NextResponse } from "next/server";
import { readIndex } from "@/lib/server/results";

export async function GET() {
  try {
    const index = await readIndex();
    return NextResponse.json(index);
  } catch {
    return NextResponse.json({ error: "results_index_not_found" }, { status: 404 });
  }
}
