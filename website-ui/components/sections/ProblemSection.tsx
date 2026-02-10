"use client";

import TransitionDiagram from "@/components/visuals/TransitionDiagram";
import { motion } from "framer-motion";

export default function ProblemSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[0.95fr_1.05fr] gap-8 lg:gap-10 items-center py-10 md:py-12 lg:py-14 xl:py-16">
      <motion.div
        className="rounded-[24px] border border-zinc-800 bg-zinc-950/60 p-8 ax-glow"
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">O problema</div>
        <h2 className="mt-3 text-3xl md:text-4xl font-semibold tracking-tight">
          Modelos falham quando o regime muda.
        </h2>
        <p className="mt-3 text-zinc-300 text-base lg:text-lg">
          Previsores tradicionais ignoram a mudança estrutural. A Assyntrax detecta a transição,
          mede estabilidade e explica quando não faz sentido prever.
        </p>
      </motion.div>
      <TransitionDiagram />
    </section>
  );
}
