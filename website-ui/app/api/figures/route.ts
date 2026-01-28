import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export async function GET() {
  const root = repoRoot();
  const wfDir = path.join(root, "results", "finance_walkforward_all", "plots");
  const riskDir = path.join(root, "results", "finance_risk_all");

  const out = {
    walkforward: { base: "/data/plots/walkforward", files: [] as string[] },
    risk: { base: "/data/risk", files: [] as string[] },
  };

  try {
    const files = await fs.readdir(wfDir);
    out.walkforward.files = files.filter((f) => f.endsWith(".png") || f.endsWith(".jpg"));
  } catch {
    // ignore
  }

  try {
    const assets = await fs.readdir(riskDir);
    const files: string[] = [];
    for (const asset of assets) {
      const base = path.join(riskDir, asset);
      const cand = ["master_plot.png", "vol_prob_logreg.png"];
      for (const file of cand) {
        const p = path.join(base, file);
        try {
          await fs.access(p);
          files.push(`${asset}/${file}`);
        } catch {
          // ignore
        }
      }
    }
    out.risk.files = files;
  } catch {
    // ignore
  }

  return NextResponse.json(out);
}
