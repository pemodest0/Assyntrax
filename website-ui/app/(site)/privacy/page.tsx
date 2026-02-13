export default function PrivacyPage() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-6 items-center">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight">PolÃ­tica de Privacidade</h1>
          <p className="mt-3 text-zinc-300 max-w-3xl">
            Esta Ã© uma pÃ¡gina de polÃ­tica de privacidade em construÃ§Ã£o. A Assyntrax coleta apenas dados
            tÃ©cnicos necessÃ¡rios para operaÃ§Ã£o da plataforma. Nenhuma informaÃ§Ã£o sensÃ­vel Ã© vendida.
          </p>
        </div>
        <div className="relative h-[200px] rounded-3xl border border-zinc-800 overflow-hidden">
          <div className="absolute inset-0 bg-[url('/visuals/hero-graph.svg')] bg-cover bg-center opacity-90 animate-glow" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
        </div>
      </div>
      <p className="text-zinc-300 max-w-3xl">
        Para dÃºvidas, entre em contato via{" "}
        <a className="underline" href="mailto:contact@assyntrax.ai">
          contact@assyntrax.ai
        </a>
        .
      </p>
    </div>
  );
}


