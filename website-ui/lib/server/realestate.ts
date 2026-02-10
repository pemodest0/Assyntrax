import { promises as fs } from "fs";
import path from "path";

type Point = { date: string; value: number };

export type RealEstateAssetMeta = {
  asset: string;
  city: string;
  state: string;
  region: string;
  source_type: string;
  source_name: string;
};

type DataLayer = {
  asset: string;
  profile: {
    n_points: number;
    coverage_years: number;
    gap_ratio: number;
    start_date: string;
    end_date: string;
    required_fields: {
      P: boolean;
      L: boolean;
      J: boolean;
      D: boolean;
    };
    notes: string[];
  };
  series: {
    P: Point[];
    L: Point[];
    J: Point[];
    D: Point[];
  };
};

type DynamicRow = {
  date: string;
  regime: string;
  microstate: "M1" | "M2" | "M3" | "UNK";
  transition: boolean;
  confidence: number;
  quality: number;
  entropy: number;
  persistence: number;
  instability_score: number;
};

type DynamicLayer = {
  m: number;
  tau: number;
  rows: DynamicRow[];
};

type OperationalLayer = {
  status: "validated" | "watch" | "inconclusive";
  explanation: string;
  adequacy_ok: boolean;
  thresholds: {
    min_points: number;
    min_coverage_years: number;
    max_gap_ratio: number;
    validated_confidence: number;
    validated_quality: number;
    watch_confidence: number;
    watch_quality: number;
    hysteresis_days: number;
  };
  latest: {
    date: string;
    regime: string;
    confidence: number;
    quality: number;
    entropy: number;
    persistence: number;
    instability_score: number;
  } | null;
};

export type RealEstateAssetPayload = {
  data: DataLayer;
  dynamic: DynamicLayer;
  operational: OperationalLayer;
};

const MIN_POINTS = 200;
const MIN_COVERAGE_YEARS = 3;
const MAX_GAP_RATIO = 0.12;
const HYSTERESIS_DAYS = 3;
const CITY_DICT_PATH = path.join(repoRoot(), "config", "realestate_city_uf_region.v1.json");

const REGION_BY_STATE: Record<string, string> = {
  BR: "Brasil",
  AC: "Norte",
  AP: "Norte",
  AM: "Norte",
  PA: "Norte",
  RO: "Norte",
  RR: "Norte",
  TO: "Norte",
  AL: "Nordeste",
  BA: "Nordeste",
  CE: "Nordeste",
  MA: "Nordeste",
  PB: "Nordeste",
  PE: "Nordeste",
  PI: "Nordeste",
  RN: "Nordeste",
  SE: "Nordeste",
  DF: "Centro-Oeste",
  GO: "Centro-Oeste",
  MS: "Centro-Oeste",
  MT: "Centro-Oeste",
  ES: "Sudeste",
  MG: "Sudeste",
  RJ: "Sudeste",
  SP: "Sudeste",
  PR: "Sul",
  RS: "Sul",
  SC: "Sul",
};

const CITY_TO_STATE: Record<string, string> = {
  "indice fipezap": "BR",
  aracaju: "SE",
  "balneario camboriu": "SC",
  barueri: "SP",
  "sao paulo": "SP",
  "rio de janeiro": "RJ",
  "belo horizonte": "MG",
  brasilia: "DF",
  "porto alegre": "RS",
  curitiba: "PR",
  florianopolis: "SC",
  salvador: "BA",
  recife: "PE",
  fortaleza: "CE",
  "goiania": "GO",
  "campo grande": "MS",
  cuiaba: "MT",
  manaus: "AM",
  belem: "PA",
  vitoria: "ES",
  betim: "MG",
  blumenau: "SC",
  campinas: "SP",
  canoas: "RS",
  "caxias do sul": "RS",
  contagem: "MG",
  diadema: "SP",
  guaruja: "SP",
  guarulhos: "SP",
  itajai: "SC",
  itapema: "SC",
  "jaboatao dos guararapes": "PE",
  joinville: "SC",
  "joao pessoa": "PB",
  londrina: "PR",
  maceio: "AL",
  natal: "RN",
  niteroi: "RJ",
  "novo hamburgo": "RS",
  osasco: "SP",
  pelotas: "RS",
  "praia grande": "SP",
  "ribeirao preto": "SP",
  "santa maria": "RS",
  santos: "SP",
  "santo andre": "SP",
  "sao bernardo do campo": "SP",
  "sao caetano do sul": "SP",
  "sao jose dos campos": "SP",
  "sao jose dos pinhais": "PR",
  "sao jose do rio preto": "SP",
  "sao jose": "SC",
  "sao leopoldo": "RS",
  "sao luis": "MA",
  "sao vicente": "SP",
  teresina: "PI",
  "vila velha": "ES",
};

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

