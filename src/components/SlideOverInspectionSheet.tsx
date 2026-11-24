import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Trophy,
  BookOpen,
  Award,
  Layers,
  Compass,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Mail,
  Copy,
  Check,
  Send,
  CheckCircle2,
} from 'lucide-react';
import type { CaseStudy } from '../domain/contracts';
import { TIMELINE_MILESTONES } from '../data/timeline';
import { CREDENTIALS } from '../data/credentials';
import { PRESS_CITES } from '../data/pressCites';
import { CASE_STUDIES } from '../data/caseStudies';
import { PERSONAL_INTEREST_LENSES, type PersonalInterestLens } from '../data/personalInterestLenses';
import { WHISPER_ACTS } from '../data/whisperActs';
import { SceneController } from '../graphics/SceneController';

export interface SlideOverInspectionSheetProps {
  isOpen: boolean;
  activeActIndex: number;
  activeSubTargetId: string | null;
  onClose: () => void;
  onSelectAct: (actIndex: number) => void;
  onSelectSubTarget: (actIndex: number, subTargetId: string) => void;
  onSelectCaseStudy: (study: CaseStudy) => void;
  onInspectPressModal: () => void;
}

const CHAPTER_TABS = [
  { actIndex: 0, code: '01', label: 'Atelier' },
  { actIndex: 1, code: '02', label: 'Academy' },
  { actIndex: 2, code: '03', label: 'Crucible' },
  { actIndex: 3, code: '04', label: 'Summit' },
  { actIndex: 4, code: '05', label: 'Frontier' },
  { actIndex: 5, code: '06', label: 'Horizon' },
] as const;

