"use client";

import ProductMock from "@/components/visuals/ProductMock";
import { motion } from "framer-motion";

export default function ProductSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-12 items-center">
      <motion.div
        className="space-y-4"
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-sm uppercase tracking-[0.3em] text-zinc-400">Produto</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">
          Dashboard + API pensados para decisão
        </h2>
        <p className="text-zinc-300 text-lg">
          Entregamos leitura de regimes, saúde estrutural e projeções condicionais. A API expõe
          tudo com rastreabilidade de métricas e alertas claros.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-zinc-300">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
            Diagnóstico confiável antes de forecast.
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
            Integração rápida com BI, alertas e APIs.
          </div>
        </div>
      </motion.div>
      <ProductMock />
    </section>
  );
}
