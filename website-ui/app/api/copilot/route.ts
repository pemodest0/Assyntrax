import { NextResponse } from "next/server";
import { buildCopilotContext, buildCopilotReply } from "@/lib/server/copilot";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const question = String(searchParams.get("question") || "").trim();
  const context = await buildCopilotContext();
  const answer = buildCopilotReply(question, context);
  return NextResponse.json(
    {
      ok: true,
      mode: "deterministic_physmath_v2_shadow_gate",
      context,
      answer,
    },
    { headers: { "Cache-Control": "no-store" } }
  );
}

export async function POST(request: Request) {
  let question = "";
  try {
    const body = (await request.json()) as { question?: unknown };
    question = typeof body.question === "string" ? body.question : "";
  } catch {
    question = "";
  }
  const context = await buildCopilotContext();
  const answer = buildCopilotReply(question, context);
  return NextResponse.json(
    {
      ok: true,
      mode: "deterministic_physmath_v2_shadow_gate",
      context,
      answer,
    },
    { headers: { "Cache-Control": "no-store" } }
  );
}
