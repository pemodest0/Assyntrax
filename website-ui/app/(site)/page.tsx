import HeroSection from "@/components/sections/HeroSection";
import ProblemSection from "@/components/sections/ProblemSection";
import HowItWorksSection from "@/components/sections/HowItWorksSection";
import ProductSection from "@/components/sections/ProductSection";
import UseCasesSection from "@/components/sections/UseCasesSection";
import ProofSection from "@/components/sections/ProofSection";
import CTASection from "@/components/sections/CTASection";

export default function HomePage() {
  return (
    <div className="py-12 space-y-24">
      <HeroSection />
      <ProblemSection />
      <HowItWorksSection />
      <ProductSection />
      <UseCasesSection />
      <ProofSection />
      <CTASection />
    </div>
  );
}
