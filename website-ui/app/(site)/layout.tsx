import "@/app/globals.css";
import Link from "next/link";

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-zinc-950 to-black text-zinc-100">
      <header className="mx-auto max-w-6xl px-6 py-6 flex items-center justify-between">
        <Link href="/" className="font-semibold tracking-tight text-lg">
          Assyntrax
        </Link>
        <nav className="flex items-center gap-4 text-sm text-zinc-300">
          <Link className="hover:text-white" href="/about">
            Sobre
          </Link>
          <Link className="hover:text-white" href="/methods">
            Métodos
          </Link>
          <Link className="hover:text-white" href="/contact">
            Contato
          </Link>
          <Link
            className="rounded-xl bg-zinc-100 text-black px-3 py-2 font-medium hover:bg-white transition"
            href="/app/dashboard"
          >
            Open App
          </Link>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-6 pb-16">{children}</main>
      <footer className="mx-auto max-w-6xl px-6 py-10 text-xs text-zinc-500">
        © {new Date().getFullYear()} Assyntrax • Regime &amp; Risk Engine
      </footer>
    </div>
  );
}
