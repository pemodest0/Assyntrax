"use client";

import { useMemo, useState } from "react";

type UniverseAsset = {
  asset: string;
  group?: string;
};

type Props = {
  assets: UniverseAsset[];
  selected: string[];
  onSelectedChange: (assets: string[]) => void;
  sector: string;
  onSectorChange: (value: string) => void;
  timeframe: string;
  onTimeframeChange: (value: string) => void;
  rangePreset: string;
  onRangePresetChange: (value: string) => void;
  normalize: boolean;
  onNormalizeChange: (value: boolean) => void;
  showRegimeBands: boolean;
  onShowRegimeBandsChange: (value: boolean) => void;
  smoothing: "none" | "ema_short" | "ema_long";
  onSmoothingChange: (value: "none" | "ema_short" | "ema_long") => void;
  sectors?: Array<{ value: string; label: string }>;
};

const groupLabels: Record<string, string> = {
  crypto: "Cripto",
  volatility: "Volatilidade",
  commodities_broad: "Commodities",
  energy: "Energia",
  metals: "Metais",
  bonds_rates: "Juros/Bonds",
  fx: "Moedas",
  equities_us_broad: "Equities US Broad",
  equities_us_sectors: "Equities US Setores",
  equities_international: "Equities Internacionais",
  realestate: "Imobiliário",
};

export default function DashboardFilters(props: Props) {
  const {
    assets,
    selected,
    onSelectedChange,
    sector,
    onSectorChange,
    timeframe,
    onTimeframeChange,
    rangePreset,
    onRangePresetChange,
    normalize,
    onNormalizeChange,
    showRegimeBands,
    onShowRegimeBandsChange,
    smoothing,
    onSmoothingChange,
    sectors,
  } = props;

  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return assets
      .filter((a) => (sectors && sectors.length ? true : sector === "all" || (a.group || "") === sector))
      .filter((a) => !q || a.asset.toLowerCase().includes(q) || (a.group || "").toLowerCase().includes(q))
      .slice(0, 100);
  }, [assets, query, sector, sectors]);

  const sectorsFromAssets = useMemo(() => {
    const set = new Set<string>();
    assets.forEach((a) => {
      if (a.group) set.add(a.group);
    });
    return ["all", ...Array.from(set).sort()];
  }, [assets]);

  const toggleAsset = (asset: string) => {
    if (selected.includes(asset)) {
      onSelectedChange(selected.filter((a) => a !== asset));
      return;
    }
    if (selected.length >= 12) return;
    onSelectedChange([...selected, asset]);
  };

  return (
    <div className="sticky top-2 z-20 rounded-xl border border-zinc-800 bg-zinc-950/95 p-4 md:p-5 backdrop-blur-sm">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-7 gap-3">
        <div className="xl:col-span-2 relative">
          <button
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-sm"
            onClick={() => setOpen((v) => !v)}
            title="Selecionar ativos"
          >
            {selected.length ? `${selected.length} ativos selecionados` : "Selecionar ativos"}
          </button>
          {open ? (
            <div className="absolute mt-2 w-full max-h-72 overflow-auto rounded-lg border border-zinc-700 bg-zinc-950 p-2 shadow-xl">
              <input
                className="mb-2 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs"
                placeholder="Buscar ativo"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <div className="space-y-1">
                {filtered.map((a) => (
                  <label key={a.asset} className="flex items-center gap-2 rounded px-1 py-1 text-xs hover:bg-zinc-900">
                    <input
                      type="checkbox"
                      checked={selected.includes(a.asset)}
                      onChange={() => toggleAsset(a.asset)}
                      className="h-3 w-3 accent-cyan-400"
                    />
                    <span className="font-medium">{a.asset}</span>
                    <span className="text-zinc-500">{groupLabels[a.group || ""] || a.group || ""}</span>
                  </label>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <select
          value={sector}
          onChange={(e) => onSectorChange(e.target.value)}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          title="Filtrar por setor"
        >
          {(sectors && sectors.length ? sectors : sectorsFromAssets.map((s) => ({ value: s, label: s === "all" ? "Todos os setores" : groupLabels[s] || s }))).map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>

        <select
          value={timeframe}
          onChange={(e) => onTimeframeChange(e.target.value)}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
        >
          <option value="daily">Diario</option>
          <option value="weekly">Semanal</option>
        </select>

        <select
          value={rangePreset}
          onChange={(e) => onRangePresetChange(e.target.value)}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
        >
          <option value="30d">Ultimos 30d</option>
          <option value="90d">Ultimos 90d</option>
          <option value="180d">Ultimos 180d</option>
          <option value="1y">Ultimo 1y</option>
          <option value="all">Tudo</option>
        </select>

        <select
          value={smoothing}
          onChange={(e) => onSmoothingChange(e.target.value as "none" | "ema_short" | "ema_long")}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
        >
          <option value="none">Suavização: none</option>
          <option value="ema_short">Suavização: EMA curto</option>
          <option value="ema_long">Suavização: EMA longo</option>
        </select>

        <button
          className={`rounded-lg border px-3 py-2 text-sm ${normalize ? "border-cyan-400 text-cyan-300" : "border-zinc-700"}`}
          onClick={() => onNormalizeChange(!normalize)}
        >
          {normalize ? "Normalizar: ON" : "Normalizar: OFF"}
        </button>

        <button
          className={`rounded-lg border px-3 py-2 text-sm ${showRegimeBands ? "border-cyan-400 text-cyan-300" : "border-zinc-700"}`}
          onClick={() => onShowRegimeBandsChange(!showRegimeBands)}
        >
          {showRegimeBands ? "Bandas regime: ON" : "Bandas regime: OFF"}
        </button>
      </div>
    </div>
  );
}
