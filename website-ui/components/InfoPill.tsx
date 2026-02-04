export default function InfoPill({ text }: { text: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-black/40 px-3 py-1 text-[10px] uppercase tracking-[0.3em] text-zinc-400">
      {text}
    </span>
  );
}
