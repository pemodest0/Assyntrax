"use client";

import { KeyboardEvent, useRef, useState } from "react";
import { FinanceVisual, GovernanceVisual } from "@/components/visuals/UseCasePanels";

const tabs = [
  {
    id: "financeiro",
    label: "Finanças",
    title: "Finanças: leitura de regime para reduzir erro operacional",
    description:
      "A utilidade é monitorar mudança estrutural e qualificar risco, não prever preço ou prometer retorno.",
    bullets: [
      "Regime estável: continuidade operacional com rastreio por execução.",
      "Transição persistente: reforça monitoramento e revisão de exposição.",
      "Estresse estrutural: saída permanece em modo diagnóstico com transparência.",
    ],
    Visual: FinanceVisual,
  },
  {
    id: "governanca",
    label: "Governança",
    title: "Governança: explicação técnica e trilha completa de decisão",
    description:
      "Cada leitura é publicada com checagem de qualidade, integridade temporal e artefatos de auditoria.",
    bullets: [
      "Sem look-ahead: limiares calibrados com histórico disponível até cada data.",
      "Gate de publicação: bloqueia runs que não passam cobertura mínima e QA.",
      "Post-mortem possível: id de execução, checks e métricas ficam registrados.",
    ],
    Visual: GovernanceVisual,
  },
];

export default function UseCasesSection() {
  const [activeIndex, setActiveIndex] = useState(0);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const current = tabs[activeIndex] || tabs[0];
  const Visual = current.Visual;

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, currentIndex: number) {
    const { key } = event;
    if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(key)) return;
    event.preventDefault();
    let nextIndex = currentIndex;
    if (key === "ArrowRight") nextIndex = (currentIndex + 1) % tabs.length;
    if (key === "ArrowLeft") nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    if (key === "Home") nextIndex = 0;
    if (key === "End") nextIndex = tabs.length - 1;
    setActiveIndex(nextIndex);
    tabRefs.current[nextIndex]?.focus();
  }

  return (
    <section className="space-y-6 py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Casos de uso</div>
          <h2 className="mt-2 text-3xl md:text-4xl font-semibold tracking-tight">{current.title}</h2>
          <p className="mt-2 text-zinc-300 max-w-3xl text-base lg:text-lg">{current.description}</p>
        </div>
        <div className="flex gap-2" role="tablist" aria-label="Casos de uso">
          {tabs.map((t, idx) => (
            <button
              key={t.id}
              id={`use-case-tab-${t.id}`}
              ref={(node) => {
                tabRefs.current[idx] = node;
              }}
              role="tab"
              type="button"
              aria-selected={activeIndex === idx}
              aria-controls={`use-case-panel-${t.id}`}
              tabIndex={activeIndex === idx ? 0 : -1}
              className={`rounded-full border px-4 py-2 text-sm transition ${
                activeIndex === idx
                  ? "border-cyan-400/70 bg-cyan-400/10 text-cyan-200"
                  : "border-zinc-800 text-zinc-400 hover:text-white"
              }`}
              onClick={() => setActiveIndex(idx)}
              onKeyDown={(event) => handleTabKeyDown(event, idx)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      <div
        key={current.id}
        id={`use-case-panel-${current.id}`}
        role="tabpanel"
        aria-labelledby={`use-case-tab-${current.id}`}
        className="outline-none"
      >
        <div className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-6">
          <Visual />
          <div className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-5 space-y-3">
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Leitura prática</div>
            <ul className="space-y-2 text-sm text-zinc-300 list-disc list-inside">
              {current.bullets.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <div className="text-xs text-zinc-500">
              O produto informa estado e risco estrutural; a decisão final continua sob governança da equipe usuária.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
