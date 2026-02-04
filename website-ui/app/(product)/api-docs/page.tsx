export default function ApiDocsPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">API Pública</h1>
        <p className="text-sm text-zinc-400">
          Endpoints para consumir diagnósticos e séries de regimes.
        </p>
      </header>

      <div className="rounded-xl border border-zinc-800 bg-black/40 p-4 text-sm text-zinc-200">
        <div className="font-semibold">Exemplos</div>
        <pre className="mt-3 whitespace-pre-wrap text-xs text-zinc-200">
{`GET /api/graph/universe?tf=weekly
GET /api/graph/regimes?asset=SPY&tf=weekly
GET /api/graph/series-batch?assets=SPY,QQQ&tf=weekly&limit=260
GET /api/graph/validation
GET /api/graph/hypertest`}
        </pre>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-black/40 p-4 text-sm text-zinc-200">
        <div className="font-semibold">Plano</div>
        <p className="mt-2 text-zinc-400">
          A API pública é voltada a exploração. Para uso comercial, consulte um plano dedicado.
        </p>
      </div>
    </div>
  );
}
