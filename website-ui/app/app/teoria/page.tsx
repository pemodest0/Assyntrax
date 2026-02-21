import Link from "next/link";

const physicsPillars = [
  {
    title: "Sistemas complexos",
    text: "Mercado nao e linear. Em estresse, as conexoes entre ativos mudam de forma rapida e coletiva.",
  },
  {
    title: "Transicao de regime",
    text: "O motor mede mudanca estrutural, nao so direcao de preco. O foco e detectar troca de fase do sistema.",
  },
  {
    title: "Liquidez e contagio",
    text: "Quando liquidez seca, correlacao tende a subir e clusters aumentam. Isso aparece nas metricas espectrais.",
  },
];

const mathBlocks = [
  {
    title: "Matriz rolling de correlacao",
    formula: "C_t = corr(R_{t-T+1:t})",
    note: "Base do motor por janela T (60, 120, 252).",
  },
  {
    title: "Modo dominante",
    formula: "p1_t = lambda1_t / sum_i(lambda_i_t)",
    note: "Mostra quanto da variacao do sistema esta no primeiro modo comum.",
  },
  {
    title: "Dimensao efetiva",
    formula: "deff_t = (sum_i lambda_i_t)^2 / sum_i(lambda_i_t^2)",
    note: "Quando deff cai, o sistema fica mais concentrado e fragil.",
  },
  {
    title: "Score estrutural",
    formula: "risk_t = w1*p1_z + w2*(1/deff_z) + w3*cluster_share + w4*turnover",
    note: "Combina concentracao, instabilidade de clusters e mudanca de estrutura.",
  },
  {
    title: "Regra de estado",
    formula: "state_t = hysteresis(risk_t, th_in, th_out, min_persist)",
    note: "Evita troca de estado por ruído diario.",
  },
  {
    title: "Significancia bootstrap",
    formula: "z_t = (x_t - mean(x_boot)) / std(x_boot)",
    note: "Compara o observado contra distribuicao nula para evitar autoengano.",
  },
];

const whyItWorks = [
  "Usa somente informacao disponivel ate o tempo t (modo causal).",
  "Tem gate de publicacao para bloquear release ruim.",
  "Tem checks de qualidade de dados e elegibilidade de universo.",
  "Tem comparacao com baseline simples e baseline aleatorio.",
  "Tem rastreabilidade completa por run e por artefato.",
];

const caveats = [
  "Nao promete data exata de crash.",
  "Choque totalmente exogeno pode surgir sem sinal forte previo.",
  "Em travamento de liquidez, sinal correto nao garante execucao ideal.",
  "Serve para risco e governanca; nao e recomendacao automatica de compra/venda.",
];

const references = [
  {
    id: "R1",
    title: "Financial Applications of Random Matrix Theory: a short review (arXiv:0910.1205)",
    href: "https://arxiv.org/abs/0910.1205",
    group: "Base matematica",
  },
  {
    id: "R2",
    title: "A review of two decades of correlations, hierarchies, networks and clustering in financial markets",
    href: "https://arxiv.org/abs/1510.01738",
    group: "Base matematica",
  },
  {
    id: "R3",
    title: "Principal Components as a Measure of Systemic Risk (MIT)",
    href: "https://web.mit.edu/~finlunch/Fall10/PCASystemicRisk.pdf",
    group: "Risco sistemico",
  },
  {
    id: "R4",
    title: "RiskMetrics Technical Document (MSCI, 1996)",
    href: "https://www.msci.com/www/research-report/1996-riskmetrics-technical/018482266",
    group: "Risco sistemico",
  },
  {
    id: "R5",
    title: "Estimation of Large Financial Covariances: A Cross-Validation Approach",
    href: "https://arxiv.org/abs/1909.12064",
    group: "Covariancia",
  },
  {
    id: "R6",
    title: "Application of Robust Statistics to Asset Allocation Models (MIT DSpace)",
    href: "https://dspace.mit.edu/handle/1721.1/164924",
    group: "Robustez",
  },
  {
    id: "R7",
    title: "Walk-forward optimization (conceito)",
    href: "https://en.wikipedia.org/wiki/Walk_forward_optimization",
    group: "Validacao causal",
  },
  {
    id: "R8",
    title: "Block bootstrapping technique (scores docs)",
    href: "https://scores.readthedocs.io/en/stable/tutorials/Block_Bootstrapping.html",
    group: "Validacao causal",
  },
  {
    id: "R9",
    title: "Bootstrap of dependent data in finance (Chalmers)",
    href: "https://www.math.chalmers.se/Stat/Grundutb/GU/MSA220/S11/hd1.pdf",
    group: "Validacao causal",
  },
  {
    id: "R10",
    title: "Basel III: Liquidity Coverage Ratio and liquidity risk monitoring tools (BIS)",
    href: "https://www.bis.org/publ/bcbs238.htm",
    group: "Liquidez",
  },
  {
    id: "R11",
    title: "Liquidity booklet, Comptroller's Handbook (OCC)",
    href: "https://www.occ.treas.gov/publications-and-resources/publications/comptrollers-handbook/files/liquidity/index-liquidity.html",
    group: "Liquidez",
  },
  {
    id: "R12",
    title: "SR 11-7: Guidance on Model Risk Management (Federal Reserve)",
    href: "https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm",
    group: "Governanca",
  },
  {
    id: "R13",
    title: "Fundamental review of the trading book (BIS)",
    href: "https://www.bis.org/bcbs/publ/d305.htm",
    group: "Governanca",
  },
  {
    id: "R14",
    title: "Overleaf: Modelo de Trabalho Acadêmico FEA-RP",
    href: "https://pt.overleaf.com/latex/templates/modelo-de-trabalho-academico-da-fea-rp-v-0-3/tbrnzhfwdvpt",
    group: "Padrao academico",
  },
];

