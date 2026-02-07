"use client";

import { motion } from "framer-motion";
import RegimeField from "@/components/visuals/RegimeField";

export default function HeroSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-12 items-center">
      <div className="rounded-[32px] border border-zinc-800 bg-zinc-950/70 p-12 backdrop-blur ax-glow">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">
          Motor de Regime e Risco
        </div>
        <h1 className="mt-6 text-5xl md:text-6xl font-semibold tracking-tight">
          Diagnóstico de regimes com consciência estrutural
        </h1>
        <p className="mt-5 text-zinc-300 max-w-2xl text-lg">
          A Assyntrax detecta transições e instabilidade antes de qualquer projeção. Forecast é
          condicional e sempre acompanhado de métricas, alertas e contexto.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <a
            className="rounded-xl bg-zinc-100 text-black px-5 py-3 font-medium hover:bg-white transition"
            href="/app/dashboard"
          >
            Abrir App &rarr;
          </a>
          <a
            className="rounded-xl border border-zinc-800 px-5 py-3 text-zinc-200 hover:border-zinc-600 transition"
            href="/product"
          >
            Ver Produto
          </a>
        </div>
        <div className="mt-5 text-xs text-zinc-500">
          Sem promessas de retorno. Diagnóstico antes de decisão.
        </div>
      </div>
      <motion.div
        className="relative h-[560px] rounded-[32px] border border-zinc-800 overflow-hidden"
        initial={{ opacity: 0, scale: 0.98 }}
        whileInView={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
      >
        <RegimeField className="absolute inset-0" density={120} speed={0.5} hue={215} />
        <div className="absolute inset-0 hero-noise" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
        <div className="absolute bottom-6 left-6 text-xs uppercase tracking-[0.2em] text-zinc-300">
          RegimeField
        </div>
      </motion.div>
    </section>
  );
}
