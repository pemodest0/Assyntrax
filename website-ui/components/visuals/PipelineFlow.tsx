import { motion } from "framer-motion";

const steps = [
  { title: "Embedding", text: "Reconstrução do espaço de fase." },
  { title: "Microestados", text: "Clusters densos e persistentes." },
  { title: "Grafos", text: "Transições e entropia." },
  { title: "Métricas", text: "Confiança, escape, qualidade." },
  { title: "Alertas", text: "Forecast condicional." },
];

export default function PipelineFlow() {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-8">
      <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Pipeline Assyntrax</div>
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-5 gap-4">
        {steps.map((s, idx) => (
          <motion.div
            key={s.title}
            className="relative rounded-2xl border border-zinc-800 bg-black/60 p-4 h-full transition hover:-translate-y-1 hover:border-zinc-600"
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: idx * 0.1 }}
          >
            <div className="absolute -top-3 left-4 text-[10px] uppercase tracking-[0.3em] text-zinc-500">
              {String(idx + 1).padStart(2, "0")}
            </div>
            <div className="text-sm font-semibold">{s.title}</div>
            <div className="mt-2 text-xs text-zinc-400">{s.text}</div>
            <div className="mt-4 h-1 w-full bg-zinc-800/80 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-400 via-indigo-400 to-orange-500"
                style={{ width: `${70 + idx * 6}%` }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
