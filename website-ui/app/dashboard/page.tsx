"use client";

import AssetPicker from "@/components/AssetPicker";
import KPIBar from "@/components/KPIBar";
import RegimeCard from "@/components/RegimeCard";
import ForecastCard from "@/components/ForecastCard";
import WarningsPanel from "@/components/WarningsPanel";
import GroupRanking from "@/components/GroupRanking";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import PlotsGallery from "@/components/PlotsGallery";
import { AssetProvider } from "@/lib/asset-context";

export default function DashboardPage() {
  return (
    <AssetProvider>
      <div className="min-h-screen bg-gradient-to-br from-black via-zinc-950 to-black text-zinc-100">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <div className="flex items-start justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-3 py-1 text-xs text-zinc-400">
                Production · Regime/Risk Engine
              </div>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight">
                Assyntrax — Regimes &amp; Risk Dashboard
              </h1>
              <p className="text-sm text-zinc-400 mt-2">
                Regime/Risco como produto. Forecast como diagnóstico (sempre comparado ao naïve).
              </p>
            </div>
            <AssetPicker />
          </div>

        <div className="mt-8">
          <KPIBar />
        </div>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <RegimeCard />
            <WarningsPanel />
          </div>

          <div className="lg:col-span-2 space-y-6">
            <ForecastCard />
            <GroupRanking />
            <PlotsGallery />
          </div>
        </div>

        </div>
      </div>
    </AssetProvider>
  );
}
