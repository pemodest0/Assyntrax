import Link from "next/link";

export default function VendaPage() {
  return (
    <div className="p-4 md:p-6 space-y-5">
      <section className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5 md:p-6">
        <div className="pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full bg-cyan-500/15 blur-3xl animate-glow" />
        <div className="pointer-events-none absolute -right-20 -bottom-20 h-64 w-64 rounded-full bg-orange-500/10 blur-3xl animate-glow" />
        <div className="relative z-10">
          <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Produto e venda</div>
          <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Assyntrax para operação institucional</h1>
          <p className="mt-3 text-sm text-zinc-300 max-w-3xl">
            Diagnóstico estrutural diário com rastreabilidade completa. Sem promessa de retorno, sem recomendação de compra ou venda.
            Foco real em risco, governança e clareza operacional.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/contact" className="rounded-md border border-cyan-600/70 bg-cyan-950/30 px-3 py-2 text-xs text-cyan-200 hover:border-cyan-400 transition">
              Pedir demonstração
            </Link>
            <Link href="/app/dashboard" className="rounded-md border border-zinc-700 px-3 py-2 text-xs text-zinc-100 hover:border-zinc-500 transition">
              Abrir painel
            </Link>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Básico" items={["Dashboard diário", "Leitura por ativo", "Resumo semanal"]} />
        <Card title="Completo" items={["Tudo do básico", "Relatório diário em texto", "Histórico de mudança de regime"]} />
        <Card title="Sob medida" items={["Tudo do completo", "Regras customizadas", "Integração com fluxo interno"]} />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
          <div className="text-sm uppercase tracking-widest text-zinc-400">Valor prático</div>
          <ul className="mt-2 space-y-1 text-sm text-zinc-300">
            <li>1. Mostra quando o mercado muda de estrutura.</li>
            <li>2. Reduz leitura subjetiva com métricas auditáveis.</li>
            <li>3. Mantém histórico para revisão e governança.</li>
          </ul>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
          <div className="text-sm uppercase tracking-widest text-zinc-400">Limites transparentes</div>
          <ul className="mt-2 space-y-1 text-sm text-zinc-300">
            <li>1. Não prevê data exata de crash.</li>
            <li>2. Não substitui decisão humana.</li>
            <li>3. Não garante retorno futuro.</li>
          </ul>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
        <div className="text-sm uppercase tracking-widest text-zinc-400">Materiais para reunião</div>
        <div className="mt-2 text-xs text-zinc-400 leading-relaxed">
          Conteúdo pronto para proposta, discussão técnica e apresentação executiva.
        </div>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <DocLink href="https://github.com/pemodest0/Assyntrax/blob/main/docs/venda/PROPOSTA_CURTA.md" label="Proposta curta" desc="Resumo de escopo e entrega." />
          <DocLink href="https://github.com/pemodest0/Assyntrax/blob/main/docs/venda/PACOTES_ENTREGA_3_NIVEIS.md" label="Pacotes" desc="Básico, completo e sob medida." />
          <DocLink href="https://github.com/pemodest0/Assyntrax/blob/main/docs/venda/RELATORIO_EXECUTIVO_1_PAGINA.md" label="Executivo 1 página" desc="Versão para decisores." />
          <DocLink href="https://github.com/pemodest0/Assyntrax/blob/main/docs/venda/ESTUDO_DE_CASO_REAL_SETOR.md" label="Estudo de caso" desc="Exemplo real de aplicação." />
          <DocLink href="https://github.com/pemodest0/Assyntrax/blob/main/docs/venda/DEMO_REUNIAO_GUIA.md" label="Roteiro de demo" desc="Passo a passo da reunião." />
        </div>
      </section>
    </div>
  );
}

function Card({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 transition hover:border-zinc-600">
      <div className="text-lg font-semibold text-zinc-100">{title}</div>
      <ul className="mt-2 space-y-1 text-sm text-zinc-300">
        {items.map((x) => (
          <li key={x}>- {x}</li>
        ))}
      </ul>
    </div>
  );
}

function DocLink({ href, label, desc }: { href: string; label: string; desc: string }) {
  return (
    <a
      className="rounded-md border border-zinc-700 px-2 py-1 text-zinc-200 hover:border-zinc-500 hover:text-white transition"
      href={href}
      target="_blank"
      rel="noreferrer"
      title={desc}
      aria-label={`${label}: ${desc}`}
    >
      {label}
    </a>
  );
}
