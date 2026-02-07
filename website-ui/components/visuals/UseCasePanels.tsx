import { motion } from "framer-motion";

export function FinanceVisual() {
  return (
    <motion.div
      className="relative rounded-3xl border border-zinc-800 bg-black/70 p-6 overflow-hidden"
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.2),_transparent_60%)]" />
      <svg viewBox="0 0 420 200" className="relative z-10 w-full h-40">
        <path
          d="M20 150 C 80 80, 150 120, 220 60 C 280 15, 340 50, 400 30"
          stroke="#38bdf8"
          strokeWidth="3"
          fill="none"
        />
        <path
          d="M20 170 L 120 130 L 220 110 L 320 90 L 400 85"
          stroke="#f97316"
          strokeWidth="2"
          fill="none"
          opacity="0.8"
        />
        <circle cx="220" cy="60" r="4" fill="#f97316" />
      </svg>
      <div className="relative z-10 text-xs text-zinc-400 mt-2">
        Volatilidade, spreads e regimes de risco em camadas.
      </div>
    </motion.div>
  );
}

export function RealEstateVisual() {
  return (
    <motion.div
      className="relative rounded-3xl border border-zinc-800 bg-black/70 p-6 overflow-hidden"
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(168,85,247,0.2),_transparent_60%)]" />
      <svg viewBox="0 0 420 200" className="relative z-10 w-full h-40">
        <rect x="20" y="80" width="60" height="90" fill="#1f2937" />
        <rect x="90" y="60" width="80" height="110" fill="#111827" />
        <rect x="190" y="40" width="70" height="130" fill="#0f172a" />
        <rect x="270" y="90" width="50" height="80" fill="#1f2937" />
        <rect x="330" y="70" width="70" height="100" fill="#111827" />
        <path
          d="M20 150 C 120 130, 220 120, 400 80"
          stroke="#f97316"
          strokeWidth="3"
          fill="none"
        />
      </svg>
      <div className="relative z-10 text-xs text-zinc-400 mt-2">
        Ciclos de preço, crédito e liquidez urbana.
      </div>
    </motion.div>
  );
}
