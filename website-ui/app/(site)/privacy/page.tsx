import type { Metadata } from "next";
import { buildPageMetadata } from "@/lib/site/metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Política de Privacidade",
  description:
    "Como a Assyntrax coleta, usa e protege dados em formulários, API e navegação do site.",
  path: "/privacy",
  locale: "pt-BR",
});

export default function PrivacyPage() {
  return (
    <div className="space-y-8">
      <section className="rounded-[28px] border border-zinc-800 bg-zinc-950/60 p-8 lg:p-10">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-400">Privacidade</div>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">Política de Privacidade</h1>
        <p className="mt-3 max-w-3xl text-zinc-300">
          Esta política explica como tratamos dados pessoais e dados técnicos no site e no produto.
          Se tiver dúvida, fale com a equipe em <a className="underline" href="mailto:contact@assyntrax.ai">contact@assyntrax.ai</a>.
        </p>
        <p className="mt-2 text-xs text-zinc-500">Última atualização: 20 de fevereiro de 2026.</p>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="1. Controlador dos dados">
          Assyntrax (motor de diagnóstico de regime). Contato oficial: contact@assyntrax.ai.
        </Card>
        <Card title="2. Dados que coletamos">
          Dados de contato enviados por formulário (nome, email, empresa, mensagem) e dados técnicos
          de uso do site (logs de acesso e diagnóstico de erro).
        </Card>
        <Card title="3. Finalidade do uso">
          Responder pedidos comerciais e técnicos, agendar demonstrações, dar suporte, proteger o ambiente
          e melhorar estabilidade do produto.
        </Card>
        <Card title="4. Base legal">
          Execução de medidas pré-contratuais, interesse legítimo para segurança e operação, e consentimento
          quando aplicável.
        </Card>
        <Card title="5. Compartilhamento">
          Não vendemos dados pessoais. Podemos usar fornecedores técnicos para hospedagem, monitoramento e
          entrega de notificações, sempre com obrigação de segurança e confidencialidade.
        </Card>
        <Card title="6. Retenção">
          Dados de contato ficam pelo tempo necessário para atendimento e histórico comercial.
          Logs técnicos seguem janela operacional e política interna de auditoria.
        </Card>
        <Card title="7. Direitos do titular">
          Você pode pedir acesso, correção, exclusão ou limitação do tratamento dos seus dados.
          Envie o pedido para contact@assyntrax.ai.
        </Card>
        <Card title="8. Cookies e analytics">
          O site pode usar cookies técnicos para funcionamento e analytics para medição agregada de uso.
          Se novos cookies forem habilitados, esta página será atualizada.
        </Card>
        <Card title="9. Segurança">
          Aplicamos controles razoáveis para reduzir risco de acesso indevido, perda e alteração de dados.
          Nenhum sistema é 100% imune, mas revisamos rotina e configurações periodicamente.
        </Card>
        <Card title="10. Transferência internacional">
          Dependendo da infraestrutura, dados podem ser processados fora do país de origem.
          Quando isso ocorre, adotamos medidas contratuais e técnicas de proteção.
        </Card>
      </section>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6">
      <h2 className="text-lg font-semibold text-zinc-100">{title}</h2>
      <p className="mt-3 text-sm leading-relaxed text-zinc-300">{children}</p>
    </article>
  );
}
