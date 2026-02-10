"use client";

import { motion } from "framer-motion";
import RegimeField from "@/components/visuals/RegimeField";

export default function HeroSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-8 lg:gap-10 items-center min-h-[70vh] lg:min-h-[78vh] max-h-[860px] py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="rounded-[28px] border border-zinc-800 bg-zinc-950/70 p-8 lg:p-10 backdrop-blur ax-glow">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">
          Motor de Regime e Risco
        </div>
        <h1 className="mt-5 text-4xl md:text-5xl font-semibold tracking-tight">
          Diagnóstico de regimes com consciência estrutural
        </h1>
        <p className="mt-4 text-zinc-300 max-w-2xl text-base lg:text-lg">
          A Assyntrax detecta transições e instabilidade antes de qualquer projeção. O forecast
          é condicional e sempre acompanhado de métricas, alertas e contexto.
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
        <div className="mt-4 text-xs text-zinc-500">
          Sem promessas de retorno. Diagnóstico antes da decisão.
        </div>
      </div>
      <motion.div
        className="relative h-[420px] lg:h-[520px] rounded-[28px] border border-zinc-800 overflow-hidden"
        initial={{ opacity: 0, scale: 0.98 }}
        whileInView={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
      >
        <RegimeField className="absolute inset-0" density={120} speed={0.5} hue={215} />
        <div className="absolute inset-0 hero-noise" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
        <div className="absolute bottom-5 left-5 text-xs uppercase tracking-[0.2em] text-zinc-300">
          RegimeField
        </div>
      </motion.div>
    </section>
  );
}
