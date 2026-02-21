import Link from "next/link";
import Script from "next/script";

const notationRows = [
  { symbol: String.raw`(\Omega,\mathcal{F},\mathbb{P})`, meaning: "Espaço de probabilidade fundamental." },
  { symbol: String.raw`\{\mathcal{F}_t\}_{t\ge 0}`, meaning: "Filtração de informação disponível até o tempo t." },
  { symbol: "N", meaning: "Número de ativos no universo." },
  { symbol: "T", meaning: "Comprimento da janela temporal." },
  { symbol: String.raw`Q=\frac{T}{N}`, meaning: "Razão de dimensionalidade amostral." },
  { symbol: String.raw`C_t`, meaning: "Matriz empírica de correlação no tempo t." },
  { symbol: String.raw`\lambda_{k,t}`, meaning: "k-ésimo autovalor de C_t." },
  { symbol: String.raw`\mathbf{v}_{k,t}`, meaning: "k-ésimo autovetor de C_t." },
  { symbol: String.raw`AR_t,\ ED_t,\ IPR_t`, meaning: "Métricas de compressão estrutural." },
];

const coreEquations = [
  {
    title: "Retorno logarítmico",
    tex: String.raw`r_{i,t}=\ln\left(\frac{S_{i,t}}{S_{i,t-1}}\right)`,
    note: "Torna variações aditivas no tempo e comparáveis entre ativos.",
  },
  {
    title: "Padronização",
    tex: String.raw`z_{i,t}=\frac{r_{i,t}-\bar r_i}{\sigma_i}`,
    note: "Reduz dominância de ativos naturalmente mais voláteis.",
  },
  {
    title: "EWMA da correlação",
    tex: String.raw`C_t=(1-\lambda)\mathbf z_t\mathbf z_t^\top + \lambda C_{t-1},\ \lambda\in(0,1)`,
    note: "Atualização causal com maior peso para informação recente.",
  },
  {
    title: "Janela efetiva",
    tex: String.raw`T_{eff}=\frac{1}{1-\lambda}`,
    note: "Escala de memória operacional induzida pelo EWMA.",
  },
  {
    title: "Decomposição espectral",
    tex: String.raw`C_t=V_t\Lambda_tV_t^\top=\sum_{k=1}^N \lambda_{k,t}\mathbf v_{k,t}\mathbf v_{k,t}^\top`,
    note: "Separa fatores coletivos e estrutura de ruído.",
  },
  {
    title: "Conservação de traço",
    tex: String.raw`\sum_{k=1}^{N}\lambda_{k,t}=N`,
    note: "Com retornos padronizados, a energia espectral total é constante.",
  },
];

const rmtEquations = [
  String.raw`\lambda_{\pm}=\sigma^2\left(1\pm\sqrt{\frac{1}{Q}}\right)^2`,
  String.raw`f(\lambda)=\frac{Q}{2\pi\sigma^2\lambda}\sqrt{(\lambda_+-\lambda)(\lambda-\lambda_-)}`,
];

const metrics = [
  {
    title: "Absorption Ratio",
    tex: String.raw`AR_n(t)=\frac{\sum_{k=1}^{n}\lambda_{k,t}}{\sum_{k=1}^{N}\lambda_{k,t}}`,
    read: "Mede quanta variância ficou concentrada em poucos modos.",
  },
  {
    title: "Entropia espectral",
    tex: String.raw`H_t=-\sum_{k=1}^{N}p_{k,t}\ln p_{k,t},\quad p_{k,t}=\frac{\lambda_{k,t}}{\sum_{j=1}^{N}\lambda_{j,t}}`,
    read: "Mede dispersão de informação entre os modos do sistema.",
  },
  {
    title: "Dimensão efetiva",
    tex: String.raw`ED_t=\exp(H_t)`,
    read: "Aproxima quantos graus de liberdade ainda existem no mercado.",
  },
  {
    title: "IPR",
    tex: String.raw`IPR_{k,t}=\sum_{i=1}^{N}\left(v_{k,t}^{(i)}\right)^4`,
    read: "Distingue choque sistêmico de choque localizado.",
  },
  {
    title: "Overlap temporal",
    tex: String.raw`O_{ij}(t_1,t_2)=\left|\langle \mathbf v_{i,t_1}, \mathbf v_{j,t_2}\rangle\right|^2`,
    read: "Captura rotação de autovetores e quebra de estabilidade estrutural.",
  },
];

const regimeRules = [
  {
    title: "Score estrutural",
    tex: String.raw`\Phi_t=-\ln(ED_t),\quad S_t=\frac{\Phi_t-\mu_{\Phi}}{\sigma_{\Phi}}`,
  },
  {
    title: "Classificação com histerese",
    tex: String.raw`R_t=\begin{cases}
1, & S_t\ge\theta_{up}\\
0, & S_t\le\theta_{down}\\
R_{t-1}, & \theta_{down}<S_t<\theta_{up}
\end{cases}`,
  },
];

