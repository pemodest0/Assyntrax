"use client";

import PipelineFlow from "@/components/visuals/PipelineFlow";
import { motion } from "framer-motion";

export default function HowItWorksSection() {
  return (
    <section className="space-y-10">
      <motion.div
        className="space-y-3"
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-sm uppercase tracking-[0.3em] text-zinc-400">Como funciona</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">
          Pipeline científico para regimes, risco e forecast condicional
        </h2>
        <p className="text-zinc-300 max-w-3xl text-lg">
          Embedding, microestados, grafos e métricas se conectam em um fluxo auditável, com
          alertas explícitos e transparência operacional.
        </p>
      </motion.div>
      <PipelineFlow />
    </section>
  );
}
