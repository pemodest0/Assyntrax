(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/components/BrMap.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>BrMap
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2d$simple$2d$maps$2f$dist$2f$index$2e$umd$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react-simple-maps/dist/index.umd.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
const NAME_TO_UF = {
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
    tocantins: "TO"
};
function normalizeText(value) {
    return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}
function resolveUF(props) {
    if (props.sigla) return props.sigla.toUpperCase();
    if (props.UF) return props.UF.toUpperCase();
    if (props.uf) return props.uf.toUpperCase();
    const name = props.name || props.NAME_1 || "";
    return NAME_TO_UF[normalizeText(name)] || "";
}
function resolveName(props) {
    return props.name || props.NAME_1 || "Estado";
}
function BrMap({ selectedUF, onSelectUF }) {
    _s();
    const [geoData, setGeoData] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const [error, setError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [hover, setHover] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [reloadKey, setReloadKey] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(0);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BrMap.useEffect": ()=>{
            let mounted = true;
            fetch(`/geo/br-states.geojson?v=${reloadKey}`).then({
                "BrMap.useEffect": (r)=>{
                    if (!r.ok) {
                        throw new Error(`HTTP ${r.status}`);
                    }
                    return r.json();
                }
            }["BrMap.useEffect"]).then({
                "BrMap.useEffect": (json)=>{
                    if (!mounted) return;
                    setGeoData(json);
                }
            }["BrMap.useEffect"]).catch({
                "BrMap.useEffect": ()=>{
                    if (!mounted) return;
                    setGeoData(null);
                    setError("Falha ao carregar mapa (GeoJSON)");
                }
            }["BrMap.useEffect"]).finally({
                "BrMap.useEffect": ()=>{
                    if (!mounted) return;
                    setLoading(false);
                }
            }["BrMap.useEffect"]);
            return ({
                "BrMap.useEffect": ()=>{
                    mounted = false;
                }
            })["BrMap.useEffect"];
        }
    }["BrMap.useEffect"], [
        reloadKey
    ]);
    const mapBlock = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "BrMap.useMemo[mapBlock]": ()=>{
            if (loading) {
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "h-full w-full animate-pulse rounded-lg bg-zinc-900/70"
                }, void 0, false, {
                    fileName: "[project]/components/BrMap.tsx",
                    lineNumber: 112,
                    columnNumber: 14
                }, this);
            }
            if (error || !geoData) {
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex h-full w-full flex-col items-center justify-center gap-3 rounded-lg border border-zinc-800 bg-zinc-950/70 px-4 text-sm text-zinc-400",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            children: error || "Falha ao carregar mapa (GeoJSON)"
                        }, void 0, false, {
                            fileName: "[project]/components/BrMap.tsx",
                            lineNumber: 117,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            className: "rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-200 hover:border-zinc-500",
                            onClick: {
                                "BrMap.useMemo[mapBlock]": ()=>{
                                    setLoading(true);
                                    setError(null);
                                    setGeoData(null);
                                    setReloadKey({
                                        "BrMap.useMemo[mapBlock]": (k)=>k + 1
                                    }["BrMap.useMemo[mapBlock]"]);
                                }
                            }["BrMap.useMemo[mapBlock]"],
                            children: "Recarregar mapa"
                        }, void 0, false, {
                            fileName: "[project]/components/BrMap.tsx",
                            lineNumber: 118,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/BrMap.tsx",
                    lineNumber: 116,
                    columnNumber: 9
                }, this);
            }
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2d$simple$2d$maps$2f$dist$2f$index$2e$umd$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ComposableMap"], {
                projection: "geoMercator",
                projectionConfig: {
                    scale: 680,
                    center: [
                        -52,
                        -15
                    ]
                },
                style: {
                    width: "100%",
                    height: "100%"
                },
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2d$simple$2d$maps$2f$dist$2f$index$2e$umd$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Geographies"], {
                    geography: geoData,
                    children: {
                        "BrMap.useMemo[mapBlock]": ({ geographies })=>geographies.map({
                                "BrMap.useMemo[mapBlock]": (geo)=>{
                                    const props = geo.properties ?? {};
                                    const uf = resolveUF(props);
                                    const name = resolveName(props);
                                    const isSelected = uf === selectedUF;
                                    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2d$simple$2d$maps$2f$dist$2f$index$2e$umd$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Geography"], {
                                        geography: geo,
                                        onMouseEnter: {
                                            "BrMap.useMemo[mapBlock]": ()=>setHover({
                                                    name,
                                                    sigla: uf || "--"
                                                })
                                        }["BrMap.useMemo[mapBlock]"],
                                        onMouseLeave: {
                                            "BrMap.useMemo[mapBlock]": ()=>setHover(null)
                                        }["BrMap.useMemo[mapBlock]"],
                                        onClick: {
                                            "BrMap.useMemo[mapBlock]": ()=>{
                                                if (uf) onSelectUF(uf);
                                            }
                                        }["BrMap.useMemo[mapBlock]"],
                                        style: {
                                            default: {
                                                fill: isSelected ? "rgba(251,146,60,0.35)" : "rgba(255,255,255,0.06)",
                                                stroke: isSelected ? "rgba(251,146,60,0.85)" : "rgba(255,255,255,0.16)",
                                                strokeWidth: isSelected ? 1.2 : 0.8,
                                                outline: "none"
                                            },
                                            hover: {
                                                fill: "rgba(168,85,247,0.24)",
                                                stroke: "rgba(255,255,255,0.28)",
                                                strokeWidth: 1.1,
                                                outline: "none",
                                                cursor: "pointer"
                                            },
                                            pressed: {
                                                fill: "rgba(251,146,60,0.4)",
                                                stroke: "rgba(251,146,60,1)",
                                                strokeWidth: 1.25,
                                                outline: "none"
                                            }
                                        }
                                    }, geo.rsmKey, false, {
                                        fileName: "[project]/components/BrMap.tsx",
                                        lineNumber: 147,
                                        columnNumber: 17
                                    }, this);
                                }
                            }["BrMap.useMemo[mapBlock]"])
                    }["BrMap.useMemo[mapBlock]"]
                }, void 0, false, {
                    fileName: "[project]/components/BrMap.tsx",
                    lineNumber: 139,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/BrMap.tsx",
                lineNumber: 134,
                columnNumber: 7
            }, this);
        }
    }["BrMap.useMemo[mapBlock]"], [
        loading,
        error,
        geoData,
        selectedUF,
        onSelectUF
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "relative h-[420px] lg:h-[520px] w-full rounded-lg border border-zinc-800 bg-zinc-950/70 p-2",
        children: [
            mapBlock,
            hover ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "pointer-events-none absolute right-3 top-3 rounded-md border border-zinc-700 bg-black/80 px-2 py-1 text-xs text-zinc-200",
                children: [
                    hover.name,
                    " (",
                    hover.sigla,
                    ")"
                ]
            }, void 0, true, {
                fileName: "[project]/components/BrMap.tsx",
                lineNumber: 189,
                columnNumber: 9
            }, this) : null
        ]
    }, void 0, true, {
        fileName: "[project]/components/BrMap.tsx",
        lineNumber: 186,
        columnNumber: 5
    }, this);
}
_s(BrMap, "LdBhP+yVd/lTPLFE6kDqekEbQfo=");
_c = BrMap;
var _c;
__turbopack_context__.k.register(_c, "BrMap");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/RealEstateDashboard.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>RealEstateDashboard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BrMap$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/BrMap.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
const palette = {
    STABLE: "#34d399",
    TRANSITION: "#fbbf24",
    UNSTABLE: "#fb7185"
};
const REGION_ORDER = [
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul"
];
const REGION_STATES = {
    Norte: [
        "AC",
        "AP",
        "AM",
        "PA",
        "RO",
        "RR",
        "TO"
    ],
    Nordeste: [
        "AL",
        "BA",
        "CE",
        "MA",
        "PB",
        "PE",
        "PI",
        "RN",
        "SE"
    ],
    "Centro-Oeste": [
        "DF",
        "GO",
        "MS",
        "MT"
    ],
    Sudeste: [
        "ES",
        "MG",
        "RJ",
        "SP"
    ],
    Sul: [
        "PR",
        "RS",
        "SC"
    ]
};
const STATE_TO_REGION = Object.fromEntries(_c1 = Object.entries(REGION_STATES).flatMap(_c = ([region, states])=>states.map((uf)=>[
            uf,
            region
        ])));
