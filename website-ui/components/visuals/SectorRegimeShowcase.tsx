"use client";

import { useEffect, useMemo, useState } from "react";
import RegimeField from "@/components/visuals/RegimeField";

const sectors = [
  {
    id: "energia",
    title: "Setor: Energia",
    subtitle: "Espaço de fase de carga, custo marginal e risco operacional.",
    hue: 185,
    accent: "rgba(34,211,238,0.92)",
    density: 132,
    speed: 0.28,
    regime: "Transição de custo e oferta",
    visual: "/visuals/hero-embedding.svg",
  },
  {
    id: "financas",
    title: "Setor: Finanças",
    subtitle: "Topologia de liquidez, volatilidade e fragilidade de spreads.",
    hue: 220,
    accent: "rgba(249,115,22,0.9)",
    density: 124,
    speed: 0.24,
    regime: "Regime sensível a risco de mercado",
    visual: "/visuals/hero-graph.svg",
  },
  {
    id: "imobiliario",
    title: "Setor: Imobiliário",
    subtitle: "Preço, liquidez, juros e crédito em dinâmica de baixa frequência.",
    hue: 276,
    accent: "rgba(168,85,247,0.9)",
    density: 112,
    speed: 0.2,
    regime: "Mudança lenta de ciclo urbano",
    visual: "/visuals/realestate-skyline.svg",
  },
];

export default function SectorRegimeShowcase() {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIdx((prev) => (prev + 1) % sectors.length);
    }, 9500);
    return () => clearInterval(timer);
  }, []);

  const sector = useMemo(() => sectors[idx], [idx]);

  return (
    <div className="relative h-[420px] lg:h-[520px] rounded-[28px] border border-zinc-800 overflow-hidden">
      <RegimeField
        key={sector.id}
        className="absolute inset-0"
        density={sector.density}
        speed={sector.speed}
        hue={sector.hue}
        accent={sector.accent}
      />
      <div
        className="absolute inset-0 opacity-40 bg-center bg-cover transition-opacity duration-700"
        style={{ backgroundImage: `url('${sector.visual}')` }}
      />
      <div className="absolute inset-0 hero-noise" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />
      <div className="absolute bottom-5 left-5 right-5">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-300">{sector.title}</div>
        <div className="mt-2 text-xs text-zinc-400 max-w-md">{sector.subtitle}</div>
        <div className="mt-2 inline-flex items-center rounded-full border border-zinc-700 bg-black/45 px-3 py-1 text-[11px] text-zinc-300">
          {sector.regime}
        </div>
      </div>
      <div className="absolute top-5 right-5 flex gap-2">
        {sectors.map((item, itemIdx) => (
          <button
            key={item.id}
            aria-label={`Selecionar ${item.title}`}
            className={`h-2.5 w-2.5 rounded-full transition ${
              itemIdx === idx ? "bg-cyan-300" : "bg-zinc-600"
            }`}
            onClick={() => setIdx(itemIdx)}
          />
        ))}
      </div>
    </div>
  );
}
