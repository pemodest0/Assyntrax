"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

const steps = [
  {
    title: "1. Abrir o painel cedo",
    text: "Comece pelo bloco de saúde do motor. Se o gate estiver bloqueado, não força leitura.",
  },
  {
    title: "2. Ver o nível do dia",
    text: "Olhe verde, amarelo ou vermelho com risco e confiança. Isso define o tom da sessão.",
  },
  {
    title: "3. Checar setores e ativos",
    text: "Veja onde o risco está concentrado. Compare transição e instabilidade por setor.",
  },
  {
    title: "4. Ajustar exposição",
    text: "Reduza risco quando fragilidade subir. Mantenha posição quando estrutura estiver estável.",
  },
  {
    title: "5. Registrar decisão",
    text: "Salve o porquê da decisão. Isso cria rotina auditável e melhora o processo com o tempo.",
  },
];

const moneyDrivers = [
  {
    title: "Evita perdas grandes",
    text: "O maior ganho vem de cortar dano em fase ruim, não de tentar acertar topo e fundo todo dia.",
    metric: "Foco: proteger capital",
  },
  {
    title: "Reduz erro por impulso",
    text: "Com leitura objetiva de regime, cai o número de decisões no calor do mercado.",
    metric: "Foco: disciplina operacional",
  },
  {
    title: "Ajusta risco mais cedo",
    text: "Quando transição cresce, você muda postura antes de o problema ficar caro.",
    metric: "Foco: timing de cautela",
  },
];

type CaseClass = "confirmado" | "parcial";
type SignalLevel = "forte" | "moderado" | "fraco" | "nao_confirmado";

type LeadSignals = {
  d5: SignalLevel;
  d10: SignalLevel;
  d20: SignalLevel;
};

type FeaturedCase = {
  name: string;
  setup: string;
  use: string;
  outcome: string;
  signals: LeadSignals;
};

type MasterCase = {
  nome: string;
  regiao: string;
  inicio: string;
  pico: string;
  normal: string;
  confianca: number;
  classe: CaseClass;
  categoria: string;
  sinais: LeadSignals;
};

const featuredCases: FeaturedCase[] = [
  {
    name: "Lehman Brothers (2008)",
    setup: "EUA / global | pico 15/09/2008 | confiança 98",
    use: "Quebra do crédito interbancário e choque de liquidez sistêmica.",
    outcome: "Uso do motor: reduzir alavancagem cedo e priorizar proteção de carteira.",
    signals: { d5: "moderado", d10: "forte", d20: "forte" },
  },
  {
    name: "Crise dos Gilts (Reino Unido, 2022)",
    setup: "Reino Unido | pico 28/09/2022 | confiança 97",
    use: "Fundos LDI com chamadas de margem e espiral de liquidação.",
    outcome: "Uso do motor: elevar caixa e reduzir exposição a ativos com risco de venda forçada.",
    signals: { d5: "forte", d10: "forte", d20: "forte" },
  },
  {
    name: "Silicon Valley Bank (2023)",
    setup: "EUA | pico 10/03/2023 | confiança 99",
    use: "Descasamento de duração + corrida digital de depósitos.",
    outcome: "Uso do motor: cortar risco em bancos regionais e reforçar hedge de liquidez.",
    signals: { d5: "moderado", d10: "forte", d20: "forte" },
  },
];

