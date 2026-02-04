"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

type IndexFile = {
  rel_path: string;
  filename: string;
  size_bytes: number;
  mtime_iso: string;
  run_id: string;
  asset: string;
  freq?: string;
  artifact_type: string;
  tags?: string[];
  metrics?: Record<string, any>;
};

type IndexPayload = {
  generated_at?: string;
  assets: string[];
  tags: string[];
  runs: Record<string, { files: number; assets: string[]; tags: string[] }>;
  files: IndexFile[];
  metrics?: Record<string, Record<string, Record<string, any>>>;
};

export default function AssetDetailPage() {
  const params = useParams();
  const asset = (params?.asset as string) ?? "";
  const [tf, setTf] = useState<"daily" | "weekly">("weekly");
  const [index, setIndex] = useState<IndexPayload | null>(null);

  useEffect(() => {
    fetch("/api/index")
      .then((r) => r.json())
      .then((j) => setIndex(j))
      .catch(() => setIndex(null));
  }, []);

  const files = useMemo(() => {
    const list = index?.files || [];
    return list.filter((f) => f.asset === asset && (f.freq || "unknown") === tf);
  }, [index, asset, tf]);

  const images = useMemo(() => files.filter((f) => f.artifact_type === "image").slice(0, 8), [files]);
  const reports = useMemo(
    () => files.filter((f) => f.artifact_type === "pdf" || f.artifact_type === "md").slice(0, 6),
    [files]
  );

  const metrics = useMemo(() => {
    const metricsIndex = index?.metrics || {};
    const runKeys = Object.keys(metricsIndex);
    const rows: Record<string, any>[] = [];
    for (const rk of runKeys) {
      const assets = metricsIndex[rk] || {};
      const freqs = assets[asset] || {};
      const row = freqs[tf];
      if (row) rows.push(row);
    }
    const agg = (key: string) => {
      const vals = rows.map((r) => r?.[key]).filter((v) => typeof v === "number");
      if (!vals.length) return null;
      return vals.reduce((a, b) => a + b, 0) / vals.length;
    };
    return {
      mase: agg("mase"),
      dir_acc: agg("dir_acc"),
      roc_auc: agg("roc_auc"),
      f1: agg("f1"),
    };
  }, [index, asset, tf]);

  const usage = useMemo(() => {
    if (!metrics.mase) return "No data";
    if (metrics.mase > 1.1) return "Avoid";
    if (metrics.mase > 0.95) return "Caution";
    return "Use";
  }, [metrics.mase]);

  return (
    <div className="p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-2xl font-semibold tracking-tight">{asset}</div>
          <div className="text-sm text-zinc-400 mt-1">Asset diagnostics from results index</div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-xl border border-zinc-800 bg-black/40 p-1">
            <button
              onClick={() => setTf("weekly")}
              className={`px-3 py-1.5 rounded-lg text-sm transition ${
                tf === "weekly" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Weekly
            </button>
            <button
              onClick={() => setTf("daily")}
              className={`px-3 py-1.5 rounded-lg text-sm transition ${
                tf === "daily" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Daily
            </button>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card title="MASE" value={formatNum(metrics.mase)} subtitle="Lower is better" />
        <Card title="DirAcc" value={formatNum(metrics.dir_acc)} subtitle="Directional accuracy" />
        <Card title="ROC-AUC" value={formatNum(metrics.roc_auc)} subtitle="Classification quality" />
        <Card title="F1" value={formatNum(metrics.f1)} subtitle="Balanced score" />
      </div>

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Key images">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {images.map((f) => (
              <div key={f.rel_path} className="rounded-xl border border-zinc-800 bg-black/40 p-3">
                <div className="text-xs uppercase text-zinc-500">{f.run_id}</div>
                <div className="mt-2 text-sm font-semibold text-zinc-100 break-all">{f.filename}</div>
                <img
                  src={`/api/files/${f.rel_path}`}
                  alt={f.filename}
                  className="mt-3 h-28 w-full rounded-lg object-cover"
                />
              </div>
            ))}
            {!images.length ? <div className="text-sm text-zinc-500">No images found.</div> : null}
          </div>
        </Panel>
        <Panel title="Reports & evidence">
          <div className="space-y-3">
            {reports.map((f) => (
              <a
                key={f.rel_path}
                href={`/api/files/${f.rel_path}`}
                target="_blank"
                className="block rounded-xl border border-zinc-800 bg-black/40 p-3 hover:border-cyan-400/50 transition"
              >
                <div className="text-xs uppercase text-zinc-500">{f.artifact_type}</div>
                <div className="mt-1 text-sm font-semibold text-zinc-100 break-all">{f.filename}</div>
                <div className="mt-1 text-xs text-zinc-400">{f.run_id}</div>
              </a>
            ))}
            {!reports.length ? <div className="text-sm text-zinc-500">No reports found.</div> : null}
          </div>
        </Panel>
      </div>

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Recommended usage">
          <div className="text-3xl font-semibold tracking-tight">{usage}</div>
          <div className="text-sm text-zinc-400 mt-2">
            Simple rule based on MASE thresholds from indexed metrics.
          </div>
        </Panel>
        <Panel title="Index coverage">
          <div className="text-sm text-zinc-400">
            Files for {asset} ({tf}): {files.length}
          </div>
        </Panel>
      </div>

      <div className="mt-6 rounded-2xl border border-zinc-800 bg-zinc-950/30 p-4 text-sm text-zinc-400">
        Index updated: {index?.generated_at ?? "—"} • Timeframe: {tf}
      </div>
    </div>
  );
}

function Card({ title, value, subtitle }: { title: string; value: string; subtitle?: string }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-4">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{title}</div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">{value}</div>
      {subtitle ? <div className="mt-1 text-xs text-zinc-500">{subtitle}</div> : null}
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-4">
      <div className="text-base font-semibold">{title}</div>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function formatNum(value: number | null) {
  if (value === null || Number.isNaN(value)) return "—";
  return value.toFixed(3);
}
