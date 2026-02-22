import type { Metadata } from "next";
import ContactForm from "@/components/forms/ContactForm";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Contato",
  description: "Versão espelhada em /pt. Conteúdo principal publicado em /contact.",
  path: "/pt/contact",
  locale: "pt-BR",
  noIndex: true,
  canonicalPath: "/contact",
});

export default function ContactPage() {
  return (
    <div className="space-y-10">
      <section className="rounded-[28px] border border-zinc-800 bg-zinc-950/60 p-8 lg:p-10">
        <div className="space-y-3 max-w-3xl">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Contato</div>
          <h1 className="text-4xl font-semibold tracking-tight">Fale com a equipe da Assyntrax</h1>
          <p className="text-zinc-300">
            Envie seu caso de uso com setor, ativos e horizonte. A resposta sai com plano de avaliação técnica e
            próximo passo de piloto.
          </p>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
          <ContactForm locale="pt" />
        </div>

        <aside className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Canais</div>
          <div className="mt-4 flex flex-col gap-3 text-sm">
            <a className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500" href="mailto:contact@assyntrax.ai">
              E-mail direto
            </a>
            <a className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500" href="https://github.com/pemodest0/Assyntrax">
              GitHub do projeto
            </a>
            <a className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-300 hover:text-white hover:border-zinc-500" href="https://www.linkedin.com/in/pedro-henrique-gesualdo-modesto-39a135272/">
              LinkedIn
            </a>
          </div>
          <div className="mt-4 text-xs text-zinc-500">
            Dica: inclua volume de ativos e periodicidade para acelerar o retorno.
          </div>
        </aside>
      </section>
    </div>
  );
}