function clamp01(v: number) {
  return Math.max(0, Math.min(1, v));
}

function normalizeText(input: string) {
  return input
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function normalizeKey(input: string) {
  return normalizeText(input).replace(/[^a-z0-9_]/g, "_");
}

function normalizeDate(input: string) {
  if (!input) return "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(input)) return input;
  if (/^\d{4}-\d{2}$/.test(input)) return `${input}-01`;
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString().slice(0, 10);
}

async function readCsvSeries(filePath: string) {
  const text = await fs.readFile(filePath, "utf-8");
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  return lines
    .slice(1)
    .map((line) => line.split(","))
    .map((parts) => {
      const date = normalizeDate((parts[0] || "").trim());
      const value = Number((parts[1] || "").trim());
      return { date, value };
    })
    .filter((p) => p.date && Number.isFinite(p.value))
    .sort((a, b) => a.date.localeCompare(b.date));
}

function rollingMean(values: number[], window: number) {
  const out: number[] = [];
  let acc = 0;
  for (let i = 0; i < values.length; i++) {
    acc += values[i];
    if (i >= window) acc -= values[i - window];
    out.push(acc / Math.min(window, i + 1));
  }
  return out;
}

function inferMeta(asset: string): RealEstateAssetMeta {
  const clean = asset.replace(/^FipeZap_/i, "").replace(/_Total$/i, "").replace(/_core$/i, "");
  const city = clean.replace(/_/g, " ");
  const state = CITY_TO_STATE[normalizeText(city)] || "NA";
  const region = REGION_BY_STATE[state] || "Desconhecida";
  return {
    asset,
    city,
    state,
    region,
    source_type: "proxy",
    source_name: "fallback_mapping",
  };
}

type CityDictEntry = {
  asset?: string;
  city?: string;
  city_key?: string;
  uf?: string;
  region?: string;
  source_type?: string;
  source_name?: string;
};

let cityDictCache: CityDictEntry[] | null = null;

async function loadCityDictionary(): Promise<CityDictEntry[]> {
  if (cityDictCache) return cityDictCache;
  try {
    const raw = await fs.readFile(CITY_DICT_PATH, "utf-8");
    const parsed = JSON.parse(raw) as { entries?: CityDictEntry[] };
    cityDictCache = Array.isArray(parsed.entries) ? parsed.entries : [];
  } catch {
    cityDictCache = [];
  }
  return cityDictCache;
}

async function inferMetaFromDictionary(asset: string): Promise<RealEstateAssetMeta> {
  const fallback = inferMeta(asset);
  const dict = await loadCityDictionary();
  if (!dict.length) return fallback;

  const cityKey = normalizeText(fallback.city);
  const byAsset = dict.find((e) => String(e.asset || "").toLowerCase() === asset.toLowerCase());
  const byCity = dict.find((e) => String(e.city_key || "").toLowerCase() === cityKey);
  const hit = byAsset || byCity;
  if (!hit) return fallback;

  const state = String(hit.uf || fallback.state || "NA");
  const region = String(hit.region || REGION_BY_STATE[state] || fallback.region || "Desconhecida");
  return {
    asset,
    city: String(hit.city || fallback.city),
    state,
    region,
    source_type: String(hit.source_type || "proxy"),
    source_name: String(hit.source_name || "dictionary"),
  };
}

function getNormalizedBaseDir() {
  return path.join(repoRoot(), "data", "realestate", "normalized");
}

function getCoreBaseDir() {
  return path.join(repoRoot(), "data", "realestate", "core");
}

function getCoreFilePath(asset: string) {
  return path.join(getCoreBaseDir(), `${asset}_core.csv`);
}

function getNormalizedFilePath(asset: string) {
  return path.join(getNormalizedBaseDir(), `${asset}.csv`);
}

function buildDataLayerFromCore(asset: string, rows: Array<{ date: string; P: number; L: number; J: number; D: number | null }>): DataLayer {
  const valid = rows
    .map((r) => ({
      date: normalizeDate(r.date),
      P: Number(r.P),
      L: Number(r.L),
      J: Number(r.J),
      D: r.D == null ? Number.NaN : Number(r.D),
    }))
    .filter((r) => r.date && Number.isFinite(r.P))
    .sort((a, b) => a.date.localeCompare(b.date));

  const dates = valid.map((r) => r.date);
  const start = dates[0] || "";
  const end = dates[dates.length - 1] || "";
  const coverageYears = start && end ? (new Date(end).getTime() - new Date(start).getTime()) / (365.25 * 86400000) : 0;

  let missingGap = 0;
  for (let i = 1; i < valid.length; i++) {
    const prev = new Date(valid[i - 1].date).getTime();
    const cur = new Date(valid[i].date).getTime();
    const dayGap = Math.round((cur - prev) / 86400000);
    if (dayGap > 35) missingGap += 1;
  }
  const gapRatio = valid.length > 1 ? missingGap / (valid.length - 1) : 1;

  return {
    asset,
    profile: {
      n_points: valid.length,
      coverage_years: Number(coverageYears.toFixed(2)),
      gap_ratio: Number(gapRatio.toFixed(4)),
      start_date: start,
      end_date: end,
      required_fields: {
        P: valid.length > 0,
        L: valid.some((r) => Number.isFinite(r.L)),
        J: valid.some((r) => Number.isFinite(r.J)),
        D: valid.some((r) => Number.isFinite(r.D)),
      },
      notes: [
        "P(t): preco medio do m2",
        "L(t): proxy de liquidez",
        "J(t): juros (Selic/financiamento)",
        "D(t): desconto medio (quando disponivel)",
      ],
    },
    series: {
      P: valid.map((r) => ({ date: r.date, value: r.P })),
      L: valid.filter((r) => Number.isFinite(r.L)).map((r) => ({ date: r.date, value: r.L })),
      J: valid.filter((r) => Number.isFinite(r.J)).map((r) => ({ date: r.date, value: r.J })),
      D: valid.filter((r) => Number.isFinite(r.D)).map((r) => ({ date: r.date, value: Number(r.D) })),
    },
  };
}

function buildDataLayerFromNormalized(asset: string, price: Point[], rate: Point[]): DataLayer {
  const byDateRate = new Map(rate.map((p) => [p.date, p.value]));
  const priceAligned = price.filter((p) => Number.isFinite(p.value));
  const dates = priceAligned.map((p) => p.date);
  const start = dates[0] || "";
  const end = dates[dates.length - 1] || "";
  const coverageYears = start && end ? (new Date(end).getTime() - new Date(start).getTime()) / (365.25 * 86400000) : 0;

  const priceVals = priceAligned.map((p) => p.value);
  const rets = priceVals.map((v, i) => (i === 0 ? 0 : Math.log(Math.max(v, 1e-9) / Math.max(priceVals[i - 1], 1e-9))));
  const absRet = rets.map((v) => Math.abs(v));
  const absRetRoll = rollingMean(absRet, 3);
  const maxRoll = Math.max(...absRetRoll, 1e-9);

  const L = priceAligned.map((p, i) => ({
    date: p.date,
    value: clamp01(1 - absRetRoll[i] / maxRoll),
  }));

  let lastRate = rate.length ? rate[0].value : 0;
  const sortedRate = [...rate].sort((a, b) => a.date.localeCompare(b.date));
  let rIdx = 0;
  const J = priceAligned.map((p) => {
    while (rIdx < sortedRate.length && sortedRate[rIdx].date <= p.date) {
      lastRate = sortedRate[rIdx].value;
      rIdx += 1;
    }
    const exact = byDateRate.get(p.date);
    return { date: p.date, value: Number.isFinite(exact as number) ? (exact as number) : lastRate };
  });

  const D: Point[] = [];

  let missingGap = 0;
  for (let i = 1; i < priceAligned.length; i++) {
    const prev = new Date(priceAligned[i - 1].date).getTime();
    const cur = new Date(priceAligned[i].date).getTime();
    const dayGap = Math.round((cur - prev) / 86400000);
    if (dayGap > 35) missingGap += 1;
  }
  const gapRatio = priceAligned.length > 1 ? missingGap / (priceAligned.length - 1) : 1;

  return {
    asset,
    profile: {
      n_points: priceAligned.length,
      coverage_years: Number(coverageYears.toFixed(2)),
      gap_ratio: Number(gapRatio.toFixed(4)),
      start_date: start,
      end_date: end,
      required_fields: {
        P: priceAligned.length > 0,
        L: L.length > 0,
        J: J.length > 0,
        D: false,
      },
      notes: [
        "L(t) usa proxy de liquidez via estabilidade local de retornos.",
        "D(t) ainda nao existe no repositorio; TODO: integrar desconto pedido x fechamento.",
      ],
    },
    series: {
      P: priceAligned,
      L,
      J,
      D,
    },
  };
}

async function inferEmbeddingParams(asset: string) {
  const candidates = [
    path.join(repoRoot(), "results", "validation", "universe_mini", `RE_${normalizeKey(asset)}`, "summary.json"),
    path.join(repoRoot(), "results", "validation", "universe_mini_full", `RE_${normalizeKey(asset)}`, "summary.json"),
  ];
  for (const c of candidates) {
    try {
      const raw = await fs.readFile(c, "utf-8");
      const obj = JSON.parse(raw) as Record<string, unknown>;
      const m = Number(obj.m);
      const tau = Number(obj.tau);
      if (Number.isFinite(m) && Number.isFinite(tau)) {
        return { m, tau };
      }
    } catch {
      // no-op
    }
  }
  return { m: 4, tau: 2 };
}

function parseCsvRows(text: string) {
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());
  const idxDate = headers.indexOf("date");
  const idxRegime = headers.indexOf("regime");
  const idxConfidence = headers.indexOf("confidence");
  if (idxDate < 0 || idxRegime < 0) return [];
  return lines.slice(1).map((line) => {
    const cols = line.split(",");
    return {
      date: normalizeDate((cols[idxDate] || "").trim()),
      regime: (cols[idxRegime] || "").trim(),
      confidence: idxConfidence >= 0 ? Number((cols[idxConfidence] || "").trim()) : Number.NaN,
    };
  });
}

