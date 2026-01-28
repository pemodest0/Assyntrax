import { PredictionSchema, PredictionData } from "./schema";

export async function loadPrediction(path: string): Promise<PredictionData> {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`failed to load ${path}`);
  }
  const data = await res.json();
  return PredictionSchema.parse(data);
}