export default function TeoriaPage() {
  return (
    <div className="p-4 md:p-6 space-y-6">
      <section className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5 md:p-6">
        <div className="ax-theory-grid absolute inset-0 opacity-35" aria-hidden />
        <div className="pointer-events-none absolute -left-16 -top-12 h-52 w-52 rounded-full border border-cyan-500/30 ax-orbit-spin" />
        <div className="pointer-events-none absolute -right-14 top-8 h-40 w-40 rounded-full border border-emerald-500/35 ax-orbit-spin-rev" />
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full border border-zinc-700/50 ax-wave-ring" />
        <div className="relative z-10">
          <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Teoria Fisica e Matematica</div>
          <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">
            Fundacao tecnica do Assyntrax
          </h1>
          <p className="mt-3 text-sm text-zinc-300 max-w-3xl">
            Esta pagina concentra o lado complicado do motor: fundamentos, equacoes e limites.
            A ideia e mostrar por que o diagnostico estrutural faz sentido, onde ele e valido e onde ele nao e.
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link href="/app/dashboard" className="rounded-md border border-cyan-700/60 bg-cyan-950/30 px-3 py-2 text-cyan-200 hover:border-cyan-500 transition">
              Ver motor no painel
            </Link>
            <Link href="/app/venda" className="rounded-md border border-zinc-700 px-3 py-2 text-zinc-100 hover:border-zinc-500 transition">
              Voltar para venda
            </Link>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Pilares fisicos</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Intuicao do modelo</h2>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          {physicsPillars.map((item) => (
            <article key={item.title} className="rounded-xl border border-zinc-800 bg-black/30 p-4">
              <div className="text-sm font-semibold text-zinc-100">{item.title}</div>
              <p className="mt-2 text-xs text-zinc-400 leading-relaxed">{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Equacoes-chave</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Nucleo matematico</h2>
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
          {mathBlocks.map((item) => (
            <article key={item.title} className="rounded-xl border border-zinc-800 bg-black/30 p-4 ax-eq-fade">
              <div className="text-sm font-semibold text-zinc-100">{item.title}</div>
              <pre className="mt-2 overflow-auto rounded-lg border border-zinc-800 bg-zinc-950/70 p-3 text-xs text-cyan-200">
                <code>{item.formula}</code>
              </pre>
              <p className="mt-2 text-xs text-zinc-400">{item.note}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
          <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Por que faz sentido</div>
          <h3 className="mt-1 text-lg font-semibold text-zinc-100">Validacao pratica</h3>
          <ul className="mt-3 space-y-2 text-sm text-zinc-300">
            {whyItWorks.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
          <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Limites reais</div>
          <h3 className="mt-1 text-lg font-semibold text-zinc-100">O que o motor nao promete</h3>
          <ul className="mt-3 space-y-2 text-sm text-zinc-300">
            {caveats.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Referencias</div>
        <h3 className="mt-1 text-lg font-semibold text-zinc-100">Base tecnica e regulatoria</h3>
        <p className="mt-2 text-xs text-zinc-400">
          Referencias usadas para o framework matematico, validacao estatistica, liquidez e governanca de modelo.
        </p>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {references.map((ref) => (
            <a
              key={ref.id}
              href={ref.href}
              target="_blank"
              rel="noreferrer"
              className="rounded-xl border border-zinc-800 bg-black/30 p-3 hover:border-zinc-600 transition"
            >
              <div className="text-[10px] uppercase tracking-[0.14em] text-zinc-500">
                {ref.id} · {ref.group}
              </div>
              <div className="mt-1 text-sm text-zinc-200">{ref.title}</div>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
