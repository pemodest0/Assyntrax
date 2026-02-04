"use client";

import { useState } from "react";

export default function SimuladorPage() {
  const [preview, setPreview] = useState<string[]>([]);
  const [error, setError] = useState<string>("");

  function onFile(file: File | null) {
    if (!file) return;
    setError("");
    if (file.size > 5 * 1024 * 1024) {
      setError("Arquivo muito grande. Limite: 5MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || "");
      const lines = text.split(/\r?\n/).filter(Boolean);
      setPreview(lines.slice(0, 10));
    };
    reader.readAsText(file);
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Sandbox de Simulação</h1>
        <p className="text-sm text-zinc-400">
          Faça upload de um CSV com colunas <code>datetime,price</code> para diagnóstico.
        </p>
      </header>

      <div className="rounded-xl border border-zinc-800 bg-black/40 p-4">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => onFile(e.target.files?.[0] || null)}
          className="text-sm text-zinc-300"
        />
        {error && <div className="mt-2 text-sm text-rose-300">{error}</div>}
        <div className="mt-4 text-xs text-zinc-400">
          O diagnóstico completo requer o motor em execução no backend.
        </div>
        <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-black/60 p-3 text-xs text-zinc-200">
          {preview.length ? preview.join("\n") : "Aguardando upload..."}
        </pre>
      </div>
    </div>
  );
}
