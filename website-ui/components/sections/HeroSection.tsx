"use client";

import { motion } from "framer-motion";
import SectorRegimeShowcase from "@/components/visuals/SectorRegimeShowcase";

export default function HeroSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-8 lg:gap-10 items-center min-h-[70vh] lg:min-h-[78vh] max-h-[860px] py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="rounded-[28px] border border-zinc-800 bg-zinc-950/70 p-8 lg:p-10 backdrop-blur ax-glow">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Aplicação de regime e risco</div>
        <h1 className="mt-5 text-4xl md:text-5xl font-semibold tracking-tight">Eigen Engine</h1>
        <p className="mt-4 text-zinc-300 max-w-2xl text-base lg:text-lg">
          Sistema de diagnóstico estrutural para setores financeiros, energia e mercado imobiliário.
          A leitura operacional prioriza estabilidade, transição e nível de confiabilidade antes de qualquer decisão.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <a
            className="rounded-xl bg-zinc-100 text-black px-5 py-3 font-medium hover:bg-white transition"
            href="/app/dashboard"
          >
            Abrir App
          </a>
          <a
            className="rounded-xl border border-zinc-800 px-5 py-3 text-zinc-200 hover:border-zinc-600 transition"
            href="/product"
          >
            Ver Produto
          </a>
        </div>
        <div className="mt-4 text-xs text-zinc-500">Sem promessa de retorno. Decisão orientada por evidência estrutural.</div>
      </div>
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        whileInView={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
      >
        <SectorRegimeShowcase />
      </motion.div>
    </section>
  );
}

