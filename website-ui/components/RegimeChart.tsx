type RegimePoint = {
  t: number;
  confidence: number;
  regime: string;
};

const palette: Record<string, string> = {
  STABLE: "#34d399",
  TRANSITION: "#fbbf24",
  UNSTABLE: "#fb7185",
  NOISY: "#94a3b8",
};

export default function RegimeChart({ data }: { data: RegimePoint[] }) {
  if (!data.length) {
    return <div className="text-xs text-zinc-500">Sem dados de regime disponíveis.</div>;
  }
  const width = 560;
  const height = 180;
  const padding = 16;
  const xs = data.map((d) => d.t);
  const ys = data.map((d) => d.confidence);
  const xmin = Math.min(...xs);
  const xmax = Math.max(...xs);
  const ymin = Math.min(...ys);
  const ymax = Math.max(...ys);
  const scaleX = (x: number) => padding + ((x - xmin) / Math.max(1, xmax - xmin)) * (width - padding * 2);
  const scaleY = (y: number) =>
    height - padding - ((y - ymin) / Math.max(1e-6, ymax - ymin)) * (height - padding * 2);
  const path = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${scaleX(d.t)} ${scaleY(d.confidence)}`)
    .join(" ");
  const last = data[data.length - 1];
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3 text-xs text-zinc-400">
        <span>Último: {last?.regime ?? "--"}</span>
        <span>Confiança: {last?.confidence != null ? last.confidence.toFixed(2) : "--"}</span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: palette.STABLE }} />
          Estável
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: palette.TRANSITION }} />
          Transição
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: palette.UNSTABLE }} />
          Instável
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: palette.NOISY }} />
          Ruidoso
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-44">
        <defs>
          <linearGradient id="confGlow" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="rgba(56,189,248,0.4)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0)" />
          </linearGradient>
        </defs>
        <rect x="0" y="0" width={width} height={height} fill="rgba(0,0,0,0.35)" rx="16" />
        <path d={path} stroke="#7dd3fc" strokeWidth="2" fill="none" />
        <path d={`${path} L ${scaleX(xmax)} ${height - padding} L ${scaleX(xmin)} ${height - padding} Z`} fill="url(#confGlow)" />
        {data.map((d) => (
          <circle
            key={d.t}
            cx={scaleX(d.t)}
            cy={scaleY(d.confidence)}
            r="2.5"
            fill={palette[d.regime] || "#94a3b8"}
          />
        ))}
      </svg>
    </div>
  );
}
