import "@/app/globals.css";
import SiteHeader from "@/components/SiteHeader";
import Link from "next/link";

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  const year = 2026;
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(24,24,27,0.55),_rgba(0,0,0,1))] text-zinc-100">
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8 pb-10 md:pb-12 lg:pb-14 xl:pb-16">{children}</main>
      <footer className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8 py-6 md:py-8 text-xs text-zinc-500 space-y-3">
        <div className="flex flex-wrap gap-4">
          <Link className="hover:text-zinc-200" href="/about">Sobre</Link>
          <Link className="hover:text-zinc-200" href="/contact">Contato</Link>
          <Link className="hover:text-zinc-200" href="/privacy">Politica de Privacidade</Link>
        </div>
        <div>(c) {year} Assyntrax - Regime & Risk Engine</div>
        <div className="text-zinc-600">
          Aviso legal: Assyntrax é uma ferramenta de diagnóstico, sem promessas de retorno financeiro.
        </div>
      </footer>
    </div>
  );
}
