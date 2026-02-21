import type { Metadata } from "next";
import ProductPage from "@/app/(site)/product/page";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Produto: painel e API com gates auditáveis",
  description: "Versão espelhada em /pt. Conteúdo principal publicado em /product.",
  path: "/pt/product",
  locale: "pt-BR",
  noIndex: true,
  canonicalPath: "/product",
});

export default ProductPage;
