import { motion } from "framer-motion";

const metrics = [
  { label: "F1", value: "0.71", note: "Regimes" },
  { label: "MCC", value: "0.63", note: "Transições" },
  { label: "MASE", value: "0.88", note: "Forecast condicional" },
  { label: "TPR", value: "0.79", note: "Alertas críticos" },
];

export default function ProofMatrix() {
  return (
    <motion.div
      className="rounded-3xl border border-zinc-800 bg-zinc-950/70 p-6"
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Benchmarks</div>
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((m) => (
          <div
            key={m.label}
            className="rounded-2xl border border-zinc-800 bg-black/60 p-4 transition hover:-translate-y-1 hover:border-zinc-600"
          >
            <div className="text-xs text-zinc-500">{m.note}</div>
            <div className="mt-2 text-2xl font-semibold text-zinc-100">{m.value}</div>
            <div className="mt-1 text-xs uppercase tracking-[0.2em] text-zinc-400">{m.label}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 text-xs text-zinc-500">
        Resultados indicativos. Sem promessa de retorno financeiro.
      </div>
    </motion.div>
  );
}
