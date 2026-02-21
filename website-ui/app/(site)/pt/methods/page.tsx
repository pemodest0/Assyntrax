import type { Metadata } from "next";
import MethodsPageClient from "@/components/pages/MethodsPageClient";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Métodos: diagnóstico causal e análise espectral",
  description: "Versão espelhada em /pt. Conteúdo principal publicado em /methods.",
  path: "/pt/methods",
  locale: "pt-BR",
  noIndex: true,
  canonicalPath: "/methods",
});

export default function MethodsPagePT() {
  return <MethodsPageClient />;
}