async function loadPipelineRegimes(asset: string) {
  const root = path.join(repoRoot(), "results", "realestate", "assets");
  const candidates = [
    `${asset}_monthly_regimes.csv`,
    `${asset.toUpperCase()}_monthly_regimes.csv`,
    `${normalizeKey(asset)}_monthly_regimes.csv`,
    `${normalizeKey(asset).toUpperCase()}_monthly_regimes.csv`,
  ];
  for (const file of candidates) {
    const fp = path.join(root, file);
    try {
      const raw = await fs.readFile(fp, "utf-8");
      const parsed = parseCsvRows(raw).filter((r) => r.date && r.regime);
      if (parsed.length) return parsed;
    } catch {
      // try next
    }
  }
  return [];
}

type HMMPayload = {
  sequence?: number[];
  probabilities?: number[][];
  means?: number[][];
  states?: number;
};

async function loadHMMPayload(asset: string): Promise<HMMPayload | null> {
  const hmmDir = path.join(repoRoot(), "results", "realestate", "hmm");
  const candidates = [
    `${asset}_hmm.json`,
    `${asset.toUpperCase()}_hmm.json`,
    `${normalizeKey(asset)}_hmm.json`,
    `${normalizeKey(asset).toUpperCase()}_hmm.json`,
  ];
  for (const c of candidates) {
    try {
      const raw = await fs.readFile(path.join(hmmDir, c), "utf-8");
      const parsed = JSON.parse(raw) as HMMPayload;
      if (Array.isArray(parsed.sequence) && parsed.sequence.length > 0) {
        return parsed;
      }
    } catch {
      // try next
    }
  }
  return null;
}

