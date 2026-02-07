"use client";

import ProofMatrix from "@/components/visuals/ProofMatrix";
import { motion } from "framer-motion";

export default function ProofSection() {
  return (
    <section className="space-y-10">
      <motion.div
        className="space-y-3"
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-sm uppercase tracking-[0.3em] text-zinc-400">Prova &amp; rigor</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">
          Métricas transparentes, sem promessas
        </h2>
        <p className="text-zinc-300 max-w-3xl text-lg">
          Validamos com walk-forward, baselines e métricas por regime. A Assyntrax sinaliza quando o
          mercado está sem estrutura.
        </p>
      </motion.div>
      <ProofMatrix />
      <div className="text-xs text-zinc-500">
        Resultados ilustrativos. Sem promessa de retorno financeiro ou precisão garantida.
      </div>
    </section>
  );
}
