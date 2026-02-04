import MetricsCard from "@/components/MetricsCard";
import RegimeChart from "@/components/RegimeChart";

type AssetRecord = {
  asset: string;
  state?: { label: string; confidence?: number };
  quality?: { score?: number };
  metrics?: { escape_prob?: number; stretch_mu?: number };
  recommendation?: string;
};

type RegimePoint = { t: number; confidence: number; regime: string };

export default function ComparePanel({
  left,
  right,
  leftSeries,
  rightSeries,
}: {
  left?: AssetRecord;
  right?: AssetRecord;
  leftSeries: RegimePoint[];
  rightSeries: RegimePoint[];
}) {
  return (
    <section className="rounded-3xl border border-zinc-800 bg-zinc-950/60 p-6 space-y-4">
      <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">Compare assets</div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-zinc-800 bg-black/40 p-4 space-y-3">
          <div className="text-sm text-zinc-300">A: {left?.asset ?? "--"}</div>
          <div className="grid grid-cols-2 gap-3">
            <MetricsCard title="Regime" value={left?.state?.label ?? "--"} />
            <MetricsCard title="Conf" value={(left?.state?.confidence ?? 0).toFixed(2)} />
            <MetricsCard title="Quality" value={(left?.quality?.score ?? 0).toFixed(2)} />
            <MetricsCard title="Escape" value={(left?.metrics?.escape_prob ?? 0).toFixed(2)} />
          </div>
          <RegimeChart data={leftSeries} />
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-black/40 p-4 space-y-3">
          <div className="text-sm text-zinc-300">B: {right?.asset ?? "--"}</div>
          <div className="grid grid-cols-2 gap-3">
            <MetricsCard title="Regime" value={right?.state?.label ?? "--"} />
            <MetricsCard title="Conf" value={(right?.state?.confidence ?? 0).toFixed(2)} />
            <MetricsCard title="Quality" value={(right?.quality?.score ?? 0).toFixed(2)} />
            <MetricsCard title="Escape" value={(right?.metrics?.escape_prob ?? 0).toFixed(2)} />
          </div>
          <RegimeChart data={rightSeries} />
        </div>
      </div>
    </section>
  );
}
