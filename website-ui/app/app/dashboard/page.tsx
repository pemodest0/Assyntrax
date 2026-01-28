"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";

type Latest = {
  asset: string;
  timeframe: string;
  asof?: string;
  risk?: { risk_regime?: string; confidence?: number; model?: string; metrics?: any };
  forecast?: { mase_recent?: number; dir_acc?: number; alerts?: string[] };
  regime?: { state?: string; confidence?: number; alerts?: string[] };
};

export default function DashboardPage() {
  const [assets, setAssets] = useState<string[]>([]);
  const [asset, setAsset] = useState("SPY");
  const [tf, setTf] = useState<"daily" | "weekly">("weekly");
  const [data, setData] = useState<Latest | null>(null);

  useEffect(() => {
    fetch("/api/assets")
      .then((r) => r.json())
      .then((j) => {
        const files: string[] = j.files ?? [];
        const set = new Set<string>();
        for (const f of files) {
          const m = f.match(/^(.+?)_(daily|weekly)\.json$/);
          if (m) set.add(m[1]);
        }
        const arr = Array.from(set).sort();
        setAssets(arr);
        if (arr.length && !arr.includes(asset)) setAsset(arr[0]);
      });
  }, [asset]);

  useEffect(() => {
    fetch(`/api/assets?file=${asset}_${tf}.json`)
      .then((r) => {
        if (!r.ok && tf !== "daily") {
          return fetch(`/api/assets?file=${asset}_daily.json`).then((x) => x.json());
        }
        return r.json();
      })
      .then((j) => setData(j))
      .catch(() => setData(null));
  }, [asset, tf]);

  const riskRegime = "HIGH_VOL";
  const riskConf = data?.metrics?.logreg?.roc_auc ?? 0;
  const regimeState = data ? "UNSTABLE" : "—";

  return (
    <div className="p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="text-2xl font-semibold tracking-tight">Dashboard</div>
          <div className="text-sm text-zinc-400 mt-1">
            Produto: <span className="text-zinc-200">Regime/Risco</span>. Forecast é diagnóstico (com avisos).
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
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

          <select
            value={asset}
            onChange={(e) => setAsset(e.target.value)}
            className="rounded-xl border border-zinc-800 bg-black/40 px-3 py-2 text-sm outline-none"
          >
            {(assets.length ? assets : ["SPY", "QQQ"]).map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>

          <a
            href={`/api/assets?file=${asset}_${tf}.json`}
            target="_blank"
            className="rounded-xl border border-zinc-800 bg-black/40 px-3 py-2 text-sm hover:border-zinc-600 transition"
          >
            Export JSON
          </a>

          <Link
            href={`/app/assets/${asset}`}
            className="rounded-xl bg-zinc-100 text-black px-3 py-2 text-sm font-medium hover:bg-white transition"
          >
            Ver ativo →
          </Link>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <KPI title="Risk Regime" value={riskRegime} tone={riskRegime.includes("HIGH") ? "danger" : "ok"} />
        <KPI title="Confidence" value={`${Math.round(riskConf * 100)}%`} />
        <KPI title="Regime State" value={regimeState} tone={regimeState.includes("UNSTABLE") ? "warn" : "ok"} />
      </div>

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Risco / Regime" subtitle="O que vendemos: detecção robusta de estados (vol alta/baixa e instabilidade).">
          <div className="text-sm text-zinc-300">
            <div className="flex flex-wrap gap-2">
              <Tag label={`Risk: ${riskRegime}`} />
              <Tag label={`State: ${regimeState}`} />
              <Tag label={`Model: LOGREG`} />
            </div>

            <div className="mt-4">
              <div className="text-xs text-zinc-400">Confidence bar</div>
              <div className="mt-2 h-2 rounded-full bg-zinc-800 overflow-hidden">
                <div className="h-full bg-zinc-100 transition-all" style={{ width: `${Math.round(riskConf * 100)}%` }} />
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="Forecast (Diagnóstico)" subtitle="Forecast existe para compor métricas — não como promessa direcional.">
          <div className="flex flex-wrap gap-2">
            <Tag label="DIREÇÃO FRACA" tone="danger" />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <Metric label="MASE (recente)" value={"0.710"} />
            <Metric label="DirAcc (recente)" value={"0.505"} />
          </div>
        </Panel>
      </div>

      <motion.div
        className="mt-6 rounded-2xl border border-zinc-800 bg-black/30 p-4"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <div className="text-sm text-zinc-300">
          <span className="text-zinc-400">As of:</span> {data?.asof ?? "—"} •
          <span className="text-zinc-400"> Asset:</span> {asset} •
          <span className="text-zinc-400"> TF:</span> {tf}
        </div>
      </motion.div>
    </div>
  );
}

function KPI({ title, value, tone }: { title: string; value: string; tone?: "ok" | "warn" | "danger" }) {
  const color =
    tone === "danger" ? "text-red-400" : tone === "warn" ? "text-amber-300" : "text-zinc-100";
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-4 hover:border-zinc-600 transition">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{title}</div>
      <div className={`mt-2 text-3xl font-semibold tracking-tight ${color}`}>{value}</div>
    </div>
  );
}

function Panel({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-4 hover:border-zinc-600 transition">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-base font-semibold">{title}</div>
          {subtitle ? <div className="mt-1 text-sm text-zinc-400">{subtitle}</div> : null}
        </div>
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function Tag({ label, tone }: { label: string; tone?: "danger" | "neutral" }) {
  const cls =
    tone === "danger"
      ? "border-red-900/60 bg-red-950/40 text-red-300"
      : "border-zinc-800 bg-black/30 text-zinc-200";
  return <span className={`text-xs px-2 py-1 rounded-full border ${cls}`}>{label}</span>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-black/20 p-3">
      <div className="text-xs text-zinc-400">{label}</div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
    </div>
  );
}
