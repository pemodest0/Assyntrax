import { NextResponse } from "next/server";
import { findLatestApiRecords, readJsonlWithValidationGate } from "@/lib/server/data";

export async function GET() {
  const apiPath = await findLatestApiRecords();
  if (!apiPath) {
    return NextResponse.json({ error: "no api_records found" }, { status: 404 });
  }
  const records = await readJsonlWithValidationGate(apiPath);
  const total = records.length || 1;
  const useForecast = records.filter((r) => r.use_forecast_bool).length / total;
  const validatedPct =
    records.filter((r) => (r.signal_status || "").toLowerCase() === "validated").length / total;
  const warnings = new Map<string, number>();
  const regimes = new Map<string, number>();

  for (const r of records) {
    if (Array.isArray(r.warnings)) {
      for (const w of r.warnings) {
        warnings.set(w, (warnings.get(w) || 0) + 1);
      }
    }
    const reg = r.regime_label || r.regime || r.state?.label;
    if (reg) {
      regimes.set(reg, (regimes.get(reg) || 0) + 1);
    }
  }

  return NextResponse.json({
    use_forecast_pct: useForecast,
    validated_pct: validatedPct,
    warnings: Array.from(warnings.entries()).map(([code, count]) => ({ code, count })),
    regimes: Array.from(regimes.entries()).map(([label, count]) => ({ label, count })),
  });
}
