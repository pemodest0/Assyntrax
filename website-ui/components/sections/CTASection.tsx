"use client";

import { motion } from "framer-motion";

export default function CTASection() {
  return (
    <motion.section
      className="rounded-[28px] border border-zinc-800 bg-zinc-950/70 p-8 lg:p-10 flex flex-col md:flex-row items-center justify-between gap-5 ax-glow py-10 md:py-12 lg:py-14 xl:py-16"
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div>
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Pronto para explorar</div>
        <h3 className="mt-3 text-3xl md:text-4xl font-semibold tracking-tight">
          Solicite uma demonstracao guiada
        </h3>
        <p className="mt-2 text-zinc-300 max-w-2xl text-base lg:text-lg">
          Veja o diagnostico estrutural no seu fluxo de decisao, com governanca e rastreabilidade.
        </p>
      </div>
      <div className="flex gap-3">
        <a
          className="rounded-xl bg-zinc-100 text-black px-6 py-3 font-medium hover:bg-white transition"
          href="/contact"
        >
          Solicitar demonstracao
        </a>
        <a
          className="rounded-xl border border-zinc-800 px-6 py-3 text-zinc-200 hover:border-zinc-600 transition"
          href="/app/dashboard"
        >
          Abrir painel
        </a>
      </div>
    </motion.section>
  );
}

