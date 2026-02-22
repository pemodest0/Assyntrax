import Link from "next/link";
import TransitionDiagram from "@/components/visuals/TransitionDiagram";

export default function ProblemSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[0.95fr_1.05fr] gap-8 lg:gap-10 items-center py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="rounded-[24px] border border-zinc-800 bg-zinc-950/60 p-8 ax-glow">
        <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">O problema</div>
        <h2 className="mt-3 text-3xl md:text-4xl font-semibold tracking-tight">
          Equipes erram quando o regime muda sem aviso operacional.
        </h2>
        <p className="mt-3 text-zinc-300 text-base lg:text-lg">
          O erro mais caro costuma vir da extrapolação de um cenário que já mudou.
          O Assyntrax identifica transição estrutural, mede confiança e sinaliza quando a leitura deve ficar em modo diagnóstico.
        </p>
        <Link className="mt-4 inline-flex text-sm text-cyan-300 hover:text-cyan-200" href="/methods">
          Ver como medimos transições
        </Link>
      </div>
      <TransitionDiagram />
    </section>
  );
}
