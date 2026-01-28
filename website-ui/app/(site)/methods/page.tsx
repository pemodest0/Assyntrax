export default function MethodsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-semibold tracking-tight">Métodos</h1>
      <p className="text-zinc-300 max-w-3xl">
        O produto não promete “prever preço”. Ele detecta <b>mudanças de estado</b> do sistema:
        volatilidade alta/baixa, instabilidade e transições. Forecast existe como diagnóstico,
        sempre comparado ao naïve.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Regime de risco (V1)">
          Classificação de vol alta/baixa com modelos simples e robustos (LogReg/RF). Métricas:
          ROC‑AUC, F1, balanced accuracy.
        </Card>
        <Card title="Motor físico (R&amp;D)">
          Reconstrução de espaço de fase (Takens) + assinaturas geométricas
          (recorrência/entropia) para diagnóstico.
        </Card>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="text-lg font-semibold">{title}</div>
      <div className="mt-2 text-sm text-zinc-300">{children}</div>
    </div>
  );
}