_c2 = STATE_TO_REGION;
const CITY_MAP = [
    {
        asset: "FipeZap_São_Paulo_Total",
        state: "SP",
        city: "Sao Paulo",
        region: "Sudeste"
    },
    {
        asset: "FipeZap_Rio_de_Janeiro_Total",
        state: "RJ",
        city: "Rio de Janeiro",
        region: "Sudeste"
    },
    {
        asset: "FipeZap_Belo_Horizonte_Total",
        state: "MG",
        city: "Belo Horizonte",
        region: "Sudeste"
    },
    {
        asset: "FipeZap_Brasília_Total",
        state: "DF",
        city: "Brasilia",
        region: "Centro-Oeste"
    },
    {
        asset: "FipeZap_Porto_Alegre_Total",
        state: "RS",
        city: "Porto Alegre",
        region: "Sul"
    }
];
// TODO: Expand this list with complete city coverage per UF when real-estate feeds are added.
const CITY_MOCK_BY_UF = {
    SP: [
        "Sao Paulo"
    ],
    RJ: [
        "Rio de Janeiro"
    ],
    MG: [
        "Belo Horizonte"
    ],
    DF: [
        "Brasilia"
    ],
    RS: [
        "Porto Alegre"
    ]
};
function getCitiesForState(uf) {
    const fromAssets = CITY_MAP.filter((c)=>c.state === uf).map((c)=>c.city);
    const fromMock = CITY_MOCK_BY_UF[uf] || [];
    return Array.from(new Set([
        ...fromAssets,
        ...fromMock
    ]));
}
function formatPct(v) {
    if (v == null || Number.isNaN(v)) return "--";
    return `${(v * 100).toFixed(2)}%`;
}
function formatDateLabel(date, mode) {
    if (!date) return "";
    if (mode === "anual") return date.slice(0, 4);
    if (mode === "mensal") return date.slice(0, 7);
    return date;
}
function toTitleRegime(regime) {
    if (!regime) return "--";
    if (regime === "STABLE") return "Estavel";
    if (regime === "TRANSITION") return "Transicao";
    if (regime === "UNSTABLE") return "Instavel";
    return regime;
}
function RealEstateDashboard() {
    _s();
    const [summary, setSummary] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [regionFilter, setRegionFilter] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("Sudeste");
    const [stateFilter, setStateFilter] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("SP");
    const [cityFilter, setCityFilter] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("Sao Paulo");
    const [horizonDays, setHorizonDays] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(5);
    const [series, setSeries] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [regimes, setRegimes] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [viewMode, setViewMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("mensal");
    const [hoverIndex, setHoverIndex] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const selectedAsset = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[selectedAsset]": ()=>{
            const safeCity = getCitiesForState(stateFilter).includes(cityFilter) ? cityFilter : getCitiesForState(stateFilter)[0] || "";
            const match = CITY_MAP.find({
                "RealEstateDashboard.useMemo[selectedAsset].match": (c)=>c.state === stateFilter && c.city === safeCity
            }["RealEstateDashboard.useMemo[selectedAsset].match"]);
            return match?.asset || CITY_MAP[0].asset;
        }
    }["RealEstateDashboard.useMemo[selectedAsset]"], [
        stateFilter,
        cityFilter
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "RealEstateDashboard.useEffect": ()=>{
            const load = {
                "RealEstateDashboard.useEffect.load": async ()=>{
                    try {
                        const res = await fetch("/api/realestate/summary");
                        if (!res.ok) {
                            setSummary(null);
                            return;
                        }
                        setSummary(await res.json());
                    } catch  {
                        setSummary(null);
                    }
                }
            }["RealEstateDashboard.useEffect.load"];
            load();
        }
    }["RealEstateDashboard.useEffect"], []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "RealEstateDashboard.useEffect": ()=>{
            const loadSeries = {
                "RealEstateDashboard.useEffect.loadSeries": async ()=>{
                    try {
                        const res = await fetch(`/api/realestate/series?asset=${encodeURIComponent(selectedAsset)}`);
                        const data = await res.json();
                        setSeries(Array.isArray(data) ? data : []);
                    } catch  {
                        setSeries([]);
                    }
                }
            }["RealEstateDashboard.useEffect.loadSeries"];
            loadSeries();
        }
    }["RealEstateDashboard.useEffect"], [
        selectedAsset
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "RealEstateDashboard.useEffect": ()=>{
            const loadRegimes = {
                "RealEstateDashboard.useEffect.loadRegimes": async ()=>{
                    try {
                        const base = selectedAsset.toUpperCase().replace(/\s+/g, "_");
                        const res = await fetch(`/api/files/realestate/assets/${base}_monthly_regimes.csv`);
                        if (!res.ok) {
                            setRegimes([]);
                            return;
                        }
                        const text = await res.text();
                        const parsed = text.trim().split("\n").slice(1).map({
                            "RealEstateDashboard.useEffect.loadRegimes.parsed": (line)=>{
                                const [date, regime, confidence] = line.split(",");
                                return {
                                    date,
                                    regime,
                                    confidence: Number(confidence)
                                };
                            }
                        }["RealEstateDashboard.useEffect.loadRegimes.parsed"]);
                        setRegimes(parsed);
                    } catch  {
                        setRegimes([]);
                    }
                }
            }["RealEstateDashboard.useEffect.loadRegimes"];
            loadRegimes();
        }
    }["RealEstateDashboard.useEffect"], [
        selectedAsset
    ]);
    const derivedRegimes = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[derivedRegimes]": ()=>{
            if (!series.length) return [];
            const diffs = series.map({
                "RealEstateDashboard.useMemo[derivedRegimes].diffs": (p, i)=>{
                    if (i === 0 || p.value == null || series[i - 1].value == null) return 0;
                    return Math.abs((p.value - series[i - 1].value) / Math.max(1e-9, series[i - 1].value));
                }
            }["RealEstateDashboard.useMemo[derivedRegimes].diffs"]);
            const sorted = [
                ...diffs
            ].sort({
                "RealEstateDashboard.useMemo[derivedRegimes].sorted": (a, b)=>a - b
            }["RealEstateDashboard.useMemo[derivedRegimes].sorted"]);
            const q = {
                "RealEstateDashboard.useMemo[derivedRegimes].q": (k)=>sorted[Math.floor((sorted.length - 1) * k)] || 0
            }["RealEstateDashboard.useMemo[derivedRegimes].q"];
            const q1 = q(0.35);
            const q2 = q(0.75);
            return series.map({
                "RealEstateDashboard.useMemo[derivedRegimes]": (p, i)=>{
                    const v = diffs[i] ?? 0;
                    let regime = "STABLE";
                    if (v >= q2) regime = "UNSTABLE";
                    else if (v >= q1) regime = "TRANSITION";
                    const confidence = Math.max(0.3, Math.min(0.95, regime === "STABLE" ? 0.75 : regime === "TRANSITION" ? 0.58 : 0.42));
                    return {
                        date: p.date,
                        regime,
                        confidence
                    };
                }
            }["RealEstateDashboard.useMemo[derivedRegimes]"]);
        }
    }["RealEstateDashboard.useMemo[derivedRegimes]"], [
        series
    ]);
    const activeRegimes = regimes.length ? regimes : derivedRegimes;
    const rqaMap = summary?.rqa ?? {};
    const forecastMap = summary?.forecast ?? {};
    const rqa = rqaMap[selectedAsset.toUpperCase()] || null;
    const forecast = forecastMap[selectedAsset.toUpperCase()] || null;
    const displaySeries = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[displaySeries]": ()=>{
            if (!series.length) return [];
            if (viewMode === "diario") return series;
            if (viewMode === "anual") {
                const byYear = {};
                for (const p of series)byYear[p.date.slice(0, 4)] = p;
                return Object.values(byYear);
            }
            return series;
        }
    }["RealEstateDashboard.useMemo[displaySeries]"], [
        series,
        viewMode
    ]);
    const chart = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[chart]": ()=>{
            if (!displaySeries.length) return null;
            const width = 1400;
            const height = 780;
            const pad = 90;
            const yVals = displaySeries.map({
                "RealEstateDashboard.useMemo[chart].yVals": (d)=>d.value
            }["RealEstateDashboard.useMemo[chart].yVals"]).filter({
                "RealEstateDashboard.useMemo[chart].yVals": (v)=>v != null
            }["RealEstateDashboard.useMemo[chart].yVals"]);
            if (!yVals.length) return null;
            const ymin = Math.min(...yVals);
            const ymax = Math.max(...yVals);
            const scaleX = {
                "RealEstateDashboard.useMemo[chart].scaleX": (i, total)=>pad + i / Math.max(1, total - 1) * (width - pad * 2)
            }["RealEstateDashboard.useMemo[chart].scaleX"];
            const scaleY = {
                "RealEstateDashboard.useMemo[chart].scaleY": (v)=>height - pad - (v - ymin) / Math.max(1e-6, ymax - ymin) * (height - pad * 2)
            }["RealEstateDashboard.useMemo[chart].scaleY"];
            return {
                width,
                height,
                pad,
                scaleX,
                scaleY,
                ymin,
                ymax
            };
        }
    }["RealEstateDashboard.useMemo[chart]"], [
        displaySeries
    ]);
    const availableStates = REGION_STATES[regionFilter] || [];
    const citiesForState = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[citiesForState]": ()=>getCitiesForState(stateFilter)
    }["RealEstateDashboard.useMemo[citiesForState]"], [
        stateFilter
    ]);
    const cityFilterValue = citiesForState.includes(cityFilter) ? cityFilter : citiesForState[0] || "";
    const regimeAt = (idx)=>{
        if (idx == null || !activeRegimes.length || !displaySeries.length) return null;
        const mapped = Math.round(idx / Math.max(1, displaySeries.length - 1) * (activeRegimes.length - 1));
        return activeRegimes[Math.max(0, Math.min(activeRegimes.length - 1, mapped))] || null;
    };
    const latestValue = displaySeries.length ? displaySeries[displaySeries.length - 1].value : null;
    const regimeNow = activeRegimes.length ? activeRegimes[activeRegimes.length - 1] : null;
    const periodInfo = displaySeries.length ? `${displaySeries[0].date} ate ${displaySeries[displaySeries.length - 1].date}` : "Sem periodo";
    const forecastValue = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[forecastValue]": ()=>{
            if (!latestValue || !Number.isFinite(latestValue)) return null;
            const baseConfidence = regimeNow?.confidence ?? 0.55;
            const drift = regimeNow?.regime === "STABLE" ? 0.005 : regimeNow?.regime === "TRANSITION" ? 0.002 : -0.004;
            const factor = 1 + drift * horizonDays;
            return {
                p50: latestValue * factor,
                confidence: Math.max(0.3, Math.min(0.95, baseConfidence - (horizonDays - 1) * 0.03))
            };
        }
    }["RealEstateDashboard.useMemo[forecastValue]"], [
        latestValue,
        regimeNow,
        horizonDays
    ]);
    const onSelectUF = (uf)=>{
        const nextRegion = STATE_TO_REGION[uf] || regionFilter;
        setRegionFilter(nextRegion);
        setStateFilter(uf);
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "p-6 space-y-6",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("header", {
                className: "space-y-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                        className: "text-2xl font-semibold",
                        children: "Setor Imobiliario"
                    }, void 0, false, {
                        fileName: "[project]/components/RealEstateDashboard.tsx",
                        lineNumber: 242,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-sm text-zinc-400",
                        children: "Diagnostico de regimes para precos residenciais com leitura de estabilidade, transicao e instabilidade."
                    }, void 0, false, {
                        fileName: "[project]/components/RealEstateDashboard.tsx",
                        lineNumber: 243,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/RealEstateDashboard.tsx",
                lineNumber: 241,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "grid grid-cols-12 gap-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "col-span-12 lg:col-span-4 space-y-4",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-xl border border-zinc-800 bg-black/40 p-4",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-zinc-500 mb-2",
                                        children: "Filtro geografico"
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 252,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "space-y-3",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                className: "text-xs text-zinc-400",
                                                children: "Regiao"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 254,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                className: "w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm",
                                                value: regionFilter,
                                                onChange: (e)=>{
                                                    const reg = e.target.value;
                                                    const firstState = REGION_STATES[reg]?.[0] || "SP";
                                                    setRegionFilter(reg);
                                                    setStateFilter(firstState);
                                                },
                                                children: REGION_ORDER.map((r)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                        value: r,
                                                        children: r
                                                    }, r, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 266,
                                                        columnNumber: 19
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 255,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                className: "text-xs text-zinc-400",
                                                children: "Estado"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 272,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                className: "w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm",
                                                value: stateFilter,
                                                onChange: (e)=>setStateFilter(e.target.value),
                                                children: availableStates.map((s)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                        value: s,
                                                        children: s
                                                    }, s, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 279,
                                                        columnNumber: 19
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 273,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                className: "text-xs text-zinc-400",
                                                children: "Cidade"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 285,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                className: "w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm",
                                                value: cityFilterValue,
                                                onChange: (e)=>setCityFilter(e.target.value),
                                                children: citiesForState.map((c)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                        value: c,
                                                        children: c
                                                    }, c, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 292,
                                                        columnNumber: 19
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 286,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 253,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 251,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-xl border border-zinc-800 bg-black/40 p-4",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-zinc-500 mb-2",
                                        children: "Mapa politico do Brasil por estados"
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 301,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BrMap$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                        selectedUF: stateFilter,
                                        onSelectUF: onSelectUF
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 302,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "mt-2 text-xs text-zinc-400",
                                        children: "Clique no estado para sincronizar o filtro e atualizar a cidade."
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 303,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 300,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-xl border border-zinc-800 bg-black/40 p-4 grid grid-cols-3 gap-3 text-center",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500",
                                                children: "DET"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 310,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-lg font-semibold",
                                                children: formatPct(rqa?.rqa?.det)
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 311,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 309,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500",
                                                children: "LAM"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 314,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-lg font-semibold",
                                                children: formatPct(rqa?.rqa?.lam)
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 315,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 313,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500",
                                                children: "TT"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 318,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-lg font-semibold",
                                                children: rqa?.rqa?.tt?.toFixed(1) ?? "--"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 319,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 317,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 308,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RealEstateDashboard.tsx",
                        lineNumber: 250,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "col-span-12 lg:col-span-8 space-y-4",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-2xl border border-zinc-800 bg-zinc-950/40 p-5",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "mb-3 flex flex-wrap items-center justify-between gap-3",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500",
                                                children: "Preco medio (R$) com bandas de regime"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 327,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "flex items-center gap-2 text-xs text-zinc-400",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                        children: "Visao"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 329,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                        className: "rounded-lg border border-zinc-700 bg-black/30 px-2 py-1 text-xs",
                                                        value: viewMode,
                                                        onChange: (e)=>setViewMode(e.target.value),
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "mensal",
                                                                children: "Mensal"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 335,
                                                                columnNumber: 19
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "anual",
                                                                children: "Anual"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 336,
                                                                columnNumber: 19
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "diario",
                                                                children: "Diario"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 337,
                                                                columnNumber: 19
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 330,
                                                        columnNumber: 17
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 328,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 326,
                                        columnNumber: 13
                                    }, this),
                                    chart ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "relative",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                width: chart.width,
                                                height: chart.height,
                                                className: "w-full",
                                                onMouseLeave: ()=>setHoverIndex(null),
                                                onMouseMove: (e)=>{
                                                    const rect = e.currentTarget.getBoundingClientRect();
                                                    const x = e.clientX - rect.left;
                                                    const idx = Math.round((x - chart.pad) / Math.max(1, rect.width - chart.pad * 2) * (displaySeries.length - 1));
                                                    setHoverIndex(idx >= 0 && idx < displaySeries.length ? idx : null);
                                                },
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("rect", {
                                                        x: 0,
                                                        y: 0,
                                                        width: chart.width,
                                                        height: chart.height,
                                                        fill: "transparent"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 358,
                                                        columnNumber: 19
                                                    }, this),
                                                    activeRegimes.length > 1 && activeRegimes.map((r, i)=>{
                                                        if (i === activeRegimes.length - 1) return null;
                                                        const x0 = chart.scaleX(i, activeRegimes.length);
                                                        const x1 = chart.scaleX(i + 1, activeRegimes.length);
                                                        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("rect", {
                                                            x: x0,
                                                            y: chart.pad,
                                                            width: x1 - x0,
                                                            height: chart.height - chart.pad * 2,
                                                            fill: palette[r.regime] || "#3f3f46",
                                                            opacity: 0.12
                                                        }, `${r.date}-${i}`, false, {
                                                            fileName: "[project]/components/RealEstateDashboard.tsx",
                                                            lineNumber: 366,
                                                            columnNumber: 25
                                                        }, this);
                                                    }),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("polyline", {
                                                        fill: "none",
                                                        stroke: "#38bdf8",
                                                        strokeWidth: 2.2,
                                                        points: displaySeries.map((p, i)=>p.value == null ? null : `${chart.scaleX(i, displaySeries.length)},${chart.scaleY(p.value)}`).filter(Boolean).join(" ")
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 378,
                                                        columnNumber: 19
                                                    }, this),
                                                    [
                                                        0,
                                                        0.25,
                                                        0.5,
                                                        0.75,
                                                        1
                                                    ].map((p)=>{
                                                        const y = chart.pad + (1 - p) * (chart.height - chart.pad * 2);
                                                        const value = chart.ymin + p * (chart.ymax - chart.ymin);
                                                        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("g", {
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("line", {
                                                                    x1: chart.pad,
                                                                    y1: y,
                                                                    x2: chart.width - chart.pad,
                                                                    y2: y,
                                                                    stroke: "#1f2937",
                                                                    strokeDasharray: "4 6"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                    lineNumber: 393,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("text", {
                                                                    x: chart.pad - 8,
                                                                    y: y + 4,
                                                                    fill: "#9ca3af",
                                                                    fontSize: "10",
                                                                    textAnchor: "end",
                                                                    children: value.toFixed(0)
                                                                }, void 0, false, {
                                                                    fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                    lineNumber: 394,
                                                                    columnNumber: 25
                                                                }, this)
                                                            ]
                                                        }, `y-${p}`, true, {
                                                            fileName: "[project]/components/RealEstateDashboard.tsx",
                                                            lineNumber: 392,
                                                            columnNumber: 23
                                                        }, this);
                                                    }),
                                                    [
                                                        0,
                                                        0.25,
                                                        0.5,
                                                        0.75,
                                                        1
                                                    ].map((p)=>{
                                                        const idx = Math.round(p * (displaySeries.length - 1));
                                                        const x = chart.scaleX(idx, displaySeries.length);
                                                        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("text", {
                                                            x: x,
                                                            y: chart.height - chart.pad + 18,
                                                            fill: "#9ca3af",
                                                            fontSize: "10",
                                                            textAnchor: "middle",
                                                            children: formatDateLabel(displaySeries[idx]?.date ?? "", viewMode)
                                                        }, `x-${p}`, false, {
                                                            fileName: "[project]/components/RealEstateDashboard.tsx",
                                                            lineNumber: 405,
                                                            columnNumber: 23
                                                        }, this);
                                                    })
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 344,
                                                columnNumber: 17
                                            }, this),
                                            hoverIndex != null && displaySeries[hoverIndex] && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "absolute right-6 top-6 rounded-lg border border-zinc-700 bg-black/80 px-3 py-2 text-xs text-zinc-200",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "font-semibold",
                                                        children: formatDateLabel(displaySeries[hoverIndex].date, viewMode)
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 414,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: [
                                                            "Preco: R$ ",
                                                            displaySeries[hoverIndex].value?.toFixed(0) ?? "--"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 415,
                                                        columnNumber: 21
                                                    }, this),
                                                    regimeAt(hoverIndex) && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: [
                                                            "Regime: ",
                                                            toTitleRegime(regimeAt(hoverIndex)?.regime),
                                                            " | Conf. ",
                                                            regimeAt(hoverIndex)?.confidence?.toFixed(2) ?? "--"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 417,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 413,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 343,
                                        columnNumber: 15
                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-sm text-zinc-400",
                                        children: "Sem dados carregados."
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 425,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 325,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "grid gap-4 lg:grid-cols-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "rounded-xl border border-zinc-800 bg-black/40 p-4",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500 mb-2",
                                                children: "Resumo por ativo"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 431,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "grid grid-cols-2 gap-2 text-sm text-zinc-200",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "text-zinc-400",
                                                        children: "Ativo"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 433,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: selectedAsset
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 434,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "text-zinc-400",
                                                        children: "Periodo analisado"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 435,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: periodInfo
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 436,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "text-zinc-400",
                                                        children: "Regime atual"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 437,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: toTitleRegime(regimeNow?.regime)
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 438,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "text-zinc-400",
                                                        children: "Confianca"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 439,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: regimeNow?.confidence?.toFixed(2) ?? "--"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 440,
                                                        columnNumber: 17
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 432,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 430,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "rounded-xl border border-zinc-800 bg-black/40 p-4",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "mb-2 flex items-center justify-between",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "text-xs text-zinc-500",
                                                        children: "Forecast e diagnostico"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 446,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                        className: "rounded-lg border border-zinc-700 bg-black/30 px-2 py-1 text-xs",
                                                        value: horizonDays,
                                                        onChange: (e)=>setHorizonDays(Number(e.target.value)),
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: 1,
                                                                children: "1 dia"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 452,
                                                                columnNumber: 19
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: 5,
                                                                children: "5 dias"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 453,
                                                                columnNumber: 19
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: 10,
                                                                children: "10 dias"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 454,
                                                                columnNumber: 19
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 447,
                                                        columnNumber: 17
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 445,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "space-y-1 text-sm text-zinc-200",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: [
                                                            "Projecao p50 (",
                                                            horizonDays,
                                                            "d): R$ ",
                                                            forecastValue?.p50?.toFixed(0) ?? "--"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 458,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: [
                                                            "Confianca da projecao: ",
                                                            forecastValue?.confidence?.toFixed(2) ?? "--"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 459,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "text-zinc-400",
                                                        children: "Use como diagnostico de regime, nao como sinal isolado."
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 460,
                                                        columnNumber: 17
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 457,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "mt-3 text-xs text-zinc-400",
                                                children: forecast ? `${Object.keys(forecast).length} horizontes no resumo por regime do motor.` : "Resumo de forecast por regime indisponivel (fallback local ativo)."
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 462,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 444,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 429,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RealEstateDashboard.tsx",
                        lineNumber: 324,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/RealEstateDashboard.tsx",
                lineNumber: 249,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/RealEstateDashboard.tsx",
        lineNumber: 240,
        columnNumber: 5
    }, this);
}
_s(RealEstateDashboard, "EENFcfDwpiSqC4DRiq/GV7uARsU=");
_c3 = RealEstateDashboard;
var _c, _c1, _c2, _c3;
__turbopack_context__.k.register(_c, "STATE_TO_REGION$Object.fromEntries$Object.entries(REGION_STATES).flatMap");
__turbopack_context__.k.register(_c1, "STATE_TO_REGION$Object.fromEntries");
__turbopack_context__.k.register(_c2, "STATE_TO_REGION");
__turbopack_context__.k.register(_c3, "RealEstateDashboard");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=components_0d8230d6._.js.map