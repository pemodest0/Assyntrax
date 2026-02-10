import { NextResponse } from "next/server";
import {
  buildRealEstateAssetPayload,
  listRealEstateAssets,
  listRealEstateAssetMeta,
} from "@/lib/server/realestate";

export async function GET() {
  try {
    const [assets, assetsMeta] = await Promise.all([
      listRealEstateAssets(),
      listRealEstateAssetMeta(),
    ]);
    if (!assets.length) {
      return NextResponse.json({ error: "realestate_summary_not_found" }, { status: 404 });
    }
    const rows = await Promise.all(assets.map(async (asset) => buildRealEstateAssetPayload(asset)));
    const summary = rows.map((r) => ({
      asset: r.data.asset,
      profile: r.data.profile,
      dynamic: {
        m: r.dynamic.m,
        tau: r.dynamic.tau,
        n_rows: r.dynamic.rows.length,
      },
      operational: r.operational,
    }));
    return NextResponse.json({ assets, assets_meta: assetsMeta, summary });
  } catch (err) {
    return NextResponse.json(
      {
        error: "realestate_summary_not_found",
        reason: err instanceof Error ? err.message : "unknown_error",
      },
      { status: 404 }
    );
  }
}
