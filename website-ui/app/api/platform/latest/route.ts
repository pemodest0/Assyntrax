import { NextResponse } from "next/server";
import { readPlatformDbRelease, readPlatformDbSnapshot } from "@/lib/server/data";

export const dynamic = "force-dynamic";

export async function GET() {
  const [snapshot, release] = await Promise.all([readPlatformDbSnapshot(), readPlatformDbRelease()]);
  return NextResponse.json(
    {
      ok: true,
      snapshot,
      release,
    },
    { headers: { "Cache-Control": "no-store" } }
  );
}

