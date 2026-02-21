import Link from "next/link";
import PipelineFlow from "@/components/visuals/PipelineFlow";

export default function HowItWorksSection() {
  return (
    <section className="space-y-6 py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="space-y-2">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Como funciona</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Do dado ao diagnóstico com gate e auditoria</h2>
        <p className="text-zinc-300 max-w-3xl text-base lg:text-lg">
          O fluxo técnico é baseado em análise espectral de correlações com validação causal.
          A saída final é objetiva: estado atual, risco estrutural e confiança.
        </p>
        <Link className="inline-flex text-sm text-cyan-300 hover:text-cyan-200" href="/methods">
          Ver metodologia completa
        </Link>
      </div>
      <PipelineFlow />
    </section>
  );
}
