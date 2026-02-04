import "@/app/globals.css";
import SiteHeader from "@/components/SiteHeader";
import Link from "next/link";

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  const year = 2026;
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(24,24,27,0.55),_rgba(0,0,0,1))] text-zinc-100">
      <SiteHeader />
      <main className="mx-auto max-w-6xl px-6 pb-16">{children}</main>
      <footer className="mx-auto max-w-6xl px-6 py-10 text-xs text-zinc-500 space-y-4">
        <div className="flex flex-wrap gap-4">
          <Link className="hover:text-zinc-200" href="/about">Sobre</Link>
          <Link className="hover:text-zinc-200" href="/contact">Contato</Link>
          <Link className="hover:text-zinc-200" href="/privacy">Política de Privacidade</Link>
        </div>
        <div>(c) {year} Assyntrax - Regime &amp; Risk Engine</div>
        <div className="text-zinc-600">
          Aviso legal: Assyntrax é uma ferramenta de diagnóstico, sem promessas de retorno financeiro.
        </div>
      </footer>
    </div>
  );
}
