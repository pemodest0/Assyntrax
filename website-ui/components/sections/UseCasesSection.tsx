"use client";

import { useState } from "react";
import { FinanceVisual } from "@/components/visuals/UseCasePanels";
import { motion } from "framer-motion";

function GovernanceVisual() {
  return (
    <div className="relative rounded-3xl border border-zinc-800 bg-black/70 p-6 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.2),_transparent_60%)]" />
      <div className="relative z-10 space-y-4">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Governanca - Trilha de decisao</div>
        <div className="rounded-xl border border-zinc-800 bg-black/35 p-4 space-y-2 text-sm">
          <div className="flex items-center justify-between text-zinc-300">
            <span>Run</span>
            <span className="text-zinc-100">20260210_contractfix</span>
          </div>
          <div className="flex items-center justify-between text-zinc-300">
            <span>Status</span>
            <span className="text-amber-300">watch</span>
          </div>
          <div className="flex items-center justify-between text-zinc-300">
            <span>Gate</span>
            <span className="text-zinc-100">publish green</span>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-2 text-xs text-zinc-400">
            Registro de decisao, justificativa de exposicao e rastreabilidade para comites e auditoria.
          </div>
        </div>
      </div>
    </div>
  );
}

const tabs = [
  {
    id: "financas",
    label: "Financas",
    title: "Financas",
    description:
      "Utilize o regime como um barometro estrutural. Em mercado estavel, mantenha posicionamentos. Em transicao, reduza exposicao e monitore setores de risco. Em estresse, corte posicoes e proteja capital.",
    note: "Leitura estrutural nao e recomendacao de compra ou venda. A decisao final e do usuario.",
    Visual: FinanceVisual,
  },
  {
    id: "governanca",
    label: "Governanca",
    title: "Governanca",
    description:
      "Mantenha auditoria continua. Registre decisoes, justifique mudancas de exposicao e demonstre transparencia para investidores e reguladores. O motor preserva historico e criterios objetivos por regime.",
    note: "Governanca forte reduz risco reputacional e melhora consistencia de comites de investimento.",
    Visual: GovernanceVisual,
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
          <h2 className="mt-2 text-3xl md:text-4xl font-semibold tracking-tight">{current.title}</h2>
          <p className="mt-2 text-zinc-300 max-w-3xl text-base lg:text-lg">{current.description}</p>
          <p className="mt-2 text-xs text-zinc-500">{current.note}</p>
        </div>
        <div className="flex gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`rounded-full border px-4 py-2 text-sm transition ${
                active === tab.id
                  ? "border-cyan-400/70 bg-cyan-400/10 text-cyan-200"
                  : "border-zinc-800 text-zinc-400 hover:text-white"
              }`}
              onClick={() => setActive(tab.id)}
            >
              {tab.label}
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
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Uso pratico</div>
            <ul className="space-y-2 text-sm text-zinc-300">
              <li>- Ajuste exposicao com base no regime, nao em previsao de preco.</li>
              <li>- Use o gate para documentar quando agir e quando esperar.</li>
              <li>- Mantenha registro historico para auditoria e revisao de estrategia.</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
