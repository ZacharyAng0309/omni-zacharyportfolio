import React, { useState, useRef, useEffect } from 'react';
import { ArrowDown, ExternalLink, Award, Sparkles, UserCheck } from 'lucide-react';
import { ModalInspectionDrawer } from './ModalInspectionDrawer';

export interface HeroSectionProps {
  onExploreCaseStudies?: () => void;
  onExecutiveInquiries?: () => void;
  /** @deprecated Use onExploreCaseStudies */
  onExploreClick?: () => void;
  /** @deprecated Use onExecutiveInquiries */
  onCaseStudiesClick?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onExploreCaseStudies,
  onExecutiveInquiries,
  onExploreClick,
  onCaseStudiesClick,
}) => {
  const [isDossierOpen, setIsDossierOpen] = useState(false);
  const [activePose, setActivePose] = useState<string | null>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const portraitCardRef = useRef<HTMLDivElement>(null);

  const handleCaseStudies = onExploreCaseStudies || onExploreClick || (() => {});
  const handleInquiries = onExecutiveInquiries || onCaseStudiesClick || (() => {});

  const dispatchHeroSceneAction = (
    action = 'glasses_adjust',
    options?: { autoReturn?: boolean; duration?: number }
  ) => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action, source: 'hero', ...options },
        })
      );
    }
  };

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handleSceneAction = (e: Event) => {
      const customEvent = e as CustomEvent<{ action?: string }>;
      const action = customEvent.detail?.action;
      if (action === 'glasses_adjust' || action === 'inspect_tablet' || action === 'keynote_present') {
        setActivePose(action);
      } else if (action === 'reset_pose' || action === 'neutral') {
        setActivePose(null);
      }
    };
    window.addEventListener('portfolio:scene_action', handleSceneAction);
    return () => {
      window.removeEventListener('portfolio:scene_action', handleSceneAction);
    };
  }, []);

  const handlePoseSelect = (pose: string) => {
    if (pose === 'reset_pose') {
      setActivePose(null);
    } else {
      setActivePose(pose);
    }
    dispatchHeroSceneAction(pose);
  };

  const handlePortraitMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!portraitCardRef.current) return;
    const rect = portraitCardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: x * 14, y: -y * 14 });
  };

  const handlePortraitMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
    setIsHovered(false);
  };

  return (
    <section
      id="hero"
      aria-label="Executive Introduction & Product Reveal"
      className="relative min-h-[90vh] sm:min-h-screen flex items-center pt-16 sm:pt-20 lg:pt-16 pb-8 sm:pb-10 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto w-full hero-spotlight"
    >
      <div
        data-peek-hide
        className="w-full flex flex-col lg:grid lg:grid-cols-12 gap-8 lg:gap-12 items-start z-10"
      >
        {/* Block 1 (Desktop Cols 1–7, Row 1): Peak Accolade Eyebrow & Monumental Headline */}
        <div className="lg:col-span-7 lg:col-start-1 lg:row-start-1 flex flex-col items-start text-left space-y-3.5 sm:space-y-4 w-full">
          {/* Peak Accolade Eyebrow Badge */}
          <button
            type="button"
            onClick={() => dispatchHeroSceneAction('pulse_summit')}
            onMouseEnter={() => dispatchHeroSceneAction('pulse_summit')}
            data-cursor="AWARD"
            className="inline-flex items-center gap-2 min-h-[44px] px-3.5 py-1.5 rounded-full bg-white/5 border border-amber-400/30 text-xs sm:text-sm font-medium text-amber-300 backdrop-blur-xl shadow-lg shadow-amber-500/10 hover:border-amber-400/60 hover:bg-amber-400/10 transition-all cursor-pointer"
          >
            <Award className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span className="font-semibold tracking-tight">Global Grand Champion • Hilti IT Competition 2024</span>
          </button>

          {/* Identity & Monumental Headline */}
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs sm:text-sm font-semibold tracking-widest uppercase text-cyan-400 font-mono">
                Ang Zi Yang (Zachary)
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-mono text-cyan-300 tracking-wider">
                PRO PORTFOLIO • ACT 01
              </span>
            </div>
            <h1 className="text-3xl sm:text-5xl md:text-5xl lg:text-6xl font-black tracking-tight leading-[0.98] headline-gradient font-display kinetic-skew">
              Architect of Enterprise Intelligence
            </h1>
            <p className="text-base sm:text-lg md:text-xl font-semibold text-neutral-100 tracking-tight pt-0.5">
              <span>AI Product Strategist &amp; Solutions Architect</span>
              <span className="text-cyan-400 font-normal"> | Soft Space Fintech &amp; Multi-Modal Agentic Systems</span>
            </p>
          </div>
        </div>

        {/* Block 2 (Desktop Cols 8–12, Rows 1–2; Mobile: Surfaced immediately below Headline): 3D Stage Reticle & Kinematics Dock */}
        <div className="lg:col-span-5 lg:col-start-8 lg:row-start-1 lg:row-span-2 w-full flex flex-col items-center lg:items-end justify-start self-start pt-2 lg:pt-0">
          {/* Apple-Grade Frosted Liquid Acrylic Bezel Frame */}
          <div
            ref={portraitCardRef}
            onMouseMove={handlePortraitMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={handlePortraitMouseLeave}
            style={{
              transform: `perspective(1000px) rotateY(${tilt.x}deg) rotateX(${tilt.y}deg)`,
              transition: isHovered ? 'transform 0.1s ease-out' : 'transform 0.5s ease-out',
            }}
            className="relative group w-full max-w-sm sm:max-w-md pointer-events-auto"
          >
            {/* Ambient Multi-Hue Specular Halo */}
            <div
              className="absolute -inset-2 rounded-[2.5rem] bg-gradient-to-tr from-cyan-500/25 via-blue-500/15 to-amber-500/20 blur-2xl opacity-75 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"
              aria-hidden="true"
            />

            {/* Apple-Grade Frosted Liquid Acrylic Bezel (Framing the 3D Stage) */}
            <div className="relative rounded-[2rem] p-3.5 sm:p-4 bg-gradient-to-b from-white/[0.04] to-black/20 border border-white/15 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85)] transition-all duration-500 group-hover:border-cyan-400/40 group-hover:shadow-[0_25px_60px_-10px_rgba(6,182,212,0.25)]">
              {/* Spatial 3D Avatar Viewport Reticle (Transparent Stage Framing Real WebGL Avatar) */}
              <div className="relative rounded-2xl overflow-hidden aspect-[3/4] border border-cyan-500/20 bg-gradient-to-b from-cyan-950/5 via-transparent to-black/30 flex flex-col justify-between p-3 pointer-events-none">
                {/* Top Live Verification Status Pill */}
                <div className="z-10 flex items-center justify-between w-full pointer-events-auto">
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/80 backdrop-blur-md border border-emerald-400/30 text-emerald-300 text-[10px] sm:text-xs font-mono shadow-lg">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
                    <span>🟢 LIVE 3D AVATAR • REAL-TIME WEBGL</span>
                  </div>
                  <span className="px-2.5 py-1 rounded-full bg-black/80 backdrop-blur-md border border-white/15 text-[10px] sm:text-xs font-mono text-cyan-300 shadow-lg">
                    KL • ZURICH
                  </span>
                </div>

                {/* Spatial Reticle HUD Targeting Accents */}
                <div className="relative w-full flex-1 flex items-center justify-center my-3 opacity-30 group-hover:opacity-60 transition-opacity duration-500">
                  <div className="absolute top-0 left-0 w-3.5 h-3.5 border-t border-l border-cyan-400 rounded-tl" />
                  <div className="absolute top-0 right-0 w-3.5 h-3.5 border-t border-r border-cyan-400 rounded-tr" />
                  <div className="absolute bottom-0 left-0 w-3.5 h-3.5 border-b border-l border-cyan-400 rounded-bl" />
                  <div className="absolute bottom-0 right-0 w-3.5 h-3.5 border-b border-r border-cyan-400 rounded-br" />
                  <div className="text-[9px] font-mono tracking-widest text-cyan-300/60 uppercase select-none">
                    [ 3D SPATIAL STAGE ]
                  </div>
                </div>

                {/* Bottom Identity & Accolade Plaque */}
                <div className="z-10 p-3 sm:p-4 rounded-xl bg-slate-950/85 backdrop-blur-xl border border-white/15 space-y-2 text-left pointer-events-auto shadow-2xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm sm:text-base font-bold text-white tracking-tight font-display">
                        Ang Zi Yang (Zachary)
                      </div>
                      <div className="text-[11px] sm:text-xs text-cyan-400 font-medium">
                        AI Product Strategist • Soft Space
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setIsDossierOpen(true)}
                      data-cursor="INSPECT"
                      aria-label="Inspect Zachary Photo Dossier"
                      className="min-h-[44px] px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 border border-white/15 text-[10px] font-mono text-neutral-200 transition-all cursor-pointer flex items-center justify-center gap-1"
                    >
                      <span>Photo Dossier</span>
                      <ExternalLink className="w-3 h-3 text-cyan-400" />
                    </button>
                  </div>

                  <div className="pt-1 flex flex-wrap gap-1.5">
                    <span className="px-2 py-0.5 rounded-md bg-amber-400/10 border border-amber-400/30 text-amber-300 text-[10px] font-mono font-medium">
                      🏆 1st / 53 Teams Worldwide
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-cyan-400/10 border border-cyan-400/30 text-cyan-300 text-[10px] font-mono font-medium">
                      🎓 3.89 CGPA Distinction
                    </span>
                  </div>
                </div>
              </div>

              {/* Spatial 3D Monolith & Enterprise Engine Control Dock */}
              <div className="relative rounded-2xl p-3 sm:p-4 mt-3 bg-slate-950/75 border border-white/15 backdrop-blur-xl shadow-2xl transition-all duration-300 hover:border-cyan-400/40">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-[10px] font-mono tracking-wider whitespace-nowrap">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
                    <span>🟢 ENTERPRISE AI ENGINE • LIVE ARCHITECTURE • ACT 01</span>
                    <span className="sr-only">SPATIAL 3D MONOLITH • ACT 01</span>
                  </div>
                  <span className="text-[10px] font-mono text-neutral-400 flex-shrink-0">
                    TIER 1–3
                  </span>
                </div>

                <div className="text-left space-y-1 mb-2.5">
                  <div className="text-xs font-semibold text-white tracking-tight flex items-center justify-between">
                    <span>Multi-Tiered Production AI &amp; Fintech Core</span>
                  </div>
                  <p className="text-[11px] text-neutral-300 leading-snug">
                    Interactive enterprise AI core featuring frosted physical transmission shield, ISO-20022 clearing ring, and generative neural core.
                  </p>
                </div>

                {/* Action Controls */}
                <div className="flex items-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      dispatchHeroSceneAction('explode_strata');
                      if (typeof window !== 'undefined') {
                        window.dispatchEvent(new CustomEvent('portfolio:explode_strata'));
                      }
                    }}
                    data-cursor="EXPLODE"
                    aria-label="Explode Architecture"
                    className="flex-1 min-h-[44px] flex items-center justify-center px-3 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-[11px] font-semibold text-cyan-200 hover:text-white transition-all cursor-pointer text-center shadow-lg shadow-cyan-500/10 hover:shadow-cyan-500/20"
                  >
                    💥 Explode Architecture
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsDossierOpen(true)}
                    data-cursor="INSPECT"
                    aria-label="Inspect Keynote Dossier"
                    className="flex-1 min-h-[44px] flex items-center justify-center px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-emerald-400/40 text-[11px] font-semibold text-white transition-all cursor-pointer text-center shadow-lg hover:shadow-emerald-500/10"
                  >
                    Executive Dossier ↗
                  </button>
                </div>

                {/* Spatial Avatar Pose Actions Dock */}
                <div className="pt-2.5 mt-2.5 border-t border-white/10 text-left">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-semibold">
                      Spatial Avatar Poses
                    </span>
                    <span className="text-[9px] font-mono text-neutral-400">
                      Live Kinematics
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                    <button
                      type="button"
                      onClick={() => handlePoseSelect('glasses_adjust')}
                      data-cursor="SPECTACLES"
                      aria-label="Glasses Adjust Pose"
                      className={`min-h-[44px] flex items-center justify-center px-2 py-1.5 rounded-lg border text-[10px] font-mono font-medium transition-all cursor-pointer text-center ${
                        activePose === 'glasses_adjust'
                          ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200 shadow-md shadow-cyan-500/20'
                          : 'bg-white/5 border-white/10 text-neutral-300 hover:bg-white/10 hover:text-white hover:border-white/20'
                      }`}
                    >
                      👓 Spectacles
                    </button>
                    <button
                      type="button"
                      onClick={() => handlePoseSelect('inspect_tablet')}
                      data-cursor="TABLET"
                      aria-label="Inspect Tablet Pose"
                      className={`min-h-[44px] flex items-center justify-center px-2 py-1.5 rounded-lg border text-[10px] font-mono font-medium transition-all cursor-pointer text-center ${
                        activePose === 'inspect_tablet'
                          ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200 shadow-md shadow-cyan-500/20'
                          : 'bg-white/5 border-white/10 text-neutral-300 hover:bg-white/10 hover:text-white hover:border-white/20'
                      }`}
                    >
                      📱 Tablet
                    </button>
                    <button
                      type="button"
                      onClick={() => handlePoseSelect('keynote_present')}
                      data-cursor="KEYNOTE"
                      aria-label="Keynote Present Pose"
                      className={`min-h-[44px] flex items-center justify-center px-2 py-1.5 rounded-lg border text-[10px] font-mono font-medium transition-all cursor-pointer text-center ${
                        activePose === 'keynote_present'
                          ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200 shadow-md shadow-cyan-500/20'
                          : 'bg-white/5 border-white/10 text-neutral-300 hover:bg-white/10 hover:text-white hover:border-white/20'
                      }`}
                    >
                      🎯 Keynote
                    </button>
                    <button
                      type="button"
                      onClick={() => handlePoseSelect('reset_pose')}
                      data-cursor="RESET"
                      aria-label="Reset Pose"
                      className="min-h-[44px] flex items-center justify-center px-2 py-1.5 rounded-lg border text-[10px] font-mono font-medium bg-white/5 border-white/10 text-neutral-300 hover:bg-white/10 hover:text-white hover:border-amber-400/40 transition-all cursor-pointer text-center"
                    >
                      ↺ Reset
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Block 3 (Desktop Cols 1–7, Row 2; Mobile: Below 3D Stage Card): Key Domains, Narrative, CTAs & 4-Col Telemetry */}
        <div className="lg:col-span-7 lg:col-start-1 lg:row-start-2 flex flex-col items-start text-left space-y-3.5 sm:space-y-4 w-full">
          {/* Key Domains & Narrative */}
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-white/[0.04] border border-white/10 text-xs sm:text-sm text-neutral-200 font-medium">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
              <span>Enterprise AI Systems • Soft Space Fintech • Vertex AI</span>
            </div>

            <p className="text-xs sm:text-sm text-neutral-300 font-normal leading-relaxed">
              Bridging cutting-edge Generative AI with disciplined product execution and scalable fintech systems. Spearheading mission-critical enterprise AI solutions, from vector embeddings on Google Cloud Vertex AI to zero-defect digital banking architectures.
            </p>
          </div>

          {/* Keynote CTAs (Mobile Stacked / Desktop Inline) */}
          <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-2.5 w-full sm:w-auto pt-1">
            <button
              onClick={() => {
                dispatchHeroSceneAction('warp_perspective');
                handleCaseStudies();
              }}
              data-cursor="JOURNEY"
              aria-label="Explore Case Studies"
              className="w-full sm:w-auto min-h-[44px] flex items-center justify-center gap-2 px-6 py-2.5 rounded-full bg-white text-black text-xs sm:text-sm font-semibold hover:bg-neutral-200 transition-all cursor-pointer shadow-[0_0_24px_rgba(255,255,255,0.2)] hover:scale-105 active:scale-95"
            >
              <span>Begin Growth Journey</span>
              <ArrowDown className="w-4 h-4" />
            </button>

            <button
              onClick={() => {
                dispatchHeroSceneAction('cosmic_pulse');
                handleInquiries();
              }}
              data-cursor="APPROACH"
              aria-label="Executive Inquiries"
              className="w-full sm:w-auto min-h-[44px] flex items-center justify-center gap-2 px-5 py-2.5 rounded-full apple-glass text-white text-xs sm:text-sm font-semibold hover:bg-white/10 transition-all cursor-pointer hover:border-cyan-400/50"
            >
              <span>Interests &amp; Approach</span>
              <ExternalLink className="w-4 h-4 text-cyan-400" />
            </button>

            <button
              onClick={() => {
                dispatchHeroSceneAction('inspect_tome');
                setIsDossierOpen(true);
              }}
              data-cursor="DOSSIER"
              aria-label="Executive Keynote Dossier"
              className="w-full sm:w-auto min-h-[44px] flex items-center justify-center gap-2 px-5 py-2.5 rounded-full apple-glass text-neutral-200 hover:text-white hover:bg-white/10 transition-all cursor-pointer text-xs sm:text-sm font-semibold border border-white/15 hover:border-emerald-400/50"
            >
              <UserCheck className="w-4 h-4 text-emerald-400" />
              <span>Executive Dossier</span>
            </button>
          </div>

          {/* Canonical 4-Column Hardware Benchmark Telemetry Bar */}
          <div className="w-full grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3.5 pt-3 sm:pt-4 text-left">
            <div
              onMouseEnter={() => dispatchHeroSceneAction('pulse_summit')}
              data-cursor="RANK"
              className="glass-acrylic card-sheen p-3 sm:p-4 rounded-2xl border border-white/10 hover:border-amber-400/50 transition-all duration-300"
            >
              <div className="text-[10px] sm:text-xs font-mono text-amber-400 font-semibold mb-0.5">GLOBAL RANK</div>
              <div className="text-xl sm:text-2xl font-black text-white tracking-tight font-display">1st / 53 Teams</div>
              <div className="text-[10px] sm:text-xs text-neutral-400 mt-0.5">Hilti IT Global World Champions</div>
            </div>

            <div
              onMouseEnter={() => dispatchHeroSceneAction('inspect_tome')}
              data-cursor="HONORS"
              className="glass-acrylic card-sheen p-3 sm:p-4 rounded-2xl border border-white/10 hover:border-cyan-400/50 transition-all duration-300"
            >
              <div className="text-[10px] sm:text-xs font-mono text-cyan-400 font-semibold mb-0.5">ACADEMIC HONORS</div>
              <div className="text-xl sm:text-2xl font-black text-white tracking-tight font-display">3.89 CGPA</div>
              <div className="text-[10px] sm:text-xs text-neutral-400 mt-0.5">Top 5% Valedictorian • APU</div>
            </div>

            <div
              onMouseEnter={() => dispatchHeroSceneAction('surge_badges')}
              data-cursor="CLOUD"
              className="glass-acrylic card-sheen p-3 sm:p-4 rounded-2xl border border-white/10 hover:border-indigo-400/50 transition-all duration-300"
            >
              <div className="text-[10px] sm:text-xs font-mono text-indigo-400 font-semibold mb-0.5">CLOUD CREDENTIALS</div>
              <div className="text-xl sm:text-2xl font-black text-white tracking-tight font-display">14 Quests &amp; 7 Badges</div>
              <div className="text-[10px] sm:text-xs text-neutral-400 mt-0.5">Google Cloud &amp; Vertex AI</div>
            </div>

            <div
              onMouseEnter={() => dispatchHeroSceneAction('explode_strata')}
              data-cursor="STABILITY"
              className="glass-acrylic card-sheen p-3 sm:p-4 rounded-2xl border border-white/10 hover:border-emerald-400/50 transition-all duration-300"
            >
              <div className="text-[10px] sm:text-xs font-mono text-emerald-400 font-semibold mb-0.5">PRODUCTION STABILITY</div>
              <div className="text-xl sm:text-2xl font-black text-white tracking-tight font-display">0 Defect UAT</div>
              <div className="text-[10px] sm:text-xs text-neutral-400 mt-0.5">Enterprise Banking Super-App</div>
            </div>
          </div>
        </div>
      </div>

      {/* Relocated Executive Keynote Dossier Drawer */}
      <ModalInspectionDrawer
        isOpen={isDossierOpen}
        onClose={() => setIsDossierOpen(false)}
        title="Executive Keynote Dossier"
        subtitle="Ang Zi Yang (Zachary) • Verified Identity & Executive Credentials"
      >
        <div className="space-y-6">
          <div className="relative group w-full max-w-sm mx-auto">
            <div
              className="absolute -inset-1 rounded-3xl bg-gradient-to-tr from-cyan-500/25 via-blue-500/15 to-indigo-500/25 blur-xl opacity-75 group-hover:opacity-100 transition-opacity duration-500"
              aria-hidden="true"
            />
            <div className="relative rounded-3xl p-3 sm:p-4 apple-glass border border-white/15 shadow-2xl backdrop-blur-2xl">
              <div className="relative rounded-2xl overflow-hidden aspect-[3/4] bg-neutral-900 border border-white/10">
                <img
                  src="/images/reference_portrait.jpg"
                  alt="Ang Zi Yang (Zachary) — AI Product Strategist & Solutions Architect"
                  className="w-full h-full object-cover object-center group-hover:scale-102 transition-transform duration-700 ease-out"
                  loading="eager"
                />
                <div
                  className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent pointer-events-none"
                  aria-hidden="true"
                />
                <div className="absolute bottom-3 left-3 right-3 z-10 px-3 py-2 rounded-xl bg-slate-950/80 backdrop-blur-md border border-white/10 flex items-center justify-between text-xs text-neutral-300">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
                    <span className="font-medium text-white text-[11px] sm:text-xs">Active in Enterprise AI</span>
                  </div>
                  <span className="font-mono text-[10px] sm:text-[11px] text-cyan-400">Zurich • KL</span>
                </div>
              </div>
            </div>
          </div>

          {/* Executive Narrative & Backstory */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2 text-xs text-neutral-300 text-left">
            <div className="font-mono text-cyan-400 font-semibold uppercase tracking-wider text-[11px]">
              Executive Profile &amp; Ethos
            </div>
            <p className="leading-relaxed">
              Product strategist and solutions architect specializing in multi-modal agentic systems, enterprise fintech infrastructure, and Google Cloud Vertex AI. Graduated with First Class Honours Distinction (3.89 / 4.00 CGPA) dual degree from Asia Pacific University (APU) and Staffordshire University (UK).
            </p>
            <p className="leading-relaxed text-neutral-400 pt-1">
              Captained Team Sweetzerland to 1st Place Worldwide at the 13th Hilti IT Competition in Schaan, Liechtenstein, defeating 53 international university teams. Commended by the Hilti Global CIO and featured in <em>The Star</em> national media.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs text-left">
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/10">
              <div className="font-mono text-amber-400 text-[10px] uppercase font-bold">Championship</div>
              <div className="font-bold text-white text-sm mt-0.5">Global 1st Place</div>
              <div className="text-neutral-400 text-[11px]">Hilti ITC 2024 (53 Univs)</div>
            </div>
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/10">
              <div className="font-mono text-cyan-400 text-[10px] uppercase font-bold">Academic Distinction</div>
              <div className="font-bold text-white text-sm mt-0.5">3.89 / 4.00 CGPA</div>
              <div className="text-neutral-400 text-[11px]">APU &amp; Staffordshire UK</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs text-left">
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/10">
              <div className="font-mono text-emerald-400 text-[10px] uppercase font-bold">Fintech Delivery</div>
              <div className="font-bold text-white text-sm mt-0.5">0 Defect UAT</div>
              <div className="text-neutral-400 text-[11px]">Soft Space Super-App</div>
            </div>
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/10">
              <div className="font-mono text-indigo-400 text-[10px] uppercase font-bold">Cloud Mastery</div>
              <div className="font-bold text-white text-sm mt-0.5">14 Quests &amp; 7 Badges</div>
              <div className="text-neutral-400 text-[11px]">Google Cloud &amp; Vertex AI</div>
            </div>
          </div>
        </div>
      </ModalInspectionDrawer>
    </section>
  );
};
