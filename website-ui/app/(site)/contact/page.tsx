import type { Metadata } from "next";
import ContactPage from "@/app/(site)/pt/contact/page";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Contato",
  description:
    "Envie seu caso de uso e receba retorno com plano de avaliação técnica e passos para piloto.",
  path: "/contact",
  locale: "pt-BR",
});

export default ContactPage;
