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
"[project]/lib/story/cases.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "DOMAIN_LABELS",
    ()=>DOMAIN_LABELS,
    "STORY_CASES",
    ()=>STORY_CASES
]);
const STORY_CASES = [
    {
        id: "yen-carry-2024",
        domain: "finance",
        title: "Yen carry unwind e explosao de volatilidade",
        period: "2024-08",
        why_matters: "Liquidez some rapido em estruturas alavancadas. O risco principal nao e direcao de preco, e regime de fragilidade.",
        what_happened: "A compressao de diferencial de juros entre EUA e Japao forca desalavancagem. O VIX salta e a estrutura de opcao perde estabilidade.",
        motor_reading: "O motor trata como transicao de regime com queda de confianca local, aumento de instabilidade e elevacao de alertas.",
        operational_use: "Uso pratico: reduzir exposicao bruta, bloquear novos riscos e acionar hedge condicional por regime.",
        risk_limit: "Nao e previsao de candle. E radar de contexto para controle de risco e de alavancagem.",
        image_hint: "Mesa de risco, tela de volatilidade e fluxo de opcao em stress.",
        sources: [
            {
                title: "BIS - Anatomy of the VIX spike in August 2024",
                url: "https://www.bis.org/",
                level: "A",
                type: "primary"
            },
            {
                title: "Euronext - Market quality and volatility shock",
                url: "https://www.euronext.com/",
                level: "A",
                type: "primary"
            },
            {
                title: "Wellington - Yen carry unwind",
                url: "https://www.wellington.com/",
                level: "B",
                type: "secondary"
            }
        ]
    },
    {
        id: "tariff-shock-2025",
        domain: "macro",
        title: "Choque tarifario e quebra de regime de comercio",
        period: "2025-04",
        why_matters: "Mudanca regulatoria abrupta desloca o equilibrio macro e contamina equities, FX e cadeia global.",
        what_happened: "Tarifas amplas elevam incerteza de custo, comprimem margem e aumentam dispersao setorial em poucos dias.",
        motor_reading: "Regime sai de estabilidade para transicao/instavel com persistencia maior de alertas e menor qualidade de sinal.",
        operational_use: "Uso pratico: mover para postura defensiva por dominio, limitar risco direcional e priorizar setores resilientes.",
        risk_limit: "Motor nao explica geopolitica; ele mede efeito no estado do sistema.",
        image_hint: "Portos, containers e curva de volatilidade em tela unica.",
        sources: [
            {
                title: "IMF - Red Sea attacks and global trade disruption",
                url: "https://www.imf.org/",
                level: "A",
                type: "primary"
            },
            {
                title: "Congress - Economic effects and fiscal stress",
                url: "https://www.congress.gov/",
                level: "A",
                type: "primary"
            },
            {
                title: "McKinsey - Supply chain risk pulse 2025",
                url: "https://www.mckinsey.com/",
                level: "B",
                type: "secondary"
            }
        ]
    },
    {
        id: "cre-maturity-wall",
        domain: "realestate",
        title: "Maturity wall no real estate comercial",
        period: "2025-2026",
        why_matters: "Crise lenta de refinanciamento causa erosao de capital sem crash unico visivel.",
        what_happened: "Vencimento de divida em ambiente de juros altos gera bifurcacao de credito e queda de liquidez de ativos.",
        motor_reading: "Sinais de transicao longa com qualidade heterogenea entre regioes e maior tempo em estado de cautela.",
        operational_use: "Uso pratico: congelar alocacao agressiva, revisar duration e exigir evidencia adicional antes de expandir risco.",
        risk_limit: "Motor identifica fragilidade de regime; nao substitui due diligence de ativo individual.",
        image_hint: "Skyline corporativo com vacancia e curva de credito em stress.",
        sources: [
            {
                title: "Congress - Commercial Real Estate and the Banking Sector",
                url: "https://www.congress.gov/",
                level: "A",
                type: "primary"
            },
            {
                title: "MBA - Commercial/Multifamily Research",
                url: "https://www.mba.org/",
                level: "A",
                type: "primary"
            },
            {
                title: "NAIOP - Challenges facing CRE in 2025",
                url: "https://www.naiop.org/",
                level: "B",
                type: "secondary"
            }
        ]
    }
];
const DOMAIN_LABELS = {
    finance: "Finance / Trading",
    macro: "Macro / Operacoes",
    realestate: "Imobiliario"
};
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
"[project]/app/app/casos/page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>CasosPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$story$2f$cases$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/story/cases.ts [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/server/data.ts [app-rsc] (ecmascript)");
;
;
;
function domainCount(entries, domain) {
    return entries.filter((entry)=>{
        const asset = String(entry.asset_id || "");
        const row = String(entry.domain || "");
        if (row) return row === domain;
        if (domain === "finance") return asset.includes("USD") || asset.includes("SPY") || asset.includes("QQQ");
        if (domain === "realestate") return asset.includes("FIPEZAP") || asset.includes("IMOB");
        if (domain === "macro") return asset.includes("DGS") || asset.includes("DX");
        return false;
    }).length;
}
async function CasosPage() {
    const [snap, panel] = await Promise.all([
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["readLatestSnapshot"])(),
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$server$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["readRiskTruthPanel"])()
    ]);
    const entries = Array.isArray(panel?.entries) ? panel.entries : [];
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "p-5 md:p-6 lg:p-8 space-y-6",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "rounded-2xl border border-zinc-800 bg-zinc-950/50 p-5",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-xs tracking-[0.14em] uppercase text-zinc-500",
                        children: "Nivel 1 - Storyline"
                    }, void 0, false, {
                        fileName: "[project]/app/app/casos/page.tsx",
                        lineNumber: 25,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                        className: "mt-2 text-2xl md:text-3xl font-semibold text-zinc-100",
                        children: "Casos reais de transicao de regime"
                    }, void 0, false, {
                        fileName: "[project]/app/app/casos/page.tsx",
                        lineNumber: 26,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "mt-3 text-sm text-zinc-300",
                        children: "Esta pagina mostra uso operacional do motor como radar de risco. Os textos sao narrativos, mas o status exibido vem do run valido mais recente e do painel de verdade de risco."
                    }, void 0, false, {
                        fileName: "[project]/app/app/casos/page.tsx",
                        lineNumber: 27,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm",
                        children: [
                            "finance",
                            "macro",
                            "realestate"
                        ].map((domain)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-xl border border-zinc-800 bg-black/30 p-3",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-zinc-400",
                                        children: __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$story$2f$cases$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["DOMAIN_LABELS"][domain]
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 34,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xl font-semibold mt-1",
                                        children: domainCount(entries, domain)
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 35,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-zinc-500 mt-1",
                                        children: "ativos com classificacao no painel"
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 36,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, domain, true, {
                                fileName: "[project]/app/app/casos/page.tsx",
                                lineNumber: 33,
                                columnNumber: 13
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/app/app/casos/page.tsx",
                        lineNumber: 31,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-4 text-xs text-zinc-500",
                        children: [
                            "run_id: ",
                            snap?.runId || "indisponivel"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/app/casos/page.tsx",
                        lineNumber: 40,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/app/casos/page.tsx",
                lineNumber: 24,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "space-y-4",
                children: __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$story$2f$cases$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["STORY_CASES"].map((item)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                        className: "rounded-2xl border border-zinc-800 bg-zinc-950/45 p-5",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex flex-wrap items-center gap-2 text-xs",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "rounded-full border border-zinc-700 px-2 py-1 text-zinc-300",
                                        children: __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$story$2f$cases$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["DOMAIN_LABELS"][item.domain]
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 47,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "rounded-full border border-zinc-700 px-2 py-1 text-zinc-400",
                                        children: item.period
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 48,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/app/casos/page.tsx",
                                lineNumber: 46,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                className: "mt-3 text-lg md:text-xl font-semibold text-zinc-100",
                                children: item.title
                            }, void 0, false, {
                                fileName: "[project]/app/app/casos/page.tsx",
                                lineNumber: 50,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-3 space-y-2 text-sm text-zinc-300",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-zinc-400",
                                                children: "Contexto:"
                                            }, void 0, false, {
                                                fileName: "[project]/app/app/casos/page.tsx",
                                                lineNumber: 52,
                                                columnNumber: 18
                                            }, this),
                                            " ",
                                            item.why_matters
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 52,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-zinc-400",
                                                children: "Evento:"
                                            }, void 0, false, {
                                                fileName: "[project]/app/app/casos/page.tsx",
                                                lineNumber: 53,
                                                columnNumber: 18
                                            }, this),
                                            " ",
                                            item.what_happened
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 53,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-zinc-400",
                                                children: "Leitura do motor:"
                                            }, void 0, false, {
                                                fileName: "[project]/app/app/casos/page.tsx",
                                                lineNumber: 54,
                                                columnNumber: 18
                                            }, this),
                                            " ",
                                            item.motor_reading
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 54,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-zinc-400",
                                                children: "Uso pratico:"
                                            }, void 0, false, {
                                                fileName: "[project]/app/app/casos/page.tsx",
                                                lineNumber: 55,
                                                columnNumber: 18
                                            }, this),
                                            " ",
                                            item.operational_use
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 55,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-zinc-400",
                                                children: "Limite:"
                                            }, void 0, false, {
                                                fileName: "[project]/app/app/casos/page.tsx",
                                                lineNumber: 56,
                                                columnNumber: 18
                                            }, this),
                                            " ",
                                            item.risk_limit
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 56,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/app/casos/page.tsx",
                                lineNumber: 51,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-4",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                        className: "text-xs tracking-[0.12em] uppercase text-zinc-500",
                                        children: "Fontes"
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 59,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("ul", {
                                        className: "mt-2 space-y-1 text-sm",
                                        children: item.sources.map((src)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                                className: "text-zinc-300",
                                                children: [
                                                    "[",
                                                    src.level,
                                                    "] ",
                                                    src.title,
                                                    " -",
                                                    " ",
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("a", {
                                                        className: "text-emerald-300 hover:text-emerald-200 underline underline-offset-2",
                                                        href: src.url,
                                                        target: "_blank",
                                                        rel: "noreferrer",
                                                        children: "link"
                                                    }, void 0, false, {
                                                        fileName: "[project]/app/app/casos/page.tsx",
                                                        lineNumber: 64,
                                                        columnNumber: 21
                                                    }, this)
                                                ]
                                            }, `${item.id}-${src.url}`, true, {
                                                fileName: "[project]/app/app/casos/page.tsx",
                                                lineNumber: 62,
                                                columnNumber: 19
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/app/app/casos/page.tsx",
                                        lineNumber: 60,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/app/casos/page.tsx",
                                lineNumber: 58,
                                columnNumber: 13
                            }, this)
                        ]
                    }, item.id, true, {
                        fileName: "[project]/app/app/casos/page.tsx",
                        lineNumber: 45,
                        columnNumber: 11
                    }, this))
            }, void 0, false, {
                fileName: "[project]/app/app/casos/page.tsx",
                lineNumber: 43,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/app/app/casos/page.tsx",
        lineNumber: 23,
        columnNumber: 5
    }, this);
}
}),
"[project]/app/app/casos/page.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/app/app/casos/page.tsx [app-rsc] (ecmascript)"));
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__39debf3c._.js.map