function _hmmStateRankingByRisk(hmm: HMMPayload): number[] {
  const means = Array.isArray(hmm.means) ? hmm.means : [];
  const riskRows = means.map((row, idx) => {
    const ret = Number(Array.isArray(row) ? row[0] : 0);
    const vol = Math.abs(Number(Array.isArray(row) ? row[1] : 0));
    // higher risk score => more unstable regime
    const risk = vol - ret;
    return { idx, risk };
  });
  if (!riskRows.length) return [];
  riskRows.sort((a, b) => a.risk - b.risk);
  return riskRows.map((r) => r.idx);
}

function buildDynamicLayerFromHMM(hmm: HMMPayload, dates: string[], m: number, tau: number): DynamicLayer {
  const seq = (hmm.sequence || []).map((x) => Number(x));
  const probs = Array.isArray(hmm.probabilities) ? hmm.probabilities : [];
  const rank = _hmmStateRankingByRisk(hmm);
  const n = Math.min(seq.length, dates.length);
  if (n <= 0) return { m, tau, rows: [] };

  const stableState = rank[0];
  const unstableState = rank[rank.length - 1];
  const transitionState = rank.length > 2 ? rank[Math.floor(rank.length / 2)] : null;

  const mapLabel = (s: number) => {
    if (s === stableState) return "STABLE";
    if (s === unstableState) return "UNSTABLE";
    if (transitionState != null && s === transitionState) return "TRANSITION";
    return "TRANSITION";
  };

  const rows: DynamicRow[] = [];
  let prev: string | null = null;
  let persistence = 0;
  const dateSlice = dates.slice(dates.length - n);
  for (let i = 0; i < n; i++) {
    const state = seq[seq.length - n + i];
    const regime = mapLabel(state);
    if (regime === prev) persistence += 1;
    else persistence = 1;
    const confidence = Number.isFinite(probs[seq.length - n + i]?.[state])
      ? clamp01(Number(probs[seq.length - n + i]?.[state]))
      : regime === "STABLE"
      ? 0.68
      : regime === "TRANSITION"
      ? 0.56
      : 0.62;
    const quality = confidence;
    const entropy = 1 - confidence;
    const instability = clamp01((1 - confidence) + (1 - quality) + entropy);
    rows.push({
      date: dateSlice[i],
      regime,
      microstate: "UNK",
      transition: prev != null && regime !== prev,
      confidence: Number(confidence.toFixed(4)),
      quality: Number(quality.toFixed(4)),
      entropy: Number(entropy.toFixed(4)),
      persistence,
      instability_score: Number(instability.toFixed(4)),
    });
    prev = regime;
  }
  return { m, tau, rows };
}

