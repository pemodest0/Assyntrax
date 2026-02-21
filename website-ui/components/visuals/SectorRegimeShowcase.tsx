"use client";

import RegimeField from "@/components/visuals/RegimeField";

const finance = {
  id: "financas",
  title: "Setor: Finanças",
  subtitle: "Análise espectral de correlações, risco estrutural e confiança do sinal em base diária.",
  hue: 214,
  accent: "rgba(56,189,248,0.92)",
  density: 132,
  speed: 0.24,
  regime: "Regime em monitoramento causal",
  visual: "/visuals/hero-graph.svg",
};

export default function SectorRegimeShowcase() {
  return (
    <div className="relative h-[420px] lg:h-[520px] rounded-[28px] border border-zinc-800 overflow-hidden">
      <RegimeField
        className="absolute inset-0"
        density={finance.density}
        speed={finance.speed}
        hue={finance.hue}
        accent={finance.accent}
      />
      <div
        className="absolute inset-0 opacity-40 bg-center bg-cover transition-opacity duration-700"
        style={{ backgroundImage: `url('${finance.visual}')` }}
      />
      <div className="absolute inset-0 hero-noise" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />
      <div className="absolute bottom-5 left-5 right-5">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-300">{finance.title}</div>
        <div className="mt-2 text-xs text-zinc-400 max-w-md">{finance.subtitle}</div>
        <div className="mt-2 inline-flex items-center rounded-full border border-zinc-700 bg-black/45 px-3 py-1 text-[11px] text-zinc-300">
          {finance.regime}
        </div>
      </div>
      <div className="absolute top-5 right-5 rounded-xl border border-zinc-700/80 bg-black/45 px-3 py-2">
        <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-400">Estado</div>
        <div className="mt-2 flex items-center gap-2 text-[11px] text-zinc-300">
          <span className="inline-flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
            Estável
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
            Transição
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
            Estresse
          </span>
        </div>
      </div>
    </div>
  );
}