const masterCases: MasterCase[] = [
  {
    nome: "Lehman Brothers",
    regiao: "Global / EUA",
    inicio: "09/08/2007",
    pico: "15/09/2008",
    normal: "30/06/2009",
    confianca: 98,
    classe: "confirmado",
    categoria: "Bancário e crédito",
    sinais: { d5: "moderado", d10: "forte", d20: "forte" },
  },
  {
    nome: "Downgrade EUA",
    regiao: "EUA / Global",
    inicio: "25/07/2011",
    pico: "05/08/2011",
    normal: "15/01/2012",
    confianca: 95,
    classe: "confirmado",
    categoria: "Soberano",
    sinais: { d5: "moderado", d10: "forte", d20: "forte" },
  },
  {
    nome: "Crash China",
    regiao: "China",
    inicio: "12/06/2015",
    pico: "24/08/2015",
    normal: "01/02/2016",
    confianca: 92,
    classe: "parcial",
    categoria: "Ações e alavancagem",
    sinais: { d5: "fraco", d10: "moderado", d20: "moderado" },
  },
  {
    nome: "Joesley Day",
    regiao: "Brasil",
    inicio: "17/05/2017",
    pico: "18/05/2017",
    normal: "30/06/2017",
    confianca: 90,
    classe: "parcial",
    categoria: "Choque político",
    sinais: { d5: "nao_confirmado", d10: "nao_confirmado", d20: "fraco" },
  },
  {
    nome: "Crise Peso Argentino",
    regiao: "Argentina",
    inicio: "01/05/2018",
    pico: "30/08/2018",
    normal: "31/12/2019",
    confianca: 88,
    classe: "confirmado",
    categoria: "Cambial e soberano",
    sinais: { d5: "moderado", d10: "moderado", d20: "forte" },
  },
  {
    nome: "Greve Caminhoneiros",
    regiao: "Brasil",
    inicio: "21/05/2018",
    pico: "28/05/2018",
    normal: "10/06/2018",
    confianca: 85,
    classe: "parcial",
    categoria: "Oferta e logística",
    sinais: { d5: "nao_confirmado", d10: "fraco", d20: "fraco" },
  },
  {
    nome: "Crise Lira Turca",
    regiao: "Turquia",
    inicio: "18/11/2021",
    pico: "23/11/2021",
    normal: "31/12/2021",
    confianca: 90,
    classe: "confirmado",
    categoria: "Cambial e política monetária",
    sinais: { d5: "moderado", d10: "forte", d20: "forte" },
  },
  {
    nome: "Squeeze do Níquel (LME)",
    regiao: "Reino Unido",
    inicio: "24/02/2022",
    pico: "08/03/2022",
    normal: "16/03/2022",
    confianca: 96,
    classe: "confirmado",
    categoria: "Commodities e margem",
    sinais: { d5: "forte", d10: "forte", d20: "forte" },
  },
  {
    nome: "Crise dos Gilts (LDI)",
    regiao: "Reino Unido",
    inicio: "23/09/2022",
    pico: "28/09/2022",
    normal: "14/10/2022",
    confianca: 97,
    classe: "confirmado",
    categoria: "Soberano e fundos",
    sinais: { d5: "forte", d10: "forte", d20: "forte" },
  },
  {
    nome: "Americanas",
    regiao: "Brasil",
    inicio: "11/01/2023",
    pico: "19/01/2023",
    normal: "31/03/2023",
    confianca: 88,
    classe: "parcial",
    categoria: "Fraude e crédito privado",
    sinais: { d5: "nao_confirmado", d10: "nao_confirmado", d20: "fraco" },
  },
  {
    nome: "Silicon Valley Bank",
    regiao: "EUA",
    inicio: "08/03/2023",
    pico: "10/03/2023",
    normal: "13/03/2023",
    confianca: 99,
    classe: "confirmado",
    categoria: "Bancário e liquidez",
    sinais: { d5: "moderado", d10: "forte", d20: "forte" },
  },
  {
    nome: "Unwind Yen Carry Trade",
    regiao: "Global / Japão",
    inicio: "31/07/2024",
    pico: "05/08/2024",
    normal: "20/08/2024",
    confianca: 95,
    classe: "confirmado",
    categoria: "Câmbio e alavancagem",
    sinais: { d5: "moderado", d10: "forte", d20: "forte" },
  },
  {
    nome: "Estresse Fiscal Brasil",
    regiao: "Brasil",
    inicio: "01/01/2025",
    pico: "em andamento",
    normal: "em aberto",
    confianca: 80,
    classe: "parcial",
    categoria: "Fiscal e juros longos",
    sinais: { d5: "fraco", d10: "fraco", d20: "moderado" },
  },
];

const limitsTruths = [
  "O motor não prevê data exata de quebra.",
  "Choque totalmente exógeno pode vir sem aviso prévio forte.",
  "Em mercado com trava de liquidez, sair pode ser difícil mesmo com sinal correto.",
  "Fraude contábil é difícil de capturar antes do fato público.",
];