function buildDynamicLayerFromPipeline(regimeRows: Array<{ date: string; regime: string; confidence: number }>, m: number, tau: number): DynamicLayer {
  const rows: DynamicRow[] = [];
  let persistence = 0;
  let prevRegime: string | null = null;

  for (let i = 0; i < regimeRows.length; i++) {
    const current = regimeRows[i];
    const regime = current.regime || "INCONCLUSIVE";
    const confidence = Number.isFinite(current.confidence) ? clamp01(current.confidence) : 0;
    if (regime === prevRegime) persistence += 1;
    else persistence = 1;
    const transition = prevRegime != null && regime !== prevRegime;
    const instabilityScore = regime === "UNSTABLE" ? 0.8 : regime === "TRANSITION" ? 0.55 : regime === "STABLE" ? 0.2 : 0.95;
    rows.push({
      date: current.date,
      regime,
      microstate: "UNK",
      transition,
      confidence: Number(confidence.toFixed(4)),
      quality: 0,
      entropy: 0,
      persistence,
      instability_score: Number(instabilityScore.toFixed(4)),
    });
    prevRegime = regime;
  }
  return { m, tau, rows };
}

function applyHysteresis(statuses: OperationalLayer["status"][]) {
  if (!statuses.length) return statuses;
  const out: OperationalLayer["status"][] = [statuses[0]];
  let current = statuses[0];
  let candidate: OperationalLayer["status"] | null = null;
  let candidateCount = 0;

  for (let i = 1; i < statuses.length; i++) {
    const s = statuses[i];
    if (s === current) {
      candidate = null;
      candidateCount = 0;
      out.push(current);
      continue;
    }

    if (candidate === s) {
      candidateCount += 1;
    } else {
      candidate = s;
      candidateCount = 1;
    }

    if (candidateCount >= HYSTERESIS_DAYS) {
      current = s;
      candidate = null;
      candidateCount = 0;
    }
    out.push(current);
  }
  return out;
}

