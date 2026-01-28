"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAsset } from "@/lib/asset-context";
import LoadingSkeleton from "./LoadingSkeleton";

const demo = {
  risk_regime: "HIGH_VOL",
  risk_conf: 0.93,
  regime_state: "UNSTABLE",
  regime_conf: 0.82,
  model: "RF",
};

function pct(x: number) {
  return `${Math.round(x * 100)}%`;
}

export default function RegimeCard() {
  const { asset, timeframe } = useAsset();
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState(demo);

  useEffect(() => {
    const file = `${asset}_${timeframe}.json`;
    fetch(`/api/assets?file=${file}`)
      .then((r) => r.json())
      .then((data) => {
        const metrics = data.metrics || {};
        const best = Object.entries(metrics).sort((a: any, b: any) => (b[1]?.roc_auc ?? 0) - (a[1]?.roc_auc ?? 0))[0];
        const bestModel = best ? best[0] : "model";
        const bestAuc = best ? best[1].roc_auc ?? 0.5 : 0.5;
        setState({
          risk_regime: "HIGH_VOL",
          risk_conf: Number(bestAuc) || 0.5,
          regime_state: "UNSTABLE",
          regime_conf: Number(bestAuc) || 0.5,
          model: String(bestModel).toUpperCase(),
        });
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [asset, timeframe]);

  if (loading) return <LoadingSkeleton />;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <Card className="rounded-2xl bg-zinc-900/80 border border-zinc-800 shadow-lg backdrop-blur hover:border-zinc-600 transition">
        <CardHeader className="space-y-1">
          <CardTitle className="text-lg">Risco / Regime Atual</CardTitle>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Risk: {demo.risk_regime}</Badge>
            <Badge variant="outline">Regime: {demo.regime_state}</Badge>
            <Badge variant="outline">Model: {demo.model}</Badge>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4">
          <div className="rounded-xl border border-zinc-800 p-4">
            <div className="text-xs text-zinc-500">Confiança (Risco)</div>
            <div className="text-2xl font-semibold mt-1 text-zinc-100">{pct(demo.risk_conf)}</div>
          </div>
          <div className="rounded-xl border border-zinc-800 p-4">
            <div className="text-xs text-zinc-500">Confiança (Regime)</div>
            <div className="text-2xl font-semibold mt-1 text-zinc-100">{pct(demo.regime_conf)}</div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
