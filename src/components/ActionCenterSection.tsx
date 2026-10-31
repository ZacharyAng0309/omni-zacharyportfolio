import React, { useState, useRef, useEffect } from 'react';
import {
  Mail,
  Send,
  CheckCircle2,
  MapPin,
  FileDown,
  Copy,
  Check,
  Radio,
  Sparkles,
  Compass,
  MessageSquarePlus,
} from 'lucide-react';

const CURRENT_YEAR = new Date().getFullYear();

export interface PersonalInterestLens {
  id: string;
  title: string;
  shortLabel: string;
  color: string;
  tagline: string;
  description: string;
  approachTitle: string;
  approachSubject: string;
  starterPrompt: string;
}

export const PERSONAL_INTEREST_LENSES: readonly PersonalInterestLens[] = [
  {
    id: 'ai-systems',
    title: 'AI Systems & Multi-Agent Orchestration',
    shortLabel: 'AI & Multi-Agent Systems',
    color: '#06b6d4',
    tagline: 'Autonomous LLM workflows, Vertex AI embeddings & tool-calling agents',
    description:
      'Building deterministic multi-agent pipelines, RAG evaluation harnesses, and local-first AI desktop tools that turn frontier models into reliable production software.',
    approachTitle: 'Co-Design an Agentic AI System or Product Strategy',
    approachSubject: 'AI Systems & Multi-Agent Strategy Inquiry',
    starterPrompt:
      'Hi Zachary — I explored your AI Systems lens and would love to discuss architecting an agentic workflow / LLM product roadmap.',
  },
  {
    id: 'crypto-quant',
    title: 'Crypto & Quantitative Market Structure',
    shortLabel: 'Crypto & Quant Markets',
    color: '#f59e0b',
    tagline: 'On-chain liquidity, algorithmic execution & market microstructure',
    description:
      'Analyzing digital asset market structure, order-flow dynamics, and automated quantitative research pipelines across decentralized and institutional venues.',
    approachTitle: 'Exchange Alpha on Crypto & Quantitative Market Structure',
    approachSubject: 'Crypto & Quantitative Market Structure Discussion',
    starterPrompt:
      'Hi Zachary — I saw your Crypto & Quantitative Market Structure lens and wanted to connect on algorithmic market mechanics and digital asset infrastructure.',
  },
  {
    id: 'cinematic-video',
    title: 'Cinematic Video Editing & Visual Storytelling',
    shortLabel: 'Cinematic Video & Direction',
    color: '#a855f7',
    tagline: 'Keynote-grade pacing, sound design & narrative visual direction',
    description:
      'Crafting high-impact product reveal films, motion choreography, and executive pitch narratives that make complex engineering feel visceral and human.',
    approachTitle: 'Collaborate on Cinematic Product Storytelling & Direction',
    approachSubject: 'Cinematic Video Direction & Product Storytelling',
    starterPrompt:
      'Hi Zachary — Your Cinematic Video Editing & Visual Storytelling lens caught my eye. Let’s talk about directing a high-impact product reveal or narrative showcase.',
  },
  {
    id: 'hackathons-mentorship',
    title: 'Global Hackathons & Mentorship',
    shortLabel: 'Hackathons & Mentorship',
    color: '#10b981',
    tagline: 'Hilti Global Grand Champion • GDSC APU 500+ developer workshops',
    description:
      'Mentoring student builders, judging hackathons, and coaching engineering teams on how to turn 48-hour prototypes into globally competitive executive pitches.',
    approachTitle: 'Invite for Hackathon Judging, Keynote Speaking, or Mentorship',
    approachSubject: 'Hackathon Mentorship / Speaking Invitation',
    starterPrompt:
      'Hi Zachary — Reaching out via your Global Hackathons & Mentorship lens regarding a speaking, judging, or builder mentorship opportunity.',
  },
  {
    id: 'fintech-architecture',
    title: 'Fintech & Enterprise Architecture',
    shortLabel: 'Fintech & Super-Apps',
    color: '#3b82f6',
    tagline: 'Zero-defect digital banking super-apps, ISO 20022 & EMV L2 kernels',
    description:
      'Bridging C-suite commercial strategy with bank-grade Functional Specifications (BRD/FSD), cross-border payment rails, and high-availability mobile wallets.',
    approachTitle: 'Advisory on Fintech Super-Apps & Enterprise BA Architecture',
    approachSubject: 'Fintech & Enterprise Architecture Advisory',
    starterPrompt:
      'Hi Zachary — Connecting through your Fintech & Enterprise Architecture lens to discuss digital banking super-app delivery and enterprise BA strategy.',
  },
] as const;

