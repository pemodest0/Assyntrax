"use client";

import { motion } from "framer-motion";

const layers = [
  {
    id: "R",
    label: "Risco estrutural",
    color: "#22d3ee",
    path: "M20 82 C 80 40, 146 110, 208 64 C 272 26, 338 98, 402 60",
  },
  {
    id: "C",
    label: "Confiança do sinal",
    color: "#f97316",
    path: "M20 156 C 76 116, 138 166, 210 120 C 282 82, 344 136, 402 100",
  },
  {
    id: "G",
    label: "Gate de publicação",
    color: "#a3e635",
    path: "M20 214 C 88 176, 154 224, 216 182 C 274 142, 340 188, 402 154",
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
        {layers.map((s, i) => (
          <g key={s.id}>
            <text x="20" y={46 + i * 66} fill="rgba(255,255,255,0.65)" fontSize="12">
              {s.label}
            </text>
            <path d={s.path} stroke={s.color} strokeWidth="2.5" fill="none" />
            <motion.circle
              cx="20"
              cy={82 + i * 66}
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
        Núcleo do produto: diagnóstico de regime em finanças com governança quantitativa.
      </div>
    </motion.div>
  );
}

