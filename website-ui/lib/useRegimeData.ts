"use client";

import { useEffect, useState } from "react";

export function useRegimeData(asset: string, tf: string) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!asset) return;
    setLoading(true);
    fetch(`/api/regime?asset=${asset}&tf=${tf}`)
      .then((r) => r.json())
      .then((j) => setData(j))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [asset, tf]);
  return { data, loading };
}
