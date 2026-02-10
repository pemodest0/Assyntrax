(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/components/RealEstateDashboard.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>RealEstateDashboard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
const palette = {
    STABLE: "#34d399",
    TRANSITION: "#fbbf24",
    UNSTABLE: "#fb7185"
};
const CITY_MAP = [
    {
        asset: "FipeZap_São_Paulo_Total",
        state: "SP",
        city: "Sao Paulo",
        region: "Sudeste",
        x: 264,
        y: 302
    },
    {
        asset: "FipeZap_Rio_de_Janeiro_Total",
        state: "RJ",
        city: "Rio de Janeiro",
        region: "Sudeste",
        x: 288,
        y: 306
    },
    {
        asset: "FipeZap_Belo_Horizonte_Total",
        state: "MG",
        city: "Belo Horizonte",
        region: "Sudeste",
        x: 260,
        y: 280
    },
    {
        asset: "FipeZap_Porto_Alegre_Total",
        state: "RS",
        city: "Porto Alegre",
        region: "Sul",
        x: 226,
        y: 370
    },
    {
        asset: "FipeZap_Brasília_Total",
        state: "DF",
        city: "Brasilia",
        region: "Centro-Oeste",
        x: 236,
        y: 248
    }
];
const REGION_ORDER = [
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul"
];
const REGION_COLORS = {
    Norte: "#0ea5e9",
    Nordeste: "#f59e0b",
    "Centro-Oeste": "#10b981",
    Sudeste: "#a855f7",
    Sul: "#f43f5e"
};
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
const HERO_IMAGES = [
    "/visuals/realestate-tiles.svg",
    "/visuals/realestate-skyline.svg"
];
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
function RealEstateDashboard() {
    _s();
    const [summary, setSummary] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [regionFilter, setRegionFilter] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("Sudeste");
    const [stateFilter, setStateFilter] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("SP");
    const [cityFilter, setCityFilter] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("Sao Paulo");
    const [series, setSeries] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [regimes, setRegimes] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [viewMode, setViewMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("mensal");
    const [hoverIndex, setHoverIndex] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const selectedAsset = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[selectedAsset]": ()=>{
            const match = CITY_MAP.find({
                "RealEstateDashboard.useMemo[selectedAsset].match": (c)=>c.state === stateFilter && c.city === cityFilter
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
                        if (!res.ok) return;
                        const data = await res.json();
                        setSummary(data);
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
                        const lines = text.trim().split("\n").slice(1);
                        const parsed = lines.map({
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
    const rqa = summary?.rqa?.[selectedAsset.toUpperCase()] || null;
    const forecast = summary?.forecast?.[selectedAsset.toUpperCase()] || null;
    const displaySeries = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[displaySeries]": ()=>{
            if (!series.length) return [];
            if (viewMode === "diario") {
                return series;
            }
            if (viewMode === "anual") {
                const byYear = {};
                for (const p of series){
                    const year = p.date.slice(0, 4);
                    byYear[year] = p;
                }
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
            const height = 700;
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
    const states = REGION_STATES[regionFilter] || [];
    const cities = CITY_MAP.filter((c)=>c.state === stateFilter).map((c)=>c.city);
    const statusColor = (assetKey)=>{
        const key = assetKey.toUpperCase();
        const det = summary?.rqa?.[key]?.rqa?.det ?? 0;
        const lam = summary?.rqa?.[key]?.rqa?.lam ?? 0;
        if (det > 0.85 && lam > 0.8) return palette.STABLE;
        if (det > 0.6) return palette.TRANSITION;
        return palette.UNSTABLE;
    };
    const regimeAt = (idx)=>{
        if (idx == null || !activeRegimes.length || !displaySeries.length) return null;
        const mapped = Math.round(idx / Math.max(1, displaySeries.length - 1) * (activeRegimes.length - 1));
        return activeRegimes[Math.max(0, Math.min(activeRegimes.length - 1, mapped))] || null;
    };
    const insight = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RealEstateDashboard.useMemo[insight]": ()=>{
            const det = rqa?.rqa?.det ?? 0;
            const lam = rqa?.rqa?.lam ?? 0;
            if (det > 0.9 && lam > 0.8) {
                return "Estrutura forte e lenta: ideal para decisoes de longo prazo.";
            }
            if (det > 0.7 && lam < 0.5) {
                return "Estrutura estavel com mobilidade: janela boa para projecoes.";
            }
            return "Estrutura instavel: use apenas diagnostico, sem projecao agressiva.";
        }
    }["RealEstateDashboard.useMemo[insight]"], [
        rqa
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "p-6 space-y-6",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("header", {
                className: "space-y-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                                        className: "text-2xl font-semibold",
                                        children: "Setor Imobiliario"
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 221,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "text-sm text-zinc-400",
                                        children: "Diagnostico de regimes para precos residenciais: estrutura, travamento de liquidez e janela de previsao valida."
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 222,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 220,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex gap-3",
                                children: HERO_IMAGES.map((src)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("img", {
                                        src: src,
                                        alt: "Fachadas residenciais",
                                        className: "h-24 w-40 rounded-xl object-cover border border-zinc-800"
                                    }, src, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 229,
                                        columnNumber: 15
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 227,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RealEstateDashboard.tsx",
                        lineNumber: 219,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "rounded-xl border border-zinc-800 bg-black/40 p-4 text-sm text-zinc-300",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "font-semibold text-zinc-100",
                                children: "Guia rapido"
                            }, void 0, false, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 240,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-2 grid gap-2 lg:grid-cols-3",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        title: "DET alto indica repeticao de padrao e previsibilidade estrutural.",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "font-semibold",
                                                children: "DET"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 243,
                                                columnNumber: 15
                                            }, this),
                                            " - mede estrutura do regime."
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 242,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        title: "LAM alto indica preco travado por longos periodos.",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "font-semibold",
                                                children: "LAM"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 246,
                                                columnNumber: 15
                                            }, this),
                                            " - mede travamento de liquidez."
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 245,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        title: "TT e o tempo medio em que o mercado fica preso em um estado.",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "font-semibold",
                                                children: "TT"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 249,
                                                columnNumber: 15
                                            }, this),
                                            " - mede persistencia do regime."
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 248,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 241,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-3 text-xs text-zinc-400",
                                children: "Dica: selecione uma regiao, depois estado e cidade. O grafico mostra o preco com faixas de regime (estavel, transicao, instavel) e a tabela resume a leitura."
                            }, void 0, false, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 252,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RealEstateDashboard.tsx",
                        lineNumber: 239,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/RealEstateDashboard.tsx",
                lineNumber: 218,
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
                                        lineNumber: 262,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "space-y-3",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                className: "text-xs text-zinc-400",
                                                title: "Escolha a macro-regiao do Brasil.",
                                                children: "Regiao"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 264,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                className: "w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm",
                                                value: regionFilter,
                                                onChange: (e)=>{
                                                    const reg = e.target.value;
                                                    setRegionFilter(reg);
                                                    const fallback = CITY_MAP.find((c)=>c.region === reg);
                                                    setStateFilter(fallback?.state || "SP");
                                                    setCityFilter(fallback?.city || "Sao Paulo");
                                                },
                                                children: REGION_ORDER.map((r)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                        value: r,
                                                        children: r
                                                    }, r, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 279,
                                                        columnNumber: 19
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 267,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                className: "text-xs text-zinc-400",
                                                title: "Selecione o estado da regiao.",
                                                children: "Estado"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 284,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                className: "w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm",
                                                value: stateFilter,
                                                onChange: (e)=>{
                                                    setStateFilter(e.target.value);
                                                    setCityFilter(CITY_MAP.find((c)=>c.state === e.target.value)?.city || "");
                                                },
                                                children: states.map((s)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                        value: s,
                                                        children: s
                                                    }, s, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 296,
                                                        columnNumber: 19
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 287,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                className: "text-xs text-zinc-400",
                                                title: "Selecione a cidade monitorada.",
                                                children: "Cidade"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 301,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                className: "w-full rounded-lg border border-zinc-700 bg-black/30 px-3 py-2 text-sm",
                                                value: cityFilter,
                                                onChange: (e)=>setCityFilter(e.target.value),
                                                children: cities.map((c)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                        value: c,
                                                        children: c
                                                    }, c, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 310,
                                                        columnNumber: 19
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 304,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 263,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 261,
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
                                        lineNumber: 319,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "relative",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("img", {
                                                src: "https://s3.static.brasilescola.uol.com.br/be/2025/02/mapa-do-brasil-mostra-estados-e-capitais-do-pais.jpg",
                                                alt: "Mapa do Brasil por estados",
                                                className: "w-full h-96 rounded-lg border border-zinc-800 object-cover"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 321,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                viewBox: "0 0 420 460",
                                                className: "absolute inset-0 h-full w-full",
                                                children: CITY_MAP.map((c)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("g", {
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                                                                cx: c.x,
                                                                cy: c.y,
                                                                r: 7,
                                                                fill: REGION_COLORS[c.region] || statusColor(c.asset),
                                                                stroke: c.city === cityFilter ? "#fff" : "#0f0f0f",
                                                                strokeWidth: c.city === cityFilter ? 2 : 1,
                                                                onClick: ()=>{
                                                                    setRegionFilter(c.region);
                                                                    setStateFilter(c.state);
                                                                    setCityFilter(c.city);
                                                                },
                                                                className: "cursor-pointer"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 329,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("text", {
                                                                x: c.x + 8,
                                                                y: c.y - 8,
                                                                fill: "#d4d4d8",
                                                                fontSize: "9",
                                                                children: c.state
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 343,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("title", {
                                                                children: `${c.city} - ${c.state} (${c.region})`
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 346,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, c.asset, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 328,
                                                        columnNumber: 19
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 326,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 320,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "mt-2 flex flex-wrap gap-3 text-xs text-zinc-400",
                                        children: REGION_ORDER.map((region)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "flex items-center gap-2",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "h-2 w-2 rounded-full",
                                                        style: {
                                                            background: REGION_COLORS[region]
                                                        }
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 354,
                                                        columnNumber: 19
                                                    }, this),
                                                    region
                                                ]
                                            }, region, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 353,
                                                columnNumber: 17
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 351,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "mt-2 text-xs text-zinc-400",
                                        children: "Clique em um ponto para selecionar a cidade."
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 359,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 318,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-xl border border-zinc-800 bg-black/40 p-4",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-zinc-500 mb-2",
                                        children: "Sinais do motor"
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 365,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-sm text-zinc-200",
                                        children: insight
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 366,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "mt-3 text-xs text-zinc-400",
                                        children: "DET = estrutura | LAM = travamento | TT = tempo preso"
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 367,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "mt-2 text-xs text-zinc-500",
                                        children: "Passe o mouse sobre as metricas para ver a interpretacao detalhada."
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 370,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 364,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-xl border border-zinc-800 bg-black/40 p-4 grid grid-cols-3 gap-3 text-center",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        title: "Determinismo: percentual de recorrencias que seguem padrao.",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500",
                                                children: "DET"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 377,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-lg font-semibold",
                                                children: formatPct(rqa?.rqa?.det)
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 378,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 376,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        title: "Laminaridade: indica tempo em que o preco fica travado.",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500",
                                                children: "LAM"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 381,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-lg font-semibold",
                                                children: formatPct(rqa?.rqa?.lam)
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 382,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 380,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        title: "Trapping Time: tempo medio de permanencia no regime.",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500",
                                                children: "TT"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 385,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-lg font-semibold",
                                                children: rqa?.rqa?.tt?.toFixed(1) ?? "--"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 386,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 384,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 375,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RealEstateDashboard.tsx",
                        lineNumber: 260,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "col-span-12 lg:col-span-8",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-2xl border border-zinc-800 bg-zinc-950/40 p-4",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex flex-wrap items-center justify-between gap-3",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-xs text-zinc-500 mb-3",
                                                title: "Linha azul = preco medio; faixas de fundo = regimes.",
                                                children: "Preco (FipeZap Total) - valores em R$"
                                            }, void 0, false, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 394,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "flex items-center gap-2 text-xs text-zinc-400",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                        className: "text-xs text-zinc-500",
                                                        title: "Escolha o nivel de agregacao temporal.",
                                                        children: "Visao"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 401,
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
                                                                lineNumber: 409,
                                                                columnNumber: 19
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "anual",
                                                                children: "Anual"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 410,
                                                                columnNumber: 19
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "diario",
                                                                children: "Diario"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 411,
                                                                columnNumber: 19
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 404,
                                                        columnNumber: 17
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 400,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "flex items-center gap-3 text-xs text-zinc-400",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "flex items-center gap-2",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                className: "h-2 w-2 rounded-full bg-sky-400"
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 416,
                                                                columnNumber: 19
                                                            }, this),
                                                            "Preco medio"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 415,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "flex items-center gap-2",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                className: "h-2 w-2 rounded-full",
                                                                style: {
                                                                    background: palette.STABLE
                                                                }
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 420,
                                                                columnNumber: 19
                                                            }, this),
                                                            "Estavel"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 419,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "flex items-center gap-2",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                className: "h-2 w-2 rounded-full",
                                                                style: {
                                                                    background: palette.TRANSITION
                                                                }
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 424,
                                                                columnNumber: 19
                                                            }, this),
                                                            "Transicao"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 423,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "flex items-center gap-2",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                className: "h-2 w-2 rounded-full",
                                                                style: {
                                                                    background: palette.UNSTABLE
                                                                }
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                lineNumber: 428,
                                                                columnNumber: 19
                                                            }, this),
                                                            "Instavel"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 427,
                                                        columnNumber: 17
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 414,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 393,
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
                                                    if (idx >= 0 && idx < displaySeries.length) {
                                                        setHoverIndex(idx);
                                                    } else {
                                                        setHoverIndex(null);
                                                    }
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
                                                        lineNumber: 454,
                                                        columnNumber: 19
                                                    }, this),
                                                    activeRegimes.length > 1 && activeRegimes.map((r, i)=>{
                                                        if (i === activeRegimes.length - 1) return null;
                                                        const x0 = chart.scaleX(i, activeRegimes.length);
                                                        const x1 = chart.scaleX(i + 1, activeRegimes.length);
                                                        const color = palette[r.regime] || "#3f3f46";
                                                        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("rect", {
                                                            x: x0,
                                                            y: chart.pad,
                                                            width: x1 - x0,
                                                            height: chart.height - chart.pad * 2,
                                                            fill: color,
                                                            opacity: 0.12
                                                        }, `${r.date}-${i}`, false, {
                                                            fileName: "[project]/components/RealEstateDashboard.tsx",
                                                            lineNumber: 463,
                                                            columnNumber: 23
                                                        }, this);
                                                    }),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("polyline", {
                                                        fill: "none",
                                                        stroke: "#38bdf8",
                                                        strokeWidth: 2,
                                                        points: displaySeries.map((p, i)=>{
                                                            if (p.value == null) return null;
                                                            return `${chart.scaleX(i, displaySeries.length)},${chart.scaleY(p.value)}`;
                                                        }).filter(Boolean).join(" ")
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 475,
                                                        columnNumber: 17
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
                                                                    lineNumber: 493,
                                                                    columnNumber: 23
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
                                                                    lineNumber: 501,
                                                                    columnNumber: 23
                                                                }, this)
                                                            ]
                                                        }, `y-${p}`, true, {
                                                            fileName: "[project]/components/RealEstateDashboard.tsx",
                                                            lineNumber: 492,
                                                            columnNumber: 21
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
                                                        const label = formatDateLabel(displaySeries[idx]?.date ?? "", viewMode);
                                                        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("g", {
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("line", {
                                                                    x1: x,
                                                                    y1: chart.height - chart.pad,
                                                                    x2: x,
                                                                    y2: chart.height - chart.pad + 6,
                                                                    stroke: "#3f3f46"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                    lineNumber: 514,
                                                                    columnNumber: 23
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("text", {
                                                                    x: x,
                                                                    y: chart.height - chart.pad + 20,
                                                                    fill: "#9ca3af",
                                                                    fontSize: "10",
                                                                    textAnchor: "middle",
                                                                    children: label
                                                                }, void 0, false, {
                                                                    fileName: "[project]/components/RealEstateDashboard.tsx",
                                                                    lineNumber: 515,
                                                                    columnNumber: 23
                                                                }, this)
                                                            ]
                                                        }, `x-${p}`, true, {
                                                            fileName: "[project]/components/RealEstateDashboard.tsx",
                                                            lineNumber: 513,
                                                            columnNumber: 21
                                                        }, this);
                                                    }),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("text", {
                                                        x: chart.pad,
                                                        y: chart.pad - 18,
                                                        fill: "#9ca3af",
                                                        fontSize: "11",
                                                        children: "Preco (R$)"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 522,
                                                        columnNumber: 17
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("text", {
                                                        x: chart.width - chart.pad,
                                                        y: chart.height - chart.pad + 40,
                                                        fill: "#9ca3af",
                                                        fontSize: "11",
                                                        textAnchor: "end",
                                                        children: "Datas"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 530,
                                                        columnNumber: 17
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 435,
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
                                                        lineNumber: 542,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        children: [
                                                            "Preco: R$ ",
                                                            displaySeries[hoverIndex].value?.toFixed(0) ?? "--"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 545,
                                                        columnNumber: 21
                                                    }, this),
                                                    regimeAt(hoverIndex) && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "mt-1",
                                                        children: [
                                                            "Regime: ",
                                                            regimeAt(hoverIndex)?.regime ?? "--",
                                                            " - Conf.",
                                                            " ",
                                                            regimeAt(hoverIndex)?.confidence?.toFixed(2) ?? "--"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 547,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 541,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 434,
                                        columnNumber: 15
                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-sm text-zinc-400",
                                        children: "Sem dados carregados."
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 556,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 392,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-4 rounded-xl border border-zinc-800 bg-black/40 p-4",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-zinc-500 mb-2",
                                        children: "Projecao (baseline por regime)"
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 561,
                                        columnNumber: 13
                                    }, this),
                                    forecast ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-zinc-300 space-y-2",
                                        children: Object.entries(forecast).map(([h, data])=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "flex items-center justify-between",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        children: [
                                                            "Horizonte ",
                                                            h,
                                                            " meses"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 568,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "text-zinc-400",
                                                        children: Object.keys(data.by_regime || {}).length ? `${Object.keys(data.by_regime || {}).length} regimes avaliados` : "sem regimes suficientes"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                                        lineNumber: 569,
                                                        columnNumber: 21
                                                    }, this)
                                                ]
                                            }, h, true, {
                                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                                lineNumber: 567,
                                                columnNumber: 19
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 565,
                                        columnNumber: 15
                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-sm text-zinc-400",
                                        children: "Sem projecao disponivel."
                                    }, void 0, false, {
                                        fileName: "[project]/components/RealEstateDashboard.tsx",
                                        lineNumber: 578,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/RealEstateDashboard.tsx",
                                lineNumber: 560,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RealEstateDashboard.tsx",
                        lineNumber: 391,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/RealEstateDashboard.tsx",
                lineNumber: 259,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/RealEstateDashboard.tsx",
        lineNumber: 217,
        columnNumber: 5
    }, this);
}
_s(RealEstateDashboard, "WCVDKVfuqLy5q2gOpA1DAL6/jsA=");
_c = RealEstateDashboard;
var _c;
__turbopack_context__.k.register(_c, "RealEstateDashboard");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/node_modules/next/dist/compiled/react/cjs/react-jsx-dev-runtime.development.js [app-client] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
/**
 * @license React
 * react-jsx-dev-runtime.development.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */ "use strict";
