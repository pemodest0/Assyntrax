export default function VendaPage() {
  return (
    <div className="p-5 md:p-6 lg:p-8 space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5">
        <p className="text-xs tracking-[0.14em] uppercase text-zinc-500">Venda</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">
          Assyntrax para gestores institucionais: diagnostico estrutural de risco
        </h1>
        <p className="mt-3 text-sm text-zinc-300">
          Solucao para comites e mesas que precisam reduzir subjetividade, manter trilha de decisao e reagir melhor a
          mudancas de regime.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Pack
          title="Basico"
          items={[
            "Dashboard operacional",
            "Relatorio diario de regime",
            "Acesso ao historico recente",
          ]}
        />
        <Pack
          title="Completo"
          items={[
            "Historico completo de execucoes",
            "Suporte de implantacao",
            "Camada de auditoria expandida",
          ]}
        />
        <Pack
          title="Sob medida"
          items={[
            "Customizacao de politicas e filtros",
            "Integracao por API",
            "Acompanhamento tecnico dedicado",
          ]}
        />
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
        <h2 className="text-lg font-semibold text-zinc-100">Valor pratico</h2>
        <ul className="mt-3 space-y-2 text-sm text-zinc-300">
          <li>- Mostrar mudanca de regime com criterio objetivo.</li>
          <li>- Reduzir subjetividade em ajustes de exposicao.</li>
          <li>- Manter registro historico para comite, investidor e auditoria.</li>
        </ul>
      </section>

      <section className="rounded-2xl border border-amber-800/40 bg-amber-950/15 p-5">
        <h2 className="text-lg font-semibold text-zinc-100">Limites declarados</h2>
        <ul className="mt-3 space-y-2 text-sm text-zinc-300">
          <li>- Nao preve data de crash.</li>
          <li>- Nao substitui decisao humana.</li>
          <li>- Nao garante retorno.</li>
        </ul>
      </section>
    </div>
  );
}

function Pack({ title, items }: { title: string; items: string[] }) {
  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-950/55 p-5">
      <h3 className="text-lg font-semibold text-zinc-100">{title}</h3>
      <ul className="mt-3 space-y-2 text-sm text-zinc-300">
        {items.map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
    </article>
  );
}
