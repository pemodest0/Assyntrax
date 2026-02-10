import { NextResponse } from "next/server";
import { readDashboardOverview } from "@/lib/server/data";

export async function GET() {
  try {
    const data = await readDashboardOverview();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "dashboard overview not found" }, { status: 404 });
  }
}
