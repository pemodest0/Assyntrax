"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import LoadingSkeleton from "./LoadingSkeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type WarningRow = { code: string; count: number };

export default function WarningsPanel() {
  const [loading, setLoading] = useState(true);
  const [warnings, setWarnings] = useState<WarningRow[]>([]);

  useEffect(() => {
    fetch("/api/overview")
      .then((r) => r.json())
      .then((data) => {
        setWarnings(data.warnings || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <Card className="rounded-2xl bg-zinc-900/80 border border-zinc-800 shadow-lg backdrop-blur hover:border-zinc-600 transition">
      <CardHeader>
        <CardTitle className="text-lg">System Health</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {warnings.map((w) => (
          <div key={w.code} className="flex items-center justify-between">
            <div className="text-sm">{w.code}</div>
            <Badge variant={w.count > 50 ? "destructive" : "secondary"}>
              {w.count}
            </Badge>
          </div>
        ))}
      </CardContent>
      </Card>
    </motion.div>
  );
}
