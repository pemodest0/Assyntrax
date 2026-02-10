"use client";

import { useEffect, useMemo, useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";

type BrMapProps = {
  selectedUF: string;
  onSelectUF: (uf: string) => void;
};

type HoverState = {
  name: string;
  sigla: string;
} | null;

type GeoFeatureProps = {
  name?: string;
  sigla?: string;
  UF?: string;
  uf?: string;
  NAME_1?: string;
};

const NAME_TO_UF: Record<string, string> = {
  acre: "AC",
  alagoas: "AL",
  amapa: "AP",
  amazonas: "AM",
  bahia: "BA",
  ceara: "CE",
  "distrito federal": "DF",
  "espirito santo": "ES",
  goias: "GO",
  maranhao: "MA",
  "mato grosso": "MT",
  "mato grosso do sul": "MS",
  "minas gerais": "MG",
  para: "PA",
  paraiba: "PB",
  parana: "PR",
  pernambuco: "PE",
  piaui: "PI",
  "rio de janeiro": "RJ",
  "rio grande do norte": "RN",
  "rio grande do sul": "RS",
  rondonia: "RO",
  roraima: "RR",
  "santa catarina": "SC",
  "sao paulo": "SP",
  sergipe: "SE",
  tocantins: "TO",
};

function normalizeText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function resolveUF(props: GeoFeatureProps): string {
  if (props.sigla) return props.sigla.toUpperCase();
  if (props.UF) return props.UF.toUpperCase();
  if (props.uf) return props.uf.toUpperCase();
  const name = props.name || props.NAME_1 || "";
  return NAME_TO_UF[normalizeText(name)] || "";
}

function resolveName(props: GeoFeatureProps): string {
  return props.name || props.NAME_1 || "Estado";
}

export default function BrMap({ selectedUF, onSelectUF }: BrMapProps) {
  const [geoData, setGeoData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hover, setHover] = useState<HoverState>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let mounted = true;

    fetch(`/geo/br-states.geojson?v=${reloadKey}`)
      .then((r) => {
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}`);
        }
        return r.json();
      })
      .then((json) => {
        if (!mounted) return;
        setGeoData(json);
      })
      .catch(() => {
        if (!mounted) return;
        setGeoData(null);
        setError("Falha ao carregar mapa (GeoJSON)");
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [reloadKey]);

  const mapBlock = useMemo(() => {
    if (loading) {
      return <div className="h-full w-full animate-pulse rounded-lg bg-zinc-900/70" />;
    }
    if (error || !geoData) {
      return (
        <div className="flex h-full w-full flex-col items-center justify-center gap-3 rounded-lg border border-zinc-800 bg-zinc-950/70 px-4 text-sm text-zinc-400">
          <div>{error || "Falha ao carregar mapa (GeoJSON)"}</div>
          <button
            className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-200 hover:border-zinc-500"
            onClick={() => {
              setLoading(true);
              setError(null);
              setGeoData(null);
              setReloadKey((k) => k + 1);
            }}
          >
            Recarregar mapa
          </button>
        </div>
      );
    }

    return (
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ scale: 680, center: [-52, -15] }}
        style={{ width: "100%", height: "100%" }}
      >
        <Geographies geography={geoData}>
          {({ geographies }: { geographies: Array<{ rsmKey: string; properties: unknown }> }) =>
            geographies.map((geo) => {
              const props = (geo.properties ?? {}) as GeoFeatureProps;
              const uf = resolveUF(props);
              const name = resolveName(props);
              const isSelected = uf === selectedUF;
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  onMouseEnter={() => setHover({ name, sigla: uf || "--" })}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => {
                    if (uf) onSelectUF(uf);
                  }}
                  style={{
                    default: {
                      fill: isSelected ? "rgba(251,146,60,0.35)" : "rgba(255,255,255,0.06)",
                      stroke: isSelected ? "rgba(251,146,60,0.85)" : "rgba(255,255,255,0.16)",
                      strokeWidth: isSelected ? 1.2 : 0.8,
                      outline: "none",
                    },
                    hover: {
                      fill: "rgba(168,85,247,0.24)",
                      stroke: "rgba(255,255,255,0.28)",
                      strokeWidth: 1.1,
                      outline: "none",
                      cursor: "pointer",
                    },
                    pressed: {
                      fill: "rgba(251,146,60,0.4)",
                      stroke: "rgba(251,146,60,1)",
                      strokeWidth: 1.25,
                      outline: "none",
                    },
                  }}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>
    );
  }, [loading, error, geoData, selectedUF, onSelectUF]);

  return (
    <div className="relative h-[460px] lg:h-[600px] w-full rounded-lg border border-zinc-800 bg-zinc-950/70 p-2">
      {mapBlock}
      {hover ? (
        <div className="pointer-events-none absolute right-3 top-3 rounded-md border border-zinc-700 bg-black/80 px-2 py-1 text-xs text-zinc-200">
          {hover.name} ({hover.sigla})
        </div>
      ) : null}
    </div>
  );
}
