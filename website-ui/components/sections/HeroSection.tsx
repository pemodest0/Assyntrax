import Link from "next/link";
import SectorRegimeShowcase from "@/components/visuals/SectorRegimeShowcase";

export default function HeroSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[1.08fr_0.92fr] gap-8 lg:gap-10 items-center min-h-[70vh] lg:min-h-[74vh] py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="rounded-[28px] border border-zinc-800 bg-zinc-950/70 p-8 lg:p-10 backdrop-blur ax-glow">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Diagnóstico de regime e risco estrutural</div>
        <h1 className="mt-5 text-4xl md:text-5xl font-semibold tracking-tight">
          Diagnóstico causal para monitorar mudança de regime no mercado
        </h1>
        <p className="mt-4 text-zinc-300 max-w-2xl text-base lg:text-lg">
          O motor mede estrutura de correlação, classifica estado do sistema e publica somente quando
          os critérios mínimos passam no gate de qualidade.
        </p>
        <ul className="mt-5 space-y-2 text-sm text-zinc-300">
          <li>Sem look-ahead: cálculo causal em modo walk-forward.</li>
          <li>Saída com regime, risco estrutural e confiança do sinal.</li>
          <li>Mesma leitura no painel, API e artefatos de auditoria.</li>
        </ul>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            className="rounded-xl bg-zinc-100 text-black px-5 py-3 font-medium hover:bg-white transition"
            href="/contact"
          >
            Pedir demo
          </Link>
          <Link
            className="rounded-xl border border-zinc-800 px-5 py-3 text-zinc-200 hover:border-zinc-600 transition"
            href="/app/dashboard"
          >
            Abrir app
          </Link>
        </div>
        <div className="mt-4 text-xs text-zinc-500">
          Sem promessa de retorno. Uso focado em risco, governança e auditoria.
        </div>
      </div>
      <div className="animate-float-slow">
        <SectorRegimeShowcase />
      </div>
    </section>
  );
}
