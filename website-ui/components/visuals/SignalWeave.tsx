"use client";

import { motion } from "framer-motion";

const sectors = [
  {
    id: "F",
    label: "Finanças",
    color: "#22d3ee",
    path: "M20 72 C 80 34, 146 108, 208 62 C 272 22, 338 96, 402 56",
  },
  {
    id: "E",
    label: "Energia",
    color: "#f97316",
    path: "M20 138 C 76 96, 138 146, 210 106 C 282 66, 344 120, 402 88",
  },
  {
    id: "I",
    label: "Imobiliário",
    color: "#a855f7",
    path: "M20 204 C 88 164, 154 212, 216 170 C 274 130, 340 176, 402 144",
  },
];

export default function SignalWeave() {
  return (
    <motion.div
      className="relative rounded-[28px] border border-zinc-800 bg-black/70 p-6 overflow-hidden"
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(249,115,22,0.12),_transparent_60%)]" />

      <svg viewBox="0 0 430 236" className="relative z-10 w-full h-52">
        <rect x="0" y="0" width="430" height="236" rx="24" fill="rgba(8,8,12,0.62)" />
        {sectors.map((s, i) => (
          <g key={s.id}>
            <text x="20" y={46 + i * 66} fill="rgba(255,255,255,0.65)" fontSize="12">
              {s.label}
            </text>
            <path d={s.path} stroke={s.color} strokeWidth="2.5" fill="none" />
            <motion.circle
              cx="20"
              cy={72 + i * 66}
              r="4"
              fill={s.color}
              animate={{ cx: [20, 402] }}
              transition={{
                duration: 7 + i,
                repeat: Number.POSITIVE_INFINITY,
                repeatType: "mirror",
                ease: "easeInOut",
              }}
            />
          </g>
        ))}
      </svg>
      <div className="relative z-10 text-xs text-zinc-400 mt-2">
        Estrutura dinâmica multicamada para finanças, energia e imobiliário.
      </div>
    </motion.div>
  );
}
