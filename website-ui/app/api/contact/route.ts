import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

type ContactPayload = {
  name?: string;
  email?: string;
  company?: string;
  sector?: string;
  horizon?: string;
  message?: string;
  website?: string;
  locale?: string;
};

function validate(payload: ContactPayload) {
  const email = String(payload.email || "").trim();
  const message = String(payload.message || "").trim();
  if (!email || !email.includes("@")) return "invalid_email";
  if (message.length < 20) return "message_too_short";
  return null;
}

function nowIso() {
  return new Date().toISOString();
}

function randomId() {
  return Math.random().toString(36).slice(2, 8);
}

async function appendToLocalLog(record: Record<string, unknown>) {
  const dir = process.env.CONTACT_INBOX_DIR || path.join("/tmp", "assyntrax_contact_inbox");
  const filePath = path.join(dir, "submissions.ndjson");
  await fs.mkdir(dir, { recursive: true });
  await fs.appendFile(filePath, `${JSON.stringify(record)}\n`, "utf-8");
}

async function postWebhook(record: Record<string, unknown>) {
  const url = process.env.CONTACT_WEBHOOK_URL;
  if (!url) return "local_log" as const;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(record),
  });
  if (!res.ok) throw new Error(`webhook_failed_${res.status}`);
  return "webhook" as const;
}

export async function POST(request: Request) {
  let payload: ContactPayload;
  try {
    payload = (await request.json()) as ContactPayload;
  } catch {
    return NextResponse.json(
      { ok: false, message: "invalid_json" },
      { status: 400 }
    );
  }

  if (String(payload.website || "").trim().length > 0) {
    return NextResponse.json({ ok: true, id: `lead_${randomId()}`, received_at: nowIso(), delivery: "local_log" });
  }

  const invalidReason = validate(payload);
  if (invalidReason) {
    return NextResponse.json({ ok: false, message: invalidReason }, { status: 400 });
  }

  const id = `lead_${new Date().toISOString().slice(0, 10).replace(/-/g, "")}_${randomId()}`;
  const record = {
    id,
    received_at: nowIso(),
    source: "website_contact_form",
    name: String(payload.name || "").trim(),
    email: String(payload.email || "").trim(),
    company: String(payload.company || "").trim(),
    sector: String(payload.sector || "").trim(),
    horizon: String(payload.horizon || "").trim(),
    message: String(payload.message || "").trim(),
    locale: String(payload.locale || "pt"),
    user_agent: request.headers.get("user-agent") || "",
    forwarded_for: request.headers.get("x-forwarded-for") || "",
  };

  try {
    const delivery = await postWebhook(record);
    await appendToLocalLog({ ...record, delivery });
    return NextResponse.json({
      ok: true,
      id,
      received_at: record.received_at,
      delivery,
      message: "received",
    });
  } catch (err) {
    try {
      await appendToLocalLog({ ...record, delivery: "local_log", warning: err instanceof Error ? err.message : "unknown_error" });
      return NextResponse.json({
        ok: true,
        id,
        received_at: record.received_at,
        delivery: "local_log",
        message: "received_local_log_only",
      });
    } catch {
      return NextResponse.json(
        {
          ok: false,
          message: err instanceof Error ? err.message : "contact_submission_failed",
        },
        { status: 500 }
      );
    }
  }
}

export async function GET() {
  return NextResponse.json({
    ok: true,
    endpoint: "/api/contact",
    webhook_configured: Boolean(process.env.CONTACT_WEBHOOK_URL),
  });
}