const validationEquations = [
  String.raw`\mathrm{Recall}=\frac{TP}{TP+FN}`,
  String.raw`\mathrm{Precision}=\frac{TP}{TP+FP}`,
  String.raw`\tau_{lead}=t_0-\inf\{t<t_0: R_t=1\}`,
  String.raw`P(L=k)=p(1-p)^{k-1},\ k=1,2,\ldots`,
];

const limits = [
  "Se Q=T/N < 1, a matriz pode perder posto e o espectro degrada.",
  "Sem warmup suficiente no EWMA, os estados iniciais ficam enviesados.",
  "Caudas pesadas podem inflar autovalores e exigir robustez extra.",
  "Fragilidade estrutural não implica direção imediata de preço.",
];

const references = [
  {
    id: "R1",
    title: "Laloux et al. (1999) - Noise dressing of financial correlation matrices",
    href: "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.83.1467",
  },
  {
    id: "R2",
    title: "Bouchaud & Potters - Financial Applications of RMT",
    href: "https://arxiv.org/abs/0910.1205",
  },
  {
    id: "R3",
    title: "Kritzman et al. (2011) - Principal Components as a Measure of Systemic Risk",
    href: "https://www.nber.org/papers/w17590",
  },
  {
    id: "R4",
    title: "Politis & Romano (1994) - The Stationary Bootstrap",
    href: "https://www.jstor.org/stable/2290993",
  },
  {
    id: "R5",
    title: "Del Giudice (2020) - Effective dimensionality: A tutorial",
    href: "https://doi.org/10.1080/00273171.2020.1743631",
  },
  {
    id: "R6",
    title: "SR 11-7 - Federal Reserve (Model Risk Management)",
    href: "https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm",
  },
  {
    id: "R7",
    title: "Basel III - Liquidity Coverage Ratio (BIS)",
    href: "https://www.bis.org/publ/bcbs238.htm",
  },
];

