"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { nameForAsset } from "@/lib/assetNames";

const regimeColor: Record<string, string> = {
  STABLE: "bg-emerald-500/20 text-emerald-200 border-emerald-500/40",
  TRANSITION: "bg-amber-500/20 text-amber-200 border-amber-500/40",
  UNSTABLE: "bg-rose-500/20 text-rose-200 border-rose-500/40",
  NOISY: "bg-zinc-500/20 text-zinc-200 border-zinc-500/40",
};

function fmt(n?: number, digits = 2) {
  if (n == null || Number.isNaN(n)) return "--";
  return n.toFixed(digits);
}

export default function AtivosPage() {
  const [tf, setTf] = useState("weekly");
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetch(`/api/graph/universe?tf=${tf}`)
      .then((r) => r.json())
      .then((data) => {
        if (!alive) return;
        setRows(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => {
        if (!alive) return;
        setRows([]);
        setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [tf]);

  const filtered = useMemo(() => {
    const q = query.trim().toUpperCase();
    if (!q) return rows;
    return rows.filter((r) => String(r.asset || "").toUpperCase().includes(q));
  }, [rows, query]);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Painel de Ativos</h1>
          <p className="text-sm text-zinc-400">
            Diagnóstico por ativo com regime atual, confiança e alertas.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-black/40 px-3 py-2 text-sm">
            <span className="text-zinc-400">Frequência</span>
            <select
              className="bg-transparent text-zinc-100 outline-none"
              value={tf}
              onChange={(e) => setTf(e.target.value)}
            >
              <option value="weekly">Semanal</option>
              <option value="daily">Diário</option>
            </select>
          </div>
          <input
            className="w-full rounded-xl border border-zinc-800 bg-black/40 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500"
            placeholder="Buscar ativo"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </header>

      <div className="rounded-2xl border border-zinc-800 bg-black/30 p-4">
        {loading ? (
          <div className="text-sm text-zinc-400">Carregando ativos...</div>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-zinc-500">
                <tr>
                  <th className="py-2">Ativo</th>
                  <th className="py-2">Regime</th>
                  <th className="py-2">Confiança</th>
                  <th className="py-2">Qualidade</th>
                  <th className="py-2">Recomendação</th>
                  <th className="py-2">Alertas</th>
                  <th className="py-2">Detalhes</th>
                </tr>
              </thead>
              <tbody className="text-zinc-100">
                {filtered.map((r) => {
                  const label = r?.state?.label || "--";
                  const conf = r?.state?.confidence ?? r?.state?.conf;
                  const quality = r?.quality?.score;
                  const cls = regimeColor[label] || "bg-zinc-500/20 text-zinc-200 border-zinc-500/40";
                  return (
                    <tr key={`${r.asset}-${r.timeframe}`} className="border-t border-zinc-800/60">
                      <td className="py-3">
                        <div className="font-medium">{r.asset}</div>
                        <div className="text-xs text-zinc-400">{nameForAsset(r.asset)}</div>
                      </td>
                      <td className="py-3">
                        <span className={`inline-flex items-center rounded-full border px-2 py-1 text-xs ${cls}`}>
                          {label}
                        </span>
                      </td>
                      <td className="py-3">{fmt(conf, 2)}</td>
                      <td className="py-3">{fmt(quality, 2)}</td>
                      <td className="py-3">{r.recommendation || "--"}</td>
                      <td className="py-3">
                        <div className="flex flex-wrap gap-1">
                          {(r.alerts || []).slice(0, 3).map((a: string) => (
                            <span
                              key={a}
                              className="rounded-full border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-300"
                            >
                              {a}
                            </span>
                          ))}
                          {(r.alerts || []).length === 0 && (
                            <span className="text-xs text-zinc-500">Sem alertas</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3">
                        <Link
                          className="text-xs text-emerald-300 hover:text-emerald-200"
                          href={`/ativos/${encodeURIComponent(r.asset)}?tf=${tf}`}
                        >
                          Ver detalhes →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
