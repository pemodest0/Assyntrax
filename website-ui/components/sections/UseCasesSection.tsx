"use client";

import { useState } from "react";
import { FinanceVisual, RealEstateVisual } from "@/components/visuals/UseCasePanels";
import { motion } from "framer-motion";

const tabs = [
  {
    id: "financeiro",
    label: "Financeiro",
    title: "Risco estrutural e regimes multiativos",
    description:
      "Monitoramento de volatilidade, spreads e regimes de risco com alertas de instabilidade e transparência no forecast.",
    Visual: FinanceVisual,
  },
  {
    id: "imobiliario",
    label: "Imobiliário",
    title: "Ciclos urbanos e liquidez estrutural",
    description:
      "Diagnóstico de ciclos de preço, travamento de liquidez e transições críticas em indicadores regionais.",
    Visual: RealEstateVisual,
  },
];

export default function UseCasesSection() {
  const [active, setActive] = useState(tabs[0].id);
  const current = tabs.find((t) => t.id === active) || tabs[0];
  const Visual = current.Visual;

  return (
    <section className="space-y-6 py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Casos de uso</div>
          <h2 className="mt-2 text-3xl md:text-4xl font-semibold tracking-tight">
            {current.title}
          </h2>
          <p className="mt-2 text-zinc-300 max-w-3xl text-base lg:text-lg">{current.description}</p>
        </div>
        <div className="flex gap-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`rounded-full border px-4 py-2 text-sm transition ${
                active === t.id
                  ? "border-cyan-400/70 bg-cyan-400/10 text-cyan-200"
                  : "border-zinc-800 text-zinc-400 hover:text-white"
              }`}
              onClick={() => setActive(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      <motion.div
        key={current.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-6">
          <Visual />
          <div className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-5 space-y-3">
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">
              O que observar
            </div>
            <ul className="space-y-2 text-sm text-zinc-300">
              <li>- Estabilidade do regime e qualidade do grafo.</li>
              <li>- Alertas de transição e mudanças de volatilidade.</li>
              <li>- Forecast condicional apenas quando há estrutura.</li>
            </ul>
            <div className="text-xs text-zinc-500">
              A leitura de risco muda conforme o regime detectado.
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
