export function FinanceVisual() {
  return (
    <div className="relative rounded-3xl border border-zinc-800 bg-black/70 p-6 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.2),_transparent_60%)]" />
      <div className="relative z-10 space-y-4">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Finanças - radar de regime</div>
        <svg viewBox="0 0 420 220" className="w-full h-44 rounded-xl border border-zinc-800 bg-black/35">
          <g stroke="rgba(148,163,184,0.16)">
            <line x1="20" y1="175" x2="400" y2="175" />
            <line x1="20" y1="130" x2="400" y2="130" />
            <line x1="20" y1="85" x2="400" y2="85" />
          </g>
          <path d="M20 160 C 80 96, 132 118, 190 74 C 250 34, 300 40, 400 28" stroke="#38bdf8" strokeWidth="3" fill="none" />
          <path d="M20 184 L 88 168 L 154 152 L 218 146 L 282 122 L 346 116 L 400 98" stroke="#f97316" strokeWidth="2.4" fill="none" opacity="0.9" />
          <rect x="246" y="22" width="150" height="30" rx="8" fill="rgba(251,191,36,0.14)" stroke="rgba(251,191,36,0.42)" />
          <text x="256" y="40" fill="#fbbf24" fontSize="11">Transição estrutural detectada</text>
        </svg>
        <div className="grid grid-cols-3 gap-2 text-[11px] text-zinc-300">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Risco: em alta</div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Confiança: moderada</div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Estado: transição</div>
        </div>
      </div>
    </div>
  );
}

export function GovernanceVisual() {
  return (
    <div className="relative rounded-3xl border border-zinc-800 bg-black/70 p-6 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.16),_transparent_60%)]" />
      <div className="relative z-10 space-y-4">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">Governança - trilha auditável</div>
        <svg viewBox="0 0 420 220" className="w-full h-44 rounded-xl border border-zinc-800 bg-black/35">
          <rect x="24" y="30" width="372" height="30" rx="8" fill="rgba(15,23,42,0.9)" stroke="rgba(56,189,248,0.3)" />
          <rect x="24" y="78" width="372" height="30" rx="8" fill="rgba(15,23,42,0.9)" stroke="rgba(56,189,248,0.3)" />
          <rect x="24" y="126" width="372" height="30" rx="8" fill="rgba(15,23,42,0.9)" stroke="rgba(56,189,248,0.3)" />
          <text x="36" y="50" fill="#93c5fd" fontSize="11">execução: 2026-02-20_001 | janela oficial: T120</text>
          <text x="36" y="98" fill="#93c5fd" fontSize="11">gate: aprovado | cobertura: ok | universo: ok</text>
          <text x="36" y="146" fill="#93c5fd" fontSize="11">status final: transição | confiança: 0.64</text>
        </svg>
        <div className="grid grid-cols-3 gap-2 text-[11px] text-zinc-300">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Causalidade: ativa</div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Auditabilidade: completa</div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">Publicação: por gate</div>
        </div>
      </div>
    </div>
  );
}
