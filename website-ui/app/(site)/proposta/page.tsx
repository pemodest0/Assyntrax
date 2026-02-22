import type { Metadata } from "next";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Proposta: piloto e integração",
  description:
    "Pacotes de entrega, estudo de caso e material comercial para validar o motor em piloto de 30 dias.",
  path: "/proposta",
  locale: "pt-BR",
});

export default function PropostaPage() {
  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Proposta</div>
        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">Proposta curta de uso do motor</h1>
        <p className="text-zinc-300 max-w-3xl text-lg">
          Leitura diária de risco estrutural com protocolo simples de diagnóstico. Objetivo: reduzir erro de decisão, sem prometer prever o dia exato da crise.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Básico">
          Painel diário, nível por setor e resumo semanal.
        </Card>
        <Card title="Completo">
          Painel + relatório diário + ranking de ativos e setores.
        </Card>
        <Card title="Sob medida">
          Regras customizadas e integração no fluxo do cliente.
        </Card>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h2 className="text-2xl font-semibold">Material pronto para reunião</h2>
        <div className="mt-3 flex flex-wrap gap-2 text-sm">
          <DocLink href="https://github.com/pemodest0/Assyntrax/blob/main/docs/venda/RELATORIO_EXECUTIVO_1_PAGINA.md" label="Relatório executivo (1 página)" />
          <DocLink href="https://github.com/pemodest0/Assyntrax/blob/main/docs/venda/ESTUDO_DE_CASO_REAL_SETOR.md" label="Estudo de caso real" />
          <DocLink href="https://github.com/pemodest0/Assyntrax/blob/main/docs/venda/DEMO_REUNIAO_GUIA.md" label="Guia de demo para reunião" />
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="O que faz">
          Detecta mudança estrutural de risco por setor e por ativo, com histórico de estado e explicação humana do alerta.
        </Card>
        <Card title="O que não faz">
          Não prevê data exata de crash, não garante retorno e não substitui decisão humana.
        </Card>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h2 className="text-2xl font-semibold">Próximo passo</h2>
        <p className="mt-3 text-zinc-300">
          Fechar piloto de 30 dias com critério objetivo de sucesso: acerto, ruído e utilidade para governança de risco.
        </p>
        <a
          href="/contact"
          className="mt-4 inline-flex rounded-xl border border-zinc-700 px-3 py-2 text-sm text-zinc-100 hover:border-zinc-500 transition"
        >
          Pedir proposta
        </a>
        <div className="mt-4 text-sm text-zinc-400">
          Referências: <code>docs/venda/PROPOSTA_CURTA.md</code> e <code>docs/venda/PACOTES_ENTREGA_3_NIVEIS.md</code>.
        </div>
      </section>
    </div>
  );
}

function DocLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      className="rounded-xl border border-zinc-700 px-3 py-2 text-zinc-100 hover:border-zinc-500 transition"
      href={href}
      target="_blank"
      rel="noreferrer"
    >
      {label}
    </a>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
      <div className="text-lg font-semibold">{title}</div>
      <div className="mt-3 text-sm text-zinc-300">{children}</div>
    </div>
  );
}
