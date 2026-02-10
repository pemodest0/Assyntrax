import HeroSection from "@/components/sections/HeroSection";
import ProblemSection from "@/components/sections/ProblemSection";
import HowItWorksSection from "@/components/sections/HowItWorksSection";
import ProductSection from "@/components/sections/ProductSection";
import UseCasesSection from "@/components/sections/UseCasesSection";
import ProofSection from "@/components/sections/ProofSection";
import CTASection from "@/components/sections/CTASection";

export default function HomePage() {
  return (
    <div className="py-10 md:py-12 lg:py-14 xl:py-16">
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
