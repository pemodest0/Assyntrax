"use client";

import { useMemo, useState } from "react";
import MethodLattice from "@/components/visuals/MethodLattice";
import PipelineFlow from "@/components/visuals/PipelineFlow";

const topics = [
  {
    id: "regimes",
    label: "Regimes",
    leigo:
      "Regime é o estado dinâmico do sistema: estável, transição, instável ou ruidoso, com persistência temporal e risco associado.",
    formal: (
      <>
        <p>Conjunto de estados com transições internas fortes e fronteiras observáveis.</p>
        <CodeBlock code={`regime_t in {STABLE, TRANSITION, UNSTABLE, NOISY}`} />
      </>
    ),
    aplicacao:
      "Regime estável permite projeção condicional; transição pede cautela; instável e ruidoso acionam bloqueio operacional.",
  },
  {
    id: "embedding",
    label: "Embedding (Takens)",
    leigo:
      "A série temporal é transformada em espaço de fase para expor geometria e recorrência do sistema, em vez de olhar apenas o preço.",
    formal: (
      <>
        <p>Embedding por atrasos:</p>
        <CodeBlock code={`X_t = [x_t, x_{t-tau}, x_{t-2tau}, ..., x_{t-(m-1)tau}]`} />
        <p className="mt-3">tau por AMI/ACF e m por Cao/FNN, com controle de ruído em janela.</p>
      </>
    ),
    aplicacao:
      "Revela perda de estrutura antes de ruptura visual no gráfico bruto.",
  },
  {
    id: "microstates",
    label: "Microestados",
    leigo:
      "Discretização do espaço dinâmico em estados locais persistentes para reduzir ruído sem destruir sinal estrutural.",
    formal: <CodeBlock code={`state_t = argmin_k || X_t - c_k ||`} />,
    aplicacao: "Permite medir persistência, frequência de transições e robustez do regime dominante.",
  },
  {
    id: "graphs",
    label: "Grafos e Markov",
    leigo:
      "As transições entre estados viram uma rede temporal. Entropia e conectividade indicam estabilidade ou fragilidade.",
    formal: (
      <>
        <p>Matriz de transição:</p>
        <CodeBlock code={`P_{ij} = count(i->j) / sum_j count(i->j)`} />
        <p className="mt-3">Entropia de Markov:</p>
        <CodeBlock code={`H = -sum_i pi_i sum_j P_{ij} log P_{ij}`} />
      </>
    ),
    aplicacao:
      "Conectividade excessiva e entropia alta tendem a aparecer antes de mudança de regime relevante.",
  },
  {
    id: "metrics",
    label: "Métricas",
    leigo:
      "Confiança, qualidade e instabilidade dizem se há base operacional ou se a leitura deve ficar só em diagnóstico.",
    formal: (
      <>
        <CodeBlock code={`confidence_t = sum_{j in regime} P_{ij}`} />
        <CodeBlock code={`instability_t = (1-confidence_t) + (1-quality_t) + entropy_norm`} />
      </>
    ),
    aplicacao:
      "Sem gate aprovado, o sistema bloqueia ação automática e preserva rastreabilidade.",
  },
  {
    id: "validation",
    label: "Validação",
    leigo:
      "Walk-forward, placebo, ablação e checagem de pseudo-bifurcação para separar estrutura real de ruído estatístico.",
    formal: (
      <>
        <p>Métricas: ROC-AUC, F1, MCC, MASE, TPR e estabilidade por regime.</p>
        <p>Sem vazamento temporal, sem ajuste retroativo e com auditoria por run_id.</p>
      </>
    ),
    aplicacao:
      "Se robustez cai, status muda para watch ou inconclusive e o produto entra em modo conservador.",
  },
];

export default function MethodsPage() {
  const [active, setActive] = useState(topics[0].id);
  const current = useMemo(() => topics.find((t) => t.id === active) || topics[0], [active]);

  return (
    <div className="space-y-10">
      <div className="relative isolate grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-10 items-center overflow-hidden">
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Métodos</div>
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
            Fundamentos científicos com execução prática
          </h1>
          <p className="text-zinc-300 max-w-3xl text-lg">
            Diagnóstico de estado antes de previsão. Esta página conecta conceito, formalismo,
            hipótese operacional e limitações de uso.
          </p>
        </div>
        <div className="overflow-hidden rounded-[28px]">
          <MethodLattice />
        </div>
      </div>

      <PipelineFlow />

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-8">
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
            <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">Detalhe técnico</div>
            <p className="text-sm text-zinc-400">
              Cada bloco responde três perguntas: o que é, como é modelado e como impacta a decisão operacional.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
            <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">{current.label}</div>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <InfoCard title="Contexto" content={current.leigo} />
              <InfoCard title="Formal" content={current.formal} />
              <InfoCard title="Uso operacional" content={current.aplicacao} />
            </div>
          </div>
        </section>
      </div>
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
