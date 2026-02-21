import MotorControlCenter from "@/components/MotorControlCenter";
import SectorDashboard from "@/components/SectorDashboard";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <MotorControlCenter />
      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 md:p-5">
        <div className="mb-4">
          <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Finanças</div>
          <h2 className="mt-1 text-xl font-semibold text-zinc-100">Painel financeiro por ativo</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Bloco complementar do motor com leitura por ativo, grupos e série temporal.
          </p>
        </div>
        <SectorDashboard title="Finanças" showTable initialDomain="finance" />
      </section>
    </div>
  );
}
