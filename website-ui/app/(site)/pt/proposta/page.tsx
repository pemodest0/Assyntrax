import type { Metadata } from "next";
import PropostaPage from "@/app/(site)/proposta/page";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Proposta: piloto e integração",
  description: "Versão espelhada em /pt. Conteúdo principal publicado em /proposta.",
  path: "/pt/proposta",
  locale: "pt-BR",
  noIndex: true,
  canonicalPath: "/proposta",
});

export default PropostaPage;