export const ActionCenterSection: React.FC = () => {
  const [selectedInterestId, setSelectedInterestId] = useState<string>(
    PERSONAL_INTEREST_LENSES[0]?.id ?? 'ai-systems'
  );
  const [inquirySubject, setInquirySubject] = useState<string>(
    PERSONAL_INTEREST_LENSES[0]?.approachSubject ?? 'AI Systems & Multi-Agent Strategy Inquiry'
  );
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [submitted, setSubmitted] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const submitTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const activeLens =
    PERSONAL_INTEREST_LENSES.find((lens) => lens.id === selectedInterestId) ??
    PERSONAL_INTEREST_LENSES[0]!;

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      if (submitTimeoutRef.current) clearTimeout(submitTimeoutRef.current);
    };
  }, []);

  const dispatchSceneAction = (action: string, detail?: Record<string, unknown>) => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action, ...detail },
        })
      );
    }
  };

  const handleSelectInterestLens = (lens: PersonalInterestLens, prefillMessage = false) => {
    setSelectedInterestId(lens.id);
    setInquirySubject(lens.approachSubject);
    dispatchSceneAction('interest_focus', {
      interestId: lens.id,
      color: lens.color,
      subject: lens.approachSubject,
    });
    if (prefillMessage) {
      setFormData((prev) => ({
        ...prev,
        message: lens.starterPrompt,
      }));
    }
  };

  const copyFallback = (text: string) => {
    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.left = '-9999px';
      textarea.style.top = '-9999px';
      textarea.setAttribute('readonly', '');
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    } catch {
      // Best-effort fallback
    }
  };

  const handleCopyEmail = () => {
    const email = 'ziyang.ang02@gmail.com';
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(email).catch(() => {
          copyFallback(email);
        });
      } else {
        copyFallback(email);
      }
    } catch {
      copyFallback(email);
    }
    setCopiedEmail(true);
    dispatchSceneAction('handshake_wave');
    if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
    copyTimeoutRef.current = setTimeout(() => {
      setCopiedEmail(false);
    }, 2500);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.message) return;
    setSubmitted(true);
    dispatchSceneAction('handshake_wave', { subject: inquirySubject });
    const subject = encodeURIComponent(`${inquirySubject} — ${formData.name}`);
    const body = encodeURIComponent(
      `Topic: ${inquirySubject}\nFrom: ${formData.name} (${formData.email})\n\nMessage:\n${formData.message}`
    );
    window.location.href = `mailto:ziyang.ang02@gmail.com?subject=${subject}&body=${body}`;
    if (submitTimeoutRef.current) clearTimeout(submitTimeoutRef.current);
    submitTimeoutRef.current = setTimeout(() => {
      setSubmitted(false);
      setFormData({ name: '', email: '', message: '' });
    }, 4000);
  };

  return (
    <footer
      id="contact"
      role="contentinfo"
      aria-label="Executive Action Center"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 md:px-12 py-20 sm:py-28 relative z-10 max-w-7xl mx-auto w-full"
    >
      <div data-peek-hide className="w-full space-y-8">
        <div className="space-y-3 text-left">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono uppercase tracking-widest text-cyan-400">
              Act 06: Epilogue • Horizon Collaboration Dock
            </span>
            {/* < 24H SLA Response Protocol Badge */}
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
              <span className="font-semibold">&lt; 24H SLA</span>
              <span className="text-neutral-400 text-[11px]">• Response Protocol Active</span>
            </div>
          </div>

          <h2 className="text-3xl sm:text-5xl md:text-6xl font-bold tracking-tighter headline-gradient mb-2 font-display">
            Initiate Collaboration.
          </h2>
          <p className="text-neutral-300 text-xs sm:text-sm md:text-base max-w-2xl font-sans leading-relaxed">
            Available for high-stakes AI product strategy, enterprise solution architecture, and fintech advisory — or a conversation across any of the personal lenses below.
          </p>
        </div>

        {/* 1. Beyond the Architecture — Personal Interests & Lenses */}
        <div
          data-testid="personal-interests-panel"
          className="apple-glass p-5 sm:p-7 rounded-2xl sm:rounded-3xl border border-white/10 space-y-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-cyan-400" />
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight font-display">
                Beyond the Architecture — Personal Interests &amp; Lenses
              </h3>
            </div>
            <span className="text-[11px] font-mono text-cyan-400">
              CLICK A LENS TO TINT 3D HORIZON PORTAL
            </span>
          </div>

          {/* 5 Interactive Passion Pills */}
          <div className="flex flex-wrap gap-2">
            {PERSONAL_INTEREST_LENSES.map((lens) => {
              const isSelected = lens.id === selectedInterestId;
              return (
                <button
                  key={lens.id}
                  type="button"
                  data-testid={`interest-pill-${lens.id}`}
                  aria-pressed={isSelected}
                  onClick={() => handleSelectInterestLens(lens, false)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer flex items-center gap-2 min-h-[44px] border ${
                    isSelected
                      ? 'bg-white/15 text-white font-semibold shadow-lg'
                      : 'bg-white/[0.04] text-neutral-300 hover:bg-white/10 hover:text-white border-white/10'
                  }`}
                  style={
                    isSelected
                      ? { borderColor: lens.color, boxShadow: `0 0 18px ${lens.color}33` }
                      : undefined
                  }
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: lens.color }}
                  />
                  <span>{lens.title}</span>
                </button>
              );
            })}
          </div>

          {/* Active Lens Spotlight Card */}
          <div
            data-testid="active-interest-spotlight"
            className="p-4 sm:p-5 rounded-2xl bg-slate-950/75 border transition-all space-y-2"
            style={{ borderColor: `${activeLens.color}55` }}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span
                className="text-xs font-mono font-bold uppercase tracking-wider"
                style={{ color: activeLens.color }}
              >
                {activeLens.title}
              </span>
              <span className="text-[11px] font-mono text-neutral-400">
                {activeLens.tagline}
              </span>
            </div>
            <p className="text-xs sm:text-sm text-neutral-200 leading-relaxed">
              {activeLens.description}
            </p>
          </div>
        </div>

        {/* 2. Ways to Approach Me — Interactive Conversation Starters */}
        <div
          data-testid="ways-to-approach-panel"
          className="apple-glass p-5 sm:p-7 rounded-2xl sm:rounded-3xl border border-white/10 space-y-4"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <MessageSquarePlus className="w-4 h-4 text-emerald-400" />
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight font-display">
                Ways to Approach Me
              </h3>
            </div>
            <span className="text-[11px] font-mono text-neutral-400">
              SELECT A CONVERSATION STARTER TO PRE-FILL DISPATCH
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {PERSONAL_INTEREST_LENSES.map((lens) => {
              const isSelected = inquirySubject === lens.approachSubject;
              return (
                <button
                  key={lens.id}
                  type="button"
                  data-testid={`approach-starter-${lens.id}`}
                  aria-pressed={isSelected}
                  onClick={() => handleSelectInterestLens(lens, true)}
                  className={`p-3.5 rounded-xl text-left transition-all cursor-pointer border flex flex-col justify-between gap-1.5 ${
                    isSelected
                      ? 'bg-white/12 border-cyan-400/60 text-white shadow-md'
                      : 'bg-white/[0.03] border-white/10 text-neutral-300 hover:bg-white/[0.07] hover:text-white'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className="text-[10px] font-mono font-bold uppercase tracking-wider"
                      style={{ color: lens.color }}
                    >
                      {lens.shortLabel}
                    </span>
                    {isSelected && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-semibold">
                        Selected
                      </span>
                    )}
                  </div>
                  <div className="text-xs sm:text-sm font-semibold text-white">
                    {lens.approachTitle}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. Direct Executive Coordinates & Direct Dispatch Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          {/* Direct Coordinates & Quick Actions with Concentric Radar Beacon */}
          <div className="apple-glass p-5 sm:p-7 rounded-2xl sm:rounded-3xl border-t-2 border-cyan-400/40 space-y-5 relative overflow-hidden">
            {/* Concentric 2D Radar Pulse Beacon Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative flex items-center justify-center w-10 h-10 flex-shrink-0" aria-label="Concentric Radar Beacon">
                  <span className="absolute w-10 h-10 rounded-full border border-cyan-400/20 animate-ping" />
                  <span className="absolute w-7 h-7 rounded-full border border-cyan-400/40" />
                  <span className="absolute w-4 h-4 rounded-full border border-cyan-400/70" />
                  <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-lg shadow-cyan-400/60" />
                </div>
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight font-display">
                    Direct Executive Coordinates
                  </h3>
                  <span className="text-[11px] font-mono text-cyan-400">TELEMETRY BEACON LIVE</span>
                </div>
              </div>
              <div className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-[11px] font-mono text-neutral-300">
                <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                <span>RADAR ACTIVE</span>
              </div>
            </div>

            <p className="text-xs text-neutral-400 leading-relaxed font-sans">
              Open to fractional AI strategy, enterprise architecture reviews, and global leadership roles.
            </p>

            <div className="space-y-3">
              {/* Email Contact + Copy Email Address Button */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-2 rounded-2xl bg-white/5 border border-white/5">
                <a
                  href="mailto:ziyang.ang02@gmail.com"
                  className="flex-1 flex items-center gap-3 p-2.5 text-neutral-200 text-xs font-mono min-h-[44px] hover:text-white transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 flex-shrink-0">
                    <Mail className="w-4 h-4" />
                  </div>
                  <span className="truncate">ziyang.ang02@gmail.com</span>
                </a>

                <button
                  type="button"
                  onClick={handleCopyEmail}
                  aria-label="Copy Email Address"
                  className="min-h-[44px] px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-neutral-200 hover:text-white transition-all flex items-center justify-center gap-2 text-xs font-mono cursor-pointer border border-white/10"
                >
                  {copiedEmail ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400 font-semibold">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Copy Email Address</span>
                    </>
                  )}
                </button>
              </div>

              <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-white/5 border border-white/5 text-neutral-300 text-xs font-mono min-h-[48px]">
                <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 flex-shrink-0">
                  <MapPin className="w-4 h-4" />
                </div>
                <span>Kuala Lumpur, Malaysia (Open to Global Remote)</span>
              </div>
            </div>

            <div className="flex flex-col gap-2.5 pt-1">
              <a
                href={`mailto:ziyang.ang02@gmail.com?subject=${encodeURIComponent(inquirySubject)}&body=Hi%20Zachary%2C%0A%0AI%20would%20like%20to%20get%20in%20touch%20regarding...`}
                className="w-full min-h-[46px] flex items-center justify-center gap-2 py-2.5 px-4 rounded-full text-xs font-semibold bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-md"
              >
                <Mail className="w-3.5 h-3.5" />
                <span>Get in Touch via Email</span>
              </a>

              <a
                href="mailto:ziyang.ang02@gmail.com?subject=Strategic%20Inquiry%20%2F%20Executive%20CV%20Request%20-%20Ang%20Zi%20Yang%20(Zachary)&body=Hi%20Zachary%2C%0A%0AI%20would%20like%20to%20request%20your%20executive%20CV%20and%20credentials%20brief."
                className="w-full min-h-[46px] flex items-center justify-center gap-2 py-2.5 px-4 rounded-full text-xs font-semibold apple-glass text-white hover:bg-white/10 transition-all cursor-pointer"
              >
                <FileDown className="w-3.5 h-3.5 text-cyan-400" />
                <span>Request Executive CV</span>
              </a>

              <div className="flex justify-center gap-2 pt-1">
                <a
                  href="https://www.linkedin.com/in/zacharyangziyang"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-11 h-11 rounded-full apple-glass text-neutral-300 hover:text-white hover:bg-white/10 transition-all border border-white/10 flex items-center justify-center cursor-pointer min-w-[44px] min-h-[44px]"
                  title="Connect on LinkedIn"
                >
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 8.76a1.64 1.64 0 0 0 0-3.28 1.64 1.64 0 0 0 0 3.28m1.4 9.74v-8.37H5.06v8.37h2.8z" />
                  </svg>
                </a>

                <a
                  href="https://github.com/ZacharyAng0309"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-11 h-11 rounded-full apple-glass text-neutral-300 hover:text-white hover:bg-white/10 transition-all border border-white/10 flex items-center justify-center cursor-pointer min-w-[44px] min-h-[44px]"
                  title="Explore GitHub"
                >
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                    <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z" />
                  </svg>
                </a>
              </div>
            </div>
          </div>

          {/* Executive Direct Dispatch Form */}
          <div className="apple-glass p-5 sm:p-7 rounded-2xl sm:rounded-3xl border-t-2 border-indigo-400/40">
            <div className="flex items-center justify-between gap-2 mb-2">
              <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight font-display">
                Direct Dispatch
              </h3>
              <Sparkles className="w-4 h-4 text-cyan-400" />
            </div>
            <p className="text-xs text-neutral-400 mb-4 font-sans">
              Leave a direct inquiry. Responses guaranteed within 24 hours.
            </p>

            {/* Active Inquiry Topic Pill */}
            <div className="mb-4 p-2.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between gap-2">
              <span className="text-[10px] font-mono uppercase text-neutral-400">Topic:</span>
              <span
                data-testid="selected-inquiry-topic"
                className="text-xs font-mono font-semibold text-cyan-300 truncate"
              >
                {inquirySubject}
              </span>
            </div>

            {submitted ? (
              <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-center space-y-2 animate-fadeIn">
                <CheckCircle2 className="w-8 h-8 mx-auto" />
                <div className="font-semibold text-sm">Message Transmitted Successfully</div>
                <p className="text-xs text-neutral-400">
                  Thank you. Zachary will review your inquiry promptly.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-bold">
                    Your Name / Organization
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Elena Rostova • Hilti Corporate IT"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs sm:text-sm placeholder:text-neutral-600 focus:outline-none focus:border-cyan-400 transition-colors min-h-[44px]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-bold">
                    Corporate Email
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="e.g. elena.rostova@hilti.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs sm:text-sm placeholder:text-neutral-600 focus:outline-none focus:border-cyan-400 transition-colors min-h-[44px]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-bold">
                    Executive Brief / Project Scope
                  </label>
                  <textarea
                    required
                    rows={4}
                    placeholder="Outline key objectives, timeline, or collaboration scope..."
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs sm:text-sm placeholder:text-neutral-600 focus:outline-none focus:border-cyan-400 transition-colors resize-none"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full min-h-[48px] py-3.5 px-6 rounded-full bg-white text-black text-xs sm:text-sm font-semibold hover:bg-neutral-200 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg hover:scale-101 active:scale-99"
                >
                  <span>Transmit Message</span>
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            )}
          </div>
        </div>

        <div className="pt-10 mt-10 border-t border-white/10 text-center sm:flex sm:justify-between sm:items-center text-xs text-neutral-500 font-mono space-y-3 sm:space-y-0">
          <div>
            © {CURRENT_YEAR} Zachary Ang Zi Yang.
          </div>
          <div className="flex flex-wrap justify-center gap-3 text-[11px]">
            <span>APPLE KEYNOTE AESTHETIC</span>
            <span>•</span>
            <span>THREE.JS WEBGL</span>
            <span>•</span>
            <span>REACT 19</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