export default function TeoriaPage() {
  return (
    <div className="p-4 md:p-6 space-y-6">
      <Script id="mathjax-config" strategy="afterInteractive">{`
        window.MathJax = {
          tex: {
            inlineMath: [['\\\\(', '\\\\)']],
            displayMath: [['\\\\[', '\\\\]']],
            processEscapes: true
          },
          options: {
            skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
          }
        };
      `}</Script>
      <Script
        id="mathjax-core"
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        strategy="afterInteractive"
      />

      <section className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5 md:p-6">
        <div className="ax-theory-grid absolute inset-0 opacity-35" aria-hidden />
        <div className="pointer-events-none absolute -left-16 -top-12 h-52 w-52 rounded-full border border-cyan-500/30 ax-orbit-spin" />
        <div className="pointer-events-none absolute -right-14 top-8 h-40 w-40 rounded-full border border-emerald-500/35 ax-orbit-spin-rev" />
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full border border-zinc-700/50 ax-wave-ring" />
        <div className="relative z-10">
          <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Teoria física e matemática</div>
          <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">Fundamentação formal do Assyntrax</h1>
          <p className="mt-3 text-sm text-zinc-300 max-w-4xl">
            Versão curada do núcleo teórico: rigor suficiente para auditoria técnica e leitura executiva.
            Foco em causalidade, decomposição espectral e validação robusta.
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link href="/app/dashboard" className="rounded-md border border-cyan-700/60 bg-cyan-950/30 px-3 py-2 text-cyan-200 hover:border-cyan-500 transition">
              Ver motor no painel
            </Link>
            <Link href="/app/venda" className="rounded-md border border-zinc-700 px-3 py-2 text-zinc-100 hover:border-zinc-500 transition">
              Voltar para venda
            </Link>
            <a
              href="https://github.com/pemodest0/Assyntrax/blob/main/docs/motor/FUNDAMENTACAO_TEORICA_ASSYNTRAX_LATEX.md"
              target="_blank"
              rel="noreferrer"
              className="rounded-md border border-emerald-700/70 bg-emerald-950/20 px-3 py-2 text-emerald-200 hover:border-emerald-500 transition"
            >
              Abrir texto completo
            </a>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">1) Espaço probabilístico</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Causalidade e informação disponível</h2>
        <p className="mt-2 text-sm text-zinc-300">
          O modelo é formulado em processo filtrado para impedir look-ahead bias e garantir que o estado em \(t\) use apenas
          informação observada até \(t\).
        </p>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          <MathCard tex={String.raw`(\Omega,\mathcal F,\mathbb P)`} note="Espaço de probabilidade." />
          <MathCard tex={String.raw`\{\mathcal F_t\}_{t\ge0},\ \mathcal F_s\subseteq\mathcal F_t\ (s\le t)`} note="Filtração temporal." />
          <MathCard tex={String.raw`\mathbf S_t=(S_{1,t},\ldots,S_{N,t})^\top`} note="Vetor multivariado de preços." />
          <MathCard tex={String.raw`C_t \approx \text{realização empírica de } \Sigma_t`} note="Observável finito vs estrutura latente." />
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">2-4) Núcleo matemático</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Retornos, EWMA e espectro</h2>
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
          {coreEquations.map((item) => (
            <article key={item.title} className="rounded-xl border border-zinc-800 bg-black/30 p-4">
              <div className="text-sm font-semibold text-zinc-100">{item.title}</div>
              <MathBlock tex={item.tex} />
              <p className="mt-2 text-xs text-zinc-400">{item.note}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">5) RMT</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Separação entre sinal e ruído</h2>
        <p className="mt-2 text-sm text-zinc-300">
          O limite de Marcenko-Pastur define um envelope estatístico para autovalores sob hipótese nula.
          O que excede esse envelope é candidato a estrutura real.
        </p>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          {rmtEquations.map((tex, idx) => (
            <MathCard key={`rmt-${idx}`} tex={tex} note={idx === 0 ? "Limites do suporte espectral." : "Densidade assintótica de referência."} />
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">6-7) Métricas de regime</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Compressão estrutural e estabilidade temporal</h2>
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
          {metrics.map((item) => (
            <article key={item.title} className="rounded-xl border border-zinc-800 bg-black/30 p-4">
              <div className="text-sm font-semibold text-zinc-100">{item.title}</div>
              <MathBlock tex={item.tex} />
              <p className="mt-2 text-xs text-zinc-400">{item.read}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">7-8) Classificação e validação</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Score, histerese e event study</h2>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          {regimeRules.map((item) => (
            <MathCard key={item.title} tex={item.tex} note={item.title} />
          ))}
        </div>
        <div className="mt-3 rounded-xl border border-zinc-800 bg-black/25 p-4">
          <div className="text-sm font-semibold text-zinc-100">Métricas de avaliação</div>
          <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-3">
            {validationEquations.map((tex, idx) => (
              <MathCard key={`val-${idx}`} tex={tex} note="Validação causal e robusta." />
            ))}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
          <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">9) Limites de validade</div>
          <h3 className="mt-1 text-lg font-semibold text-zinc-100">Quando o motor perde confiabilidade</h3>
          <ul className="mt-3 space-y-2 text-sm text-zinc-300">
            {limits.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
          <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">10) Escopo atual</div>
          <h3 className="mt-1 text-lg font-semibold text-zinc-100">O que está explicitamente fora da prova</h3>
          <ul className="mt-3 space-y-2 text-sm text-zinc-300">
            <li>- Prova completa por transformada de Stieltjes dos limites MP.</li>
            <li>- Solução fechada universal para os limiares de histerese (theta_up, theta_down) em todos os universos.</li>
            <li>- Garantia determinística de direção de preço no curto prazo.</li>
          </ul>
          <div className="mt-3 rounded-lg border border-amber-700/40 bg-amber-950/20 p-3 text-xs text-amber-200">
            O Assyntrax é um observador causal de risco estrutural. Não é sistema de recomendação de compra ou venda.
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Notação consolidada</div>
        <h3 className="mt-1 text-lg font-semibold text-zinc-100">Tabela rápida de símbolos</h3>
        <div className="mt-3 overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-zinc-500 uppercase text-xs">
              <tr>
                <th className="text-left py-2">Símbolo</th>
                <th className="text-left py-2">Definição</th>
              </tr>
            </thead>
            <tbody>
              {notationRows.map((row) => (
                <tr key={row.symbol} className="border-t border-zinc-800/70 text-zinc-300">
                  <td className="py-2">
                    <span className="ax-math-inline">{`\\(${row.symbol}\\)`}</span>
                  </td>
                  <td className="py-2">{row.meaning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">11) Referências</div>
        <h3 className="mt-1 text-lg font-semibold text-zinc-100">Base técnica e regulatória principal</h3>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {references.map((ref) => {
            const href = String(ref.href || "").trim();
            return href ? (
              <a
                key={ref.id}
                href={href}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border border-zinc-800 bg-black/30 p-3 hover:border-zinc-600 transition"
              >
                <div className="text-[10px] uppercase tracking-[0.14em] text-zinc-500">{ref.id}</div>
                <div className="mt-1 text-sm text-zinc-200">{ref.title}</div>
              </a>
            ) : (
              <div key={ref.id} className="rounded-xl border border-zinc-800 bg-black/30 p-3">
                <div className="text-[10px] uppercase tracking-[0.14em] text-zinc-500">{ref.id}</div>
                <div className="mt-1 text-sm text-zinc-200">{ref.title}</div>
                <div className="mt-1 text-xs text-zinc-500">Link indisponível.</div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function MathCard({ tex, note }: { tex: string; note: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-black/30 p-4">
      <MathBlock tex={tex} />
      <p className="mt-2 text-xs text-zinc-400">{note}</p>
    </div>
  );
}

function MathBlock({ tex }: { tex: string }) {
  return <div className="ax-math-block">{`\\[${tex}\\]`}</div>;
}