const notConfirmed = [
  "Sinal prévio de 5-20 dias no Joesley Day (choque investigativo).",
  "Sinal prévio de 5-20 dias no caso Americanas (fraude).",
  "Parte dos indicadores granulares de CDS no crash da China.",
];

const sourceLinks = [
  { label: "FDIC (crises bancárias)", href: "https://www.fdic.gov/" },
  { label: "BIS (estabilidade global)", href: "https://www.bis.org/" },
  { label: "IMF (staff reports)", href: "https://www.imf.org/" },
  { label: "Bank of England (crise dos gilts)", href: "https://www.bankofengland.co.uk/" },
  { label: "Federal Reserve (SVB review)", href: "https://www.federalreserve.gov/" },
  { label: "Banco Central do Brasil", href: "https://www.bcb.gov.br/" },
];

const signalMeta: Record<SignalLevel, { label: string; className: string }> = {
  forte: {
    label: "Forte",
    className: "text-emerald-200 border-emerald-700/50 bg-emerald-950/30",
  },
  moderado: {
    label: "Moderado",
    className: "text-cyan-200 border-cyan-700/50 bg-cyan-950/30",
  },
  fraco: {
    label: "Fraco",
    className: "text-amber-200 border-amber-700/50 bg-amber-950/30",
  },
  nao_confirmado: {
    label: "Não confirmado",
    className: "text-zinc-300 border-zinc-700/70 bg-zinc-900/40",
  },
};

