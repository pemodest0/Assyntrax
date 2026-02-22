export type SourceLevel = "A" | "B" | "C";

export type CaseSource = {
  title: string;
  url: string;
  level: SourceLevel;
  type: "primary" | "secondary";
};

export type StoryCase = {
  id: string;
  domain: "finance" | "macro" | "realestate";
  title: string;
  period: string;
  why_matters: string;
  what_happened: string;
  motor_reading: string;
  operational_use: string;
  risk_limit: string;
  image_hint: string;
  sources: CaseSource[];
};

export const STORY_CASES: StoryCase[] = [
  {
    id: "yen-carry-2024",
    domain: "finance",
    title: "Yen carry unwind e explosão de volatilidade",
    period: "2024-08",
    why_matters:
      "Liquidez some rápido em estruturas alavancadas. O risco principal não é direção de preço, é regime de fragilidade.",
    what_happened:
      "A compressão de diferencial de juros entre EUA e Japão força desalavancagem. O VIX salta e a estrutura de opção perde estabilidade.",
    motor_reading:
      "O motor trata como transição de regime com queda de confiança local, aumento de instabilidade e elevação de alertas.",
    operational_use:
      "Uso prático: reduzir exposição bruta, bloquear novos riscos e acionar hedge condicional por regime.",
    risk_limit:
      "Não é previsão de candle. É radar de contexto para controle de risco e de alavancagem.",
    image_hint: "Mesa de risco, tela de volatilidade e fluxo de opção em stress.",
    sources: [
      {
        title: "BIS - Anatomy of the VIX spike in August 2024",
        url: "https://www.bis.org/",
        level: "A",
        type: "primary",
      },
      {
        title: "Euronext - Market quality and volatility shock",
        url: "https://www.euronext.com/",
        level: "A",
        type: "primary",
      },
      {
        title: "Wellington - Yen carry unwind",
        url: "https://www.wellington.com/",
        level: "B",
        type: "secondary",
      },
    ],
  },
  {
    id: "tariff-shock-2025",
    domain: "macro",
    title: "Choque tarifário e quebra de regime de comércio",
    period: "2025-04",
    why_matters:
      "Mudança regulatória abrupta desloca o equilíbrio macro e contamina equities, FX e cadeia global.",
    what_happened:
      "Tarifas amplas elevam incerteza de custo, comprimem margem e aumentam dispersão setorial em poucos dias.",
    motor_reading:
      "Regime sai de estabilidade para transição/instável com persistência maior de alertas e menor qualidade de sinal.",
    operational_use:
      "Uso prático: mover para postura defensiva por domínio, limitar risco direcional e priorizar setores resilientes.",
    risk_limit:
      "Motor não explica geopolítica; ele mede efeito no estado do sistema.",
    image_hint: "Portos, containers e curva de volatilidade em tela única.",
    sources: [
      {
        title: "IMF - Red Sea attacks and global trade disruption",
        url: "https://www.imf.org/",
        level: "A",
        type: "primary",
      },
      {
        title: "Congress - Economic effects and fiscal stress",
        url: "https://www.congress.gov/",
        level: "A",
        type: "primary",
      },
      {
        title: "McKinsey - Supply chain risk pulse 2025",
        url: "https://www.mckinsey.com/",
        level: "B",
        type: "secondary",
      },
    ],
  },
  {
    id: "cre-maturity-wall",
    domain: "realestate",
    title: "Maturity wall no real estate comercial",
    period: "2025-2026",
    why_matters:
      "Crise lenta de refinanciamento causa erosão de capital sem crash único visível.",
    what_happened:
      "Vencimento de dívida em ambiente de juros altos gera bifurcação de crédito e queda de liquidez de ativos.",
    motor_reading:
      "Sinais de transição longa com qualidade heterogênea entre regiões e maior tempo em estado de cautela.",
    operational_use:
      "Uso prático: congelar alocação agressiva, revisar duration e exigir evidência adicional antes de expandir risco.",
    risk_limit:
      "Motor identifica fragilidade de regime; não substitui due diligence de ativo individual.",
    image_hint: "Skyline corporativo com vacância e curva de crédito em stress.",
    sources: [
      {
        title: "Congress - Commercial Real Estate and the Banking Sector",
        url: "https://www.congress.gov/",
        level: "A",
        type: "primary",
      },
      {
        title: "MBA - Commercial/Multifamily Research",
        url: "https://www.mba.org/",
        level: "A",
        type: "primary",
      },
      {
        title: "NAIOP - Challenges facing CRE in 2025",
        url: "https://www.naiop.org/",
        level: "B",
        type: "secondary",
      },
    ],
  },
];

export const DOMAIN_LABELS: Record<StoryCase["domain"], string> = {
  finance: "Finance / Trading",
  macro: "Macro / Operações",
  realestate: "Imobiliário",
};
