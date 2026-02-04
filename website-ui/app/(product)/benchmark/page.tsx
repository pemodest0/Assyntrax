"use client";

import { useEffect, useState } from "react";

export default function BenchmarkPage() {
  const [validation, setValidation] = useState<any>(null);
  const [hyper, setHyper] = useState<any>(null);

  useEffect(() => {
    fetch("/api/graph/validation")
      .then((r) => r.json())
      .then(setValidation)
      .catch(() => setValidation({ error: "validation_not_found" }));
    fetch("/api/graph/hypertest")
      .then((r) => r.json())
      .then(setHyper)
      .catch(() => setHyper({ error: "hypertest_not_found" }));
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Benchmarks & Validação</h1>
        <p className="text-sm text-zinc-400">
          Comparativos do motor com referências oficiais e testes de robustez.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
          <div className="text-sm font-semibold">Validação Oficial</div>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap text-xs text-zinc-200">
            {validation ? JSON.stringify(validation, null, 2) : "Carregando..."}
          </pre>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
          <div className="text-sm font-semibold">Hypertest</div>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap text-xs text-zinc-200">
            {hyper ? JSON.stringify(hyper, null, 2) : "Carregando..."}
          </pre>
        </div>
      </div>
    </div>
  );
}
