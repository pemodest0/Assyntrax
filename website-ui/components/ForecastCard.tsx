"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAsset } from "@/lib/asset-context";
import LoadingSkeleton from "./LoadingSkeleton";

const demo = {
  p10: 476.2,
  p50: 481.0,
  p90: 489.5,
  model: "ARIMA",
  mase: 0.71,
  dir_acc: 0.505,
  forecast_conf: 0.41,
  alerts: ["DIRECAO_FRACA"],
};

export default function ForecastCard() {
  const { asset, timeframe } = useAsset();
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState(demo);

  useEffect(() => {
    fetch(`/api/latest?asset=${asset}&timeframe=${timeframe}`)
      .then((r) => r.json())
      .then((data) => {
        setState({
          p10: data.y_pred_p10 ?? demo.p10,
          p50: data.y_pred_p50 ?? demo.p50,
          p90: data.y_pred_p90 ?? demo.p90,
          model: data.model_name ?? "MODEL",
          mase: data.mase_6m ?? demo.mase,
          dir_acc: data.diracc_6m ?? demo.dir_acc,
          forecast_conf: data.forecast_confidence ?? demo.forecast_conf,
          alerts: data.warnings ?? demo.alerts,
        });
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [asset, timeframe]);

  if (loading) return <LoadingSkeleton />;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <Card className="rounded-2xl bg-zinc-900/60 border border-zinc-800 shadow-lg backdrop-blur hover:border-zinc-600 transition opacity-80">
      <CardHeader className="flex-row items-start justify-between space-y-0">
        <div className="space-y-1">
          <CardTitle className="text-lg">Forecast (Diagnóstico)</CardTitle>
          <p className="text-sm text-zinc-400">
            Sempre comparar com naïve. Direção não é promessa de produto.
          </p>
        </div>
        <Badge variant="secondary">{demo.model}</Badge>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl border border-zinc-800 p-4">
            <div className="text-xs text-zinc-500">p10</div>
            <div className="text-xl font-semibold mt-1">{demo.p10.toFixed(2)}</div>
          </div>
          <div className="rounded-xl border border-zinc-800 p-4">
            <div className="text-xs text-zinc-500">p50</div>
            <div className="text-xl font-semibold mt-1">{demo.p50.toFixed(2)}</div>
          </div>
          <div className="rounded-xl border border-zinc-800 p-4">
            <div className="text-xs text-zinc-500">p90</div>
            <div className="text-xl font-semibold mt-1">{demo.p90.toFixed(2)}</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">MASE: {state.mase.toFixed(3)}</Badge>
          <Badge variant="outline">DirAcc: {state.dir_acc.toFixed(3)}</Badge>
          <Badge variant="outline">Conf: {(state.forecast_conf * 100).toFixed(0)}%</Badge>
          {state.alerts.map((a) => (
            <Badge key={a} variant="destructive">
              {a}
            </Badge>
          ))}
        </div>
      </CardContent>
      </Card>
    </motion.div>
  );
}
