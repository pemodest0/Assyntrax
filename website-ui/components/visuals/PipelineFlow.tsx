const steps = [
  {
    title: "Dados",
    text: "Retornos por ativo com checagem de cobertura e consistência temporal.",
    details:
      "Ver mais: o run exige qualidade mínima de dados antes de calcular regime.",
  },
  {
    title: "Winsorização",
    text: "Tratamento de outliers por janela de 252 dias (0,5% a 99,5%).",
    details:
      "Ver mais: reduz distorções de choques extremos na matriz de correlação.",
  },
  {
    title: "Espectro",
    text: "Análise espectral da matriz de correlação para medir estrutura do sistema.",
    details:
      "Ver mais: extração de métricas como concentração de risco e dimensão efetiva.",
  },
  {
    title: "Regime",
    text: "Classificação causal walk-forward em estável, transição ou estresse.",
    details:
      "Ver mais: limiares calibrados somente com histórico disponível até cada data.",
  },
  {
    title: "Gate",
    text: "Publicação automática apenas quando checks mínimos são aprovados.",
    details:
      "Ver mais: run bloqueado quando cobertura, universo ou QA ficam abaixo do limite.",
  },
];

export default function PipelineFlow() {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-8">
      <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Pipeline do motor</div>
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-5 gap-4">
        {steps.map((s, idx) => (
          <div
            key={s.title}
            className="relative rounded-2xl border border-zinc-800 bg-black/60 p-4 h-full transition hover:-translate-y-1 hover:border-zinc-600"
          >
            <div className="absolute -top-3 left-4 text-[10px] uppercase tracking-[0.3em] text-zinc-500">
              {String(idx + 1).padStart(2, "0")}
            </div>
            <div className="text-sm font-semibold">{s.title}</div>
            <div className="mt-2 text-xs text-zinc-300">{s.text}</div>
            <details className="mt-3">
              <summary className="cursor-pointer text-xs text-cyan-300">Ver mais</summary>
              <p className="mt-2 text-xs text-zinc-400">{s.details}</p>
            </details>
          </div>
        ))}
      </div>
    </div>
  );
}

