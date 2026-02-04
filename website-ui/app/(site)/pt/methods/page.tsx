"use client";

import { useMemo, useState } from "react";

const topics = [
  {
    id: "regimes",
    label: "Regimes",
    leigo: "Um regime é o estado dinâmico do sistema: estável, em transição, instável ou ruidoso.",
    formal: (
      <>
        <p>Regime = conjunto de estados com transições internas fortes.</p>
        <CodeBlock code={`regime_t ∈ {STABLE, TRANSITION, UNSTABLE, NOISY}`} />
      </>
    ),
    aplicacao:
      "Regimes estáveis permitem previsão; transição pede cautela; instável bloqueia sinal.",
  },
  {
    id: "embedding",
    label: "Embedding (Takens)",
    leigo: "Transformamos a série em espaço de fase para enxergar a geometria do sistema.",
    formal: (
      <>
        <p>Embedding por atrasos:</p>
        <CodeBlock code={`X_t = [x_t, x_{t-τ}, x_{t-2τ}, ..., x_{t-(m-1)τ}]`} />
        <p className="mt-3">τ via AMI/ACF e m via Cao/FNN.</p>
      </>
    ),
    aplicacao: "Revela estabilidade local e transições que séries cruas escondem.",
  },
  {
    id: "microstates",
    label: "Microestados",
    leigo: "Dividimos o espaço em pequenos estados (clusters) para discretizar a dinâmica.",
    formal: <CodeBlock code={`state_t = argmin_k || X_t - c_k ||`} />,
    aplicacao: "Permite contar transições e montar o grafo do sistema.",
  },
  {
    id: "graphs",
    label: "Grafos & Markov",
    leigo: "Contamos como o sistema transita entre microestados e medimos conectividade.",
    formal: (
      <>
        <p>Matriz de transição:</p>
        <CodeBlock code={`P_{ij} = count(i→j) / sum_j count(i→j)`} />
        <p className="mt-3">Entropia de Markov:</p>
        <CodeBlock code={`H = -∑_i π_i ∑_j P_{ij} log P_{ij}`} />
      </>
    ),
    aplicacao: "Conectividade e entropia indicam estabilidade e risco.",
  },
  {
    id: "metrics",
    label: "Métricas (confiança, escape, stretch, qualidade)",
    leigo: "Medimos confiança, risco de fuga e qualidade do grafo para decidir se há estrutura.",
    formal: (
      <>
        <CodeBlock code={`conf_t = ∑_{j∈regime} P_{ij}`} />
        <CodeBlock code={`escape_t = 1 - conf_t`} />
      </>
    ),
    aplicacao: "Essas métricas ligam previsão apenas quando há estrutura confiável.",
  },
  {
    id: "forecast",
    label: "Forecast (condicional)",
    leigo: "O forecast só aparece quando regime e qualidade estão altos.",
    formal: (
      <CodeBlock
        code={`forecast_visible = (state == STABLE) && (quality ≥ q*)`}
      />
    ),
    aplicacao: "Se o sinal é fraco, bloqueamos previsão e mostramos aviso.",
  },
  {
    id: "validation",
    label: "Validação (sem maquiagem)",
    leigo: "Testamos em walk-forward e sempre com baselines.",
    formal: (
      <>
        <p>Métricas: ROC-AUC, F1, MASE, Directional Accuracy.</p>
        <p>Sem vazamento. Sem ajuste retroativo.</p>
      </>
    ),
    aplicacao: "Se o sinal é fraco, o sistema marca DIREÇÃO_FRACA ou REGIME_INSTÁVEL.",
  },
];

export default function MethodsPage() {
  const [active, setActive] = useState(topics[0].id);
  const current = useMemo(() => topics.find((t) => t.id === active) || topics[0], [active]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-8">
      <aside className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 h-fit">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">Tópicos</div>
        <div className="mt-4 flex flex-col gap-2">
          {topics.map((t) => (
            <button
              key={t.id}
              className={`text-left rounded-xl px-3 py-2 text-sm transition ${
                t.id === active
                  ? "bg-zinc-100 text-black"
                  : "text-zinc-300 hover:bg-zinc-900/60"
              }`}
              onClick={() => setActive(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </aside>

      <section className="space-y-6">
        <div className="space-y-3">
          <h1 className="text-4xl font-semibold tracking-tight">Métodos &amp; Filosofia</h1>
          <p className="text-zinc-300 max-w-3xl">
            Diagnosticamos o estado do sistema. Forecast sem consciência de regime é extrapolação
            cega. Selecione um tópico para ver a explicação leiga, o formalismo e a aplicação.
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">{current.label}</div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <InfoCard title="Para leigos" content={current.leigo} />
            <InfoCard title="Formal" content={current.formal} />
            <InfoCard title="Aplicação" content={current.aplicacao} />
          </div>
        </div>
      </section>
    </div>
  );
}

function InfoCard({ title, content }: { title: string; content: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="text-sm uppercase tracking-[0.2em] text-zinc-400">{title}</div>
      <div className="mt-3 text-sm text-zinc-300">{content}</div>
    </div>
  );
}

function CodeBlock({ code }: { code: string }) {
  return (
    <pre className="mt-3 rounded-xl border border-zinc-800 bg-black/60 p-4 text-xs text-zinc-200 overflow-x-auto">
      {code}
    </pre>
  );
}
