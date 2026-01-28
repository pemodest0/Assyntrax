"use client";

export default function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-6 w-40 rounded bg-zinc-800 animate-pulse" />
      <div className="h-24 rounded-2xl bg-zinc-900/60 border border-zinc-800 animate-pulse" />
      <div className="h-24 rounded-2xl bg-zinc-900/60 border border-zinc-800 animate-pulse" />
      <div className="h-24 rounded-2xl bg-zinc-900/60 border border-zinc-800 animate-pulse" />
    </div>
  );
}
