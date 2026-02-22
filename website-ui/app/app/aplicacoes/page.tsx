import { readLatestSnapshot, readRiskTruthPanel } from "@/lib/server/data";

function toNum(v: unknown, fallback = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

const steps = [
  "Acesse o painel pela manha e confirme run_id, gate e status operacional.",
  "Veja o nivel do dia (verde, amarelo, vermelho) e o regime dominante.",
  "Verifique setores e ativos criticos com maior risco estrutural.",
  "Ajuste exposicao por faixa de risco, sem buscar previsao de preco.",
  "Registre a decisao no comite com justificativa e referencia do run.",
];

export default async function AplicacoesPage() {
  const [snap, panel] = await Promise.all([readLatestSnapshot(), readRiskTruthPanel()]);
  const counts = (panel?.counts || {}) as Record<string, unknown>;

  return (
    <div className="p-5 md:p-6 lg:p-8 space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5">
        <p className="text-xs tracking-[0.14em] uppercase text-zinc-500">Aplicacoes</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Tutorial operacional de uso diario</h1>
        <p className="mt-3 text-sm text-zinc-300">
          Fluxo recomendado para transformar o diagnostico estrutural em decisao disciplinada e auditavel.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-5 gap-3">
        <Kpi title="Run atual" value={String(snap?.runId || "n/a")} />
        <Kpi title="Ativos" value={String(toNum(counts.assets, 0))} />
        <Kpi title="Validated" value={String(toNum(counts.validated, 0))} />
        <Kpi title="Watch" value={String(toNum(counts.watch, 0))} />
        <Kpi title="Inconclusive" value={String(toNum(counts.inconclusive, 0))} />
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
        <h2 className="text-lg font-semibold text-zinc-100">Passo a passo</h2>
        <ol className="mt-3 space-y-2 text-sm text-zinc-300">
          {steps.map((step, idx) => (
            <li key={step}>
              {idx + 1}. {step}
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5 space-y-2">
        <h2 className="text-lg font-semibold text-zinc-100">Grafico de efeito acumulado</h2>
        <p className="text-sm text-zinc-300">
          A curva verde representa crescimento controlado com reducao de drawdown em relacao ao benchmark bruto.
        </p>
        <p className="text-sm text-zinc-400">
          Leitura principal: o valor vem de evitar erros graves em mudancas de regime, nao de prever o proximo movimento
          de preco.
        </p>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5">
        <p className="text-sm text-zinc-300">
          Ganho de capital vem de reduzir erros de alocacao, nao de previsoes milagrosas.
        </p>
      </section>
    </div>
  );
}

function Kpi({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
      <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">{title}</div>
      <div className="mt-2 text-lg font-semibold text-zinc-100">{value}</div>
    </div>
  );
}
