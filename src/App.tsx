import { useState } from 'react';
import { ThreeCanvas } from './graphics/ThreeCanvas';
import { NavbarHUD } from './components/NavbarHUD';
import { HeroSection } from './components/HeroSection';
import { SummitSection } from './components/SummitSection';
import { AISolutionsSection } from './components/AISolutionsSection';
import { CredentialVaultSection } from './components/CredentialVaultSection';
import { CareerTimelineSection } from './components/CareerTimelineSection';
import { ActionCenterSection } from './components/ActionCenterSection';
import { CaseStudyModal } from './components/CaseStudyModal';
import { PressModal } from './components/PressModal';
import { useScrollProgress } from './hooks/useScrollProgress';
import { usePrefersReducedMotion } from './hooks/usePrefersReducedMotion';
import type { CaseStudy } from './domain/contracts';
import { CASE_STUDIES } from './data/caseStudies';
import { Sparkles } from 'lucide-react';

export default function App() {
  const { scrollProgress, activeSection } = useScrollProgress();
  const [isReducedMotion, toggleReducedMotion] = usePrefersReducedMotion();
  const [selectedCaseStudy, setSelectedCaseStudy] = useState<CaseStudy | null>(null);
  const [isPressModalOpen, setIsPressModalOpen] = useState(false);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleSelectCaseStudyBySlug = (slug: string) => {
    const found = CASE_STUDIES.find((cs) => cs.slug === slug);
    if (found) {
      setSelectedCaseStudy(found);
    }
  };

  return (
    <div className="relative min-h-screen bg-black text-neutral-100 font-sans selection:bg-blue-500/30 selection:text-white">
      {/* 3D WebGL Background Canvas with Direct Raycasting & Interaction */}
      <ThreeCanvas
        scrollProgress={scrollProgress}
        isReducedMotion={isReducedMotion}
        onSelectSummitBeacon={() => setIsPressModalOpen(true)}
        onSelectCaseStudyNode={handleSelectCaseStudyBySlug}
      />

      {/* Apple Pro Minimalist Navigation Bar */}
      <NavbarHUD
        activeSection={activeSection}
        isReducedMotion={isReducedMotion}
        onToggleReducedMotion={toggleReducedMotion}
      />

      {/* Floating 3D Interactivity HUD Pill */}
      <aside
        aria-label="3D Interaction Guidance"
        className="fixed bottom-5 left-5 z-20 pointer-events-none hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-full apple-glass text-[11px] font-mono text-neutral-300 shadow-xl backdrop-blur-xl"
      >
        <Sparkles className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
        <span>3D Engine: Drag canvas to rotate • Click glowing beacons & nodes</span>
      </aside>

      {/* Main Storyline Narrative Content (Composited HUD Layer) */}
      <main className="relative z-10 flex flex-col pointer-events-none">
        {/* Section 0: Hero & Identity */}
        <div className="pointer-events-auto">
          <HeroSection
            onExploreClick={() => scrollTo('summit')}
            onCaseStudiesClick={() => scrollTo('ai-solutions')}
          />
        </div>

        {/* Section 1: The Summit & Global Championship */}
        <div className="pointer-events-auto">
          <SummitSection
            onInspectPressModal={() => setIsPressModalOpen(true)}
          />
        </div>

        {/* Section 2: AI Solutions & Architecture */}
        <div className="pointer-events-auto">
          <AISolutionsSection
            onSelectCaseStudy={(study) => setSelectedCaseStudy(study)}
          />
        </div>

        {/* Section 3: Credential Vault */}
        <div className="pointer-events-auto">
          <CredentialVaultSection />
        </div>

        {/* Section 4: Calibrated Career Timeline */}
        <div className="pointer-events-auto">
          <CareerTimelineSection />
        </div>

        {/* Section 5: Action Center & Direct Collaboration */}
        <div className="pointer-events-auto">
          <ActionCenterSection />
        </div>
      </main>

      {/* Inspection Modal Drawers */}
      <CaseStudyModal
        caseStudy={selectedCaseStudy}
        onClose={() => setSelectedCaseStudy(null)}
      />

      <PressModal
        isOpen={isPressModalOpen}
        onClose={() => setIsPressModalOpen(false)}
      />
    </div>
  );
}
