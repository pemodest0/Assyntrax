import { motion } from "framer-motion";

const steps = [
  {
    title: "Embedding",
    text: "Reconstrução do espaço de fase com atraso temporal e geometria observável.",
    details:
      "Ver mais: define m e tau, mede recorrência e prepara a estrutura dinâmica para classificação.",
  },
  {
    title: "Microestados",
    text: "Clusters densos e persistentes para separar comportamentos locais.",
    details:
      "Ver mais: estados de curta duração são agregados para reduzir ruído e identificar padrões reais.",
  },
  {
    title: "Grafos",
    text: "Rede de transições entre estados, com entropia e conectividade.",
    details:
      "Ver mais: o grafo permite medir quebra de estrutura, sincronização e risco de mudança de regime.",
  },
  {
    title: "Métricas",
    text: "Confiança, qualidade, instabilidade e persistência de regime.",
    details:
      "Ver mais: indicadores são usados em gates operacionais e trilha de auditoria por execução.",
  },
  {
    title: "Alertas",
    text: "Saída operacional com status validated, watch ou inconclusive.",
    details:
      "Ver mais: quando não há estrutura, o sistema sinaliza diagnóstico inconclusivo em vez de ação.",
  },
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
            transition={{ duration: 0.4, delay: idx * 0.08 }}
          >
            <div className="absolute -top-3 left-4 text-[10px] uppercase tracking-[0.3em] text-zinc-500">
              {String(idx + 1).padStart(2, "0")}
            </div>
            <div className="text-sm font-semibold">{s.title}</div>
            <div className="mt-2 text-xs text-zinc-300">{s.text}</div>
            <details className="mt-3">
              <summary className="cursor-pointer text-xs text-cyan-300">Ver mais</summary>
              <p className="mt-2 text-xs text-zinc-400">{s.details}</p>
            </details>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
