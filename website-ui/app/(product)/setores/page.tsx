"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { sectorMap, sectorLabels } from "@/lib/sectorMap";
import { nameForAsset } from "@/lib/assetNames";

export default function SetoresPage() {
  const [tf, setTf] = useState("weekly");
  const [rows, setRows] = useState<any[]>([]);
  const [sector, setSector] = useState<keyof typeof sectorMap>("finance");

  useEffect(() => {
    fetch(`/api/graph/universe?tf=${tf}`)
      .then((r) => r.json())
      .then((data) => setRows(Array.isArray(data) ? data : []))
      .catch(() => setRows([]));
  }, [tf]);

  const assets = sectorMap[sector] || [];
  const data = useMemo(() => rows.filter((r) => assets.includes(r.asset)), [rows, assets]);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Painel por Setores</h1>
          <p className="text-sm text-zinc-400">Agrupe ativos por setor e compare regimes.</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-xl border border-zinc-800 bg-black/40 px-3 py-2 text-sm"
            value={sector}
            onChange={(e) => setSector(e.target.value as keyof typeof sectorMap)}
          >
            {Object.keys(sectorMap).map((key) => (
              <option key={key} value={key}>
                {sectorLabels[key] || key}
              </option>
            ))}
          </select>
          <select
            className="rounded-xl border border-zinc-800 bg-black/40 px-3 py-2 text-sm"
            value={tf}
            onChange={(e) => setTf(e.target.value)}
          >
            <option value="weekly">Semanal</option>
            <option value="daily">Diário</option>
          </select>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {data.map((r) => (
          <div key={r.asset} className="rounded-xl border border-zinc-800 bg-black/40 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">{r.asset}</div>
                <div className="text-xs text-zinc-400">{nameForAsset(r.asset)}</div>
              </div>
              <div className="text-xs text-zinc-400">{r.state?.label || "--"}</div>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-zinc-400">
              <span>Conf: {r.state?.confidence?.toFixed?.(2) ?? "--"}</span>
              <span>Qual: {r.quality?.score?.toFixed?.(2) ?? "--"}</span>
            </div>
            <div className="mt-3">
              <Link
                className="text-xs text-emerald-300 hover:text-emerald-200"
                href={`/ativos/${encodeURIComponent(r.asset)}?tf=${tf}`}
              >
                Ver detalhes →
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
