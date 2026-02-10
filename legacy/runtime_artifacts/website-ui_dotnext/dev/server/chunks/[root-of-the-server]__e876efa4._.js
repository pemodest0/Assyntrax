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
"[project]/lib/server/results.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "contentTypeFor",
    ()=>contentTypeFor,
    "indexPath",
    ()=>indexPath,
    "readIndex",
    ()=>readIndex,
    "resolveResultsPath",
    ()=>resolveResultsPath,
    "resultsRoot",
    ()=>resultsRoot
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
;
;
function repoRoot() {
    return __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(process.cwd(), "..");
}
function resultsRoot() {
    const root = repoRoot();
    return process.env.RESULTS_DIR || __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(root, "results");
}
function indexPath() {
    return __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(resultsRoot(), "results_index.json");
}
async function readIndex() {
    const p = indexPath();
    const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(p, "utf-8");
    return JSON.parse(text);
}
function resolveResultsPath(rel) {
    const root = resultsRoot();
    const target = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(root, rel);
    const rootNorm = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(root);
    if (!target.startsWith(rootNorm + __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].sep) && target !== rootNorm) {
        throw new Error("path_outside_results");
    }
    return target;
}
function contentTypeFor(filePath) {
    const ext = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].extname(filePath).toLowerCase();
    if (ext === ".png") return "image/png";
    if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
    if (ext === ".svg") return "image/svg+xml";
    if (ext === ".pdf") return "application/pdf";
    if (ext === ".json") return "application/json";
    if (ext === ".csv") return "text/csv";
    if (ext === ".md") return "text/markdown";
    return "application/octet-stream";
}
}),
"[project]/app/api/graph/series-batch/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$results$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/server/results.ts [app-route] (ecmascript)");
;
;
;
;
function parseCsv(text) {
    const lines = text.trim().split("\n");
    const header = (lines.shift()?.split(",") || []).map((h)=>h.trim());
    return lines.map((line)=>{
        const parts = line.split(",").map((p)=>p.trim());
        const row = {};
        header.forEach((h, idx)=>{
            row[h] = parts[idx];
        });
        return row;
    });
}
function toWeeklyIndices(dates) {
    const out = [];
    let lastKey = "";
    for(let i = 0; i < dates.length; i += 1){
        const d = dates[i];
        const dt = new Date(d + "T00:00:00Z");
        const year = dt.getUTCFullYear();
        const week = Math.ceil(((dt.getTime() - Date.UTC(year, 0, 1)) / 86400000 + 1) / 7);
        const key = `${year}-W${week}`;
        if (key !== lastKey) {
            out.push(i);
            lastKey = key;
        } else {
            out[out.length - 1] = i;
        }
    }
    return out;
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
async function loadFallbackSeries(asset, tf, limit, step) {
    const priceFile = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join((0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$results$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["resultsRoot"])(), "..", "data", "raw", "finance", "yfinance_daily", `${asset}.csv`);
    const rawPrice = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(priceFile, "utf-8");
    const priceRows = parseCsv(rawPrice);
    const dates = priceRows.map((r)=>r.date).filter(Boolean);
    const returns = priceRows.map((r)=>Number(r.r)).filter((v)=>Number.isFinite(v));
    const window = 20;
    const volSeries = [];
    for(let i = window; i < returns.length; i += 1){
        const slice = returns.slice(i - window, i);
        volSeries.push(std(slice));
    }
    const q1 = quantile(volSeries, 0.33);
    const q2 = quantile(volSeries, 0.66);
    const minVol = Math.min(...volSeries, q1);
    const maxVol = Math.max(...volSeries, q2);
    const seriesRaw = priceRows.map((row, idx)=>{
        const vol = volSeries[idx - window] ?? volSeries[volSeries.length - 1] ?? 0;
        const regime = computeRegime(vol, q1, q2);
        const confidence = computeConfidence(vol, minVol, maxVol);
        return {
            date: row.date,
            confidence,
            regime,
            price: Number(row.price ?? NaN) || null
        };
    });
    let indices = [];
    if (tf === "weekly") {
        indices = toWeeklyIndices(dates);
    } else {
        indices = seriesRaw.map((_, idx)=>idx);
    }
    const sliced = indices.map((i)=>seriesRaw[i]).filter((r)=>r && r.date);
    const total = sliced.length;
    const n = limit ? Math.min(limit, total) : total;
    return sliced.slice(-n).filter((_, idx)=>idx % step === 0);
}
async function GET(request) {
    const { searchParams } = new URL(request.url);
    const assetsParam = searchParams.get("assets");
    const tf = searchParams.get("tf") || "weekly";
    const limitParam = searchParams.get("limit");
    const stepParam = searchParams.get("step");
    const limit = limitParam ? Math.max(1, Number(limitParam)) : 0;
    const step = stepParam ? Math.max(1, Number(stepParam)) : 1;
    if (!assetsParam) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: "missing_assets"
        }, {
            status: 400
        });
    }
    const assets = assetsParam.split(",").map((s)=>s.trim()).filter(Boolean);
    const out = {};
    await Promise.all(assets.map(async (asset)=>{
        try {
            const regimesFile = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join((0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$results$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["resultsRoot"])(), "latest_graph", "assets", `${asset}_${tf}_regimes.csv`);
            const rawReg = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(regimesFile, "utf-8");
            const regRows = parseCsv(rawReg);
            const priceFile = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join((0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$results$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["resultsRoot"])(), "..", "data", "raw", "finance", "yfinance_daily", `${asset}.csv`);
            const rawPrice = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(priceFile, "utf-8");
            const priceRows = parseCsv(rawPrice);
            const dates = priceRows.map((r)=>r.date).filter(Boolean);
            const indices = tf === "weekly" ? toWeeklyIndices(dates) : priceRows.map((_, idx)=>idx);
            const total = regRows.length;
            const n = limit ? Math.min(limit, total) : total;
            const sliceRegs = regRows.slice(-n);
            const sliceIdx = indices.slice(-n);
            const series = sliceRegs.filter((_, idx)=>idx % step === 0).map((r, i)=>{
                const priceRow = priceRows[sliceIdx[i] ?? 0];
                return {
                    date: priceRow?.date || "",
                    confidence: Number(r.confidence),
                    regime: r.regime,
                    price: Number(priceRow?.price ?? NaN) || null
                };
            });
            out[asset] = series;
        } catch  {
            try {
                out[asset] = await loadFallbackSeries(asset, tf, limit, step);
            } catch  {
                out[asset] = [];
            }
        }
    }));
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json(out);
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__e876efa4._.js.map