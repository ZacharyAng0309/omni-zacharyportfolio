import { useState, useCallback } from 'react';
import { ThreeCanvas } from './graphics/ThreeCanvas';
import { NavbarHUD } from './components/NavbarHUD';
import { HeroSection } from './components/HeroSection';
import { CareerTimelineSection } from './components/CareerTimelineSection';
import { CredentialVaultSection } from './components/CredentialVaultSection';
import { SummitSection } from './components/SummitSection';
import { AISolutionsSection } from './components/AISolutionsSection';
import { ActionCenterSection } from './components/ActionCenterSection';
import { SpatialStageControlDock } from './components/SpatialStageControlDock';
import { CaseStudyModal } from './components/CaseStudyModal';
import { PressModal } from './components/PressModal';
import { MagneticCursor } from './components/MagneticCursor';
import { MarqueeTicker } from './components/MarqueeTicker';
import { useScrollProgress } from './hooks/useScrollProgress';
import { usePrefersReducedMotion } from './hooks/usePrefersReducedMotion';
import type { CaseStudy } from './domain/contracts';
import { CASE_STUDIES } from './data/caseStudies';
import type { SceneController } from './graphics/SceneController';

export default function App() {
  const { scrollProgress, activeSection } = useScrollProgress();
  const [isReducedMotion, toggleReducedMotion] = usePrefersReducedMotion();
  const [selectedCaseStudy, setSelectedCaseStudy] = useState<CaseStudy | null>(null);
  const [isPressModalOpen, setIsPressModalOpen] = useState(false);
  const [controller, setController] = useState<SceneController | null>(null);
  const [isAudioEnabled, setIsAudioEnabled] = useState(false);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleControllerReady = useCallback((sc: SceneController | null) => {
    setController(sc);
  }, []);

  const handleToggleAudio = useCallback(() => {
    if (controller) {
      const nextState = controller.toggleAudio();
      setIsAudioEnabled(nextState);
    }
  }, [controller]);

  const handleSelectCaseStudyBySlug = useCallback((slug: string) => {
    const found = CASE_STUDIES.find(
      (cs) =>
        cs.slug === slug ||
        cs.id === slug ||
        cs.slug.startsWith(slug) ||
        cs.id === `cs-${slug}` ||
        slug.startsWith(cs.slug)
    );
    if (found) {
      setSelectedCaseStudy(found);
    }
  }, []);

  const handleOpenPressModal = useCallback(() => {
    setIsPressModalOpen(true);
  }, []);

  const handleClosePressModal = useCallback(() => {
    setIsPressModalOpen(false);
  }, []);

  const handleCloseCaseStudyModal = useCallback(() => {
    setSelectedCaseStudy(null);
  }, []);

  return (
    <div className="relative min-h-screen bg-[#050507] text-neutral-100 font-sans selection:bg-blue-500/30 selection:text-white">
      {/* Spring-Lerped Magnetic Hardware Cursor */}
      <MagneticCursor />

      {/* 3D WebGL Background Canvas with Direct Raycasting & Interaction */}
      <ThreeCanvas
        scrollProgress={scrollProgress}
        isReducedMotion={isReducedMotion}
        onSelectSummitBeacon={handleOpenPressModal}
        onSelectCaseStudyNode={handleSelectCaseStudyBySlug}
        onControllerReady={handleControllerReady}
      />

      {/* Apple Pro Minimalist Navigation Bar (6-Act Growth Journey) */}
      <NavbarHUD
        activeSection={activeSection}
        isReducedMotion={isReducedMotion}
        onToggleReducedMotion={toggleReducedMotion}
        isAudioEnabled={isAudioEnabled}
        onToggleAudio={handleToggleAudio}
      />

      {/* Main Storyline Narrative Content (Chronological 6-Act Growth Journey) */}
      <main className="relative z-10 flex flex-col">
        {/* Act 1 (#hero): Overview & Executive Strategy Studio */}
        <HeroSection
          onExploreCaseStudies={() => scrollTo('timeline')}
          onExecutiveInquiries={() => scrollTo('contact')}
          onExploreClick={() => scrollTo('timeline')}
          onCaseStudiesClick={() => scrollTo('contact')}
        />

        {/* Global Credentials Infinite Marquee Ribbon */}
        <MarqueeTicker />

        {/* Act 2 (#timeline): Academic Foundations & Career Ascent (The Academy) */}
        <CareerTimelineSection />

        {/* Act 3 (#vault): Cloud Mastery & GDSC Leadership (The Crucible) */}
        <CredentialVaultSection />

        {/* Act 4 (#summit): Global Championship Peak (The Alpine Summit / Hilti) */}
        <SummitSection
          onInspectPressModal={handleOpenPressModal}
        />

        {/* Act 5 (#ai-solutions): Production AI & Enterprise Systems (The Frontier) */}
        <AISolutionsSection
          onSelectCaseStudy={(study) => setSelectedCaseStudy(study)}
        />

        {/* Act 6 (#contact): Beyond the Architecture — Personal Interests & Approach Hub (The Horizon) */}
        <ActionCenterSection />
      </main>

      {/* Floating Spatial Stage Control Dock (3D Peek & Gesture Trigger) */}
      <SpatialStageControlDock
        activeSection={activeSection}
        controller={controller}
      />

      {/* Inspection Modal Drawers */}
      <CaseStudyModal
        caseStudy={selectedCaseStudy}
        onClose={handleCloseCaseStudyModal}
      />

      <PressModal
        isOpen={isPressModalOpen}
        onClose={handleClosePressModal}
      />
    </div>
  );
}
