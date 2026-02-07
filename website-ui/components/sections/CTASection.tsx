"use client";

import { motion } from "framer-motion";

export default function CTASection() {
  return (
    <motion.section
      className="rounded-[32px] border border-zinc-800 bg-zinc-950/70 p-12 flex flex-col md:flex-row items-center justify-between gap-6 ax-glow"
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div>
        <div className="text-sm uppercase tracking-[0.3em] text-zinc-400">Pronto para explorar</div>
        <h3 className="mt-4 text-3xl md:text-4xl font-semibold tracking-tight">
          Abra a Dashboard
        </h3>
        <p className="mt-3 text-zinc-300 max-w-2xl text-lg">
          Diagnóstico de regimes com alertas explícitos e forecast condicional.
        </p>
      </div>
      <div className="flex gap-3">
        <a
          className="rounded-xl bg-zinc-100 text-black px-6 py-3 font-medium hover:bg-white transition"
          href="/app/dashboard"
        >
          Abrir App &rarr;
        </a>
        <a
          className="rounded-xl border border-zinc-800 px-6 py-3 text-zinc-200 hover:border-zinc-600 transition"
          href="/contact"
        >
          Falar com a equipe
        </a>
      </div>
    </motion.section>
  );
}
