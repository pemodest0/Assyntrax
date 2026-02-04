export default function MetricsCard({
  title,
  value,
  subtitle,
  hint,
  tone = "default",
}: {
  title: string;
  value: string;
  subtitle?: string;
  hint?: string;
  tone?: "default" | "good" | "warn" | "bad";
}) {
  const toneClass =
    tone === "good"
      ? "border-emerald-500/40 text-emerald-200"
      : tone === "warn"
      ? "border-amber-500/40 text-amber-200"
      : tone === "bad"
      ? "border-rose-500/40 text-rose-200"
      : "border-zinc-800 text-zinc-200";
  return (
    <div className={`rounded-2xl border bg-black/40 p-4 ${toneClass}`} title={hint}>
      <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">{title}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {subtitle ? <div className="mt-1 text-xs text-zinc-400">{subtitle}</div> : null}
    </div>
  );
}