function parseBrDate(raw: string): Date | null {
  if (!/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) {
    return null;
  }
  const [day, month, year] = raw.split("/").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function getTimelineTime(item: MasterCase): number {
  const date = parseBrDate(item.pico) ?? parseBrDate(item.inicio);
  return date ? date.getTime() : Number.MAX_SAFE_INTEGER;
}

function resolveRegionBucket(region: string): "brasil" | "global" | "internacional" {
  const low = region.toLowerCase();
  if (low.includes("brasil")) return "brasil";
  if (low.includes("global")) return "global";
  return "internacional";
}

export default function AplicacoesPage() {
  const [search, setSearch] = useState("");
  const [regionFilter, setRegionFilter] = useState<"todos" | "brasil" | "global" | "internacional">("todos");
  const [statusFilter, setStatusFilter] = useState<"todos" | CaseClass>("todos");
  const [minConfidence, setMinConfidence] = useState<number>(0);

  const filteredCases = useMemo(() => {
    const query = search.trim().toLowerCase();
    return masterCases
      .filter((row) => {
        if (statusFilter !== "todos" && row.classe !== statusFilter) return false;
        if (regionFilter !== "todos" && resolveRegionBucket(row.regiao) !== regionFilter) return false;
        if (row.confianca < minConfidence) return false;
        if (!query) return true;
        return (
          row.nome.toLowerCase().includes(query) ||
          row.regiao.toLowerCase().includes(query) ||
          row.categoria.toLowerCase().includes(query)
        );
      })
      .sort((a, b) => {
        const aTime = getTimelineTime(a);
        const bTime = getTimelineTime(b);
        if (aTime !== bTime) return aTime - bTime;
        return b.confianca - a.confianca;
      });
  }, [minConfidence, regionFilter, search, statusFilter]);

  const timelineCases = filteredCases.slice(0, 13);

  return (
    <div className="p-4 md:p-6 space-y-6">
      <section className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5 md:p-6">
        <div className="pointer-events-none absolute -left-16 top-4 h-52 w-52 rounded-full bg-emerald-500/15 blur-3xl animate-glow" />
        <div className="pointer-events-none absolute -right-20 bottom-0 h-56 w-56 rounded-full bg-cyan-500/10 blur-3xl animate-glow" />
        <div className="relative z-10 grid grid-cols-1 xl:grid-cols-[1.05fr_0.95fr] gap-5 items-center">
          <div>
            <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Aplicações no dia a dia</div>
            <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-zinc-100">
              Como usar o motor para proteger capital e crescer com mais controle
            </h1>
            <p className="mt-3 text-sm text-zinc-300 max-w-2xl">
              Aqui é uso real: rotina simples, leitura clara e decisão disciplinada. Sem promessa mágica.
              O ganho vem de reduzir erro e cortar dano quando o mercado muda de estrutura.
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <Link href="/app/dashboard" className="rounded-md border border-emerald-700/60 bg-emerald-950/30 px-3 py-2 text-emerald-200 hover:border-emerald-500 transition">
                Abrir painel agora
              </Link>
              <Link href="/app/venda" className="rounded-md border border-zinc-700 px-3 py-2 text-zinc-100 hover:border-zinc-500 transition">
                Ver proposta comercial
              </Link>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-black/30 p-4">
            <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Efeito acumulado</div>
            <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
              <svg viewBox="0 0 560 220" className="w-full h-[190px]">
                <defs>
                  <linearGradient id="moneyLine" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#34d399" />
                    <stop offset="100%" stopColor="#22d3ee" />
                  </linearGradient>
                </defs>
                <rect x="0" y="0" width="560" height="220" rx="14" fill="rgba(9,12,19,0.9)" />
                <line x1="36" y1="184" x2="528" y2="184" stroke="rgba(120,130,150,0.5)" />
                <line x1="36" y1="184" x2="36" y2="26" stroke="rgba(120,130,150,0.5)" />
                <path
                  d="M36 178 C 90 175, 102 168, 140 154 C 180 140, 208 150, 250 128 C 282 111, 310 114, 348 92 C 380 74, 416 82, 454 58 C 482 44, 500 48, 528 30"
                  fill="none"
                  stroke="url(#moneyLine)"
                  strokeWidth="5"
                  strokeLinecap="round"
                  className="ax-money-line"
                />
                <g className="ax-coin-float">
                  <circle cx="140" cy="154" r="6" fill="#34d399" />
                  <circle cx="250" cy="128" r="6" fill="#34d399" />
                  <circle cx="348" cy="92" r="6" fill="#22d3ee" />
                  <circle cx="454" cy="58" r="6" fill="#22d3ee" />
                  <circle cx="528" cy="30" r="7" fill="#f59e0b" />
                </g>
                <text x="42" y="24" fontSize="11" fill="rgba(180,190,210,0.9)">capital</text>
                <text x="500" y="200" fontSize="11" fill="rgba(180,190,210,0.9)">tempo</text>
              </svg>
            </div>
            <div className="mt-2 text-xs text-zinc-400">
              Crescimento saudável = menos drawdown + mais consistência de processo.
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Passo a passo</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Como usar o motor em 5 passos simples</h2>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
          {steps.map((step, idx) => (
            <article key={step.title} className="rounded-xl border border-zinc-800 bg-black/30 p-3 transition hover:border-zinc-600">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-cyan-700/70 bg-cyan-950/40 text-[11px] text-cyan-200">
                  {idx + 1}
                </span>
                <h3 className="text-sm font-medium text-zinc-100">{step.title}</h3>
              </div>
              <p className="mt-2 text-xs text-zinc-400 leading-relaxed">{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Como isso gera dinheiro</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Três fontes reais de valor</h2>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          {moneyDrivers.map((card) => (
            <article key={card.title} className="relative overflow-hidden rounded-xl border border-zinc-800 bg-black/30 p-4">
              <div className="pointer-events-none absolute -right-7 -top-6 h-16 w-16 rounded-full bg-emerald-500/10 blur-2xl" />
              <div className="text-sm font-semibold text-zinc-100">{card.title}</div>
              <p className="mt-2 text-xs text-zinc-400 leading-relaxed">{card.text}</p>
              <div className="mt-3 text-[11px] text-emerald-300">{card.metric}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Estudos de caso</div>
        <h2 className="mt-1 text-xl font-semibold text-zinc-100">Casos ilustrativos para reunião e demo</h2>
        <p className="mt-2 text-xs text-zinc-400">
          Casos abaixo baseados no seu relatório. Onde o estudo indicou baixa confirmação, deixamos marcado como parcial.
        </p>
        <div className="mt-4 space-y-3">
          {featuredCases.map((item) => (
            <article key={item.name} className="rounded-xl border border-zinc-800 bg-black/30 p-4">
              <h3 className="text-sm font-semibold text-zinc-100">{item.name}</h3>
              <div className="mt-2 grid grid-cols-1 lg:grid-cols-3 gap-3 text-xs">
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <div className="text-zinc-500 uppercase tracking-[0.12em] text-[10px]">Contexto</div>
                  <p className="mt-1 text-zinc-300">{item.setup}</p>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <div className="text-zinc-500 uppercase tracking-[0.12em] text-[10px]">Uso do motor</div>
                  <p className="mt-1 text-zinc-300">{item.use}</p>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <div className="text-zinc-500 uppercase tracking-[0.12em] text-[10px]">Resultado</div>
                  <p className="mt-1 text-zinc-300">{item.outcome}</p>
                </div>
              </div>
              <div className="mt-3">
                <div className="text-zinc-500 uppercase tracking-[0.12em] text-[10px]">Sinal prévio observado</div>
                <div className="mt-2 grid grid-cols-3 gap-2">
                  {(
                    [
                      { label: "5 dias", value: item.signals.d5 },
                      { label: "10 dias", value: item.signals.d10 },
                      { label: "20 dias", value: item.signals.d20 },
                    ] as const
                  ).map((signal) => (
                    <div key={signal.label} className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">
                      <div className="text-[10px] uppercase tracking-[0.12em] text-zinc-500">{signal.label}</div>
                      <span
                        className={`mt-1 inline-flex rounded-md border px-2 py-0.5 text-[11px] ${signalMeta[signal.value].className}`}
                      >
                        {signalMeta[signal.value].label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </div>
        <div className="mt-4 rounded-xl border border-zinc-800 bg-black/30 p-3">
          <div className="text-xs uppercase tracking-[0.12em] text-zinc-500 mb-2">Tabela mestre filtrável</div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2">
            <label className="text-xs text-zinc-300">
              Buscar caso
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Lehman, Brasil, bancário..."
                className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950/60 px-2 py-1.5 text-xs text-zinc-100 outline-none focus:border-cyan-500"
              />
            </label>
            <label className="text-xs text-zinc-300">
              Região
              <select
                value={regionFilter}
                onChange={(event) =>
                  setRegionFilter(event.target.value as "todos" | "brasil" | "global" | "internacional")
                }
                className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950/60 px-2 py-1.5 text-xs text-zinc-100 outline-none focus:border-cyan-500"
              >
                <option value="todos">Todas</option>
                <option value="brasil">Brasil</option>
                <option value="internacional">Internacional</option>
                <option value="global">Global</option>
              </select>
            </label>
            <label className="text-xs text-zinc-300">
              Status
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as "todos" | CaseClass)}
                className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950/60 px-2 py-1.5 text-xs text-zinc-100 outline-none focus:border-cyan-500"
              >
                <option value="todos">Todos</option>
                <option value="confirmado">Confirmado</option>
                <option value="parcial">Parcial</option>
              </select>
            </label>
            <label className="text-xs text-zinc-300">
              Confiança mínima
              <select
                value={minConfidence}
                onChange={(event) => setMinConfidence(Number(event.target.value))}
                className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950/60 px-2 py-1.5 text-xs text-zinc-100 outline-none focus:border-cyan-500"
              >
                <option value={0}>Sem corte</option>
                <option value={85}>85+</option>
                <option value={90}>90+</option>
                <option value={95}>95+</option>
              </select>
            </label>
          </div>
          <div className="mt-2 text-xs text-zinc-400">
            {filteredCases.length} casos encontrados.
          </div>
          <div className="mt-3 overflow-auto">
            <table className="w-full text-xs">
              <thead className="text-zinc-500 uppercase">
                <tr>
                  <th className="text-left py-2">Caso</th>
                  <th className="text-left py-2">Região</th>
                  <th className="text-left py-2">Categoria</th>
                  <th className="text-left py-2">Início</th>
                  <th className="text-left py-2">Pico</th>
                  <th className="text-left py-2">Normalização</th>
                  <th className="text-left py-2">Confiança</th>
                  <th className="text-left py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredCases.map((row) => (
                  <tr key={row.nome} className="border-t border-zinc-800/70 text-zinc-300">
                    <td className="py-2">{row.nome}</td>
                    <td className="py-2">{row.regiao}</td>
                    <td className="py-2">{row.categoria}</td>
                    <td className="py-2">{row.inicio}</td>
                    <td className="py-2">{row.pico}</td>
                    <td className="py-2">{row.normal}</td>
                    <td className="py-2">{row.confianca}</td>
                    <td className="py-2">
                      <span
                        className={`rounded-md border px-2 py-0.5 text-[11px] ${
                          row.classe === "confirmado"
                            ? "text-emerald-200 border-emerald-700/50 bg-emerald-950/30"
                            : "text-amber-200 border-amber-700/50 bg-amber-950/30"
                        }`}
                      >
                        {row.classe}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-4 rounded-xl border border-zinc-800 bg-black/30 p-3">
          <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Timeline animada (2008-2026)</div>
          <p className="mt-1 text-xs text-zinc-400">
            Linha do tempo com cor por status e leitura de sinal em 5/10/20 dias antes do pico.
          </p>
          <div className="mt-3 relative pl-6">
            <div className="absolute left-[11px] top-0 bottom-0 w-px bg-zinc-800" />
            <div className="space-y-4">
              {timelineCases.map((item, index) => (
                <article key={`${item.nome}-${item.inicio}`} className="relative rounded-lg border border-zinc-800/80 bg-zinc-950/40 p-3">
                  <span
                    className={`absolute -left-5 top-4 inline-flex h-3 w-3 rounded-full border animate-pulse ${
                      item.classe === "confirmado"
                        ? "border-emerald-400 bg-emerald-500/70"
                        : "border-amber-400 bg-amber-500/70"
                    }`}
                    style={{ animationDelay: `${index * 120}ms` }}
                  />
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[11px] text-zinc-500">{item.inicio} -&gt; {item.pico}</span>
                    <span className="rounded-md border border-zinc-700 bg-zinc-900/40 px-2 py-0.5 text-[11px] text-zinc-300">
                      {item.categoria}
                    </span>
                    <span
                      className={`rounded-md border px-2 py-0.5 text-[11px] ${
                        item.classe === "confirmado"
                          ? "text-emerald-200 border-emerald-700/50 bg-emerald-950/30"
                          : "text-amber-200 border-amber-700/50 bg-amber-950/30"
                      }`}
                    >
                      {item.classe}
                    </span>
                  </div>
                  <div className="mt-1 text-sm text-zinc-100">{item.nome}</div>
                  <div className="text-xs text-zinc-400">{item.regiao}</div>
                  <div className="mt-2 grid grid-cols-3 gap-2">
                    {(
                      [
                        { label: "5 dias", value: item.sinais.d5 },
                        { label: "10 dias", value: item.sinais.d10 },
                        { label: "20 dias", value: item.sinais.d20 },
                      ] as const
                    ).map((signal) => (
                      <div key={signal.label} className="rounded-md border border-zinc-800 bg-zinc-950/50 p-2">
                        <div className="text-[10px] uppercase tracking-[0.12em] text-zinc-500">{signal.label}</div>
                        <span
                          className={`mt-1 inline-flex rounded-md border px-2 py-0.5 text-[11px] ${signalMeta[signal.value].className}`}
                        >
                          {signalMeta[signal.value].label}
                        </span>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div className="rounded-xl border border-zinc-800 bg-black/30 p-3">
            <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Verdades e limites</div>
            <ul className="mt-2 space-y-1 text-xs text-zinc-300">
              {limitsTruths.map((item) => (
                <li key={item}>- {item}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-black/30 p-3">
            <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Itens não confirmados</div>
            <ul className="mt-2 space-y-1 text-xs text-zinc-300">
              {notConfirmed.map((item) => (
                <li key={item}>- {item}</li>
              ))}
            </ul>
          </div>
        </div>
        <div className="mt-4 rounded-xl border border-zinc-800 bg-black/30 p-3">
          <div className="text-xs uppercase tracking-[0.12em] text-zinc-500">Fontes prioritárias</div>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {sourceLinks.map((src) => (
              <a
                key={src.href}
                href={src.href}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-zinc-700 px-2 py-1 text-zinc-200 hover:border-zinc-500"
              >
                {src.label}
              </a>
            ))}
          </div>
        </div>
        <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-950/40 p-3 text-xs text-zinc-400">
          Sem promessa de retorno. O motor é suporte de risco e governança, não recomendação automática de compra ou venda.
        </div>
      </section>
    </div>
  );
}
