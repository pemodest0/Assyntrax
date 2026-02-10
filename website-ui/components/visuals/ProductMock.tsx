"use client";

import { motion } from "framer-motion";

export default function ProductMock() {
  return (
    <motion.div
      className="relative rounded-3xl border border-zinc-800 bg-black/70 p-6 overflow-hidden"
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.2),_transparent_55%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(249,115,22,0.2),_transparent_55%)]" />
      <div className="relative z-10 space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Dashboard</div>
          <div className="text-[10px] text-zinc-500">Live</div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Regime", value: "Estavel" },
            { label: "Confiança", value: "0.82" },
            { label: "Qualidade", value: "0.76" },
          ].map((item) => (
            <div
              key={item.label}
              className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3 transition hover:-translate-y-1 hover:border-zinc-600"
            >
              <div className="text-[10px] uppercase text-zinc-500">{item.label}</div>
              <div className="mt-2 text-lg font-semibold text-zinc-100">{item.value}</div>
            </div>
          ))}
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
          <div className="text-xs text-zinc-500">Serie principal</div>
          <svg viewBox="0 0 420 140" className="mt-2 w-full h-28">
            <defs>
              <linearGradient id="mock-line" x1="0" x2="1">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="100%" stopColor="#f97316" />
              </linearGradient>
            </defs>
            <rect x="0" y="0" width="420" height="140" rx="16" fill="rgba(8,8,10,0.4)" />
            <path
              d="M20 110 C 90 60, 140 80, 210 52 C 260 34, 320 40, 400 30"
              stroke="url(#mock-line)"
              strokeWidth="3"
              fill="none"
            />
          </svg>
        </div>
        <div className="grid grid-cols-2 gap-3 text-xs text-zinc-400">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3 transition hover:-translate-y-1 hover:border-zinc-600">
            Forecast condicional ativo
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3 transition hover:-translate-y-1 hover:border-zinc-600">
            Alertas estruturais em tempo real
          </div>
        </div>
      </div>
    </motion.div>
  );
}
