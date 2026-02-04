import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

async function readDoc(name: string) {
  const p = path.join(repoRoot(), "docs", name);
  return fs.readFile(p, "utf-8");
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
        <h1 key={`h1-${idx}`} className="text-3xl font-semibold tracking-tight">
          {line.slice(2)}
        </h1>
      );
      return;
    }
    if (line.startsWith("## ")) {
      flushList();
      nodes.push(
        <h2 key={`h2-${idx}`} className="text-xl font-semibold tracking-tight mt-4">
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

export default async function PrinciplesPage() {
  const [principles, spec, thesis] = await Promise.all([
    readDoc("PRINCIPLES.md"),
    readDoc("DASHBOARD_SPEC.md"),
    readDoc("PRODUCT_THESIS.md"),
  ]);
  const methodsStudy = await readDoc("REGIME_METHODS_STUDY.md");

  return (
    <div className="p-6 space-y-8">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-6 card-depth">
        <div className="text-xs uppercase tracking-[0.3em] text-cyan-200/60">Ideia central</div>
        <div className="mt-3 text-2xl font-semibold tracking-tight">Princípios</div>
        <div className="mt-4 space-y-2">{renderMarkdown(principles)}</div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-6 card-depth">
        <div className="text-xs uppercase tracking-[0.3em] text-cyan-200/60">Dashboard</div>
        <div className="mt-3 text-2xl font-semibold tracking-tight">Spec</div>
        <div className="mt-4 space-y-2">{renderMarkdown(spec)}</div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-6 card-depth">
        <div className="text-xs uppercase tracking-[0.3em] text-cyan-200/60">Product</div>
        <div className="mt-3 text-2xl font-semibold tracking-tight">Thesis</div>
        <div className="mt-4 space-y-2">{renderMarkdown(thesis)}</div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-6 card-depth">
        <div className="text-xs uppercase tracking-[0.3em] text-cyan-200/60">Methods</div>
        <div className="mt-3 text-2xl font-semibold tracking-tight">Regime Study</div>
        <div className="mt-4 space-y-2">{renderMarkdown(methodsStudy)}</div>
      </div>
    </div>
  );
}
