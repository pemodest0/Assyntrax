"use client";

import { useEffect, useState } from "react";

export function useRegimeData(asset: string, tf: string) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!asset) return;
    const timer = setTimeout(() => setLoading(true), 0);
    fetch(`/api/regime?asset=${asset}&tf=${tf}`)
      .then((r) => r.json())
      .then((j: Record<string, unknown>) => setData(j))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
    return () => clearTimeout(timer);
  }, [asset, tf]);

  return { data, loading };
}
