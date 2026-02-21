import ProductMock from "@/components/visuals/ProductMock";
import Link from "next/link";

export default function ProductSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-8 lg:gap-10 items-center py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="space-y-3">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Produto</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">
          Painel + API: o mesmo diagnóstico para humanos e máquinas
        </h2>
        <p className="text-zinc-300 text-base lg:text-lg">
          Em vez de prometer retorno, o produto entrega leitura técnica auditável:
          cada execução informa regime, confiança, qualidade e motivo do gate.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-zinc-300">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
            Integração rápida com BI, alertas e rotinas de risco.
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
            Trilha auditável por execução e regras de bloqueio explícitas.
          </div>
        </div>
        <Link className="inline-flex text-sm text-cyan-300 hover:text-cyan-200" href="/product">
          Ver formato de saída e integração
        </Link>
      </div>
      <ProductMock />
    </section>
  );
}
