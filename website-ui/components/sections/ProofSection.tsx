import Link from "next/link";
import ProofMatrix from "@/components/visuals/ProofMatrix";

export default function ProofSection() {
  return (
    <section className="space-y-6 py-10 md:py-12 lg:py-14 xl:py-16">
      <div className="space-y-2">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Prova e rigor</div>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Métricas transparentes com limites explícitos</h2>
        <p className="text-zinc-300 max-w-3xl text-base lg:text-lg">
          Validação com walk-forward e baselines simples.
          Quando não existe estrutura suficiente, o sistema marca diagnóstico inconclusivo.
        </p>
        <Link className="inline-flex text-sm text-cyan-300 hover:text-cyan-200" href="/methods">
          Abrir metodologia e evidências
        </Link>
      </div>
      <ProofMatrix />
      <div className="text-xs text-zinc-500">
        Resultado para gestão de risco, não para promessa de retorno financeiro.
      </div>
    </section>
  );
}
