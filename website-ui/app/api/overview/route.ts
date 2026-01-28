import { NextResponse } from "next/server";
import { findLatestApiRecords, readJsonl } from "@/lib/server/data";

export async function GET() {
  const apiPath = await findLatestApiRecords();
  if (!apiPath) {
    return NextResponse.json({ error: "no api_records found" }, { status: 404 });
  }
  const records = await readJsonl(apiPath);
  const total = records.length || 1;
  const useForecast = records.filter((r) => r.use_forecast_bool).length / total;
  const warnings = new Map<string, number>();
  const regimes = new Map<string, number>();

  for (const r of records) {
    if (Array.isArray(r.warnings)) {
      for (const w of r.warnings) {
        warnings.set(w, (warnings.get(w) || 0) + 1);
      }
    }
    if (r.regime_label) {
      regimes.set(r.regime_label, (regimes.get(r.regime_label) || 0) + 1);
    }
  }

  return NextResponse.json({
    use_forecast_pct: useForecast,
    warnings: Array.from(warnings.entries()).map(([code, count]) => ({ code, count })),
    regimes: Array.from(regimes.entries()).map(([label, count]) => ({ label, count })),
  });
}
