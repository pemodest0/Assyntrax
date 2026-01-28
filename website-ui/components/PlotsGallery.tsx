"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import LoadingSkeleton from "./LoadingSkeleton";

type FigurePayload = {
  walkforward: { files: string[]; base: string };
  risk: { files: string[]; base: string };
};

export default function PlotsGallery() {
  const [loading, setLoading] = useState(true);
  const [payload, setPayload] = useState<FigurePayload>({
    walkforward: { files: [], base: "/data/plots/walkforward" },
    risk: { files: [], base: "/data/risk" },
  });

  useEffect(() => {
    fetch("/api/figures")
      .then((r) => r.json())
      .then((data) => {
        setPayload(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <Card className="rounded-2xl bg-zinc-900/80 border border-zinc-800 shadow-lg backdrop-blur hover:border-zinc-600 transition">
        <CardHeader>
          <CardTitle className="text-lg">Plots & Figures</CardTitle>
        </CardHeader>
        <CardContent>
          {payload.walkforward.files.length === 0 && payload.risk.files.length === 0 ? (
            <div className="text-sm text-zinc-400">Nenhuma figura encontrada.</div>
          ) : (
            <div className="space-y-6">
              <div>
                <div className="text-xs uppercase text-zinc-500 mb-2">Walk-forward</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {payload.walkforward.files.slice(0, 6).map((f) => (
                    <div key={f} className="rounded-xl border border-zinc-800 p-2">
                      <img src={`${payload.walkforward.base}/${f}`} alt={f} className="rounded-lg" />
                      <div className="text-xs text-zinc-500 mt-2 truncate">{f}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-xs uppercase text-zinc-500 mb-2">Risk Regime</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {payload.risk.files.slice(0, 6).map((f) => (
                    <div key={f} className="rounded-xl border border-zinc-800 p-2">
                      <img src={`${payload.risk.base}/${f}`} alt={f} className="rounded-lg" />
                      <div className="text-xs text-zinc-500 mt-2 truncate">{f}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
