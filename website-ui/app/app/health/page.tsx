import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export default async function HealthPage() {
  let sanity: any = null;
  try {
    const target = path.join(repoRoot(), "results", "latest_graph", "sanity_summary.json");
    const text = await fs.readFile(target, "utf-8");
    sanity = JSON.parse(text);
  } catch {
    sanity = null;
  }

  return (
    <div className="p-6">
      <div className="text-2xl font-semibold tracking-tight">System Health</div>
      <div className="text-sm text-zinc-400 mt-1">Sanity checks from latest_graph.</div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Pipeline status" value="Online" />
        <Card title="Sanity file" value={sanity ? "Found" : "Missing"} />
        <Card title="Checked assets" value={sanity ? String(Object.keys(sanity).length) : "0"} />
      </div>

      <div className="mt-6 rounded-2xl border border-zinc-800 bg-zinc-950/30 p-4 text-sm text-zinc-300">
        {sanity ? <pre className="whitespace-pre-wrap">{JSON.stringify(sanity, null, 2)}</pre> : "No sanity data."}
      </div>
    </div>
  );
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-4">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{title}</div>
      <div className="mt-2 text-2xl font-semibold tracking-tight">{value}</div>
    </div>
  );
}