export const SlideOverInspectionSheet: React.FC<SlideOverInspectionSheetProps> = ({
  isOpen,
  activeActIndex,
  activeSubTargetId,
  onClose,
  onSelectAct,
  onSelectSubTarget,
  onSelectCaseStudy,
  onInspectPressModal,
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [credentialFilter, setCredentialFilter] = useState<
    'all' | 'cloud-ai' | 'product-ba' | 'global-wins'
  >('all');
  const [openPressId, setOpenPressId] = useState<string>(PRESS_CITES[0]?.id ?? 'cite-the-star');
  const [selectedLensId, setSelectedLensId] = useState<string>(
    PERSONAL_INTEREST_LENSES[0]?.id ?? 'ai-systems'
  );
  const [inquirySubject, setInquirySubject] = useState<string>(
    PERSONAL_INTEREST_LENSES[0]?.approachSubject ?? 'AI Systems & Multi-Agent Strategy Inquiry'
  );
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [submitted, setSubmitted] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [prevSubTargetId, setPrevSubTargetId] = useState<string | null>(activeSubTargetId);
  const [prevActIndexProp, setPrevActIndexProp] = useState<number>(activeActIndex);
  const [scrollSpyActIndex, setScrollSpyActIndex] = useState<number | null>(null);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const submitTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const programmaticScrollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isProgrammaticScrollRef = useRef(false);

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      if (submitTimeoutRef.current) clearTimeout(submitTimeoutRef.current);
      if (programmaticScrollTimeoutRef.current) clearTimeout(programmaticScrollTimeoutRef.current);
    };
  }, []);

  if (activeActIndex !== prevActIndexProp) {
    setPrevActIndexProp(activeActIndex);
    setScrollSpyActIndex(null);
  }

  // Synchronize internal filter/accordion state when activeSubTargetId changes without effect cascades
  if (activeSubTargetId !== prevSubTargetId) {
    setPrevSubTargetId(activeSubTargetId);
    if (
      activeSubTargetId === 'cloud-ai' ||
      activeSubTargetId === 'product-ba' ||
      activeSubTargetId === 'global-wins'
    ) {
      setCredentialFilter(activeSubTargetId);
    }
    const matchingLens = PERSONAL_INTEREST_LENSES.find((l) => l.id === activeSubTargetId);
    if (matchingLens) {
      setSelectedLensId(matchingLens.id);
      setInquirySubject(matchingLens.approachSubject);
    }
  }

  // Smoothly scroll ONLY the inner scroll container when opening or switching chapters
  // (never call Element.scrollIntoView, which scrolls ancestor overflow-hidden containers and clips the sticky header;
  // omit activeSubTargetId from dependencies so clicking intra-chapter filters/accordions/lenses preserves scroll position)
  useEffect(() => {
    if (!isOpen || !scrollContainerRef.current) return;
    const container = scrollContainerRef.current;
    const chapterEl = container.querySelector(
      `[data-sheet-chapter="${activeActIndex}"]`
    ) as HTMLElement | null;
    if (chapterEl) {
      const containerRect = container.getBoundingClientRect();
      const chapterRect = chapterEl.getBoundingClientRect();
      const targetTop = Math.max(
        0,
        container.scrollTop + (chapterRect.top - containerRect.top) - 16
      );
      if (typeof container.scrollTo === 'function') {
        isProgrammaticScrollRef.current = true;
        if (programmaticScrollTimeoutRef.current) clearTimeout(programmaticScrollTimeoutRef.current);
        programmaticScrollTimeoutRef.current = setTimeout(() => {
          isProgrammaticScrollRef.current = false;
          programmaticScrollTimeoutRef.current = null;
        }, 520);
        const prefersReduced =
          typeof window !== 'undefined' &&
          typeof window.matchMedia === 'function' &&
          window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        container.scrollTo({ top: targetTop, behavior: prefersReduced ? 'auto' : 'smooth' });
      } else {
        container.scrollTop = targetTop;
      }
    }
  }, [isOpen, activeActIndex]);

  const handleContainerScroll = () => {
    if (!isOpen || isProgrammaticScrollRef.current || !scrollContainerRef.current) return;
    const container = scrollContainerRef.current;
    const containerTop = container.getBoundingClientRect().top;
    const sections = container.querySelectorAll('[data-sheet-chapter]');
    let detected = activeActIndex;
    sections.forEach((sec) => {
      const idxAttr = sec.getAttribute('data-sheet-chapter');
      const idx = idxAttr !== null ? Number(idxAttr) : NaN;
      if (Number.isNaN(idx)) return;
      if (sec.getBoundingClientRect().top - containerTop <= 88) {
        detected = idx;
      }
    });
    if (detected !== scrollSpyActIndex) {
      setScrollSpyActIndex(detected);
    }
  };

  // Escape key closes the slide-over inspection sheet
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const filteredCredentials = CREDENTIALS.filter((cred) => {
    if (credentialFilter === 'all') return true;
    if (credentialFilter === 'cloud-ai') {
      return /Cloud|AI/i.test(cred.badgeType);
    }
    if (credentialFilter === 'product-ba') {
      return /PM|Business Analysis/i.test(cred.badgeType);
    }
    return /World Championship|Academic|Hackathon/i.test(cred.badgeType);
  });

  const activeSubTargets = SceneController.DIORAMA_SUB_TARGETS.filter(
    (t) => t.actIndex === activeActIndex
  );

  const activeLens: PersonalInterestLens =
    PERSONAL_INTEREST_LENSES.find((l) => l.id === selectedLensId) ??
    PERSONAL_INTEREST_LENSES[0]!;

  const handleSelectLens = (lens: PersonalInterestLens, prefill = false) => {
    setSelectedLensId(lens.id);
    setInquirySubject(lens.approachSubject);
    onSelectSubTarget(5, lens.id);
    if (prefill) {
      setFormData((prev) => ({ ...prev, message: lens.starterPrompt }));
    }
  };

  const activeAct = WHISPER_ACTS[activeActIndex] ?? WHISPER_ACTS[0]!;
  const highlightedActIndex = scrollSpyActIndex ?? activeActIndex;

  const handleCopyEmail = () => {
    const email = 'ziyang.ang02@gmail.com';
    try {
      navigator.clipboard?.writeText(email).catch(() => {});
    } catch {
      // Ignore clipboard errors in headless environments
    }
    setCopiedEmail(true);
    if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
    copyTimeoutRef.current = setTimeout(() => {
      setCopiedEmail(false);
      copyTimeoutRef.current = null;
    }, 2200);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.message) return;
    setSubmitted(true);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action: 'handshake_wave', subject: inquirySubject },
        })
      );
    }
    const subject = encodeURIComponent(`${inquirySubject} — ${formData.name}`);
    const body = encodeURIComponent(
      `Topic: ${inquirySubject}\nFrom: ${formData.name} (${formData.email})\n\nMessage:\n${formData.message}`
    );
    window.location.href = `mailto:ziyang.ang02@gmail.com?subject=${subject}&body=${body}`;
    if (submitTimeoutRef.current) clearTimeout(submitTimeoutRef.current);
    submitTimeoutRef.current = setTimeout(() => {
      setSubmitted(false);
      setFormData({ name: '', email: '', message: '' });
      submitTimeoutRef.current = null;
    }, 3500);
  };

  return (
    <aside
      aria-label="3D Chapter & Prop Inspection Sheet"
      aria-hidden={!isOpen}
      inert={!isOpen}
      data-testid="slide-over-inspection-sheet"
      data-sheet-open={isOpen ? 'true' : 'false'}
      data-peek-sheet
      className={`fixed top-[110px] bottom-[74px] sm:top-[132px] sm:bottom-[92px] right-3 sm:right-6 z-40 w-[calc(100vw-1.5rem)] sm:w-[440px] xl:w-[500px] max-w-xl rounded-3xl bg-[#12100e]/92 backdrop-blur-2xl border border-white/12 shadow-[0_24px_80px_rgba(0,0,0,0.85)] flex flex-col overflow-clip transition-all duration-300 ${
        isOpen
          ? 'translate-x-0 opacity-100 pointer-events-auto'
          : 'translate-x-[112%] opacity-0 pointer-events-none'
      }`}
    >
      {/* Sticky Drawer Header: Slim Editorial Badge + Inline Chapter Switcher + Sub-Target Pills */}
      <div className="px-3.5 py-2.5 sm:px-4 sm:py-3 border-b border-white/10 bg-white/[0.02] space-y-2 flex-shrink-0">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span
              aria-hidden="true"
              className="w-2 h-2 rounded-full flex-shrink-0 transition-colors duration-300"
              style={{ backgroundColor: activeAct.accentColor }}
            />
            <span
              className="text-[10px] font-mono uppercase tracking-[0.08em] sm:tracking-[0.15em] font-semibold truncate transition-colors duration-300"
              style={{ color: activeAct.accentColor }}
            >
              {activeAct.actBadge}
            </span>
          </div>

          <div className="flex items-center gap-1 sm:gap-1.5 flex-shrink-0">
            {/* Compact Inline 01..06 Chapter Switcher */}
            <div className="flex items-center gap-0.5 sm:gap-1" role="group" aria-label="Chapter switcher">
              {CHAPTER_TABS.map((tab) => {
                const isCurrent = highlightedActIndex === tab.actIndex;
                const tabAccent = WHISPER_ACTS[tab.actIndex]?.accentColor ?? '#c8a97e';
                return (
                  <button
                    key={tab.code}
                    type="button"
                    data-testid={`sheet-tab-act-${tab.actIndex}`}
                    title={`${tab.code} · ${tab.label}`}
                    onClick={() => onSelectAct(tab.actIndex)}
                    style={
                      isCurrent
                        ? {
                            borderColor: `${tabAccent}88`,
                            backgroundColor: `${tabAccent}1c`,
                            color: tabAccent,
                          }
                        : undefined
                    }
                    className={`px-1.5 py-0.5 rounded-md text-[10px] font-mono transition-all cursor-pointer border ${
                      isCurrent
                        ? 'font-semibold'
                        : 'bg-white/[0.03] text-neutral-400 hover:text-[#F4F0EA] border-white/5'
                    }`}
                  >
                    {tab.code}
                    <span className="sr-only"> {tab.label}</span>
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              data-testid="close-inspection-sheet-btn"
              aria-label="Close inspection sheet"
              onClick={onClose}
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 text-[#D6D0C4] hover:text-[#F4F0EA] flex items-center justify-center transition-colors cursor-pointer flex-shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Slim Sub-Target Switcher for the Active Act */}
        {activeSubTargets.length > 0 && (
          <div className="flex flex-nowrap sm:flex-wrap gap-1.5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {activeSubTargets.map((target) => {
              const isSelected = activeSubTargetId === target.id;
              return (
                <button
                  key={target.id}
                  type="button"
                  data-testid={`sheet-subtarget-${target.id}`}
                  onClick={() => onSelectSubTarget(activeActIndex, target.id)}
                  className={`shrink-0 px-2.5 py-1 sm:px-2 sm:py-0.5 rounded-md text-[10px] font-mono transition-all cursor-pointer border ${
                    isSelected
                      ? 'bg-[#F4F0EA] text-[#14110f] font-semibold border-[#F4F0EA]'
                      : 'bg-white/[0.05] text-[#D6D0C4] hover:text-[#F4F0EA] border-white/10'
                  }`}
                >
                  {target.label}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Scrollable Deep-Dive Evidence Body */}
      <div
        ref={scrollContainerRef}
        onScroll={handleContainerScroll}
        className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-5 space-y-8 divide-y divide-white/10"
      >
        {/* =================================================================
         * ACT 01: SOVEREIGN TITANIUM ATELIER & EXECUTIVE DOSSIER
         * ================================================================= */}
        <section data-sheet-chapter="0" className="min-h-full pb-6 space-y-4">
          <div
            data-subtarget-active={activeSubTargetId === 'executive-dossier' ? 'true' : 'false'}
            className={`flex items-start gap-4 rounded-2xl transition-all duration-300 ${
              activeSubTargetId === 'executive-dossier'
                ? 'p-2.5 -mx-2.5 bg-[#d4b483]/[0.07] ring-1 ring-[#d4b483]/45'
                : ''
            }`}
          >
            <div className="relative w-[104px] h-[138px] flex-shrink-0 rounded-2xl overflow-hidden border border-[#d4b483]/35 bg-[#0e0d10] shadow-[0_12px_32px_rgba(0,0,0,0.6)]">
              <img
                src="/images/zachary_editorial_portrait.webp"
                alt="Ang Zi Yang (Zachary) — Executive Studio Portrait"
                data-testid="executive-editorial-portrait"
                width={104}
                height={138}
                decoding="async"
                className="w-full h-full object-cover object-top"
              />
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-[#0e0d10]/85 to-transparent"
              />
            </div>

            <div className="space-y-1.5 min-w-0">
              <span className="text-[11px] font-mono uppercase tracking-widest text-[#d4b483]">
                EXECUTIVE DOSSIER • KUALA LUMPUR / ZÜRICH
              </span>
              <h3 className="text-xl font-bold text-[#F4F0EA] font-display leading-tight">
                Ang Zi Yang (Zachary)
              </h3>
              <p className="text-[11px] font-mono text-[#e2c799]/90 leading-snug">
                Business Analyst, Soft Space · Hilti Global Champion
              </p>
              <p className="text-xs text-[#D6D0C4] leading-relaxed">
                Bridging C-suite commercial strategy, zero-defect digital banking super-apps, and multi-agent AI architectures.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-3 rounded-2xl bg-white/[0.04] border border-white/10">
              <div className="text-lg font-bold text-[#c8a97e] font-display">1st / 53</div>
              <div className="text-[11px] text-[#D6D0C4]">Hilti Global IT Champion</div>
            </div>
            <div className="p-3 rounded-2xl bg-white/[0.04] border border-white/10">
              <div className="text-lg font-bold text-[#e2c799] font-display">3.75 · 3.89</div>
              <div className="text-[11px] text-[#D6D0C4]">First-Class BSc · SE Dip</div>
            </div>
            <div className="p-3 rounded-2xl bg-white/[0.04] border border-white/10">
              <div className="text-lg font-bold text-amber-400 font-display">14 Quests</div>
              <div className="text-[11px] text-[#D6D0C4]">Google Cloud &amp; Vertex AI</div>
            </div>
            <div className="p-3 rounded-2xl bg-white/[0.04] border border-white/10">
              <div className="text-lg font-bold text-[#e2c799] font-display">-35% BRD</div>
              <div className="text-[11px] text-[#D6D0C4]">C-Suite AI Automation</div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              data-subtarget-active={activeSubTargetId === 'strategy-table' ? 'true' : 'false'}
              onClick={() => onSelectSubTarget(0, 'strategy-table')}
              className={`px-3 py-2 rounded-xl border border-[#c8a97e]/40 text-xs font-mono text-[#f3e5cc] cursor-pointer transition-colors ${
                activeSubTargetId === 'strategy-table'
                  ? 'ring-1 ring-[#c8a97e]/70 bg-[#c8a97e]/25'
                  : 'bg-[#c8a97e]/15 hover:bg-[#c8a97e]/25'
              }`}
            >
              Explode 3D Strategy Core
            </button>
            <button
              type="button"
              data-subtarget-active={activeSubTargetId === 'optical-core' ? 'true' : 'false'}
              onClick={() => onSelectSubTarget(0, 'optical-core')}
              className={`px-3 py-2 rounded-xl border text-xs font-mono text-[#F4F0EA] cursor-pointer transition-colors ${
                activeSubTargetId === 'optical-core'
                  ? 'ring-1 ring-[#e2c799]/60 bg-[#e2c799]/15 border-[#e2c799]/50'
                  : 'bg-white/[0.06] hover:bg-white/12 border-white/10'
              }`}
            >
              Inspect Optical Nucleus
            </button>
          </div>
        </section>

        {/* =================================================================
         * ACT 02: THE ACADEMY LIBRARY (CAREER & ACADEMIC TIMELINE)
         * ================================================================= */}
        <section data-sheet-chapter="1" className="min-h-full pt-6 pb-6 space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest text-[#d4a359]">
              <BookOpen className="w-3.5 h-3.5" />
              <span>Act 02 • The Academy</span>
            </div>
            <h3 className="text-lg font-bold text-[#F4F0EA] font-display">
              Academic Foundations &amp; Career Ascent
            </h3>
            <p className="text-xs text-neutral-400">
              Click any milestone volume to slide the book off the 3D mahogany shelf and update the Illuminated Tome.
            </p>
          </div>

          <div className="space-y-2.5">
            {TIMELINE_MILESTONES.map((mile, idx) => {
              const volMap = ['vol-4', 'vol-3', 'vol-3', 'vol-2', 'vol-3', 'vol-2', 'vol-1'];
              const targetVol = volMap[idx] ?? 'vol-3';
              const isVolActive = activeSubTargetId === targetVol;
              return (
                <div
                  key={mile.id}
                  role="button"
                  tabIndex={0}
                  data-subtarget-active={isVolActive ? 'true' : 'false'}
                  onClick={() => onSelectSubTarget(1, targetVol)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelectSubTarget(1, targetVol);
                    }
                  }}
                  className={`p-3.5 rounded-2xl hover:bg-white/[0.07] focus-visible:bg-white/[0.08] border focus-visible:border-[#d4a359] transition-all cursor-pointer space-y-1.5 ${
                    isVolActive
                      ? 'bg-[#d4a359]/[0.10] border-[#d4a359]/60 shadow-[0_0_20px_rgba(212,163,89,0.14)]'
                      : 'bg-white/[0.03] border-white/10'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 text-[10px] font-mono text-[#d4a359]">
                    <span>{mile.period}</span>
                    <span className="px-2 py-0.5 rounded-full bg-white/10 text-[#D6D0C4]">
                      {mile.category}
                    </span>
                  </div>
                  <div className="text-sm font-bold text-[#F4F0EA]">{mile.role}</div>
                  <div className="text-xs text-neutral-400">
                    {mile.organization} • {mile.location}
                  </div>
                  <ul className="space-y-1 pt-1 text-xs text-[#D6D0C4] list-disc list-inside">
                    {mile.keyImpacts.slice(0, 2).map((impact, i) => (
                      <li key={i} className="leading-relaxed">
                        {impact}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </section>

        {/* =================================================================
         * ACT 03: THE CRUCIBLE STAGE (CREDENTIAL VAULT & GDSC)
         * ================================================================= */}
        <section data-sheet-chapter="2" className="min-h-full pt-6 pb-6 space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest text-[#eab308]">
              <Award className="w-3.5 h-3.5" />
              <span>Act 03 • The Crucible</span>
            </div>
            <h3 className="text-lg font-bold text-[#F4F0EA] font-display">
              Verified Credential Vault &amp; Cloud Mastery
            </h3>
          </div>

          {/* Category Filter Buttons (Synced with 3D Orbiting Medallions) */}
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              onClick={() => {
                setCredentialFilter('all');
                onSelectSubTarget(2, 'cloud-ai');
              }}
              className={`px-2.5 py-1.5 rounded-xl text-xs font-medium cursor-pointer border ${
                credentialFilter === 'all'
                  ? 'bg-[#eab308]/15 text-[#fde047] border-[#eab308]/45 font-semibold'
                  : 'bg-white/[0.04] text-[#D6D0C4] border-white/10'
              }`}
            >
              All Credentials
            </button>
            <button
              type="button"
              onClick={() => {
                setCredentialFilter('cloud-ai');
                onSelectSubTarget(2, 'cloud-ai');
              }}
              className={`px-2.5 py-1.5 rounded-xl text-xs font-medium cursor-pointer border ${
                credentialFilter === 'cloud-ai'
                  ? 'bg-sky-500/15 text-sky-200 border-sky-400/45 font-semibold'
                  : 'bg-white/[0.04] text-[#D6D0C4] border-white/10'
              }`}
            >
              Cloud &amp; AI Badges
            </button>
            <button
              type="button"
              onClick={() => {
                setCredentialFilter('product-ba');
                onSelectSubTarget(2, 'product-ba');
              }}
              className={`px-2.5 py-1.5 rounded-xl text-xs font-medium cursor-pointer border ${
                credentialFilter === 'product-ba'
                  ? 'bg-purple-500/20 text-purple-300 border-purple-400/50 font-semibold'
                  : 'bg-white/[0.04] text-neutral-300 border-white/10'
              }`}
            >
              Product &amp; BA
            </button>
            <button
              type="button"
              onClick={() => {
                setCredentialFilter('global-wins');
                onSelectSubTarget(2, 'global-wins');
              }}
              className={`px-2.5 py-1.5 rounded-xl text-xs font-medium cursor-pointer border ${
                credentialFilter === 'global-wins'
                  ? 'bg-amber-500/20 text-amber-300 border-amber-400/50 font-semibold'
                  : 'bg-white/[0.04] text-neutral-300 border-white/10'
              }`}
            >
              Academic &amp; Global Wins
            </button>
          </div>

          <div className="space-y-2.5">
            {filteredCredentials.map((cred) => {
              const credCategory = /Cloud|AI/i.test(cred.badgeType)
                ? 'cloud-ai'
                : /PM|Business Analysis/i.test(cred.badgeType)
                  ? 'product-ba'
                  : 'global-wins';
              const isCredActive = activeSubTargetId === credCategory;
              return (
                <div
                  key={cred.id}
                  data-subtarget-active={isCredActive ? 'true' : 'false'}
                  className={`p-3.5 rounded-2xl border transition-all space-y-1.5 ${
                    isCredActive
                      ? 'bg-[#eab308]/[0.08] border-[#eab308]/50'
                      : 'bg-white/[0.03] border-white/10'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 text-[10px] font-mono">
                    <span style={{ color: cred.color }}>{cred.badgeType}</span>
                    <span className="text-neutral-400">{cred.issueDate}</span>
                  </div>
                  <div className="text-sm font-bold text-white">{cred.title}</div>
                  <div className="text-xs text-neutral-400">{cred.issuer}</div>
                  <ul className="space-y-1 pt-1 text-xs text-neutral-300 list-disc list-inside">
                    {cred.highlights.slice(0, 3).map((h, idx) => (
                      <li key={idx}>{h}</li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </section>

        {/* =================================================================
         * ACT 04: THE ALPINE SUMMIT (HILTI CHAMPIONSHIP & NATIONAL PRESS)
         * ================================================================= */}
        <section data-sheet-chapter="3" className="min-h-full pt-6 pb-6 space-y-4">
          <div
            data-subtarget-active={activeSubTargetId === 'schaan-hq' ? 'true' : 'false'}
            className={`space-y-1 rounded-2xl transition-all ${
              activeSubTargetId === 'schaan-hq'
                ? 'p-2.5 -mx-2.5 bg-amber-400/[0.07] ring-1 ring-amber-400/40'
                : ''
            }`}
          >
            <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest text-amber-400">
              <Trophy className="w-3.5 h-3.5" />
              <span>Act 04 • Mount Pilatus Summit (2,128m)</span>
            </div>
            <h3 className="text-lg font-bold text-white font-display">
              1st Place Worldwide • Team Sweetzerland
            </h3>
            <p className="text-xs text-neutral-300 leading-relaxed">
              Triumphing over 53 international university teams at the Hilti IT Competition 2024, followed by an executive technical pitch in Schaan, Liechtenstein and scaling Mount Pilatus, Switzerland.
            </p>
          </div>

          <button
            type="button"
            aria-label="Inspect Trophy Proof"
            data-subtarget-active={activeSubTargetId === 'hilti-trophy' ? 'true' : 'false'}
            onClick={() => {
              onSelectSubTarget(3, 'hilti-trophy');
              onInspectPressModal();
            }}
            className={`w-full py-2.5 px-4 rounded-2xl border border-amber-400/40 text-amber-200 text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer transition-all ${
              activeSubTargetId === 'hilti-trophy'
                ? 'ring-1 ring-amber-400/75 bg-amber-400/25'
                : 'bg-amber-400/15 hover:bg-amber-400/25'
            }`}
          >
            <Trophy className="w-4 h-4 text-amber-400" />
            <span>Inspect Trophy Proof &amp; National Press Verification</span>
          </button>

          {/* Interactive Press Citation Accordions */}
          <div className="space-y-2">
            {PRESS_CITES.map((cite) => {
              const isExpanded = openPressId === cite.id;
              return (
                <div
                  key={cite.id}
                  data-subtarget-active={activeSubTargetId === 'star-press' ? 'true' : 'false'}
                  className={`rounded-2xl border overflow-hidden transition-all ${
                    activeSubTargetId === 'star-press'
                      ? 'border-amber-400/55 bg-amber-400/[0.07]'
                      : 'bg-white/[0.03] border-white/10'
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => {
                      setOpenPressId(isExpanded ? '' : cite.id);
                      onSelectSubTarget(3, 'star-press');
                    }}
                    className="w-full p-3.5 text-left flex items-center justify-between gap-2 hover:bg-white/[0.04] transition-colors cursor-pointer"
                  >
                    <div>
                      <div className="text-[10px] font-mono text-amber-400 uppercase">
                        {cite.source} • {cite.badge}
                      </div>
                      <div className="text-xs font-bold text-white mt-0.5">{cite.title}</div>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-neutral-400 flex-shrink-0" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-neutral-400 flex-shrink-0" />
                    )}
                  </button>
                  {isExpanded && (
                    <div className="px-3.5 pb-3.5 pt-1 space-y-2 text-xs text-neutral-300 border-t border-white/5">
                      <blockquote className="italic text-neutral-200 border-l-2 border-amber-400/60 pl-2.5">
                        {cite.quote}
                      </blockquote>
                      <p className="text-neutral-400 leading-relaxed">{cite.description}</p>
                      <a
                        href={cite.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[#f59e0b] hover:underline font-mono text-[11px]"
                      >
                        <span>Read Official Publication</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* =================================================================
         * ACT 05: THE FRONTIER AI LAB (FLAGSHIP CASE STUDIES)
         * ================================================================= */}
        <section data-sheet-chapter="4" className="min-h-full pt-6 pb-6 space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest text-[#f97316]">
              <Layers className="w-3.5 h-3.5" />
              <span>Act 05 • The Frontier</span>
            </div>
            <h3 className="text-lg font-bold text-[#F4F0EA] font-display">
              Flagship AI &amp; Fintech System Blueprints
            </h3>
          </div>

          <div className="space-y-3">
            {CASE_STUDIES.map((study) => {
              const isStudyActive = activeSubTargetId === study.slug;
              return (
                <div
                  key={study.id}
                  data-subtarget-active={isStudyActive ? 'true' : 'false'}
                  className={`p-4 rounded-2xl border transition-all space-y-2.5 ${
                    isStudyActive
                      ? 'bg-[#f97316]/[0.09] border-[#f97316]/60 shadow-[0_0_24px_rgba(249,115,22,0.14)]'
                      : 'bg-white/[0.03] border-white/10'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className="text-[10px] font-mono uppercase font-bold"
                      style={{ color: study.accentColor }}
                    >
                      {study.category} • {study.role}
                    </span>
                  </div>
                  <div className="text-sm font-bold text-white">{study.title}</div>
                  <p className="text-xs text-neutral-300 leading-relaxed">{study.subtitle}</p>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {study.techStack.slice(0, 4).map((tech) => (
                      <span
                        key={tech}
                        className="px-2 py-0.5 rounded-md bg-white/[0.06] text-[10px] font-mono text-neutral-300"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                  <div className="pt-2 flex items-center gap-2">
                    <button
                      type="button"
                      aria-label={`Inspect Drawer for ${study.title}`}
                      onClick={() => {
                        onSelectSubTarget(4, study.slug);
                        onSelectCaseStudy(study);
                      }}
                      className="px-3 py-1.5 rounded-xl bg-white text-black hover:bg-neutral-200 text-xs font-semibold cursor-pointer transition-colors"
                    >
                      Inspect Drawer
                    </button>
                    <button
                      type="button"
                      onClick={() => onSelectSubTarget(4, study.slug)}
                      className="px-3 py-1.5 rounded-xl bg-white/[0.06] hover:bg-white/12 text-neutral-200 text-xs font-mono cursor-pointer border border-white/10"
                    >
                      Focus 3D Core
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* =================================================================
         * ACT 06: THE HORIZON PORTAL (PERSONAL LENSES & DIRECT DISPATCH)
         * ================================================================= */}
        <section data-sheet-chapter="5" className="min-h-full pt-6 pb-6 space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest text-[#e5d3b3]">
              <Compass className="w-3.5 h-3.5" />
              <span>Act 06 • The Horizon Portal</span>
            </div>
            <h3 className="text-lg font-bold text-[#F4F0EA] font-display">
              Personal Lenses &amp; Direct Dispatch
            </h3>
            <p className="text-xs text-neutral-400">
              Click any lens below to morph the 3D Horizon Observatory color theme and pre-fill your conversation topic.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {PERSONAL_INTEREST_LENSES.map((lens) => {
              const isSelected = lens.id === selectedLensId;
              return (
                <button
                  key={lens.id}
                  type="button"
                  onClick={() => handleSelectLens(lens, true)}
                  style={isSelected ? { borderColor: lens.color } : undefined}
                  className={`px-2.5 py-1.5 rounded-xl text-xs font-medium cursor-pointer flex items-center gap-1.5 border ${
                    isSelected
                      ? 'bg-white/15 text-[#F4F0EA] font-semibold'
                      : 'bg-white/[0.04] text-[#D6D0C4] border-white/10'
                  }`}
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: lens.color }}
                  />
                  <span>{lens.shortLabel}</span>
                </button>
              );
            })}
          </div>

          <div
            data-subtarget-active={activeSubTargetId === activeLens.id ? 'true' : 'false'}
            className={`p-3.5 rounded-2xl border space-y-1.5 transition-all ${
              activeSubTargetId === activeLens.id
                ? 'bg-white/[0.08] border-white/30 ring-1 ring-white/20'
                : 'bg-white/[0.04] border-white/10'
            }`}
          >
            <div className="text-xs font-bold" style={{ color: activeLens.color }}>
              {activeLens.title}
            </div>
            <p className="text-xs text-[#D6D0C4] leading-relaxed">{activeLens.description}</p>
          </div>

          {/* Direct Email Copy Bar */}
          <div
            data-subtarget-active={activeSubTargetId === 'direct-dispatch' ? 'true' : 'false'}
            className={`flex items-center justify-between gap-2 p-2.5 rounded-2xl border transition-all ${
              activeSubTargetId === 'direct-dispatch'
                ? 'bg-[#c8a97e]/[0.10] border-[#c8a97e]/55 ring-1 ring-[#c8a97e]/35'
                : 'bg-white/[0.04] border-white/10'
            }`}
          >
            <div className="flex items-center gap-2 text-xs font-mono text-[#F4F0EA] truncate">
              <Mail className="w-3.5 h-3.5 text-[#c8a97e] flex-shrink-0" />
              <span className="truncate">ziyang.ang02@gmail.com</span>
            </div>
            <button
              type="button"
              onClick={handleCopyEmail}
              className="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-mono text-[#F4F0EA] flex items-center gap-1.5 cursor-pointer"
            >
              {copiedEmail ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-[#c8a97e]" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>

          {/* Direct Dispatch Form */}
          {submitted ? (
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-center space-y-1">
              <CheckCircle2 className="w-6 h-6 mx-auto" />
              <div className="text-xs font-bold">Dispatch Prepared</div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-2.5">
              <div>
                <label htmlFor="dispatch-name" className="sr-only">
                  Your Name / Organization
                </label>
                <input
                  id="dispatch-name"
                  type="text"
                  autoComplete="name"
                  required
                  placeholder="Your Name / Organization"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-[#F4F0EA] text-xs placeholder:text-neutral-500 focus:border-[#c8a97e]"
                />
              </div>
              <div>
                <label htmlFor="dispatch-email" className="sr-only">
                  Corporate Email
                </label>
                <input
                  id="dispatch-email"
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="Corporate Email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-[#F4F0EA] text-xs placeholder:text-neutral-500 focus:border-[#c8a97e]"
                />
              </div>
              <div>
                <label htmlFor="dispatch-message" className="sr-only">
                  Project scope or collaboration topic
                </label>
                <textarea
                  id="dispatch-message"
                  required
                  rows={3}
                  placeholder="Project scope or collaboration topic..."
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-[#F4F0EA] text-xs placeholder:text-neutral-500 focus:border-[#c8a97e] resize-none"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-full bg-[#F4F0EA] text-[#14110f] text-xs font-semibold hover:bg-white transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Transmit Direct Dispatch</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          )}
        </section>
      </div>
    </aside>
  );
};