"production" !== ("TURBOPACK compile-time value", "development") && function() {
    function getComponentNameFromType(type) {
        if (null == type) return null;
        if ("function" === typeof type) return type.$$typeof === REACT_CLIENT_REFERENCE ? null : type.displayName || type.name || null;
        if ("string" === typeof type) return type;
        switch(type){
            case REACT_FRAGMENT_TYPE:
                return "Fragment";
            case REACT_PROFILER_TYPE:
                return "Profiler";
            case REACT_STRICT_MODE_TYPE:
                return "StrictMode";
            case REACT_SUSPENSE_TYPE:
                return "Suspense";
            case REACT_SUSPENSE_LIST_TYPE:
                return "SuspenseList";
            case REACT_ACTIVITY_TYPE:
                return "Activity";
            case REACT_VIEW_TRANSITION_TYPE:
                return "ViewTransition";
        }
        if ("object" === typeof type) switch("number" === typeof type.tag && console.error("Received an unexpected object in getComponentNameFromType(). This is likely a bug in React. Please file an issue."), type.$$typeof){
            case REACT_PORTAL_TYPE:
                return "Portal";
            case REACT_CONTEXT_TYPE:
                return type.displayName || "Context";
            case REACT_CONSUMER_TYPE:
                return (type._context.displayName || "Context") + ".Consumer";
            case REACT_FORWARD_REF_TYPE:
                var innerType = type.render;
                type = type.displayName;
                type || (type = innerType.displayName || innerType.name || "", type = "" !== type ? "ForwardRef(" + type + ")" : "ForwardRef");
                return type;
            case REACT_MEMO_TYPE:
                return innerType = type.displayName || null, null !== innerType ? innerType : getComponentNameFromType(type.type) || "Memo";
            case REACT_LAZY_TYPE:
                innerType = type._payload;
                type = type._init;
                try {
                    return getComponentNameFromType(type(innerType));
                } catch (x) {}
        }
        return null;
    }
    function testStringCoercion(value) {
        return "" + value;
    }
    function checkKeyStringCoercion(value) {
        try {
            testStringCoercion(value);
            var JSCompiler_inline_result = !1;
        } catch (e) {
            JSCompiler_inline_result = !0;
        }
        if (JSCompiler_inline_result) {
            JSCompiler_inline_result = console;
            var JSCompiler_temp_const = JSCompiler_inline_result.error;
            var JSCompiler_inline_result$jscomp$0 = "function" === typeof Symbol && Symbol.toStringTag && value[Symbol.toStringTag] || value.constructor.name || "Object";
            JSCompiler_temp_const.call(JSCompiler_inline_result, "The provided key is an unsupported type %s. This value must be coerced to a string before using it here.", JSCompiler_inline_result$jscomp$0);
            return testStringCoercion(value);
        }
    }
    function getTaskName(type) {
        if (type === REACT_FRAGMENT_TYPE) return "<>";
        if ("object" === typeof type && null !== type && type.$$typeof === REACT_LAZY_TYPE) return "<...>";
        try {
            var name = getComponentNameFromType(type);
            return name ? "<" + name + ">" : "<...>";
        } catch (x) {
            return "<...>";
        }
    }
    function getOwner() {
        var dispatcher = ReactSharedInternals.A;
        return null === dispatcher ? null : dispatcher.getOwner();
    }
    function UnknownOwner() {
        return Error("react-stack-top-frame");
    }
    function hasValidKey(config) {
        if (hasOwnProperty.call(config, "key")) {
            var getter = Object.getOwnPropertyDescriptor(config, "key").get;
            if (getter && getter.isReactWarning) return !1;
        }
        return void 0 !== config.key;
    }
    function defineKeyPropWarningGetter(props, displayName) {
        function warnAboutAccessingKey() {
            specialPropKeyWarningShown || (specialPropKeyWarningShown = !0, console.error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://react.dev/link/special-props)", displayName));
        }
        warnAboutAccessingKey.isReactWarning = !0;
        Object.defineProperty(props, "key", {
            get: warnAboutAccessingKey,
            configurable: !0
        });
    }
    function elementRefGetterWithDeprecationWarning() {
        var componentName = getComponentNameFromType(this.type);
        didWarnAboutElementRef[componentName] || (didWarnAboutElementRef[componentName] = !0, console.error("Accessing element.ref was removed in React 19. ref is now a regular prop. It will be removed from the JSX Element type in a future release."));
        componentName = this.props.ref;
        return void 0 !== componentName ? componentName : null;
    }
    function ReactElement(type, key, props, owner, debugStack, debugTask) {
        var refProp = props.ref;
        type = {
            $$typeof: REACT_ELEMENT_TYPE,
            type: type,
            key: key,
            props: props,
            _owner: owner
        };
        null !== (void 0 !== refProp ? refProp : null) ? Object.defineProperty(type, "ref", {
            enumerable: !1,
            get: elementRefGetterWithDeprecationWarning
        }) : Object.defineProperty(type, "ref", {
            enumerable: !1,
            value: null
        });
        type._store = {};
        Object.defineProperty(type._store, "validated", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: 0
        });
        Object.defineProperty(type, "_debugInfo", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: null
        });
        Object.defineProperty(type, "_debugStack", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: debugStack
        });
        Object.defineProperty(type, "_debugTask", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: debugTask
        });
        Object.freeze && (Object.freeze(type.props), Object.freeze(type));
        return type;
    }
    function jsxDEVImpl(type, config, maybeKey, isStaticChildren, debugStack, debugTask) {
        var children = config.children;
        if (void 0 !== children) if (isStaticChildren) if (isArrayImpl(children)) {
            for(isStaticChildren = 0; isStaticChildren < children.length; isStaticChildren++)validateChildKeys(children[isStaticChildren]);
            Object.freeze && Object.freeze(children);
        } else console.error("React.jsx: Static children should always be an array. You are likely explicitly calling React.jsxs or React.jsxDEV. Use the Babel transform instead.");
        else validateChildKeys(children);
        if (hasOwnProperty.call(config, "key")) {
            children = getComponentNameFromType(type);
            var keys = Object.keys(config).filter(function(k) {
                return "key" !== k;
            });
            isStaticChildren = 0 < keys.length ? "{key: someKey, " + keys.join(": ..., ") + ": ...}" : "{key: someKey}";
            didWarnAboutKeySpread[children + isStaticChildren] || (keys = 0 < keys.length ? "{" + keys.join(": ..., ") + ": ...}" : "{}", console.error('A props object containing a "key" prop is being spread into JSX:\n  let props = %s;\n  <%s {...props} />\nReact keys must be passed directly to JSX without using spread:\n  let props = %s;\n  <%s key={someKey} {...props} />', isStaticChildren, children, keys, children), didWarnAboutKeySpread[children + isStaticChildren] = !0);
        }
        children = null;
        void 0 !== maybeKey && (checkKeyStringCoercion(maybeKey), children = "" + maybeKey);
        hasValidKey(config) && (checkKeyStringCoercion(config.key), children = "" + config.key);
        if ("key" in config) {
            maybeKey = {};
            for(var propName in config)"key" !== propName && (maybeKey[propName] = config[propName]);
        } else maybeKey = config;
        children && defineKeyPropWarningGetter(maybeKey, "function" === typeof type ? type.displayName || type.name || "Unknown" : type);
        return ReactElement(type, children, maybeKey, getOwner(), debugStack, debugTask);
    }
    function validateChildKeys(node) {
        isValidElement(node) ? node._store && (node._store.validated = 1) : "object" === typeof node && null !== node && node.$$typeof === REACT_LAZY_TYPE && ("fulfilled" === node._payload.status ? isValidElement(node._payload.value) && node._payload.value._store && (node._payload.value._store.validated = 1) : node._store && (node._store.validated = 1));
    }
    function isValidElement(object) {
        return "object" === typeof object && null !== object && object.$$typeof === REACT_ELEMENT_TYPE;
    }
    var React = __turbopack_context__.r("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)"), REACT_ELEMENT_TYPE = Symbol.for("react.transitional.element"), REACT_PORTAL_TYPE = Symbol.for("react.portal"), REACT_FRAGMENT_TYPE = Symbol.for("react.fragment"), REACT_STRICT_MODE_TYPE = Symbol.for("react.strict_mode"), REACT_PROFILER_TYPE = Symbol.for("react.profiler"), REACT_CONSUMER_TYPE = Symbol.for("react.consumer"), REACT_CONTEXT_TYPE = Symbol.for("react.context"), REACT_FORWARD_REF_TYPE = Symbol.for("react.forward_ref"), REACT_SUSPENSE_TYPE = Symbol.for("react.suspense"), REACT_SUSPENSE_LIST_TYPE = Symbol.for("react.suspense_list"), REACT_MEMO_TYPE = Symbol.for("react.memo"), REACT_LAZY_TYPE = Symbol.for("react.lazy"), REACT_ACTIVITY_TYPE = Symbol.for("react.activity"), REACT_VIEW_TRANSITION_TYPE = Symbol.for("react.view_transition"), REACT_CLIENT_REFERENCE = Symbol.for("react.client.reference"), ReactSharedInternals = React.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, hasOwnProperty = Object.prototype.hasOwnProperty, isArrayImpl = Array.isArray, createTask = console.createTask ? console.createTask : function() {
        return null;
    };
    React = {
        react_stack_bottom_frame: function(callStackForError) {
            return callStackForError();
        }
    };
    var specialPropKeyWarningShown;
    var didWarnAboutElementRef = {};
    var unknownOwnerDebugStack = React.react_stack_bottom_frame.bind(React, UnknownOwner)();
    var unknownOwnerDebugTask = createTask(getTaskName(UnknownOwner));
    var didWarnAboutKeySpread = {};
    exports.Fragment = REACT_FRAGMENT_TYPE;
    exports.jsxDEV = function(type, config, maybeKey, isStaticChildren) {
        var trackActualOwner = 1e4 > ReactSharedInternals.recentlyCreatedOwnerStacks++;
        if (trackActualOwner) {
            var previousStackTraceLimit = Error.stackTraceLimit;
            Error.stackTraceLimit = 10;
            var debugStackDEV = Error("react-stack-top-frame");
            Error.stackTraceLimit = previousStackTraceLimit;
        } else debugStackDEV = unknownOwnerDebugStack;
        return jsxDEVImpl(type, config, maybeKey, isStaticChildren, debugStackDEV, trackActualOwner ? createTask(getTaskName(type)) : unknownOwnerDebugTask);
    };
}();
}),
"[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
'use strict';
if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
;
else {
    module.exports = __turbopack_context__.r("[project]/node_modules/next/dist/compiled/react/cjs/react-jsx-dev-runtime.development.js [app-client] (ecmascript)");
}
}),
]);

//# sourceMappingURL=_cbd988b3._.js.map