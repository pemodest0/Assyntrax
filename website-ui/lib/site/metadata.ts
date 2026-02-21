import type { Metadata } from "next";

const DEFAULT_SITE_URL = "https://assyntrax.vercel.app";
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.VERCEL_PROJECT_PRODUCTION_URL || DEFAULT_SITE_URL;
const metadataBase = new URL(siteUrl.startsWith("http") ? siteUrl : `https://${siteUrl}`);

type PageMetadataInput = {
  title: string;
  description: string;
  path: string;
  locale?: "pt-BR";
  noIndex?: boolean;
  canonicalPath?: string;
  keywords?: string[];
};

function normalizePath(path: string) {
  if (!path) return "/";
  return path.startsWith("/") ? path : `/${path}`;
}

export function siteMetadataBase() {
  return metadataBase;
}

export function buildPageMetadata(input: PageMetadataInput): Metadata {
  const path = normalizePath(input.path);
  const canonical = normalizePath(input.canonicalPath || path);
  const noIndex = Boolean(input.noIndex);

  return {
    metadataBase,
    title: input.title,
    description: input.description,
    keywords: input.keywords,
    alternates: {
      canonical,
    },
    openGraph: {
      type: "website",
      locale: "pt-BR",
      url: canonical,
      title: input.title,
      description: input.description,
      siteName: "Assyntrax | Diagnóstico de Regime",
      images: [
        {
          url: "/assets/og/eigen-engine-og.svg",
          width: 1200,
          height: 630,
          alt: "Assyntrax - Diagnóstico de Regime",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: input.title,
      description: input.description,
      images: ["/assets/og/eigen-engine-og.svg"],
    },
    robots: noIndex
      ? { index: false, follow: false }
      : {
          index: true,
          follow: true,
          googleBot: {
            index: true,
            follow: true,
            "max-snippet": -1,
            "max-image-preview": "large",
            "max-video-preview": -1,
          },
        },
  };
}
