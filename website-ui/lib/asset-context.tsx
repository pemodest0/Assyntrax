"use client";

import { createContext, useContext, useMemo, useState } from "react";

type AssetState = {
  asset: string;
  timeframe: string;
  setAsset: (asset: string) => void;
  setTimeframe: (timeframe: string) => void;
};

const AssetContext = createContext<AssetState | null>(null);

export function AssetProvider({ children }: { children: React.ReactNode }) {
  const [asset, setAsset] = useState("SPY");
  const [timeframe, setTimeframe] = useState("daily");
  const value = useMemo(
    () => ({ asset, timeframe, setAsset, setTimeframe }),
    [asset, timeframe]
  );
  return <AssetContext.Provider value={value}>{children}</AssetContext.Provider>;
}

export function useAsset() {
  const ctx = useContext(AssetContext);
  if (!ctx) throw new Error("useAsset must be used within AssetProvider");
  return ctx;
}
