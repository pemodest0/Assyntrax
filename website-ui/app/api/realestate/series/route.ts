import { NextResponse } from "next/server";
import { buildRealEstateAssetPayload } from "@/lib/server/realestate";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const asset = searchParams.get("asset");
  if (!asset) {
    return NextResponse.json({ error: "missing_asset" }, { status: 400 });
  }
  try {
    const payload = await buildRealEstateAssetPayload(asset);
    return NextResponse.json(payload.data.series.P);
  } catch (err) {
    return NextResponse.json(
      {
        error: "series_not_found",
        reason: err instanceof Error ? err.message : "unknown_error",
      },
      { status: 404 }
    );
  }
}
