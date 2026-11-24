import { useState, useCallback, useEffect, useRef } from 'react';
import { ThreeCanvas } from './graphics/ThreeCanvas';
import { NavbarHUD } from './components/NavbarHUD';
import { CinemaTimelineHUD } from './components/CinemaTimelineHUD';
import { WhisperStageHUD } from './components/WhisperStageHUD';
import { WHISPER_ACTS } from './data/whisperActs';
import { DiegeticHotspotLayer } from './components/DiegeticHotspotLayer';
import { SlideOverInspectionSheet } from './components/SlideOverInspectionSheet';
import { SpatialStageControlDock } from './components/SpatialStageControlDock';
import { CaseStudyModal } from './components/CaseStudyModal';
import { PressModal } from './components/PressModal';
import { MagneticCursor } from './components/MagneticCursor';
import { useScrollProgress } from './hooks/useScrollProgress';
import { usePrefersReducedMotion } from './hooks/usePrefersReducedMotion';
import { scrollToSectionCinematic } from './utils/cinematicScroll';
import type { CaseStudy } from './domain/contracts';
import { CASE_STUDIES } from './data/caseStudies';
import { SceneController } from './graphics/SceneController';

const SECTION_IDS = ['hero', 'timeline', 'vault', 'summit', 'ai-solutions', 'contact'] as const;

