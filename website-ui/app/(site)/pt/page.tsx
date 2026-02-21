import type { Metadata } from "next";
import HomePage from "@/app/(site)/page";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Diagnóstico causal de regime e risco estrutural",
  description: "Versão espelhada da home em /pt. Conteúdo principal publicado em /.",
  path: "/pt",
  locale: "pt-BR",
  noIndex: true,
  canonicalPath: "/",
});

export default HomePage;
