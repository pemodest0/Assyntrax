"use client";

import { motion } from "framer-motion";

export default function OriginPulse() {
  return (
    <motion.div
      className="relative rounded-[28px] border border-zinc-800 bg-black/70 p-6 overflow-hidden"
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(124,58,237,0.25),_transparent_65%)]" />
      <svg viewBox="0 0 420 220" className="relative z-10 w-full h-44">
        <defs>
          <radialGradient id="pulse" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.8" />
            <stop offset="60%" stopColor="#22d3ee" stopOpacity="0.2" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
        </defs>
        <rect x="0" y="0" width="420" height="220" rx="24" fill="rgba(8,8,12,0.6)" />
        <circle cx="210" cy="110" r="50" fill="url(#pulse)" />
        <circle cx="210" cy="110" r="80" stroke="rgba(148,163,184,0.4)" strokeWidth="1" fill="none" />
        <circle cx="210" cy="110" r="120" stroke="rgba(148,163,184,0.2)" strokeWidth="1" fill="none" />
        <path
          d="M90 150 C 140 120, 190 120, 240 95 C 280 75, 330 80, 360 60"
          stroke="#ff7a18"
          strokeWidth="2.4"
          fill="none"
        />
      </svg>
      <div className="relative z-10 text-xs text-zinc-400 mt-2">
        Evolução do motor e pulsos de regime ao longo do tempo.
      </div>
    </motion.div>
  );
}