export default function App() {
  const { scrollProgress, activeSection } = useScrollProgress();
  const [isReducedMotion, toggleReducedMotion] = usePrefersReducedMotion();
  const [selectedCaseStudy, setSelectedCaseStudy] = useState<CaseStudy | null>(null);
  const [isPressModalOpen, setIsPressModalOpen] = useState(false);
  const [controller, setController] = useState<SceneController | null>(null);
  const [isAudioEnabled, setIsAudioEnabled] = useState(false);

  // 4-State Interactive Choreographer UI State
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const [selectedActOverride, setSelectedActOverride] = useState<number | null>(null);
  const [activeSubTargetId, setActiveSubTargetId] = useState<string | null>(null);
  const [pendingNavAct, setPendingNavAct] = useState<number | null>(null);
  const [prevActiveSection, setPrevActiveSection] = useState<string>(activeSection);

  const activeAct =
    WHISPER_ACTS.find((a) => a.sectionId === activeSection) ?? WHISPER_ACTS[0]!;
  const activeActIndexRef = useRef(activeAct.actIndex);
  useEffect(() => {
    activeActIndexRef.current = activeAct.actIndex;
  }, [activeAct.actIndex]);

  // Synchronize sheet chapter & release stale focus when external/manual scrolling crosses acts
  if (activeSection !== prevActiveSection) {
    setPrevActiveSection(activeSection);
    const scrolledActIdx = activeAct.actIndex;
    if (pendingNavAct !== null) {
      if (scrolledActIdx === pendingNavAct) {
        setPendingNavAct(null);
      }
    } else {
      if (selectedActOverride !== null && selectedActOverride !== scrolledActIdx) {
        setSelectedActOverride(null);
      }
      if (activeSubTargetId !== null) {
        const focusedCfg = SceneController.DIORAMA_SUB_TARGETS.find(
          (t) => t.id === activeSubTargetId
        );
        if (!focusedCfg || focusedCfg.actIndex !== scrolledActIdx) {
          setActiveSubTargetId(null);
        }
      }
    }
  }

  useEffect(() => {
    if (activeSubTargetId === null && controller && Boolean(controller.getActiveSubTarget())) {
      controller.clearSubTargetFocus();
    }
  }, [activeSubTargetId, controller]);

  useEffect(() => {
    if (pendingNavAct === null) return;
    const clearPending = () => setPendingNavAct(null);
    const handlePageInterrupt = (e: Event) => {
      const target = e.target;
      if (
        typeof Element !== 'undefined' &&
        target instanceof Element &&
        target.closest('[data-testid="slide-over-inspection-sheet"], [role="dialog"]')
      ) {
        return;
      }
      setPendingNavAct(null);
      if (activeActIndexRef.current !== pendingNavAct) {
        setSelectedActOverride(null);
        setActiveSubTargetId(null);
        controller?.clearSubTargetFocus();
      }
    };
    const timer = setTimeout(clearPending, 1500);
    window.addEventListener('wheel', handlePageInterrupt, { passive: true });
    window.addEventListener('touchstart', handlePageInterrupt, { passive: true });
    return () => {
      clearTimeout(timer);
      window.removeEventListener('wheel', handlePageInterrupt);
      window.removeEventListener('touchstart', handlePageInterrupt);
    };
  }, [pendingNavAct, controller]);

  const currentActIndex =
    selectedActOverride ?? activeAct.actIndex;

  const scrollTo = useCallback(
    (id: string) => {
      scrollToSectionCinematic(id, { reducedMotion: isReducedMotion });
    },
    [isReducedMotion]
  );

  const handleScrubTimelineStart = useCallback(() => {
    setPendingNavAct(null);
    setSelectedActOverride(null);
    setActiveSubTargetId(null);
    if (controller) {
      controller.clearSubTargetFocus();
    }
  }, [controller]);

  const handleNavigateToSection = useCallback(
    (sectionId: string) => {
      setPendingNavAct(null);
      setSelectedActOverride(null);
      setActiveSubTargetId(null);
      if (controller) {
        controller.clearSubTargetFocus();
      }
      scrollTo(sectionId);
    },
    [controller, scrollTo]
  );

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

  const handleSelectSubTarget = useCallback(
    (actIndex: number, subTargetId: string) => {
      setSelectedActOverride(actIndex);
      setActiveSubTargetId(subTargetId);
      setIsSheetOpen(true);
      if (actIndex !== activeAct.actIndex) {
        setPendingNavAct(actIndex);
        const secId = SECTION_IDS[actIndex];
        if (secId) {
          scrollTo(secId);
        }
      } else {
        setPendingNavAct(null);
      }
      if (controller) {
        controller.selectSubTarget(actIndex, subTargetId, { emitCallback: false });
      }
    },
    [activeAct.actIndex, controller, scrollTo]
  );

  const handleCloseSheet = useCallback(() => {
    setIsSheetOpen(false);
    setActiveSubTargetId(null);
    setSelectedActOverride(null);
    setPendingNavAct(null);
    if (controller) {
      controller.clearSubTargetFocus();
    }
  }, [controller]);

  const handleToggleSheet = useCallback(
    (actIndex: number) => {
      if (isSheetOpen) {
        handleCloseSheet();
      } else {
        setSelectedActOverride(actIndex);
        setIsSheetOpen(true);
      }
    },
    [isSheetOpen, handleCloseSheet]
  );

  const handleSelectActInSheet = useCallback(
    (actIndex: number) => {
      const isSameAct = actIndex === activeAct.actIndex;
      setSelectedActOverride(isSameAct ? null : actIndex);
      setActiveSubTargetId(null);
      setPendingNavAct(isSameAct ? null : actIndex);
      if (controller) {
        controller.clearSubTargetFocus();
      }
      const secId = SECTION_IDS[actIndex];
      if (secId) {
        scrollTo(secId);
      }
    },
    [activeAct.actIndex, controller, scrollTo]
  );

  const handleOpenPressModal = useCallback(() => {
    setIsPressModalOpen(true);
  }, []);

  const handleOpenDirectDispatch = useCallback(() => {
    handleSelectSubTarget(5, 'direct-dispatch');
  }, [handleSelectSubTarget]);

  const handleClosePressModal = useCallback(() => {
    setIsPressModalOpen(false);
  }, []);

  const handleCloseCaseStudyModal = useCallback(() => {
    setSelectedCaseStudy(null);
  }, []);

  return (
    <div className="relative min-h-screen bg-[#050507] text-neutral-100 font-sans selection:bg-blue-500/30 selection:text-white">
      {/* Spring-Lerped Magnetic Hardware Cursor */}
      <MagneticCursor accentColor={activeAct.accentColor} isReducedMotion={isReducedMotion} />

      {/* 1. Full-Viewport 3D WebGL Diorama World (>=85% Unobstructed Spatial Sovereignty) */}
      <ThreeCanvas
        scrollProgress={scrollProgress}
        isReducedMotion={isReducedMotion}
        isSheetOpen={isSheetOpen}
        onSelectSummitBeacon={handleOpenPressModal}
        onSelectCaseStudyNode={handleSelectCaseStudyBySlug}
        onSelectSubTarget={handleSelectSubTarget}
        onControllerReady={handleControllerReady}
      />

      {/* 1b. Non-Interactive Anamorphic Lens Vignette & Monograph Film-Grain Finish */}
      <div
        aria-hidden="true"
        className="cinema-vignette fixed inset-0 z-[15] pointer-events-none select-none"
      />
      <div
        aria-hidden="true"
        className="cinema-film-grain fixed inset-0 z-[15] pointer-events-none select-none"
      />

      {/* 2. Top Compact Pill Navigation Bar (6-Act Growth Journey) */}
      <NavbarHUD
        activeSection={activeSection}
        isReducedMotion={isReducedMotion}
        onToggleReducedMotion={toggleReducedMotion}
        isAudioEnabled={isAudioEnabled}
        onToggleAudio={handleToggleAudio}
        onSelectSection={handleNavigateToSection}
      />

      {/* 2b. Director's Cut SMPTE Timecode & Scrubbable Filmstrip Timeline */}
      <CinemaTimelineHUD
        scrollProgress={scrollProgress}
        activeSection={activeSection}
        isReducedMotion={isReducedMotion}
        onSelectChapter={handleNavigateToSection}
        onScrubStart={handleScrubTimelineStart}
      />

      {/* 3. Diegetic 3D Spatial Target Reticles Projected onto Scene Props */}
      <DiegeticHotspotLayer
        activeSection={activeSection}
        activeSubTargetId={activeSubTargetId}
        isSheetOpen={isSheetOpen}
        controller={controller}
        onSelectSubTarget={handleSelectSubTarget}
      />

      {/* 4. Bottom-Left Whisper Narrative HUD & Dual-Trigger Sub-Target Bar */}
      <WhisperStageHUD
        activeSection={activeSection}
        scrollProgress={scrollProgress}
        activeSubTargetId={activeSubTargetId}
        isSheetOpen={isSheetOpen}
        onSelectSubTarget={handleSelectSubTarget}
        onToggleSheet={handleToggleSheet}
        onClearFocus={handleCloseSheet}
      />

      {/* 5. Right-40% Frosted-Glass Slide-Over Inspection Sheet (Opens On Demand) */}
      <SlideOverInspectionSheet
        isOpen={isSheetOpen}
        activeActIndex={currentActIndex}
        activeSubTargetId={activeSubTargetId}
        onClose={handleCloseSheet}
        onSelectAct={handleSelectActInSheet}
        onSelectSubTarget={handleSelectSubTarget}
        onSelectCaseStudy={(study) => setSelectedCaseStudy(study)}
        onInspectPressModal={handleOpenPressModal}
      />

      {/* 6. Optically Transparent 6-Act Spatial Scroll Track (Zero 2D Card Clutter over 3D Stage) */}
      <main
        aria-label="6-Act Spatial Diorama Scroll Continuum"
        className="relative z-10 flex flex-col pointer-events-none select-none"
      >
        {WHISPER_ACTS.map((act) => (
          <section
            key={act.sectionId}
            id={act.sectionId}
            data-testid={`spatial-waypoint-${act.sectionId}`}
            className="min-h-screen w-full bg-transparent pointer-events-none"
          >
            <div className="sr-only">
              <span>{act.actBadge}</span>
              <h2>{act.title}</h2>
              <p>{act.hook}</p>
            </div>
          </section>
        ))}
      </main>

      {/* 7. Bottom-Right Spatial Stage Control Dock (3D Peek & Gesture Trigger) */}
      <SpatialStageControlDock
        activeSection={activeSection}
        controller={controller}
        onOpenDispatch={handleOpenDirectDispatch}
      />

      {/* 8. Deep Inspection Modals */}
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
