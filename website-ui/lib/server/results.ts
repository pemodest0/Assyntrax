import { promises as fs } from "fs";
import path from "path";

function repoRoot() {
  return path.resolve(process.cwd(), "..");
}

export function resultsRoot() {
  const root = repoRoot();
  return process.env.RESULTS_DIR || path.join(root, "results");
}

export function indexPath() {
  return path.join(resultsRoot(), "results_index.json");
}

export async function readIndex() {
  const p = indexPath();
  const text = await fs.readFile(p, "utf-8");
  return JSON.parse(text);
}

export function resolveResultsPath(rel: string) {
  const root = resultsRoot();
  const target = path.resolve(root, rel);
  const rootNorm = path.resolve(root);
  if (!target.startsWith(rootNorm + path.sep) && target !== rootNorm) {
    throw new Error("path_outside_results");
  }
  return target;
}

export function contentTypeFor(filePath: string) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".png") return "image/png";
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".svg") return "image/svg+xml";
  if (ext === ".pdf") return "application/pdf";
  if (ext === ".json") return "application/json";
  if (ext === ".csv") return "text/csv";
  if (ext === ".md") return "text/markdown";
  return "application/octet-stream";
}
