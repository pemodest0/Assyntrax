import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export function dataDirs() {
  const root = repoRoot();
  return {
    latest: process.env.DATA_DIR || path.join(root, "results", "latest"),
    publicLatest: path.join(process.cwd(), "public", "data", "latest"),
    results: path.join(root, "results"),
  };
}

export async function listLatestFiles() {
  const { latest, publicLatest } = dataDirs();
  let dir = latest;
  try {
    await fs.access(dir);
  } catch {
    dir = publicLatest;
  }
  const files = await fs.readdir(dir);
  return files.filter((f) => f.endsWith(".json"));
}

export async function readLatestFile(file: string) {
  const { latest, publicLatest } = dataDirs();
  let dir = latest;
  try {
    await fs.access(dir);
  } catch {
    dir = publicLatest;
  }
  const target = path.join(dir, file);
  try {
    const text = await fs.readFile(target, "utf-8");
    return JSON.parse(text);
  } catch {
    // fallback: try other dir
    const fallback = dir === latest ? path.join(publicLatest, file) : path.join(latest, file);
    const text = await fs.readFile(fallback, "utf-8");
    return JSON.parse(text);
  }
}

export async function findLatestApiRecords() {
  const { results } = dataDirs();
  const entries = await fs.readdir(results, { withFileTypes: true });
  const candidates: { path: string; mtime: number }[] = [];
  for (const ent of entries) {
    if (!ent.isDirectory()) continue;
    const p = path.join(results, ent.name, "api_records.jsonl");
    try {
      const stat = await fs.stat(p);
      candidates.push({ path: p, mtime: stat.mtimeMs });
    } catch {
      // ignore
    }
  }
  candidates.sort((a, b) => b.mtime - a.mtime);
  return candidates.length ? candidates[0].path : null;
}

export async function readJsonl(pathFile: string) {
  const text = await fs.readFile(pathFile, "utf-8");
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

export async function readDashboardOverview() {
  const { results } = dataDirs();
  const overviewPath = path.join(results, "dashboard", "overview.json");
  const text = await fs.readFile(overviewPath, "utf-8");
  return JSON.parse(text);
}
