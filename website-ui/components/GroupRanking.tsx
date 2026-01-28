"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import LoadingSkeleton from "./LoadingSkeleton";

type GroupRow = {
  group: string;
  mean_mase: number;
  mean_dir_acc: number;
};

export default function GroupRanking() {
  const [loading, setLoading] = useState(true);
  const [groups, setGroups] = useState<GroupRow[]>([]);

  useEffect(() => {
    fetch("/api/dashboard/overview")
      .then((r) => r.json())
      .then((data) => {
        setGroups(data.groups || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <Card className="rounded-2xl bg-zinc-900/80 border border-zinc-800 shadow-lg backdrop-blur hover:border-zinc-600 transition">
      <CardHeader>
        <CardTitle className="text-lg">Ranking por Grupo</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 text-xs text-zinc-500 border-b border-zinc-800 pb-2">
          <div>Grupo</div>
          <div>MASE</div>
          <div>DirAcc</div>
        </div>
        {groups.map((g) => (
          <div key={g.group} className="grid grid-cols-3 py-3 text-sm border-b border-zinc-800 last:border-0">
            <div className="capitalize">{g.group.replaceAll("_", " ")}</div>
            <div>
              <div className="text-xs text-zinc-500">{g.mean_mase.toFixed(3)}</div>
              <div className="mt-2 h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full bg-amber-400/80"
                  style={{ width: `${Math.min(1, g.mean_mase) * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="text-xs text-zinc-500">{g.mean_dir_acc.toFixed(3)}</div>
              <div className="mt-2 h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full bg-emerald-400/80"
                  style={{ width: `${Math.min(1, g.mean_dir_acc) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </CardContent>
      </Card>
    </motion.div>
  );
}
