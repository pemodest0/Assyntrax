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
      <div className="relative z-10 space-y-4">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Financeiro - Radar de regime</div>
        <svg viewBox="0 0 420 220" className="w-full h-44 rounded-xl border border-zinc-800 bg-black/35">
          <g stroke="rgba(148,163,184,0.16)">
            <line x1="20" y1="175" x2="400" y2="175" />
            <line x1="20" y1="130" x2="400" y2="130" />
            <line x1="20" y1="85" x2="400" y2="85" />
          </g>
          <path d="M20 160 C 80 96, 132 118, 190 74 C 250 34, 300 40, 400 28" stroke="#38bdf8" strokeWidth="3" fill="none" />
          <path d="M20 184 L 88 168 L 154 152 L 218 146 L 282 122 L 346 116 L 400 98" stroke="#f97316" strokeWidth="2.4" fill="none" opacity="0.9" />
          <rect x="246" y="22" width="150" height="30" rx="8" fill="rgba(251,191,36,0.14)" stroke="rgba(251,191,36,0.42)" />
          <text x="256" y="40" fill="#fbbf24" fontSize="11">Alerta: transição de volatilidade</text>
        </svg>
        <div className="grid grid-cols-3 gap-2 text-[11px] text-zinc-300">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Spreads: ampliando</div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Liquidez: reduzindo</div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Regime: transição</div>
        </div>
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
      <div className="relative z-10 space-y-4">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Imobiliário - Ciclo estrutural</div>
        <svg viewBox="0 0 420 220" className="w-full h-44 rounded-xl border border-zinc-800 bg-black/35">
          <rect x="26" y="100" width="60" height="84" fill="#172133" />
          <rect x="98" y="76" width="72" height="108" fill="#101927" />
          <rect x="184" y="60" width="74" height="124" fill="#0c1422" />
          <rect x="272" y="92" width="58" height="92" fill="#172133" />
          <rect x="342" y="68" width="52" height="116" fill="#101927" />
          <path d="M26 164 C 120 146, 206 134, 394 88" stroke="#f97316" strokeWidth="3" fill="none" />
          <path d="M26 184 C 120 180, 206 172, 394 152" stroke="#38bdf8" strokeWidth="2" fill="none" opacity="0.8" />
        </svg>
        <div className="grid grid-cols-3 gap-2 text-[11px] text-zinc-300">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Preço m²: desacelerando</div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Liquidez: travando</div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Juros: pressão alta</div>
        </div>
      </div>
    </motion.div>
  );
}
