export default function ContactPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-semibold tracking-tight">Contato</h1>
      <p className="text-zinc-300 max-w-3xl">
        Interessado em colaboração, pesquisa ou integração?
      </p>
      <div className="space-y-3 text-zinc-200">
        <div>
          Email:{" "}
          <a className="hover:text-white" href="mailto:contact@assyntrax.ai">
            contact@assyntrax.ai
          </a>
        </div>
        <div className="flex gap-4">
          <a className="hover:text-white" href="https://github.com/assyntrax">
            GitHub
          </a>
          <a className="hover:text-white" href="https://www.linkedin.com/company/assyntrax/">
            LinkedIn
          </a>
        </div>
      </div>
    </div>
  );
}
