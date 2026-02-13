"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function resolveLang(pathname: string | null) {
  const path = pathname ?? "/";
  const isEn = path === "/en" || path.startsWith("/en/");
  const base = isEn ? path.replace(/^\/en/, "") || "/" : path;
  const enPath = isEn ? path : path === "/" ? "/en" : `/en${path}`;
  return { isEn, base, enPath };
}

export default function SiteHeader() {
  const { isEn, base, enPath } = resolveLang(usePathname());

  const labels = isEn
    ? {
        product: "Product",
        methods: "Methods",
        about: "About",
        contact: "Contact",
        open: "Open App",
        home: "/en",
        productHref: "/en/product",
        methodsHref: "/en/methods",
        aboutHref: "/en/about",
        contactHref: "/en/contact",
      }
    : {
        product: "Produto",
        methods: "Métodos",
        about: "Sobre",
        contact: "Contato",
        open: "Abrir App",
        home: "/",
        productHref: "/product",
        methodsHref: "/methods",
        aboutHref: "/about",
        contactHref: "/contact",
      };

  const ptHref = base || "/";
  const enHref = enPath;

  return (
    <header className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8 py-4 md:py-5 flex items-center justify-between">
      <Link href={labels.home} className="font-semibold tracking-tight text-lg text-zinc-100">
        Assyntrax
      </Link>
      <nav className="flex items-center gap-4 text-sm text-zinc-300">
        <Link className="hover:text-white" href={labels.productHref}>
          {labels.product}
        </Link>
        <Link className="hover:text-white" href={labels.methodsHref}>
          {labels.methods}
        </Link>
        <Link className="hover:text-white" href={labels.aboutHref}>
          {labels.about}
        </Link>
        <Link className="hover:text-white" href={labels.contactHref}>
          {labels.contact}
        </Link>
        <div className="flex items-center gap-2 text-xs">
          <Link
            className={`rounded-full border px-2 py-1 ${
              !isEn ? "border-cyan-400/60 text-cyan-200" : "border-zinc-800 text-zinc-400"
            }`}
            href={ptHref}
          >
            PT
          </Link>
          <Link
            className={`rounded-full border px-2 py-1 ${
              isEn ? "border-cyan-400/60 text-cyan-200" : "border-zinc-800 text-zinc-400"
            }`}
            href={enHref}
          >
            EN
          </Link>
        </div>
        <Link
          className="rounded-xl bg-zinc-100 text-black px-3 py-2 font-medium hover:bg-white transition"
          href="/app/dashboard"
        >
          {labels.open}
        </Link>
      </nav>
    </header>
  );
}

