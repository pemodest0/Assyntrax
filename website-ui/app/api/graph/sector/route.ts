import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { resultsRoot } from "@/lib/server/results";

const sectorMap: Record<string, string[]> = {
  finance: [
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
    "VTI",
    "VT",
    "RSP",
    "XLF",
    "KRE",
    "LQD",
    "HYG",
    "SHY",
    "IEF",
    "TLT",
    "TIP",
    "UUP",
    "FXE",
    "FXY",
    "VIX",
    "^VIX",
  ],
  logistics: [
    "USO",
    "DBC",
    "DBA",
    "XLE",
    "XOP",
    "XLB",
    "GLD",
    "SLV",
    "BTC-USD",
    "ETH-USD",
  ],
  realestate: ["XLRE"],
};

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const sector = searchParams.get("sector") || "finance";
  const tf = searchParams.get("tf") || "weekly";
  const file = path.join(resultsRoot(), "latest_graph", `universe_${tf}.json`);
  try {
    const raw = await fs.readFile(file, "utf-8");
    const data = JSON.parse(raw);
    const allowed = sectorMap[sector] || [];
    const filtered = allowed.length
      ? data.filter((r: any) => allowed.includes(r.asset))
      : data;
    return NextResponse.json(filtered);
  } catch (err: any) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }
}
