import type { Metadata } from "next";
import MethodsPage from "@/app/(site)/pt/methods/page";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Métodos: diagnóstico causal e análise espectral",
  description:
    "Base metodológica do motor, limites de uso e garantias técnicas de causalidade, auditabilidade e gate.",
  path: "/methods",
  locale: "pt-BR",
});

export default MethodsPage;
