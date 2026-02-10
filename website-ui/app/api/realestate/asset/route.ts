import { NextResponse } from "next/server";
import {
  buildRealEstateAssetPayload,
  listRealEstateAssets,
  listRealEstateAssetMeta,
} from "@/lib/server/realestate";

function normalizeAssetName(input: string) {
  return input
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9_]/g, "_");
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const requested = searchParams.get("asset");
  try {
    const [assets, assetsMeta] = await Promise.all([
      listRealEstateAssets(),
      listRealEstateAssetMeta(),
    ]);
    if (!assets.length) {
      return NextResponse.json({ error: "realestate_assets_not_found" }, { status: 404 });
    }
    const requestedNorm = normalizeAssetName(requested || "");
    const asset =
      (requested && assets.find((a) => a === requested)) ||
      assets.find((a) => normalizeAssetName(a) === requestedNorm) ||
      assets[0];
    const payload = await buildRealEstateAssetPayload(asset);
    return NextResponse.json({
      asset,
      assets,
      assets_meta: assetsMeta,
      ...payload,
    });
  } catch (err) {
    return NextResponse.json(
      {
        error: "realestate_asset_failed",
        reason: err instanceof Error ? err.message : "unknown_error",
      },
      { status: 500 }
    );
  }
}
