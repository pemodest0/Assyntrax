"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { nameForAsset } from "@/lib/assetNames";

function fmt(n?: number, digits = 2) {
  if (n == null || Number.isNaN(n)) return "--";
  return n.toFixed(digits);
}

function LineChart({ data, valueKey, label }: { data: any[]; valueKey: string; label: string }) {
  const points = useMemo(() => {
    const vals = data.map((d) => Number(d[valueKey])).filter((v) => Number.isFinite(v));
    if (!vals.length) return [] as { x: number; y: number }[];
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const span = max - min || 1;
    return data.map((d, i) => ({
      x: i / (Math.max(data.length - 1, 1)) * 100,
      y: 100 - ((Number(d[valueKey]) - min) / span) * 100,
    }));
  }, [data, valueKey]);

  if (!points.length) {
    return <div className="text-xs text-zinc-500">Sem dados para {label}.</div>;
  }

  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  return (
    <svg viewBox="0 0 100 100" className="h-64 w-full">
      <path d={path} fill="none" stroke="#60a5fa" strokeWidth="1.2" />
    </svg>
  );
}

export default function AtivoDetalhePage() {
  const params = useParams();
  const search = useSearchParams();
  const asset = Array.isArray(params?.ativo) ? params?.ativo[0] : params?.ativo;
  const tf = search?.get("tf") || "weekly";

  const [series, setSeries] = useState<any[]>([]);
  const [info, setInfo] = useState<any | null>(null);
  const [report, setReport] = useState<string>("");

  useEffect(() => {
    if (!asset) return;
    fetch(`/api/graph/series-batch?assets=${encodeURIComponent(String(asset))}&tf=${tf}&limit=260`)
      .then((r) => r.json())
      .then((data) => setSeries(data?.[asset as string] || []))
      .catch(() => setSeries([]));

    fetch(`/api/files/latest_graph/assets/${asset}_${tf}.json`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setInfo(data))
      .catch(() => setInfo(null));

    fetch(`/api/files/latest_graph/assets/${asset}_${tf}_report.md`)
      .then((r) => (r.ok ? r.text() : ""))
      .then((text) => setReport(text))
      .catch(() => setReport(""));
  }, [asset, tf]);

  if (!asset) {
    return <div className="text-sm text-zinc-400">Ativo não encontrado.</div>;
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">{asset}</h1>
        <p className="text-sm text-zinc-400">{nameForAsset(String(asset))}</p>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
          <div className="text-xs text-zinc-500">Regime atual</div>
          <div className="text-lg font-semibold">{info?.state?.label || "--"}</div>
          <div className="text-xs text-zinc-500">Confiança</div>
          <div className="text-sm">{fmt(info?.state?.confidence, 2)}</div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
          <div className="text-xs text-zinc-500">Qualidade do grafo</div>
          <div className="text-lg font-semibold">{fmt(info?.quality?.score, 2)}</div>
          <div className="text-xs text-zinc-500">Escape</div>
          <div className="text-sm">{fmt(info?.metrics?.escape_prob, 2)}</div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
          <div className="text-xs text-zinc-500">Alertas</div>
          <div className="flex flex-wrap gap-2 pt-2 text-xs">
            {(info?.alerts || []).length ? (
              info.alerts.map((a: string) => (
                <span key={a} className="rounded-full border border-zinc-700 px-2 py-1 text-zinc-200">
                  {a}
                </span>
              ))
            ) : (
              <span className="text-zinc-500">Sem alertas</span>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-black/30 p-4">
        <div className="text-sm font-semibold">Curva de preço</div>
        <LineChart data={series} valueKey="price" label="Preço" />
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-black/30 p-4">
        <div className="text-sm font-semibold">Confiança do regime</div>
        <LineChart data={series} valueKey="confidence" label="Confiança" />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: "Timeline de regimes", file: "timeline_regime.png" },
          { label: "Embedding 2D", file: "embedding_2d.png" },
          { label: "Matriz de transição", file: "transition_matrix.png" },
        ].map((item) => (
          <div key={item.file} className="rounded-xl border border-zinc-800 bg-black/40 p-3">
            <div className="text-xs text-zinc-400 mb-2">{item.label}</div>
            <img
              className="w-full rounded-lg border border-zinc-800"
              alt={item.label}
              src={`/api/files/latest_graph/assets/${asset}_${tf}_plots/${item.file}`}
            />
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-black/30 p-4">
        <div className="text-sm font-semibold">Relatório</div>
        <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap text-xs text-zinc-200">
          {report || "Relatório não disponível."}
        </pre>
      </div>
    </div>
  );
}
