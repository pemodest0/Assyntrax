"use client";

import { motion } from "framer-motion";

export default function MethodLattice() {
  return (
    <motion.div
      className="relative rounded-[28px] border border-zinc-800 bg-black/70 p-6 overflow-hidden"
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.16),_transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(168,85,247,0.12),_transparent_65%)]" />
      <svg viewBox="0 0 520 220" className="relative z-10 w-full h-48">
        <rect x="0" y="0" width="520" height="220" rx="20" fill="rgba(8,8,12,0.6)" />
        <path d="M28 168 L128 118 L218 152 L312 94 L404 122 L494 72" stroke="#22d3ee" strokeWidth="2.4" fill="none" />
        <path d="M28 188 L128 136 L218 168 L312 118 L404 148 L494 102" stroke="#f97316" strokeWidth="2" fill="none" opacity="0.8" />
        <path d="M28 98 L128 66 L218 94 L312 50 L404 70 L494 38" stroke="#a855f7" strokeWidth="2" fill="none" opacity="0.85" />
        {[
          [128, 118],
          [218, 152],
          [312, 94],
          [404, 122],
          [128, 66],
          [218, 94],
          [312, 50],
          [404, 70],
        ].map(([x, y], idx) => (
          <circle key={idx} cx={x} cy={y} r="3.5" fill="#e5e7eb" opacity="0.75" />
        ))}
      </svg>
      <div className="relative z-10 mt-2 text-xs text-zinc-400">
        Arquitetura em camadas: embedding, estados, transições, gates e auditoria.
      </div>
    </motion.div>
  );
}