function buildOperationalLayer(data: DataLayer, dynamic: DynamicLayer): OperationalLayer {
  const rows = dynamic.rows;
  const adequacyOk =
    data.profile.n_points >= MIN_POINTS &&
    data.profile.coverage_years >= MIN_COVERAGE_YEARS &&
    data.profile.gap_ratio <= MAX_GAP_RATIO;

  const hasModelRegimes = rows.length > 0;
  const rawStatuses: OperationalLayer["status"][] = rows.map((r) => {
    if (!adequacyOk) return "inconclusive";
    if (!hasModelRegimes) return "inconclusive";
    const qualityForGate = r.quality > 0 ? r.quality : r.confidence;
    const confidenceForGate = r.confidence;
    if (qualityForGate >= 0.7 && confidenceForGate >= 0.6 && r.regime === "STABLE") return "validated";
    if (qualityForGate >= 0.55 && confidenceForGate >= 0.45) return "watch";
    return "inconclusive";
  });
  const statuses = applyHysteresis(rawStatuses);
  const latest = rows.length ? rows[rows.length - 1] : null;
  const latestStatus = statuses.length ? statuses[statuses.length - 1] : "inconclusive";

  let explanation = "Diagnostico inconclusivo.";
  if (!adequacyOk) {
    explanation = "Dados insuficientes para operacao: verifique n de pontos, cobertura temporal e lacunas.";
  } else if (!hasModelRegimes) {
    explanation = "Sem regime validado do motor (pipeline de regimes nao encontrado para este ativo).";
  } else if (latestStatus === "validated") {
    explanation = "Regime estavel com confianca e qualidade acima do gate.";
  } else if (latestStatus === "watch") {
    explanation = "Regime em observacao: sinais de transicao/instabilidade, manter postura defensiva.";
  }

  return {
    status: latestStatus,
    explanation,
    adequacy_ok: adequacyOk,
    thresholds: {
      min_points: MIN_POINTS,
      min_coverage_years: MIN_COVERAGE_YEARS,
      max_gap_ratio: MAX_GAP_RATIO,
      validated_confidence: 0.6,
      validated_quality: 0.7,
      watch_confidence: 0.45,
      watch_quality: 0.55,
      hysteresis_days: HYSTERESIS_DAYS,
    },
    latest: latest
      ? {
          date: latest.date,
          regime: latest.regime,
          confidence: latest.confidence,
          quality: latest.quality,
          entropy: latest.entropy,
          persistence: latest.persistence,
          instability_score: latest.instability_score,
        }
      : null,
  };
}

