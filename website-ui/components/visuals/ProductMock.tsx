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
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(249,115,22,0.14),_transparent_60%)]" />

      <div className="relative z-10 space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Painel operacional</div>
          <div className="text-[10px] text-zinc-500">run_id: ativo</div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <Metric label="Regime" value="Transição" note="Leitura atual" />
          <Metric label="Confiança" value="0.84" note="Estrutura consistente" />
          <Metric label="Qualidade" value="0.78" note="Uso operacional" />
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs text-zinc-400">Matriz de decisão por horizonte</p>
            <p className="text-[10px] text-zinc-500">janela ativa: 20d</p>
          </div>
          <div className="grid grid-cols-4 gap-2">
            <HeatCell label="h+1" state="Estável" value={0.81} color="emerald" />
            <HeatCell label="h+5" state="Transição" value={0.62} color="amber" />
            <HeatCell label="h+10" state="Transição" value={0.57} color="amber" />
            <HeatCell label="h+20" state="Instável" value={0.41} color="rose" />
          </div>
          <div className="rounded-xl border border-zinc-800 bg-black/30 p-3 text-xs text-zinc-400">
            O sistema não diz &quot;compre&quot; ou &quot;venda&quot;. Ele reduz erro operacional: libera ação apenas
            quando há estrutura válida e bloqueia extrapolação em regime frágil.
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3 transition hover:-translate-y-1 hover:border-zinc-600">
      <div className="text-[10px] uppercase text-zinc-500">{label}</div>
      <div className="mt-2 text-lg font-semibold text-zinc-100">{value}</div>
      <div className="mt-1 text-[10px] text-zinc-400">{note}</div>
    </div>
  );
}

function HeatCell({
  label,
  state,
  value,
  color,
}: {
  label: string;
  state: string;
  value: number;
  color: "emerald" | "amber" | "rose";
}) {
  const bg =
    color === "emerald"
      ? "from-emerald-500/35 to-emerald-900/20 border-emerald-500/35"
      : color === "amber"
      ? "from-amber-500/35 to-amber-900/20 border-amber-500/35"
      : "from-rose-500/35 to-rose-900/20 border-rose-500/35";
  return (
    <div className={`rounded-lg border bg-gradient-to-br p-2 ${bg}`}>
      <div className="text-[10px] text-zinc-400">{label}</div>
      <div className="mt-1 text-xs font-semibold text-zinc-100">{state}</div>
      <div className="mt-1 text-[10px] text-zinc-300">Confiabilidade: {value.toFixed(2)}</div>
    </div>
  );
}

