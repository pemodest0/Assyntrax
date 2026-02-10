module.exports = [
"[project]/app/favicon.ico.mjs { IMAGE => \"[project]/app/favicon.ico (static in ecmascript, tag client)\" } [app-rsc] (structured image object, ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/app/favicon.ico.mjs { IMAGE => \"[project]/app/favicon.ico (static in ecmascript, tag client)\" } [app-rsc] (structured image object, ecmascript)"));
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[project]/app/layout.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/app/layout.tsx [app-rsc] (ecmascript)"));
}),
"[project]/app/app/layout.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/app/app/layout.tsx [app-rsc] (ecmascript)"));
}),
"[externals]/fs [external] (fs, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("fs", () => require("fs"));

module.exports = mod;
}),
"[project]/lib/server/validated.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
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
"[project]/lib/server/data.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
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
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$validated$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/server/validated.ts [app-rsc] (ecmascript)");
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
        statusMap = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$validated$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["readAssetStatusMap"])();
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
"[project]/app/app/metodologia/page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>MetodologiaPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/server/data.ts [app-rsc] (ecmascript)");
;
;
function toNum(v, fallback = 0) {
    const n = Number(v);
    return Number.isFinite(n) ? n : fallback;
}
async function MetodologiaPage() {
    const [snap, verdict, panel] = await Promise.all([
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["readLatestSnapshot"])(),
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["readGlobalVerdict"])(),
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["readRiskTruthPanel"])()
    ]);
    const summary = snap?.summary || {};
    const checks = verdict?.gate_checks || {};
    const scores = verdict?.scores || {};
    const counts = panel?.counts || {};
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "p-5 md:p-6 lg:p-8 space-y-6",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-xs tracking-[0.14em] uppercase text-zinc-500",
                        children: "Nivel 2 - Metodo e auditoria"
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 23,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                        className: "mt-2 text-2xl md:text-3xl font-semibold text-zinc-100",
                        children: "Metodologia e evidencias do run atual"
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 24,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "mt-3 text-sm text-zinc-300",
                        children: "Todos os numeros abaixo sao carregados de artefatos reais do repositorio: snapshot validado, painel de verdade de risco e gate global."
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 25,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/app/metodologia/page.tsx",
                lineNumber: 22,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(Metric, {
                        title: "Global verdict",
                        value: String(verdict?.status || "unknown").toUpperCase()
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 31,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(Metric, {
                        title: "Run id",
                        value: String(snap?.runId || "n/a")
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 32,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(Metric, {
                        title: "Ativos no painel",
                        value: String(toNum(counts.assets, 0))
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 33,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(Metric, {
                        title: "Validated",
                        value: String(toNum(counts.validated, 0))
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 34,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/app/metodologia/page.tsx",
                lineNumber: 30,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                        className: "text-lg font-semibold text-zinc-100",
                        children: "Gate checks"
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 38,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm",
                        children: Object.keys(checks).length ? Object.entries(checks).map(([k, v])=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-zinc-400",
                                        children: [
                                            k,
                                            ":"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/app/metodologia/page.tsx",
                                        lineNumber: 43,
                                        columnNumber: 17
                                    }, this),
                                    " ",
                                    String(v)
                                ]
                            }, k, true, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 42,
                                columnNumber: 15
                            }, this)) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "text-zinc-400",
                            children: "Sem gate_checks no arquivo de veredito."
                        }, void 0, false, {
                            fileName: "[project]/app/app/metodologia/page.tsx",
                            lineNumber: 47,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 39,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/app/metodologia/page.tsx",
                lineNumber: 37,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                        className: "text-lg font-semibold text-zinc-100",
                        children: "Scores e contorno"
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 53,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-3 grid grid-cols-1 md:grid-cols-3 gap-2 text-sm",
                        children: [
                            Object.keys(scores).length ? Object.entries(scores).map(([k, v])=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "text-zinc-400",
                                            children: [
                                                k,
                                                ":"
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/app/app/metodologia/page.tsx",
                                            lineNumber: 58,
                                            columnNumber: 17
                                        }, this),
                                        " ",
                                        String(v)
                                    ]
                                }, k, true, {
                                    fileName: "[project]/app/app/metodologia/page.tsx",
                                    lineNumber: 57,
                                    columnNumber: 15
                                }, this)) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-zinc-400",
                                children: "Sem scores no arquivo de veredito."
                            }, void 0, false, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 62,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-zinc-400",
                                        children: "deployment_gate.blocked:"
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/metodologia/page.tsx",
                                        lineNumber: 65,
                                        columnNumber: 13
                                    }, this),
                                    " ",
                                    String(summary.deployment_gate?.blocked ?? "n/a")
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 64,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-lg border border-zinc-800 bg-black/25 p-2 text-zinc-300",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-zinc-400",
                                        children: "status:"
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/metodologia/page.tsx",
                                        lineNumber: 69,
                                        columnNumber: 13
                                    }, this),
                                    " ",
                                    String(summary.status || "n/a")
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 68,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 54,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/app/metodologia/page.tsx",
                lineNumber: 52,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                        className: "text-lg font-semibold text-zinc-100",
                        children: "Caveats de uso"
                    }, void 0, false, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 75,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("ul", {
                        className: "mt-3 space-y-2 text-sm text-zinc-300",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                children: "1. O motor e radar de regime e risco, nao previsao garantida de preco."
                            }, void 0, false, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 77,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                children: "2. Sinal inconclusivo deve ficar em modo diagnostico, sem acao automatica."
                            }, void 0, false, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 78,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                children: "3. Backtest e replay nao garantem resultado futuro."
                            }, void 0, false, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 79,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                children: "4. Custos de transacao e latencia podem degradar desempenho operacional."
                            }, void 0, false, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 80,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                children: "5. Decisao final exige contexto de dominio e governanca de risco."
                            }, void 0, false, {
                                fileName: "[project]/app/app/metodologia/page.tsx",
                                lineNumber: 81,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/app/metodologia/page.tsx",
                        lineNumber: 76,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/app/metodologia/page.tsx",
                lineNumber: 74,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/app/app/metodologia/page.tsx",
        lineNumber: 21,
        columnNumber: 5
    }, this);
}
function Metric({ title, value }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "rounded-xl border border-zinc-800 bg-zinc-950/55 p-3",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "text-xs uppercase tracking-[0.12em] text-zinc-500",
                children: title
            }, void 0, false, {
                fileName: "[project]/app/app/metodologia/page.tsx",
                lineNumber: 91,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-2 text-lg font-semibold text-zinc-100",
                children: value
            }, void 0, false, {
                fileName: "[project]/app/app/metodologia/page.tsx",
                lineNumber: 92,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/app/app/metodologia/page.tsx",
        lineNumber: 90,
        columnNumber: 5
    }, this);
}
}),
"[project]/app/app/metodologia/page.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/app/app/metodologia/page.tsx [app-rsc] (ecmascript)"));
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__7456d902._.js.map