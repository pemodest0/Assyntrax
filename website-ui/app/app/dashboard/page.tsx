import Link from "next/link";

export default function DashboardHome() {
  return (
    <div className="p-5 md:p-6 lg:p-8 space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/55 p-5">
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">Painel central</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Dashboard operacional</h1>
        <p className="mt-3 text-sm md:text-base text-zinc-300">
          Esta tela organiza o fluxo por domínio. Escolha o ambiente de análise para ver
          regime, confiança, qualidade e contexto operacional.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <DomainCard
          title="Finanças"
          text="Leitura de regime para ativos líquidos, com foco em risco estrutural e sinais acionáveis."
          href="/app/finance"
          cta="Abrir Finanças"
        />
        <DomainCard
          title="Imobiliário"
          text="Diagnóstico por cidade/UF com preço, liquidez, juros e transição de ciclo."
          href="/app/real-estate"
          cta="Abrir Imobiliário"
        />
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
        <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">Regra operacional</p>
        <p className="mt-2 text-sm text-zinc-300">
          O sistema responde três perguntas: se a leitura é confiável, se o estado atual é
          comum ou raro no histórico e o que deve ser evitado no momento.
        </p>
      </section>
    </div>
  );
}

function DomainCard({
  title,
  text,
  href,
  cta,
}: {
  title: string;
  text: string;
  href: string;
  cta: string;
}) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/55 p-5">
      <h2 className="text-xl font-semibold text-zinc-100">{title}</h2>
      <p className="mt-2 text-sm text-zinc-300">{text}</p>
      <Link
        href={href}
        className="inline-flex mt-4 rounded-xl border border-zinc-700 px-3 py-2 text-sm text-zinc-100 hover:border-zinc-500 transition"
      >
        {cta}
      </Link>
    </div>
  );
}
