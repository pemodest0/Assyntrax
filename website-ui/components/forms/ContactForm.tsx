"use client";

import { useMemo, useState } from "react";

type Locale = "pt" | "en";

type ContactResponse = {
  ok?: boolean;
  id?: string;
  received_at?: string;
  delivery?: "webhook" | "local_log";
  message?: string;
};

const labelsByLocale: Record<Locale, Record<string, string>> = {
  pt: {
    name: "Nome",
    email: "E-mail",
    company: "Empresa",
    sector: "Setor",
    horizon: "Horizonte",
    message: "Mensagem",
    submit: "Enviar pedido",
    sending: "Enviando...",
    successTitle: "Pedido enviado",
    successText: "Recebemos seu contato com protocolo",
    errorTitle: "Não foi possível enviar agora",
    errorText: "Tente novamente em alguns minutos ou use o e-mail direto.",
    help: "Resposta esperada em até 1 dia útil.",
  },
  en: {
    name: "Name",
    email: "Email",
    company: "Company",
    sector: "Sector",
    horizon: "Horizon",
    message: "Message",
    submit: "Send request",
    sending: "Sending...",
    successTitle: "Request sent",
    successText: "We received your message with ticket",
    errorTitle: "Could not send now",
    errorText: "Please try again in a few minutes or use direct email.",
    help: "Expected response within 1 business day.",
  },
};

export default function ContactForm({ locale = "pt" }: { locale?: Locale }) {
  const labels = labelsByLocale[locale];
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [sector, setSector] = useState("");
  const [horizon, setHorizon] = useState("");
  const [message, setMessage] = useState("");
  const [website, setWebsite] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [response, setResponse] = useState<ContactResponse | null>(null);
  const [error, setError] = useState<string>("");

  const isValid = useMemo(() => {
    return email.trim().includes("@") && message.trim().length >= 20;
  }, [email, message]);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isValid) {
      setStatus("error");
      setError(
        locale === "pt"
          ? "Preencha um e-mail válido e uma mensagem com pelo menos 20 caracteres."
          : "Please provide a valid email and a message with at least 20 characters."
      );
      return;
    }

    setStatus("loading");
    setError("");

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          email,
          company,
          sector,
          horizon,
          message,
          website,
          locale,
        }),
      });

      const data = (await res.json().catch(() => ({}))) as ContactResponse & { error?: string };
      if (!res.ok || !data.ok) {
        throw new Error(data.message || data.error || "request_failed");
      }

      setResponse(data);
      setStatus("ok");
      setName("");
      setEmail("");
      setCompany("");
      setSector("");
      setHorizon("");
      setMessage("");
      setWebsite("");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "request_failed");
    }
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Field label={labels.name}>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-xl border border-zinc-700 bg-black/40 px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
            placeholder={locale === "pt" ? "Seu nome" : "Your name"}
          />
        </Field>
        <Field label={labels.email}>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
            className="w-full rounded-xl border border-zinc-700 bg-black/40 px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
            placeholder={locale === "pt" ? "seu.email@empresa.com" : "you@company.com"}
          />
        </Field>
        <Field label={labels.company}>
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full rounded-xl border border-zinc-700 bg-black/40 px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
            placeholder={locale === "pt" ? "Nome da empresa" : "Company name"}
          />
        </Field>
        <Field label={labels.sector}>
          <input
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="w-full rounded-xl border border-zinc-700 bg-black/40 px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
            placeholder={locale === "pt" ? "Ex.: finanças, renda fixa, ações" : "Ex: finance, fixed income, equities"}
          />
        </Field>
      </div>

      <Field label={labels.horizon}>
        <input
          value={horizon}
          onChange={(e) => setHorizon(e.target.value)}
          className="w-full rounded-xl border border-zinc-700 bg-black/40 px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
          placeholder={locale === "pt" ? "Ex.: diário, semanal, 20 dias" : "Ex: daily, weekly, 20 days"}
        />
      </Field>

      <Field label={labels.message}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={7}
          required
          className="w-full rounded-xl border border-zinc-700 bg-black/40 px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
          placeholder={
            locale === "pt"
              ? "Descreva o contexto, os ativos, o objetivo e como quer consumir a saída."
              : "Describe context, assets, objective, and how you want to consume outputs."
          }
        />
      </Field>

      <div className="hidden" aria-hidden>
        <label htmlFor="website">Website</label>
        <input
          id="website"
          value={website}
          onChange={(e) => setWebsite(e.target.value)}
          autoComplete="off"
          tabIndex={-1}
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded-xl bg-zinc-100 text-black px-5 py-3 font-medium hover:bg-white transition disabled:opacity-70"
        >
          {status === "loading" ? labels.sending : labels.submit}
        </button>
        <div className="text-xs text-zinc-500">{labels.help}</div>
      </div>

      {status === "ok" && response?.id ? (
        <div className="rounded-xl border border-emerald-700/40 bg-emerald-950/20 p-3 text-sm text-emerald-200">
          {labels.successTitle}. {labels.successText} <strong>{response.id}</strong>.
        </div>
      ) : null}

      {status === "error" ? (
        <div className="rounded-xl border border-rose-700/40 bg-rose-950/20 p-3 text-sm text-rose-200">
          {labels.errorTitle}. {labels.errorText} ({error || "unknown_error"})
        </div>
      ) : null}
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-2 text-sm text-zinc-300">
      <span>{label}</span>
      {children}
    </label>
  );
}
