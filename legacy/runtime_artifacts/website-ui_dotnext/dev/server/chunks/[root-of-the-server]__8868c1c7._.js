module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/fs [external] (fs, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("fs", () => require("fs"));

module.exports = mod;
}),
"[externals]/path [external] (path, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("path", () => require("path"));

module.exports = mod;
}),
"[project]/app/api/graph/universe/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
;
;
;
function repoRoot() {
    return __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(process.cwd(), "..");
}
function parseCsv(text) {
    const lines = text.trim().split("\n");
    const header = (lines.shift()?.split(",") || []).map((h)=>h.trim());
    return lines.map((line)=>{
        const parts = line.split(",");
        const row = {};
        header.forEach((h, idx)=>{
            row[h] = (parts[idx] || "").trim();
        });
        return row;
    });
}
function std(values) {
    if (!values.length) return 0;
    const mean = values.reduce((a, b)=>a + b, 0) / values.length;
    const varSum = values.reduce((a, b)=>a + (b - mean) ** 2, 0) / values.length;
    return Math.sqrt(varSum);
}
function quantile(values, q) {
    if (!values.length) return 0;
    const sorted = [
        ...values
    ].sort((a, b)=>a - b);
    const pos = (sorted.length - 1) * q;
    const base = Math.floor(pos);
    const rest = pos - base;
    if (sorted[base + 1] !== undefined) {
        return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
    }
    return sorted[base];
}
function computeRegime(vol, q1, q2) {
    if (vol <= q1) return "STABLE";
    if (vol <= q2) return "TRANSITION";
    return "UNSTABLE";
}
function computeConfidence(vol, minVol, maxVol) {
    if (!Number.isFinite(vol) || maxVol <= minVol) return 0.6;
    const rel = (vol - minVol) / (maxVol - minVol);
    const conf = 0.6 + 0.3 * Math.abs(rel - 0.5) * 2;
    return Math.max(0.55, Math.min(0.9, conf));
}
async function GET(request) {
    const { searchParams } = new URL(request.url);
    const tf = searchParams.get("tf") || "weekly";
    const file = tf === "daily" ? "universe_daily.json" : "universe_weekly.json";
    const target = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(repoRoot(), "results", "latest_graph", file);
    try {
        const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(target, "utf-8");
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json(JSON.parse(text));
    } catch  {
        // fallback from asset_groups.csv + price data
        try {
            const groupsCsv = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(repoRoot(), "data", "asset_groups.csv"), "utf-8");
            const groups = parseCsv(groupsCsv);
            const out = [];
            for (const row of groups){
                const asset = row.asset;
                const group = row.group;
                try {
                    const priceFile = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(repoRoot(), "data", "raw", "finance", "yfinance_daily", `${asset}.csv`);
                    const raw = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(priceFile, "utf-8");
                    const rows = parseCsv(raw);
                    const returns = rows.map((r)=>Number(r.r)).filter((v)=>Number.isFinite(v));
                    const window = 20;
                    const volSeries = [];
                    for(let i = window; i < returns.length; i++){
                        const slice = returns.slice(i - window, i);
                        volSeries.push(std(slice));
                    }
                    const q1 = quantile(volSeries, 0.33);
                    const q2 = quantile(volSeries, 0.66);
                    const minVol = Math.min(...volSeries, q1);
                    const maxVol = Math.max(...volSeries, q2);
                    const lastVol = volSeries[volSeries.length - 1] ?? 0;
                    const regime = computeRegime(lastVol, q1, q2);
                    const confidence = computeConfidence(lastVol, minVol, maxVol);
                    out.push({
                        asset,
                        group,
                        state: {
                            label: regime
                        },
                        metrics: {
                            confidence
                        }
                    });
                } catch  {
                    out.push({
                        asset,
                        group,
                        state: {
                            label: "TRANSITION"
                        },
                        metrics: {
                            confidence: 0.6
                        }
                    });
                }
            }
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json(out);
        } catch  {
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                error: "graph_universe_not_found"
            }, {
                status: 404
            });
        }
    }
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__8868c1c7._.js.map