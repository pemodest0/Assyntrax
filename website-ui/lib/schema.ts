import { z } from "zod";

export const PredictionSchema = z.object({
  asset: z.string(),
  timeframe: z.string(),
  asof: z.string(),
  risk: z.object({
    risk_regime: z.string(),
    confidence: z.number(),
    risk_level: z.string(),
    model: z.string(),
    metrics: z.object({
      roc_auc: z.number().optional(),
      f1: z.number().optional(),
    }).optional(),
  }).optional(),
  regime: z.object({
    state: z.string(),
    confidence: z.number(),
    alerts: z.array(z.string()).optional(),
  }).optional(),
  forecast: z.object({
    p10: z.number().optional(),
    p50: z.number().optional(),
    p90: z.number().optional(),
    model: z.string().optional(),
    directional_accuracy_recent: z.number().optional(),
    mase_recent: z.number().optional(),
    confidence: z.number().optional(),
    alerts: z.array(z.string()).optional(),
  }).optional(),
  recent: z.object({
    mase: z.number().optional(),
    smape: z.number().optional(),
    dir_acc: z.number().optional(),
    drawdown: z.number().optional(),
  }).optional(),
  series: z.object({
    dates: z.array(z.string()).optional(),
    vol20: z.array(z.number()).optional(),
    risk_prob_highvol: z.array(z.number()).optional(),
    regime_score_instability: z.array(z.number()).optional(),
  }).optional(),
});

export type PredictionData = z.infer<typeof PredictionSchema>;
