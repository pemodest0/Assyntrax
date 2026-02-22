"use client";

import { motion } from "framer-motion";

const cards = [
  {
    title: "Diagnostico Causal de Regimes",
    text: "Regimes classificados de forma transparente (estavel, transicao, estresse, dispersao). Sem previsoes de preco ou sinais de compra/venda.",
  },
  {
    title: "Governanca e Auditabilidade",
    text: "Politica travada e publish gate garantem que cada execucao tenha rastreabilidade. Voce sabe quando, como e por que um regime foi publicado.",
  },
  {
    title: "Integracao e Painel",
    text: "O mesmo diagnostico via painel interativo, Interface de Programacao de Aplicacoes e artefatos de auditoria, facilitando integracao com sistemas internos.",
  },
];

export default function ProductSection() {
  return (
    <section className="space-y-6 py-10 md:py-12 lg:py-14 xl:py-16">
      <motion.div
        className="space-y-2"
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Entrega e valor</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Causalidade, governanca e integracao</h2>
        <p className="text-zinc-300 max-w-3xl text-base lg:text-lg">
          Foco em utilidade operacional: reduzir subjetividade, registrar decisoes e integrar o diagnostico ao fluxo
          institucional.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cards.map((card, index) => (
          <motion.article
            key={card.title}
            className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5"
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: index * 0.08 }}
          >
            <h3 className="text-lg font-semibold text-zinc-100">{card.title}</h3>
            <p className="mt-2 text-sm text-zinc-300">{card.text}</p>
          </motion.article>
        ))}
      </div>
    </section>
  );
}
