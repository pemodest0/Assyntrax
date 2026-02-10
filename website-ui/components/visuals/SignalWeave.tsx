"use client";

import { motion } from "framer-motion";

export default function SignalWeave() {
  return (
    <motion.div
      className="relative rounded-[28px] border border-zinc-800 bg-black/70 p-6 overflow-hidden"
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.18),_transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(249,115,22,0.18),_transparent_60%)]" />
      <svg viewBox="0 0 520 220" className="relative z-10 w-full h-48">
        <defs>
          <linearGradient id="weave-line" x1="0" x2="1">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="50%" stopColor="#7c3aed" />
            <stop offset="100%" stopColor="#ff7a18" />
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="520" height="220" rx="24" fill="rgba(8,8,12,0.6)" />
        <path
          d="M20 140 C 80 60, 140 170, 200 90 C 250 30, 320 150, 380 80 C 420 40, 480 90, 500 70"
          stroke="url(#weave-line)"
          strokeWidth="3"
          fill="none"
        />
        <path
          d="M20 170 C 100 130, 160 190, 240 120 C 300 60, 360 120, 420 100 C 460 85, 490 90, 500 92"
          stroke="rgba(148,163,184,0.45)"
          strokeWidth="2"
          fill="none"
        />
        <circle cx="200" cy="90" r="4" fill="#22d3ee" />
        <circle cx="380" cy="80" r="4" fill="#ff7a18" />
      </svg>
      <div className="relative z-10 text-xs text-zinc-400 mt-2">
        Estrutura dinamica com camadas de regime e ruido.
      </div>
    </motion.div>
  );
}
