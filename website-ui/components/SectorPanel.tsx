import MetricsCard from "@/components/MetricsCard";
import RegimeChart from "@/components/RegimeChart";
import BenchmarkChart from "@/components/BenchmarkChart";
import InfoPill from "@/components/InfoPill";

type AssetRecord = {
  asset: string;
  timeframe: string;
  state?: { label: string; confidence?: number };
  quality?: { score?: number };
  metrics?: { escape_prob?: number; stretch_mu?: number };
  scores?: { stability_score?: number; predictability_score?: number };
  recommendation?: string;
};

type RegimePoint = { t: number; confidence: number; regime: string };
type BenchmarkPoint = { date: string; VIX?: number; NFCI?: number; USREC?: number };

export default function SectorPanel({
  title,
  assets,
  leadAsset,
  regimeSeries,
  benchmarks,
}: {
  title: string;
  assets: AssetRecord[];
  leadAsset?: string;
  regimeSeries: RegimePoint[];
  benchmarks: BenchmarkPoint[];
}) {
  const lead = assets.find((a) => a.asset === leadAsset) || assets[0];
  const recTone = lead?.recommendation === "USE" ? "good" : lead?.recommendation === "AVOID" ? "bad" : "warn";
  if (!assets.length) {
    return (
      <section className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-6 space-y-4">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">Setor</div>
        <h2 className="text-3xl font-semibold">{title}</h2>
        <div className="rounded-2xl border border-zinc-800 bg-black/40 p-4 text-sm text-zinc-300">
          Estamos calibrando este setor com dados reais. Resultados em breve.
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-6 space-y-6">
      <div>
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">Setor</div>
        <h2 className="mt-2 text-3xl font-semibold">{title}</h2>
        {assets.length < 2 ? (
          <div className="mt-3 rounded-xl border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-xs text-amber-200">
            Cobertura baixa neste setor. Exibindo apenas os ativos disponíveis.
          </div>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          <InfoPill text="Forecast condicional" />
          <InfoPill text="Regime + qualidade" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <MetricsCard
          title="Regime"
          value={lead?.state?.label ?? "--"}
          subtitle={lead ? `Confiança ${(lead.state?.confidence ?? 0).toFixed(2)}` : undefined}
          hint="Estado dinâmico atual do setor."
          tone={lead?.state?.label === "STABLE" ? "good" : lead?.state?.label === "UNSTABLE" ? "bad" : "warn"}
        />
        <MetricsCard
          title="Qualidade"
          value={lead?.quality?.score?.toFixed?.(2) ?? "--"}
          subtitle="Saúde do grafo"
          hint="Saúde do grafo: conectividade, entropia e cobertura."
        />
        <MetricsCard
          title="Escape"
          value={lead?.metrics?.escape_prob?.toFixed?.(2) ?? "--"}
          subtitle="Risco de saída do regime"
          hint="Probabilidade de sair do regime atual."
        />
        <MetricsCard
          title="Recomendação"
          value={lead?.recommendation ?? "--"}
          subtitle={`Previsibilidade ${(lead?.scores?.predictability_score ?? 0).toFixed(2)}`}
          hint="Use / Caution / Avoid baseado em regime, confiança e qualidade."
          tone={recTone}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-zinc-800 bg-black/40 p-4">
          <div className="text-sm text-zinc-400">Curva de regime (ativo líder)</div>
          <RegimeChart data={regimeSeries} />
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-black/40 p-4">
          <div className="text-sm text-zinc-400">Contexto de benchmark (VIX/NFCI)</div>
          <BenchmarkChart data={benchmarks} />
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-black/40 p-4">
        <div className="text-sm text-zinc-400">Ativos do setor</div>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 text-xs">
          {assets.map((a) => {
            const tone =
              a.state?.label === "STABLE" ? "border-emerald-500/40" : a.state?.label === "UNSTABLE" ? "border-rose-500/40" : "border-amber-500/40";
            const forecastActive =
              (a.state?.label === "STABLE") &&
              (a.quality?.score ?? 0) >= 0.7 &&
              (a.state?.confidence ?? 0) >= 0.6;
            return (
              <div key={a.asset} className={`rounded-xl border ${tone} bg-zinc-950/60 p-3`}>
                <div className="flex items-center justify-between">
                  <div className="text-zinc-200 font-semibold">{a.asset}</div>
                  <span className="text-[10px] uppercase text-zinc-500">{a.recommendation ?? "--"}</span>
                </div>
                <div className="text-zinc-500">{a.timeframe}</div>
                <div className="mt-2 text-zinc-300">Regime: {a.state?.label ?? "--"}</div>
                <div className="text-zinc-400">Confiança: {(a.state?.confidence ?? 0).toFixed(2)}</div>
                <div className="text-zinc-500">Qualidade: {(a.quality?.score ?? 0).toFixed(2)}</div>
                <div className="text-zinc-400">
                  Forecast: {forecastActive ? "Ativo" : "Bloqueado"}
                </div>
              </div>
            );
          })}
          {!assets.length ? <div className="text-zinc-500">Sem ativos no setor.</div> : null}
        </div>
      </div>
    </section>
  );
}
