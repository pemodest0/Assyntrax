"use client";

import { motion } from "framer-motion";

export default function TransitionDiagram() {
  return (
    <div className="relative rounded-3xl border border-zinc-800 bg-black/70 p-8 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.18),_transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(255,115,0,0.18),_transparent_60%)]" />
      <div className="relative z-10">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Regime Shift</div>
        <div className="mt-4 grid grid-cols-1 gap-6">
          <motion.svg
            viewBox="0 0 640 220"
            className="w-full h-52"
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <defs>
              <linearGradient id="reg-line" x1="0" x2="1">
                <stop offset="0%" stopColor="#22d3ee" />
                <stop offset="60%" stopColor="#f97316" />
                <stop offset="100%" stopColor="#a855f7" />
              </linearGradient>
            </defs>
            <rect x="0" y="0" width="640" height="220" rx="20" fill="rgba(10,10,12,0.6)" />
            <path
              d="M30 160 C 140 80, 220 110, 310 90 C 370 76, 430 60, 520 50 C 560 46, 600 50, 610 52"
              stroke="url(#reg-line)"
              strokeWidth="3"
              fill="none"
            />
            <path d="M30 170 H610" stroke="rgba(148,163,184,0.2)" strokeDasharray="6 8" />
            <circle cx="310" cy="90" r="5" fill="#f97316" />
            <circle cx="520" cy="50" r="5" fill="#a855f7" />
            <text x="36" y="190" fill="#94a3b8" fontSize="12">Regime estável</text>
            <text x="300" y="30" fill="#f97316" fontSize="12">Transição crítica</text>
            <text x="480" y="28" fill="#a855f7" fontSize="12">Novo regime</text>
          </motion.svg>
        </div>
      </div>
    </div>
  );
}
