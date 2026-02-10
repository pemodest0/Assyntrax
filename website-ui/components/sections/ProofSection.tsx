"use client";

import ProofMatrix from "@/components/visuals/ProofMatrix";
import { motion } from "framer-motion";

export default function ProofSection() {
  return (
    <section className="space-y-6 py-10 md:py-12 lg:py-14 xl:py-16">
      <motion.div
        className="space-y-2"
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Prova e rigor</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Métricas transparentes, sem promessas</h2>
        <p className="text-zinc-300 max-w-3xl text-base lg:text-lg">
          Validação com walk-forward, baselines e métricas por regime. Quando não há estrutura,
          o sistema sinaliza diagnóstico inconclusivo.
        </p>
      </motion.div>
      <ProofMatrix />
      <div className="text-xs text-zinc-500">
        Resultados ilustrativos para gestão de risco. Sem promessa de retorno financeiro.
      </div>
    </section>
  );
}
