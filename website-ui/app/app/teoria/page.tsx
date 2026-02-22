const sections = [
  {
    title: "Espaco probabilistico e causalidade",
    summary:
      "O modelo e formulado em filtragem temporal: em cada instante, usa apenas o que ja era observavel ate t-1. Isso impede uso de informacao futura.",
    formula: "F_t = sigma(X_1, ..., X_t) e decisao_t depende de F_{t-1}.",
    purpose: "Garante causalidade operacional e evita look-ahead no sinal publicado.",
  },
  {
    title: "Retornos e espectro",
    summary:
      "Transformamos preco em log-retorno para tornar variacoes aditivas e mais comparaveis entre ativos.",
    formula: "r_t = log(P_t / P_{t-1})",
    purpose: "A leitura espectral identifica componentes estruturais e separa oscilacao util de ruido.",
  },
  {
    title: "Teoria de matrizes aleatorias",
    summary:
      "Usamos limites de Marcenko-Pastur para diferenciar autovalores compatíveis com ruido de autovalores que carregam estrutura.",
    formula: "lambda fora da banda de Marcenko-Pastur => sinal estrutural.",
    purpose: "Evita confundir coincidencia estatistica com mudanca real de regime.",
  },
  {
    title: "Classificacao e validacao",
    summary:
      "A classificacao usa histerese para reduzir falso alarme e instabilidade de estado em janelas curtas.",
    formula: "status_t = hysteresis(status_raw_t, persistencia_minima)",
    purpose: "Recall e precisao sao avaliados em validacao temporal (walk-forward), sem reescrever o passado.",
  },
];

export default function TeoriaPage() {
  return (
    <div className="p-5 md:p-6 lg:p-8 space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5">
        <p className="text-xs tracking-[0.14em] uppercase text-zinc-500">Teoria</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Base matematica, linguagem acessivel</h1>
        <p className="mt-3 text-sm text-zinc-300">
          Esta pagina resume os fundamentos para executivos e comites, mantendo os conceitos auditaveis para times
          tecnicos.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map((item) => (
          <article key={item.title} className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5 space-y-3">
            <h2 className="text-lg font-semibold text-zinc-100">{item.title}</h2>
            <p className="text-sm text-zinc-300">{item.summary}</p>
            <pre className="rounded-xl border border-zinc-800 bg-black/60 p-3 text-xs text-zinc-200 overflow-x-auto">
              {item.formula}
            </pre>
            <p className="text-xs text-zinc-400">{item.purpose}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
