import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

async function listReports() {
  const dir = path.join(repoRoot(), "results", "latest_graph", "assets");
  const items = await fs.readdir(dir);
  return items.filter((n) => n.endsWith("_report.md")).sort();
}

async function readReport(file: string) {
  const target = path.join(repoRoot(), "results", "latest_graph", "assets", file);
  return fs.readFile(target, "utf-8");
}

function renderMarkdown(text: string) {
  const lines = text.split("\n");
  const nodes: JSX.Element[] = [];
  let list: string[] = [];

  const flushList = () => {
    if (list.length) {
      nodes.push(
        <ul key={`ul-${nodes.length}`} className="list-disc pl-6 space-y-1 text-zinc-300">
          {list.map((item, idx) => (
            <li key={`${item}-${idx}`}>{item}</li>
          ))}
        </ul>
      );
      list = [];
    }
  };

  lines.forEach((line, idx) => {
    if (line.startsWith("# ")) {
      flushList();
      nodes.push(
        <h1 key={`h1-${idx}`} className="text-2xl font-semibold tracking-tight">
          {line.slice(2)}
        </h1>
      );
      return;
    }
    if (line.startsWith("## ")) {
      flushList();
      nodes.push(
        <h2 key={`h2-${idx}`} className="text-lg font-semibold tracking-tight mt-4">
          {line.slice(3)}
        </h2>
      );
      return;
    }
    if (line.startsWith("- ")) {
      list.push(line.slice(2));
      return;
    }
    if (line.trim() === "") {
      flushList();
      nodes.push(<div key={`sp-${idx}`} className="h-2" />);
      return;
    }
    flushList();
    nodes.push(
      <p key={`p-${idx}`} className="text-zinc-300">
        {line}
      </p>
    );
  });

  flushList();
  return nodes;
}

export default async function ReportsPage({
  searchParams,
}: {
  searchParams?: { file?: string };
}) {
  const reports = await listReports();
  const selected = searchParams?.file || reports[0];
  const content = selected ? await readReport(selected) : "No reports available.";

  return (
    <div className="p-6 grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6">
      <aside className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-4 card-depth">
        <div className="text-sm font-semibold">Reports</div>
        <div className="mt-3 space-y-2 text-sm">
          {reports.map((r) => (
            <a
              key={r}
              href={`/app/reports?file=${encodeURIComponent(r)}`}
              className={`block rounded-lg px-2 py-1 ${
                r === selected ? "bg-cyan-950/40 text-cyan-200" : "text-zinc-300 hover:text-white"
              }`}
            >
              {r.replace("_report.md", "")}
            </a>
          ))}
        </div>
      </aside>
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-6 card-depth">
        <div className="space-y-2">{renderMarkdown(content)}</div>
      </section>
    </div>
  );
}
