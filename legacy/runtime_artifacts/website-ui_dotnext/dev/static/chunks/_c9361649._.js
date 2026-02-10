(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/components/DashboardFilters.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>DashboardFilters
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
const groupLabels = {
    crypto: "Cripto",
    volatility: "Volatilidade",
    commodities_broad: "Commodities",
    energy: "Energia",
    metals: "Metais",
    bonds_rates: "Juros/Bonds",
    fx: "Moedas",
    equities_us_broad: "Equities US Broad",
    equities_us_sectors: "Equities US Setores",
    equities_international: "Equities Internacionais",
    realestate: "Imobiliario"
};
function DashboardFilters(props) {
    _s();
    const { assets, selected, onSelectedChange, sector, onSectorChange, timeframe, onTimeframeChange, rangePreset, onRangePresetChange, normalize, onNormalizeChange, showRegimeBands, onShowRegimeBandsChange, smoothing, onSmoothingChange } = props;
    const [query, setQuery] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [open, setOpen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const filtered = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "DashboardFilters.useMemo[filtered]": ()=>{
            const q = query.trim().toLowerCase();
            return assets.filter({
                "DashboardFilters.useMemo[filtered]": (a)=>sector === "all" || (a.group || "") === sector
            }["DashboardFilters.useMemo[filtered]"]).filter({
                "DashboardFilters.useMemo[filtered]": (a)=>!q || a.asset.toLowerCase().includes(q) || (a.group || "").toLowerCase().includes(q)
            }["DashboardFilters.useMemo[filtered]"]).slice(0, 100);
        }
    }["DashboardFilters.useMemo[filtered]"], [
        assets,
        query,
        sector
    ]);
    const sectors = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "DashboardFilters.useMemo[sectors]": ()=>{
            const set = new Set();
            assets.forEach({
                "DashboardFilters.useMemo[sectors]": (a)=>{
                    if (a.group) set.add(a.group);
                }
            }["DashboardFilters.useMemo[sectors]"]);
            return [
                "all",
                ...Array.from(set).sort()
            ];
        }
    }["DashboardFilters.useMemo[sectors]"], [
        assets
    ]);
    const toggleAsset = (asset)=>{
        if (selected.includes(asset)) {
            onSelectedChange(selected.filter((a)=>a !== asset));
            return;
        }
        if (selected.length >= 12) return;
        onSelectedChange([
            ...selected,
            asset
        ]);
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "sticky top-2 z-20 rounded-xl border border-zinc-800 bg-zinc-950/95 p-4 md:p-5 backdrop-blur-sm",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-7 gap-3",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "xl:col-span-2 relative",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            className: "w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-sm",
                            onClick: ()=>setOpen((v)=>!v),
                            title: "Selecionar ativos",
                            children: selected.length ? `${selected.length} ativos selecionados` : "Selecionar ativos"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 93,
                            columnNumber: 11
                        }, this),
                        open ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "absolute mt-2 w-full max-h-72 overflow-auto rounded-lg border border-zinc-700 bg-zinc-950 p-2 shadow-xl",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                    className: "mb-2 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs",
                                    placeholder: "Buscar ativo",
                                    value: query,
                                    onChange: (e)=>setQuery(e.target.value)
                                }, void 0, false, {
                                    fileName: "[project]/components/DashboardFilters.tsx",
                                    lineNumber: 102,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "space-y-1",
                                    children: filtered.map((a)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                            className: "flex items-center gap-2 rounded px-1 py-1 text-xs hover:bg-zinc-900",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                    type: "checkbox",
                                                    checked: selected.includes(a.asset),
                                                    onChange: ()=>toggleAsset(a.asset),
                                                    className: "h-3 w-3 accent-cyan-400"
                                                }, void 0, false, {
                                                    fileName: "[project]/components/DashboardFilters.tsx",
                                                    lineNumber: 111,
                                                    columnNumber: 21
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                    className: "font-medium",
                                                    children: a.asset
                                                }, void 0, false, {
                                                    fileName: "[project]/components/DashboardFilters.tsx",
                                                    lineNumber: 117,
                                                    columnNumber: 21
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                    className: "text-zinc-500",
                                                    children: groupLabels[a.group || ""] || a.group || ""
                                                }, void 0, false, {
                                                    fileName: "[project]/components/DashboardFilters.tsx",
                                                    lineNumber: 118,
                                                    columnNumber: 21
                                                }, this)
                                            ]
                                        }, a.asset, true, {
                                            fileName: "[project]/components/DashboardFilters.tsx",
                                            lineNumber: 110,
                                            columnNumber: 19
                                        }, this))
                                }, void 0, false, {
                                    fileName: "[project]/components/DashboardFilters.tsx",
                                    lineNumber: 108,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 101,
                            columnNumber: 13
                        }, this) : null
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/DashboardFilters.tsx",
                    lineNumber: 92,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                    value: sector,
                    onChange: (e)=>onSectorChange(e.target.value),
                    className: "rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm",
                    title: "Filtrar por setor",
                    children: sectors.map((s)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: s,
                            children: s === "all" ? "Todos os setores" : groupLabels[s] || s
                        }, s, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 133,
                            columnNumber: 13
                        }, this))
                }, void 0, false, {
                    fileName: "[project]/components/DashboardFilters.tsx",
                    lineNumber: 126,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                    value: timeframe,
                    onChange: (e)=>onTimeframeChange(e.target.value),
                    className: "rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "daily",
                            children: "Diario"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 144,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "weekly",
                            children: "Semanal"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 145,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/DashboardFilters.tsx",
                    lineNumber: 139,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                    value: rangePreset,
                    onChange: (e)=>onRangePresetChange(e.target.value),
                    className: "rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "30d",
                            children: "Ultimos 30d"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 153,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "90d",
                            children: "Ultimos 90d"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 154,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "180d",
                            children: "Ultimos 180d"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 155,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "1y",
                            children: "Ultimo 1y"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 156,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "all",
                            children: "Tudo"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 157,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/DashboardFilters.tsx",
                    lineNumber: 148,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                    value: smoothing,
                    onChange: (e)=>onSmoothingChange(e.target.value),
                    className: "rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "none",
                            children: "Suavizacao: none"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 165,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "ema_short",
                            children: "Suavizacao: EMA curto"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 166,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                            value: "ema_long",
                            children: "Suavizacao: EMA longo"
                        }, void 0, false, {
                            fileName: "[project]/components/DashboardFilters.tsx",
                            lineNumber: 167,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/DashboardFilters.tsx",
                    lineNumber: 160,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    className: `rounded-lg border px-3 py-2 text-sm ${normalize ? "border-cyan-400 text-cyan-300" : "border-zinc-700"}`,
                    onClick: ()=>onNormalizeChange(!normalize),
                    children: normalize ? "Normalizar: ON" : "Normalizar: OFF"
                }, void 0, false, {
                    fileName: "[project]/components/DashboardFilters.tsx",
                    lineNumber: 170,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    className: `rounded-lg border px-3 py-2 text-sm ${showRegimeBands ? "border-cyan-400 text-cyan-300" : "border-zinc-700"}`,
                    onClick: ()=>onShowRegimeBandsChange(!showRegimeBands),
                    children: showRegimeBands ? "Bandas regime: ON" : "Bandas regime: OFF"
                }, void 0, false, {
                    fileName: "[project]/components/DashboardFilters.tsx",
                    lineNumber: 177,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/DashboardFilters.tsx",
            lineNumber: 91,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/components/DashboardFilters.tsx",
        lineNumber: 90,
        columnNumber: 5
    }, this);
}
_s(DashboardFilters, "z9t73rnqgiD1qJ+CMbkeyl+ixRY=");
_c = DashboardFilters;
var _c;
__turbopack_context__.k.register(_c, "DashboardFilters");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/RegimeChart.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>RegimeChart
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
const regimeColors = {
    STABLE: "rgba(52,211,153,0.14)",
    TRANSITION: "rgba(251,191,36,0.14)",
    UNSTABLE: "rgba(251,113,133,0.14)"
};
const lineColors = [
    "#38bdf8",
    "#22c55e",
    "#f97316",
    "#a855f7",
    "#facc15",
    "#14b8a6",
    "#f472b6",
    "#60a5fa"
];
function formatDate(d) {
    if (!d) return "";
    const t = new Date(`${d}T00:00:00Z`);
    const mm = String(t.getUTCMonth() + 1).padStart(2, "0");
    const yy = String(t.getUTCFullYear()).slice(-2);
    return `${mm}/${yy}`;
}
function formatValue(v) {
    const a = Math.abs(v);
    if (a >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
    if (a >= 1_000) return `${(v / 1_000).toFixed(1)}K`;
    return v.toFixed(2);
}
function ema(values, period) {
    if (!values.length) return values;
    const alpha = 2 / (period + 1);
    const out = [
        values[0]
    ];
    for(let i = 1; i < values.length; i += 1){
        out.push(alpha * values[i] + (1 - alpha) * out[i - 1]);
    }
    return out;
}
function downsample(arr, max = 2000) {
    if (arr.length <= max) return arr;
    const step = Math.ceil(arr.length / max);
    return arr.filter((_, idx)=>idx % step === 0);
}
function rangeCount(preset) {
    if (preset === "30d") return 30;
    if (preset === "90d") return 90;
    if (preset === "180d") return 180;
    if (preset === "1y") return 252;
    return 0;
}
function RegimeChart(props) {
    _s();
    const { data, selected, normalize, showRegimeBands, smoothing, rangePreset } = props;
    const [hidden, setHidden] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({});
    const [hoverIndex, setHoverIndex] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const prepared = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "RegimeChart.useMemo[prepared]": ()=>{
            const active = selected.filter({
                "RegimeChart.useMemo[prepared].active": (a)=>!hidden[a] && (data[a] || []).length
            }["RegimeChart.useMemo[prepared].active"]);
            if (!active.length) return null;
            let commonLen = Math.min(...active.map({
                "RegimeChart.useMemo[prepared].commonLen": (a)=>data[a].length
            }["RegimeChart.useMemo[prepared].commonLen"]));
            const rc = rangeCount(rangePreset);
            if (rc > 0) commonLen = Math.min(commonLen, rc);
            const aligned = active.map({
                "RegimeChart.useMemo[prepared].aligned": (a)=>({
                        asset: a,
                        points: data[a].slice(-commonLen)
                    })
            }["RegimeChart.useMemo[prepared].aligned"]);
            const sampled = aligned.map({
                "RegimeChart.useMemo[prepared].sampled": (s)=>({
                        asset: s.asset,
                        points: downsample(s.points, 1600)
                    })
            }["RegimeChart.useMemo[prepared].sampled"]);
            const series = sampled.map({
                "RegimeChart.useMemo[prepared].series": (s)=>{
                    const prices = s.points.map({
                        "RegimeChart.useMemo[prepared].series.prices": (p)=>p.price == null ? NaN : p.price
                    }["RegimeChart.useMemo[prepared].series.prices"]);
                    const base = prices.find({
                        "RegimeChart.useMemo[prepared].series": (v)=>Number.isFinite(v)
                    }["RegimeChart.useMemo[prepared].series"]) || 1;
                    const normalized = prices.map({
                        "RegimeChart.useMemo[prepared].series.normalized": (v)=>Number.isFinite(v) ? v / base * 100 : NaN
                    }["RegimeChart.useMemo[prepared].series.normalized"]);
                    const source = normalize ? normalized : prices;
                    const smooth = smoothing === "ema_short" ? ema(source, 8) : smoothing === "ema_long" ? ema(source, 20) : source;
                    return {
                        asset: s.asset,
                        points: s.points,
                        values: smooth
                    };
                }
            }["RegimeChart.useMemo[prepared].series"]);
            const allValues = series.flatMap({
                "RegimeChart.useMemo[prepared].allValues": (s)=>s.values
            }["RegimeChart.useMemo[prepared].allValues"]).filter({
                "RegimeChart.useMemo[prepared].allValues": (v)=>Number.isFinite(v)
            }["RegimeChart.useMemo[prepared].allValues"]);
            if (!allValues.length) return null;
            const ymin = Math.min(...allValues);
            const ymax = Math.max(...allValues);
            return {
                series,
                ymin,
                ymax,
                count: series[0].values.length,
                focus: series[0].points
            };
        }
    }["RegimeChart.useMemo[prepared]"], [
        data,
        selected,
        normalize,
        smoothing,
        hidden,
        rangePreset
    ]);
    const width = 1200;
    const height = 480;
    const pad = 56;
    const scaleX = (i, total)=>pad + i / Math.max(1, total - 1) * (width - pad * 2);
    const scaleY = (v, ymin, ymax, h)=>h - pad - (v - ymin) / Math.max(1e-9, ymax - ymin) * (h - pad * 2);
    if (!prepared) return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "text-sm text-zinc-500",
        children: "Selecione ativos para visualizar o grafico."
    }, void 0, false, {
        fileName: "[project]/components/RegimeChart.tsx",
        lineNumber: 124,
        columnNumber: 25
    }, this);
    const h = height;
    const hover = hoverIndex != null ? Math.min(hoverIndex, prepared.count - 1) : null;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "space-y-3",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between text-xs text-zinc-400",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: "Grafico principal"
                    }, void 0, false, {
                        fileName: "[project]/components/RegimeChart.tsx",
                        lineNumber: 132,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        className: "rounded border border-zinc-700 px-2 py-1 hover:border-zinc-500",
                        onClick: ()=>setHidden({}),
                        children: "Reset series"
                    }, void 0, false, {
                        fileName: "[project]/components/RegimeChart.tsx",
                        lineNumber: 133,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/RegimeChart.tsx",
                lineNumber: 131,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "rounded-xl border border-zinc-800 p-4 md:p-5 bg-transparent",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                    viewBox: `0 0 ${width} ${h}`,
                    className: "w-full h-[360px] lg:h-[500px]",
                    onMouseMove: (e)=>{
                        const rect = e.currentTarget.getBoundingClientRect();
                        const localX = e.clientX - rect.left;
                        const idx = Math.round((localX - pad) / Math.max(1, rect.width - 2 * pad) * (prepared.count - 1));
                        setHoverIndex(Math.max(0, Math.min(prepared.count - 1, idx)));
                    },
                    onMouseLeave: ()=>setHoverIndex(null),
                    children: [
                        showRegimeBands ? prepared.focus.map((p, i, arr)=>{
                            if (i === 0) return null;
                            const x0 = scaleX(i - 1, arr.length);
                            const x1 = scaleX(i, arr.length);
                            const regime = p.regime in regimeColors ? p.regime : "TRANSITION";
                            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("rect", {
                                x: x0,
                                y: pad,
                                width: Math.max(1, x1 - x0),
                                height: h - 2 * pad,
                                fill: regimeColors[regime]
                            }, `band-${i}`, false, {
                                fileName: "[project]/components/RegimeChart.tsx",
                                lineNumber: 159,
                                columnNumber: 24
                            }, this);
                        }) : null,
                        Array.from({
                            length: 5
                        }).map((_, i)=>{
                            const y = pad + (h - 2 * pad) * i / 4;
                            const v = prepared.ymax - (prepared.ymax - prepared.ymin) * i / 4;
                            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("g", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("line", {
                                        x1: pad,
                                        y1: y,
                                        x2: width - pad,
                                        y2: y,
                                        stroke: "rgba(148,163,184,0.14)"
                                    }, void 0, false, {
                                        fileName: "[project]/components/RegimeChart.tsx",
                                        lineNumber: 168,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("text", {
                                        x: pad - 10,
                                        y: y + 4,
                                        textAnchor: "end",
                                        fill: "#94a3b8",
                                        fontSize: "11",
                                        children: formatValue(v)
                                    }, void 0, false, {
                                        fileName: "[project]/components/RegimeChart.tsx",
                                        lineNumber: 169,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, `y-${i}`, true, {
                                fileName: "[project]/components/RegimeChart.tsx",
                                lineNumber: 167,
                                columnNumber: 15
                            }, this);
                        }),
                        Array.from({
                            length: 6
                        }).map((_, i)=>{
                            const idx = Math.round(i / 5 * (prepared.count - 1));
                            const x = scaleX(idx, prepared.count);
                            const dt = prepared.series[0].points[idx]?.date;
                            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("g", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("line", {
                                        x1: x,
                                        y1: pad,
                                        x2: x,
                                        y2: h - pad,
                                        stroke: "rgba(148,163,184,0.08)"
                                    }, void 0, false, {
                                        fileName: "[project]/components/RegimeChart.tsx",
                                        lineNumber: 182,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("text", {
                                        x: x,
                                        y: h - pad + 18,
                                        textAnchor: "middle",
                                        fill: "#94a3b8",
                                        fontSize: "11",
                                        children: formatDate(dt)
                                    }, void 0, false, {
                                        fileName: "[project]/components/RegimeChart.tsx",
                                        lineNumber: 183,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, `x-${i}`, true, {
                                fileName: "[project]/components/RegimeChart.tsx",
                                lineNumber: 181,
                                columnNumber: 15
                            }, this);
                        }),
                        prepared.series.map((s, idx)=>{
                            const d = s.values.map((v, i)=>Number.isFinite(v) ? `${i === 0 ? "M" : "L"} ${scaleX(i, s.values.length)} ${scaleY(v, prepared.ymin, prepared.ymax, h)}` : "").join(" ");
                            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                d: d,
                                fill: "none",
                                stroke: lineColors[idx % lineColors.length],
                                strokeWidth: "2.2"
                            }, s.asset, false, {
                                fileName: "[project]/components/RegimeChart.tsx",
                                lineNumber: 194,
                                columnNumber: 20
                            }, this);
                        }),
                        hover != null ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("line", {
                            x1: scaleX(hover, prepared.count),
                            y1: pad,
                            x2: scaleX(hover, prepared.count),
                            y2: h - pad,
                            stroke: "rgba(226,232,240,0.5)",
                            strokeDasharray: "4 4"
                        }, void 0, false, {
                            fileName: "[project]/components/RegimeChart.tsx",
                            lineNumber: 198,
                            columnNumber: 13
                        }, this) : null
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/RegimeChart.tsx",
                    lineNumber: 142,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/RegimeChart.tsx",
                lineNumber: 141,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-wrap gap-2 text-xs",
                children: prepared.series.map((s, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        className: `rounded-full border px-2 py-1 ${hidden[s.asset] ? "border-zinc-700 text-zinc-500" : "border-zinc-600 text-zinc-200"}`,
                        onClick: ()=>setHidden((prev)=>({
                                    ...prev,
                                    [s.asset]: !prev[s.asset]
                                })),
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "inline-block h-2 w-2 rounded-full mr-2",
                                style: {
                                    background: lineColors[idx % lineColors.length]
                                }
                            }, void 0, false, {
                                fileName: "[project]/components/RegimeChart.tsx",
                                lineNumber: 210,
                                columnNumber: 13
                            }, this),
                            s.asset
                        ]
                    }, s.asset, true, {
                        fileName: "[project]/components/RegimeChart.tsx",
                        lineNumber: 205,
                        columnNumber: 11
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/RegimeChart.tsx",
                lineNumber: 203,
                columnNumber: 7
            }, this),
            hover != null ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-300",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Data: ",
                            prepared.series[0].points[hover]?.date || "--"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RegimeChart.tsx",
                        lineNumber: 218,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Regime: ",
                            prepared.series[0].points[hover]?.regime || "--"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RegimeChart.tsx",
                        lineNumber: 219,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Confianca: ",
                            ((prepared.series[0].points[hover]?.confidence || 0) * 100).toFixed(1),
                            "%"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RegimeChart.tsx",
                        lineNumber: 220,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Qualidade: ",
                            ((prepared.series[0].points[hover]?.confidence || 0) * 0.92 * 100).toFixed(1),
                            "%"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/RegimeChart.tsx",
                        lineNumber: 221,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/RegimeChart.tsx",
                lineNumber: 217,
                columnNumber: 9
            }, this) : null
        ]
    }, void 0, true, {
        fileName: "[project]/components/RegimeChart.tsx",
        lineNumber: 130,
        columnNumber: 5
    }, this);
}
_s(RegimeChart, "HNH3DK8uLuvqHjgGqfOyr6STFtE=");
_c = RegimeChart;
var _c;
__turbopack_context__.k.register(_c, "RegimeChart");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/SectorDashboard.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>SectorDashboard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$DashboardFilters$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/DashboardFilters.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$RegimeChart$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/RegimeChart.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
const regimeColor = {
    STABLE: "text-emerald-300",
    TRANSITION: "text-amber-300",
    UNSTABLE: "text-rose-300"
};
const groupLabels = {
    crypto: "Cripto",
    volatility: "Volatilidade",
    commodities_broad: "Commodities",
    energy: "Energia",
    metals: "Metais",
    bonds_rates: "Juros/Bonds",
    fx: "Moedas",
    equities_us_broad: "Equities US Broad",
    equities_us_sectors: "Equities US Setores",
    equities_international: "Equities Internacionais",
    realestate: "Imobiliario"
};
function cleanRegime(label) {
    if (!label) return "TRANSITION";
    if (label === "NOISY") return "UNSTABLE";
    if (label === "STABLE" || label === "TRANSITION" || label === "UNSTABLE") return label;
    return "TRANSITION";
}
function mean(nums) {
    if (!nums.length) return 0;
    return nums.reduce((a, b)=>a + b, 0) / nums.length;
}
function SectorDashboard({ title, showTable = true }) {
    _s();
    const [timeframe, setTimeframe] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("daily");
    const [sector, setSector] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("all");
    const [rangePreset, setRangePreset] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("180d");
    const [normalize, setNormalize] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [showRegimeBands, setShowRegimeBands] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const [smoothing, setSmoothing] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("none");
    const [summaryHorizon, setSummaryHorizon] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(5);
    const [universe, setUniverse] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [selected, setSelected] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [seriesByAsset, setSeriesByAsset] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({});
    const [forecastByAsset, setForecastByAsset] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({});
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "SectorDashboard.useEffect": ()=>{
            const loadUniverse = {
                "SectorDashboard.useEffect.loadUniverse": async ()=>{
                    const res = await fetch(`/api/graph/universe?tf=${timeframe}`);
                    const data = await res.json();
                    if (!Array.isArray(data)) {
                        setUniverse([]);
                        setSelected([]);
                        return;
                    }
                    setUniverse(data);
                    setSelected({
                        "SectorDashboard.useEffect.loadUniverse": (prev)=>{
                            const valid = prev.filter({
                                "SectorDashboard.useEffect.loadUniverse.valid": (a)=>data.find({
                                        "SectorDashboard.useEffect.loadUniverse.valid": (u)=>u.asset === a
                                    }["SectorDashboard.useEffect.loadUniverse.valid"])
                            }["SectorDashboard.useEffect.loadUniverse.valid"]);
                            return valid.length ? valid : data.slice(0, 4).map({
                                "SectorDashboard.useEffect.loadUniverse": (u)=>u.asset
                            }["SectorDashboard.useEffect.loadUniverse"]);
                        }
                    }["SectorDashboard.useEffect.loadUniverse"]);
                }
            }["SectorDashboard.useEffect.loadUniverse"];
            loadUniverse();
        }
    }["SectorDashboard.useEffect"], [
        timeframe
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "SectorDashboard.useEffect": ()=>{
            if (!universe.length) return;
            const scoped = universe.filter({
                "SectorDashboard.useEffect.scoped": (u)=>sector === "all" || (u.group || "") === sector
            }["SectorDashboard.useEffect.scoped"]).map({
                "SectorDashboard.useEffect.scoped": (u)=>u.asset
            }["SectorDashboard.useEffect.scoped"]);
            setSelected({
                "SectorDashboard.useEffect": (prev)=>{
                    const kept = prev.filter({
                        "SectorDashboard.useEffect.kept": (a)=>scoped.includes(a)
                    }["SectorDashboard.useEffect.kept"]);
                    if (kept.length) return kept;
                    return scoped.slice(0, 6);
                }
            }["SectorDashboard.useEffect"]);
        }
    }["SectorDashboard.useEffect"], [
        sector,
        universe
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "SectorDashboard.useEffect": ()=>{
            const loadSeries = {
                "SectorDashboard.useEffect.loadSeries": async ()=>{
                    if (!selected.length) {
                        setSeriesByAsset({});
                        return;
                    }
                    setLoading(true);
                    try {
                        const seriesRes = await fetch(`/api/graph/series-batch?assets=${selected.join(",")}&tf=${timeframe}&limit=2000`);
                        const seriesJson = await seriesRes.json();
                        setSeriesByAsset(seriesJson || {});
                        const forecasts = {};
                        await Promise.all(selected.map({
                            "SectorDashboard.useEffect.loadSeries": async (asset)=>{
                                forecasts[asset] = {
                                    1: null,
                                    5: null,
                                    10: null
                                };
                                try {
                                    await Promise.all([
                                        1,
                                        5,
                                        10
                                    ].map({
                                        "SectorDashboard.useEffect.loadSeries": async (h)=>{
                                            try {
                                                const f = await fetch(`/api/files/forecast_suite/${asset}/${timeframe}/${asset}_${timeframe}_log_return_h${h}.json`);
                                                if (!f.ok) {
                                                    forecasts[asset][h] = null;
                                                    return;
                                                }
                                                const j = await f.json();
                                                const preds = Array.isArray(j?.predictions) ? j.predictions : [];
                                                forecasts[asset][h] = preds.length ? preds[preds.length - 1] : null;
                                            } catch  {
                                                forecasts[asset][h] = null;
                                            }
                                        }
                                    }["SectorDashboard.useEffect.loadSeries"]));
                                } catch  {
                                    forecasts[asset] = {
                                        1: null,
                                        5: null,
                                        10: null
                                    };
                                }
                            }
                        }["SectorDashboard.useEffect.loadSeries"]));
                        setForecastByAsset(forecasts);
                    } finally{
                        setLoading(false);
                    }
                }
            }["SectorDashboard.useEffect.loadSeries"];
            loadSeries();
        }
    }["SectorDashboard.useEffect"], [
        selected,
        timeframe
    ]);
    const metrics = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "SectorDashboard.useMemo[metrics]": ()=>{
            const activeSeries = selected.flatMap({
                "SectorDashboard.useMemo[metrics].activeSeries": (a)=>seriesByAsset[a] || []
            }["SectorDashboard.useMemo[metrics].activeSeries"]);
            const lastPoints = selected.map({
                "SectorDashboard.useMemo[metrics].lastPoints": (a)=>(seriesByAsset[a] || [])[Math.max(0, (seriesByAsset[a] || []).length - 1)]
            }["SectorDashboard.useMemo[metrics].lastPoints"]).filter(Boolean);
            const avgConf = mean(lastPoints.map({
                "SectorDashboard.useMemo[metrics].avgConf": (p)=>p.confidence || 0
            }["SectorDashboard.useMemo[metrics].avgConf"]));
            const unstableCount = lastPoints.filter({
                "SectorDashboard.useMemo[metrics]": (p)=>cleanRegime(p.regime) === "UNSTABLE"
            }["SectorDashboard.useMemo[metrics]"]).length;
            const dominantRegime = ({
                "SectorDashboard.useMemo[metrics].dominantRegime": ()=>{
                    const counts = {};
                    lastPoints.forEach({
                        "SectorDashboard.useMemo[metrics].dominantRegime": (p)=>{
                            const r = cleanRegime(p.regime);
                            counts[r] = (counts[r] || 0) + 1;
                        }
                    }["SectorDashboard.useMemo[metrics].dominantRegime"]);
                    return Object.entries(counts).sort({
                        "SectorDashboard.useMemo[metrics].dominantRegime": (a, b)=>b[1] - a[1]
                    }["SectorDashboard.useMemo[metrics].dominantRegime"])[0]?.[0] || "TRANSITION";
                }
            })["SectorDashboard.useMemo[metrics].dominantRegime"]();
            return {
                state: dominantRegime,
                confidence: avgConf,
                quality: Math.max(0, Math.min(1, avgConf * 0.9)),
                alerts: unstableCount,
                sampleSize: activeSeries.length
            };
        }
    }["SectorDashboard.useMemo[metrics]"], [
        selected,
        seriesByAsset
    ]);
    const tableRows = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "SectorDashboard.useMemo[tableRows]": ()=>{
            return selected.map({
                "SectorDashboard.useMemo[tableRows]": (asset)=>{
                    const series = seriesByAsset[asset] || [];
                    const last = series[series.length - 1];
                    const first = series[0];
                    const conf = last?.confidence ?? 0;
                    const regime = cleanRegime(last?.regime);
                    const ret = forecastByAsset[asset]?.[summaryHorizon]?.y_pred;
                    const lastRegimeIdx = series.length - 1;
                    let streak = 0;
                    for(let i = lastRegimeIdx; i >= 0; i -= 1){
                        if (cleanRegime(series[i]?.regime) === regime) streak += 1;
                        else break;
                    }
                    const regimeDurationDays = timeframe === "weekly" ? streak * 7 : streak;
                    let action = "Aguardar";
                    if (regime === "STABLE" && conf >= 0.6) action = "Aplicar";
                    if (regime === "UNSTABLE" || conf < 0.45) action = "Nao operar";
                    return {
                        asset,
                        group: groupLabels[universe.find({
                            "SectorDashboard.useMemo[tableRows]": (u)=>u.asset === asset
                        }["SectorDashboard.useMemo[tableRows]"])?.group || ""] || universe.find({
                            "SectorDashboard.useMemo[tableRows]": (u)=>u.asset === asset
                        }["SectorDashboard.useMemo[tableRows]"])?.group || "",
                        regime,
                        confidence: conf,
                        period: first && last ? `${first.date} -> ${last.date}` : "--",
                        regimeDurationDays,
                        price: last?.price,
                        forecast: ret,
                        action
                    };
                }
            }["SectorDashboard.useMemo[tableRows]"]);
        }
    }["SectorDashboard.useMemo[tableRows]"], [
        selected,
        seriesByAsset,
        forecastByAsset,
        universe,
        summaryHorizon,
        timeframe
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "p-4 md:p-5 space-y-4 md:space-y-5",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-xs uppercase tracking-[0.2em] text-zinc-400",
                        children: title
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 203,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                        className: "text-2xl font-semibold",
                        children: "Regimes por setor com projecao integrada"
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 204,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-sm text-zinc-400",
                        children: "Leitura estrutural do mercado com confianca e forecast condicional."
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 205,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/SectorDashboard.tsx",
                lineNumber: 202,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "grid grid-cols-2 lg:grid-cols-4 gap-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Card, {
                        label: "Estado",
                        value: metrics.state,
                        tone: metrics.state
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 209,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Card, {
                        label: "Confianca",
                        value: `${(metrics.confidence * 100).toFixed(1)}%`
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 210,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Card, {
                        label: "Qualidade",
                        value: `${(metrics.quality * 100).toFixed(1)}%`
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 211,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Card, {
                        label: "Alertas",
                        value: String(metrics.alerts)
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 212,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/SectorDashboard.tsx",
                lineNumber: 208,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 space-y-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$DashboardFilters$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        assets: universe,
                        selected: selected,
                        onSelectedChange: setSelected,
                        sector: sector,
                        onSectorChange: setSector,
                        timeframe: timeframe,
                        onTimeframeChange: setTimeframe,
                        rangePreset: rangePreset,
                        onRangePresetChange: setRangePreset,
                        normalize: normalize,
                        onNormalizeChange: setNormalize,
                        showRegimeBands: showRegimeBands,
                        onShowRegimeBandsChange: setShowRegimeBands,
                        smoothing: smoothing,
                        onSmoothingChange: setSmoothing
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 216,
                        columnNumber: 9
                    }, this),
                    loading ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-sm text-zinc-500",
                        children: "Carregando series..."
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 234,
                        columnNumber: 20
                    }, this) : null,
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$RegimeChart$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        data: seriesByAsset,
                        selected: selected,
                        normalize: normalize,
                        showRegimeBands: showRegimeBands,
                        smoothing: smoothing,
                        rangePreset: rangePreset
                    }, void 0, false, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 236,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/SectorDashboard.tsx",
                lineNumber: 215,
                columnNumber: 7
            }, this),
            showTable ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4 md:gap-5",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-sm uppercase tracking-widest text-zinc-400",
                                children: "Tabela por ativo"
                            }, void 0, false, {
                                fileName: "[project]/components/SectorDashboard.tsx",
                                lineNumber: 249,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-3 overflow-auto",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                                    className: "w-full text-xs",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("thead", {
                                            className: "text-zinc-500 uppercase",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: "Ativo"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 254,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: "Setor"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 255,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: "Periodo"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 256,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: "Regime"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 257,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: "Duracao"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 258,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: "Conf."
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 259,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: "Preco"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 260,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: [
                                                            "Proj. h",
                                                            summaryHorizon
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 261,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                        className: "text-left py-2",
                                                        children: "Acao"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/SectorDashboard.tsx",
                                                        lineNumber: 262,
                                                        columnNumber: 21
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/SectorDashboard.tsx",
                                                lineNumber: 253,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/SectorDashboard.tsx",
                                            lineNumber: 252,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tbody", {
                                            children: tableRows.map((r)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                                    className: "border-t border-zinc-800/70 text-zinc-300",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: "py-2",
                                                            children: r.asset
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 268,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: "py-2 text-zinc-400",
                                                            children: r.group || "-"
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 269,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: "py-2 text-zinc-400",
                                                            children: r.period
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 270,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: `py-2 ${regimeColor[r.regime] || "text-zinc-300"}`,
                                                            children: r.regime
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 271,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: "py-2 text-zinc-400",
                                                            children: [
                                                                r.regimeDurationDays,
                                                                "d"
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 272,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: "py-2",
                                                            children: [
                                                                (r.confidence * 100).toFixed(1),
                                                                "%"
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 273,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: "py-2",
                                                            children: r.price != null ? r.price.toFixed(2) : "--"
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 274,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: "py-2",
                                                            children: r.forecast != null ? `${(r.forecast * 100).toFixed(2)}%` : "--"
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 275,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                            className: "py-2",
                                                            children: r.action
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/SectorDashboard.tsx",
                                                            lineNumber: 276,
                                                            columnNumber: 23
                                                        }, this)
                                                    ]
                                                }, r.asset, true, {
                                                    fileName: "[project]/components/SectorDashboard.tsx",
                                                    lineNumber: 267,
                                                    columnNumber: 21
                                                }, this))
                                        }, void 0, false, {
                                            fileName: "[project]/components/SectorDashboard.tsx",
                                            lineNumber: 265,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/components/SectorDashboard.tsx",
                                    lineNumber: 251,
                                    columnNumber: 15
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/SectorDashboard.tsx",
                                lineNumber: 250,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 248,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5 space-y-3",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-sm uppercase tracking-widest text-zinc-400",
                                children: "Resumo"
                            }, void 0, false, {
                                fileName: "[project]/components/SectorDashboard.tsx",
                                lineNumber: 285,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-2 text-xs",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-zinc-400",
                                        children: "Horizonte:"
                                    }, void 0, false, {
                                        fileName: "[project]/components/SectorDashboard.tsx",
                                        lineNumber: 287,
                                        columnNumber: 15
                                    }, this),
                                    [
                                        1,
                                        5,
                                        10
                                    ].map((h)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            className: `rounded-md border px-2 py-1 ${summaryHorizon === h ? "border-cyan-400 text-cyan-300" : "border-zinc-700 text-zinc-300"}`,
                                            onClick: ()=>setSummaryHorizon(h),
                                            children: [
                                                "h",
                                                h
                                            ]
                                        }, h, true, {
                                            fileName: "[project]/components/SectorDashboard.tsx",
                                            lineNumber: 289,
                                            columnNumber: 17
                                        }, this))
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/SectorDashboard.tsx",
                                lineNumber: 286,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-xs text-zinc-300",
                                children: [
                                    "Amostras no chart: ",
                                    metrics.sampleSize
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/SectorDashboard.tsx",
                                lineNumber: 298,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-xs text-zinc-300",
                                children: [
                                    "Ativos selecionados: ",
                                    selected.length
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/SectorDashboard.tsx",
                                lineNumber: 299,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-xs text-zinc-300",
                                children: [
                                    "Regime dominante: ",
                                    metrics.state
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/SectorDashboard.tsx",
                                lineNumber: 300,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-xs text-zinc-300",
                                children: [
                                    "Confianca media: ",
                                    (metrics.confidence * 100).toFixed(1),
                                    "%"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/SectorDashboard.tsx",
                                lineNumber: 301,
                                columnNumber: 13
                            }, this),
                            tableRows.slice(0, 3).map((r)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "rounded-lg border border-zinc-800 p-2 text-xs",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "font-medium text-zinc-200",
                                            children: r.asset
                                        }, void 0, false, {
                                            fileName: "[project]/components/SectorDashboard.tsx",
                                            lineNumber: 304,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "text-zinc-400",
                                            children: r.period
                                        }, void 0, false, {
                                            fileName: "[project]/components/SectorDashboard.tsx",
                                            lineNumber: 305,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "text-zinc-300",
                                            children: [
                                                r.regime,
                                                " por ~",
                                                r.regimeDurationDays,
                                                "d • h",
                                                summaryHorizon,
                                                ": ",
                                                r.forecast != null ? `${(r.forecast * 100).toFixed(2)}%` : "--"
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/components/SectorDashboard.tsx",
                                            lineNumber: 306,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, r.asset, true, {
                                    fileName: "[project]/components/SectorDashboard.tsx",
                                    lineNumber: 303,
                                    columnNumber: 15
                                }, this))
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/SectorDashboard.tsx",
                        lineNumber: 284,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/SectorDashboard.tsx",
                lineNumber: 247,
                columnNumber: 9
            }, this) : null
        ]
    }, void 0, true, {
        fileName: "[project]/components/SectorDashboard.tsx",
        lineNumber: 201,
        columnNumber: 5
    }, this);
}
_s(SectorDashboard, "qAjYF/kc7yao1c6EsTEyJE8fp3k=");
_c = SectorDashboard;
function Card({ label, value, tone }) {
    const color = tone === "STABLE" ? "text-emerald-300" : tone === "UNSTABLE" ? "text-rose-300" : tone === "TRANSITION" ? "text-amber-300" : "text-zinc-100";
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "rounded-xl border border-zinc-800 bg-zinc-950/70 p-3 md:p-4",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "text-[11px] uppercase tracking-[0.2em] text-zinc-500",
                children: label
            }, void 0, false, {
                fileName: "[project]/components/SectorDashboard.tsx",
                lineNumber: 322,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: `mt-1 text-lg md:text-xl font-semibold ${color}`,
                children: value
            }, void 0, false, {
                fileName: "[project]/components/SectorDashboard.tsx",
                lineNumber: 323,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/SectorDashboard.tsx",
        lineNumber: 321,
        columnNumber: 5
    }, this);
}
_c1 = Card;
var _c, _c1;
__turbopack_context__.k.register(_c, "SectorDashboard");
__turbopack_context__.k.register(_c1, "Card");
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

//# sourceMappingURL=_c9361649._.js.map