"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import LoadingSkeleton from "./LoadingSkeleton";
import { useAsset } from "@/lib/asset-context";

type Overview = {
  summary_cards?: {
    pct_assets_mase_lt_1?: number;
    pct_assets_dir_acc_gt_052?: number;
  };
};

const demo = {
  risk_regime: "HIGH_VOL",
  confidence: 0.62,
  mase: 0.71,
};

const pct = (x: number) => `${Math.round(x * 100)}%`;

function regimeColor(regime: string) {
  if (regime.includes("HIGH")) return "text-red-500";
  if (regime.includes("MID")) return "text-amber-400";
  return "text-emerald-400";
}

export default function KPIBar() {
  const { asset, timeframe } = useAsset();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<Overview | null>(null);

  useEffect(() => {
    fetch("/api/dashboard/overview")
      .then((r) => r.json())
      .then((data) => {
        setOverview(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;

  const masePct = overview?.summary_cards?.pct_assets_mase_lt_1 ?? 1;
  const dirPct = overview?.summary_cards?.pct_assets_dir_acc_gt_052 ?? 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="rounded-2xl bg-zinc-900/80 border border-zinc-800 p-5 shadow-lg backdrop-blur hover:border-zinc-600 transition"
      >
        <div className="text-xs uppercase text-zinc-500">Risk Regime — {asset} ({timeframe})</div>
        <div className={`text-4xl font-bold tracking-tight mt-2 ${regimeColor(demo.risk_regime)}`}>
          {demo.risk_regime.replace("_", " ")}
        </div>
        <div className="text-xs uppercase text-zinc-500 mt-2">RISK REGIME</div>
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.05 }}
        className="rounded-2xl bg-zinc-900/80 border border-zinc-800 p-5 shadow-lg backdrop-blur hover:border-zinc-600 transition"
      >
        <div className="text-xs uppercase text-zinc-500">MASE &gt; Naive</div>
        <div className="text-4xl font-bold tracking-tight mt-2 text-zinc-100">{pct(masePct)}</div>
        <div className="mt-3 h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
          <div className="h-full bg-emerald-500 transition-all" style={{ width: `${masePct * 100}%` }} />
        </div>
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="rounded-2xl bg-zinc-900/80 border border-zinc-800 p-5 shadow-lg backdrop-blur hover:border-zinc-600 transition"
      >
        <div className="text-xs uppercase text-zinc-500">DirAcc &gt; 0.52</div>
        <div className="text-4xl font-bold tracking-tight mt-2 text-zinc-100">{pct(dirPct)}</div>
        <div className="text-xs uppercase text-zinc-500 mt-2">consistência direcional</div>
      </motion.div>
    </div>
  );
}