async function listCoreAssets(): Promise<string[]> {
  const base = getCoreBaseDir();
  try {
    const files = await fs.readdir(base);
    return files
      .filter((f) => f.endsWith("_core.csv"))
      .map((f) => f.replace(/_core\.csv$/i, ""))
      .sort();
  } catch {
    return [];
  }
}

async function listNormalizedAssets(): Promise<string[]> {
  const base = getNormalizedBaseDir();
  try {
    const files = await fs.readdir(base);
    return files
      .filter((f) => f.startsWith("FipeZap_") && f.endsWith(".csv"))
      .map((f) => f.replace(/\.csv$/i, ""))
      .sort();
  } catch {
    return [];
  }
}

export async function listRealEstateAssets() {
  const core = await listCoreAssets();
  if (core.length) return core;
  return listNormalizedAssets();
}

export async function listRealEstateAssetMeta(): Promise<RealEstateAssetMeta[]> {
  const assets = await listRealEstateAssets();
  const metas = await Promise.all(assets.map((asset) => inferMetaFromDictionary(asset)));
  return metas.sort((a, b) => {
    const ra = a.region.localeCompare(b.region);
    if (ra !== 0) return ra;
    const sa = a.state.localeCompare(b.state);
    if (sa !== 0) return sa;
    return a.city.localeCompare(b.city);
  });
}

async function loadCoreRows(asset: string): Promise<Array<{ date: string; P: number; L: number; J: number; D: number | null }> | null> {
  const fp = getCoreFilePath(asset);
  try {
    const text = await fs.readFile(fp, "utf-8");
    const lines = text.split(/\r?\n/).filter(Boolean);
    if (lines.length < 2) return [];
    const headers = lines[0].split(",").map((h) => h.trim());
    const id = (name: string) => headers.findIndex((h) => h.toLowerCase() === name.toLowerCase());
    const iDate = id("date");
    const iP = id("P");
    const iL = id("L");
    const iJ = id("J");
    const iD = id("D");
    if (iDate < 0 || iP < 0) return null;
    return lines.slice(1).map((line) => {
      const cols = line.split(",");
      const dVal = iD >= 0 ? cols[iD] : "";
      return {
        date: (cols[iDate] || "").trim(),
        P: Number((cols[iP] || "").trim()),
        L: iL >= 0 ? Number((cols[iL] || "").trim()) : Number.NaN,
        J: iJ >= 0 ? Number((cols[iJ] || "").trim()) : Number.NaN,
        D: dVal == null || dVal.trim() === "" ? null : Number(dVal.trim()),
      };
    });
  } catch {
    return null;
  }
}

export async function buildRealEstateAssetPayload(asset: string): Promise<RealEstateAssetPayload> {
  const [coreRows, pipelineRegimes, hmm] = await Promise.all([
    loadCoreRows(asset),
    loadPipelineRegimes(asset),
    loadHMMPayload(asset),
  ]);
  let data: DataLayer;

  if (coreRows && coreRows.length) {
    data = buildDataLayerFromCore(asset, coreRows);
  } else {
    const base = getNormalizedBaseDir();
    const pricePath = getNormalizedFilePath(asset);
    const ratePath = path.join(base, "SELIC_D_11.csv");
    const [price, rate] = await Promise.all([readCsvSeries(pricePath), readCsvSeries(ratePath)]);
    data = buildDataLayerFromNormalized(asset, price, rate);
  }

  const params = await inferEmbeddingParams(asset);
  const dynamic =
    pipelineRegimes.length > 0
      ? buildDynamicLayerFromPipeline(pipelineRegimes, params.m, params.tau)
      : hmm
      ? buildDynamicLayerFromHMM(hmm, data.series.P.map((p) => p.date), params.m, params.tau)
      : buildDynamicLayerFromPipeline([], params.m, params.tau);
  const operational = buildOperationalLayer(data, dynamic);
  return { data, dynamic, operational };
}
