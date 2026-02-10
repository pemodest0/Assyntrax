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
"[project]/lib/server/validated.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "readAssetStatusMap",
    ()=>readAssetStatusMap,
    "readValidatedUniverse",
    ()=>readValidatedUniverse,
    "validatedRoot",
    ()=>validatedRoot
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
;
;
function repoRoot() {
    return __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(process.cwd(), "..");
}
function validatedRoot() {
    return process.env.VALIDATED_DIR || __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(repoRoot(), "results", "validated", "latest");
}
async function readValidatedUniverse(tf) {
    const file = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(validatedRoot(), `universe_${tf}.json`);
    const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(file, "utf-8");
    return JSON.parse(text);
}
async function readAssetStatusMap() {
    const file = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(validatedRoot(), "asset_status.csv");
    const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(file, "utf-8");
    const lines = text.trim().split("\n");
    const header = (lines.shift() || "").split(",").map((h)=>h.trim());
    const out = {};
    for (const line of lines){
        const parts = line.split(",");
        const row = {};
        header.forEach((h, i)=>{
            row[h] = (parts[i] || "").trim();
        });
        const key = `${row.asset}__${row.timeframe}`;
        out[key] = row;
    }
    return out;
}
}),
"[project]/lib/server/data.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "dataDirs",
    ()=>dataDirs,
    "findLatestApiRecords",
    ()=>findLatestApiRecords,
    "findLatestValidRun",
    ()=>findLatestValidRun,
    "listLatestFiles",
    ()=>listLatestFiles,
    "readDashboardOverview",
    ()=>readDashboardOverview,
    "readGlobalVerdict",
    ()=>readGlobalVerdict,
    "readJsonl",
    ()=>readJsonl,
    "readJsonlWithValidationGate",
    ()=>readJsonlWithValidationGate,
    "readLatestFile",
    ()=>readLatestFile,
    "readLatestSnapshot",
    ()=>readLatestSnapshot,
    "readRiskTruthPanel",
    ()=>readRiskTruthPanel
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$validated$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/server/validated.ts [app-route] (ecmascript)");
;
;
;
function repoRoot() {
    return __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].resolve(process.cwd(), "..");
}
function dataDirs() {
    const root = repoRoot();
    return {
        latest: process.env.DATA_DIR || __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(root, "results", "latest"),
        publicLatest: __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(process.cwd(), "public", "data", "latest"),
        results: __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(root, "results")
    };
}
async function listLatestFiles() {
    const { latest, publicLatest } = dataDirs();
    let dir = latest;
    try {
        await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].access(dir);
    } catch  {
        dir = publicLatest;
    }
    const files = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readdir(dir);
    return files.filter((f)=>f.endsWith(".json"));
}
async function readLatestFile(file) {
    const { latest, publicLatest } = dataDirs();
    let dir = latest;
    try {
        await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].access(dir);
    } catch  {
        dir = publicLatest;
    }
    const target = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(dir, file);
    try {
        const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(target, "utf-8");
        return JSON.parse(text);
    } catch  {
        // fallback: try other dir
        const fallback = dir === latest ? __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(publicLatest, file) : __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(latest, file);
        const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(fallback, "utf-8");
        return JSON.parse(text);
    }
}
async function findLatestApiRecords() {
    const { results } = dataDirs();
    // Preferred source: ops snapshots (production-gated payload).
    const snapshotsRoot = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(results, "ops", "snapshots");
    try {
        const runDirs = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readdir(snapshotsRoot, {
            withFileTypes: true
        });
        const snapCandidates = [];
        for (const ent of runDirs){
            if (!ent.isDirectory()) continue;
            const p = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(snapshotsRoot, ent.name, "api_snapshot.jsonl");
            try {
                const stat = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].stat(p);
                snapCandidates.push({
                    path: p,
                    mtime: stat.mtimeMs
                });
            } catch  {
            // ignore
            }
        }
        snapCandidates.sort((a, b)=>b.mtime - a.mtime);
        if (snapCandidates.length) return snapCandidates[0].path;
    } catch  {
    // ignore and fallback to legacy search
    }
    // Legacy fallback: results/*/api_records.jsonl
    const entries = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readdir(results, {
        withFileTypes: true
    });
    const candidates = [];
    for (const ent of entries){
        if (!ent.isDirectory()) continue;
        const p = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(results, ent.name, "api_records.jsonl");
        try {
            const stat = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].stat(p);
            candidates.push({
                path: p,
                mtime: stat.mtimeMs
            });
        } catch  {
        // ignore
        }
    }
    candidates.sort((a, b)=>b.mtime - a.mtime);
    return candidates.length ? candidates[0].path : null;
}
async function readJsonl(pathFile) {
    const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(pathFile, "utf-8");
    return text.split("\n").map((line)=>line.trim()).filter(Boolean).map((line)=>JSON.parse(line));
}
function isRunValid(summary) {
    const status = String(summary?.status || "").toLowerCase();
    const gate = summary?.deployment_gate || {};
    const blocked = gate?.blocked === true;
    return status === "ok" && !blocked;
}
async function findLatestValidRun() {
    const { results } = dataDirs();
    const snapshotsRoot = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(results, "ops", "snapshots");
    let runDirs = [];
    try {
        runDirs = (await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readdir(snapshotsRoot, {
            withFileTypes: true
        })).filter((ent)=>ent.isDirectory()).map((ent)=>ent.name).sort().reverse();
    } catch  {
        return null;
    }
    for (const runId of runDirs){
        const summaryPath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(snapshotsRoot, runId, "summary.json");
        const snapshotPath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(snapshotsRoot, runId, "api_snapshot.jsonl");
        try {
            const [summaryText, snapshotStat] = await Promise.all([
                __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(summaryPath, "utf-8"),
                __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].stat(snapshotPath)
            ]);
            if (!snapshotStat.size) continue;
            const summary = JSON.parse(summaryText);
            if (!isRunValid(summary)) continue;
            return {
                runId,
                summaryPath,
                snapshotPath,
                summary
            };
        } catch  {
        // ignore invalid run and keep scanning older runs
        }
    }
    return null;
}
async function readLatestSnapshot() {
    const run = await findLatestValidRun();
    if (!run) return null;
    const records = await readJsonl(run.snapshotPath);
    return {
        runId: run.runId,
        summary: run.summary,
        records
    };
}
async function readRiskTruthPanel() {
    const { results } = dataDirs();
    const target = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(results, "validation", "risk_truth_panel.json");
    try {
        const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(target, "utf-8");
        return JSON.parse(text);
    } catch  {
        return {
            status: "empty",
            counts: {
                assets: 0,
                validated: 0,
                watch: 0,
                inconclusive: 0
            },
            entries: []
        };
    }
}
async function readGlobalVerdict() {
    const { results } = dataDirs();
    const target = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(results, "validation", "VERDICT.json");
    try {
        const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(target, "utf-8");
        return JSON.parse(text);
    } catch  {
        return {
            status: "unknown",
            gate_checks: {}
        };
    }
}
async function readJsonlWithValidationGate(pathFile) {
    const records = await readJsonl(pathFile);
    let statusMap = {};
    try {
        statusMap = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$validated$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["readAssetStatusMap"])();
    } catch  {
        return records;
    }
    return records.map((record)=>{
        const key = `${record.asset || ""}__${record.timeframe || ""}`;
        const gate = statusMap[key];
        if (!gate || (gate.status || "").toLowerCase() === "validated") {
            return record;
        }
        const reason = gate.reason || "gate_not_validated";
        const warnings = Array.isArray(record.warnings) ? [
            ...record.warnings
        ] : [];
        if (!warnings.includes("INCONCLUSIVE_SIGNAL")) {
            warnings.push("INCONCLUSIVE_SIGNAL");
        }
        return {
            ...record,
            signal_status: "inconclusive",
            use_forecast_bool: false,
            action: "DIAGNOSTICO_INCONCLUSIVO",
            regime_label: "INCONCLUSIVE",
            confidence_level: "LOW",
            warnings,
            gate_reason: reason
        };
    });
}
async function readDashboardOverview() {
    const { results } = dataDirs();
    const overviewPath = __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(results, "dashboard", "overview.json");
    const text = await __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["promises"].readFile(overviewPath, "utf-8");
    return JSON.parse(text);
}
}),
"[project]/app/api/run/latest/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/server/data.ts [app-route] (ecmascript)");
;
;
async function GET() {
    const [run, verdict] = await Promise.all([
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["findLatestValidRun"])(),
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["readGlobalVerdict"])()
    ]);
    if (!run) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: "no_valid_run",
            message: "Nenhum run valido encontrado (status ok + deployment gate liberado)."
        }, {
            status: 503
        });
    }
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
        run_id: run.runId,
        summary: run.summary,
        global_verdict_status: verdict?.status || "unknown"
    });
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__7b61a65a._.js.map