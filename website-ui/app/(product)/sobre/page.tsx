export default function SobrePage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Metodologia & História</h1>
        <p className="text-sm text-zinc-400">
          Diagnóstico de regimes com foco em transparência e robustez.
        </p>
      </header>

      <section className="space-y-3 rounded-xl border border-zinc-800 bg-black/40 p-4">
        <h2 className="text-sm font-semibold">O que é um regime dinâmico?</h2>
        <p className="text-sm text-zinc-300">
          Um regime é um estado persistente do sistema (estável, transicional, instável).
          O motor identifica mudanças estruturais para evitar previsões cegas.
        </p>
      </section>

      <section className="space-y-3 rounded-xl border border-zinc-800 bg-black/40 p-4">
        <h2 className="text-sm font-semibold">Embedding, microestados e grafos</h2>
        <p className="text-sm text-zinc-300">
          A série é reconstruída via embedding de atraso; microestados agrupam a dinâmica;
          a matriz de transição gera o grafo e os regimes metastáveis.
        </p>
      </section>

      <section className="space-y-3 rounded-xl border border-zinc-800 bg-black/40 p-4">
        <h2 className="text-sm font-semibold">Como evitamos overfit</h2>
        <p className="text-sm text-zinc-300">
          Validação walk-forward, comparação com baselines e alertas quando a estrutura é fraca.
          O motor alerta quando a confiança é baixa ou a qualidade do grafo é insuficiente.
        </p>
      </section>

      <section className="space-y-3 rounded-xl border border-zinc-800 bg-black/40 p-4">
        <h2 className="text-sm font-semibold">Linha do tempo</h2>
        <ul className="text-sm text-zinc-300 list-disc pl-5">
          <li>Motor inicial: regimes com clustering clássico.</li>
          <li>Graph Engine: regimes metastáveis com validação estendida.</li>
          <li>Benchmarks: comparação com séries oficiais e métricas balanceadas.</li>
        </ul>
      </section>
    </div>
  );
}
