"use client";

import PipelineFlow from "@/components/visuals/PipelineFlow";
import { motion } from "framer-motion";

export default function HowItWorksSection() {
  return (
    <section className="space-y-6 py-10 md:py-12 lg:py-14 xl:py-16">
      <motion.div
        className="space-y-2"
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Como funciona</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">
          Pipeline científico para regime, risco e diagnóstico condicional
        </h2>
        <p className="text-zinc-300 max-w-3xl text-base lg:text-lg">
          Embedding, microestados, grafos e métricas conectados em um fluxo auditável,
          com explicações operacionais e trilha de evidências.
        </p>
      </motion.div>
      <PipelineFlow />
    </section>
  );
}
