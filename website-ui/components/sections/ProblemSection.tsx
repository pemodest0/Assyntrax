"use client";

import TransitionDiagram from "@/components/visuals/TransitionDiagram";
import { motion } from "framer-motion";

export default function ProblemSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr] gap-12 items-center">
      <motion.div
        className="rounded-[28px] border border-zinc-800 bg-zinc-950/60 p-10 ax-glow"
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">O problema</div>
        <h2 className="mt-4 text-3xl md:text-4xl font-semibold tracking-tight">
          Modelos falham quando o regime muda.
        </h2>
        <p className="mt-4 text-zinc-300 text-lg">
          Previsores tradicionais ignoram a mudança estrutural. A Assyntrax detecta a transição,
          mede estabilidade e explica quando não faz sentido prever.
        </p>
      </motion.div>
      <TransitionDiagram />
    </section>
  );
}
