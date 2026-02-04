type BenchmarkPoint = {
  date: string;
  VIX?: number;
  NFCI?: number;
  USREC?: number;
};

export default function BenchmarkChart({ data }: { data: BenchmarkPoint[] }) {
  if (!data.length) {
    return <div className="text-xs text-zinc-500">Sem dados de benchmark.</div>;
  }
  const width = 560;
  const height = 180;
  const padding = 16;
  const xs = data.map((_, i) => i);
  const vix = data.map((d) => (d.VIX == null ? 0 : d.VIX));
  const xmin = 0;
  const xmax = Math.max(1, xs.length - 1);
  const ymin = Math.min(...vix);
  const ymax = Math.max(...vix);
  const scaleX = (x: number) => padding + ((x - xmin) / Math.max(1, xmax - xmin)) * (width - padding * 2);
  const scaleY = (y: number) =>
    height - padding - ((y - ymin) / Math.max(1e-6, ymax - ymin)) * (height - padding * 2);
  const path = vix.map((y, i) => `${i === 0 ? "M" : "L"} ${scaleX(i)} ${scaleY(y)}`).join(" ");
  const last = data[data.length - 1];
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3 text-xs text-zinc-400">
        <span>VIX (último): {last?.VIX?.toFixed?.(2) ?? "--"}</span>
        <span>NFCI: {last?.NFCI?.toFixed?.(2) ?? "--"}</span>
        <span>USREC: {last?.USREC ?? "--"}</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-44">
        <rect x="0" y="0" width={width} height={height} fill="rgba(0,0,0,0.35)" rx="16" />
        <path d={path} stroke="#f97316" strokeWidth="2" fill="none" />
      </svg>
    </div>
  );
}
