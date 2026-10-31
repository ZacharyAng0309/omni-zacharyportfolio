import React, { useState } from 'react';
import { CASE_STUDIES } from '../data/caseStudies';
import type { CaseStudy } from '../domain/contracts';
import { ArrowUpRight, ChevronDown, CheckCircle2, Cpu, ExternalLink, Award, Layers, ShieldCheck, Zap } from 'lucide-react';

interface AISolutionsSectionProps {
  onSelectCaseStudy: (study: CaseStudy) => void;
}

export const AISolutionsSection: React.FC<AISolutionsSectionProps> = ({ onSelectCaseStudy }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isExploded, setIsExploded] = useState(false);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const handleExplodeStrata = () => {
    const nextState = !isExploded;
    setIsExploded(nextState);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:explode_strata', {
          detail: { exploded: nextState, timestamp: Date.now() },
        })
      );
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action: 'explode_strata', exploded: nextState, timestamp: Date.now() },
        })
      );
    }
  };

  return (
    <section
      id="ai-solutions"
      aria-label="Flagship Artificial Intelligence Systems & Case Studies"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 md:px-12 py-20 sm:py-24 relative z-10 max-w-7xl mx-auto w-full"
    >
      <div data-peek-hide className="w-full space-y-10">
        {/* Editorial Chapter Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-white/[0.08]">
          <div className="space-y-3 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 font-mono text-xs uppercase tracking-wider border border-cyan-500/20 font-bold">
                Act 05 • The Frontier • Production AI &amp; Fintech Systems
              </span>
              <span className="text-neutral-400 text-[11px] sm:text-xs font-mono">
                ENTERPRISE FINTECH • VERTEX AI VECTOR MATCHING • PRIVACY-FIRST TAURI
              </span>
            </div>

            <h2 className="text-3xl sm:text-5xl md:text-6xl font-black tracking-tight text-white font-display">
              Flagship Products &amp;{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-300">
                Generative AI Systems
              </span>
            </h2>

            <p className="text-neutral-300 text-sm sm:text-base leading-relaxed">
              Engineering production-grade AI solutions that balance deep model capability with strict privacy, low latency, and measurable business impact. Explore the flagship systems below:
            </p>
          </div>
        </div>

        {/* 12-Column Editorial Bento Grid for 5 Case Studies */}
        <div className="grid grid-cols-12 gap-6 sm:gap-7">
          {CASE_STUDIES.map((study, idx) => {
            const isExpanded = expandedId === study.id;
            // Top 2 hero case studies span 6 cols, next 3 span 4 cols
            const colSpan = idx < 2 ? 'col-span-12 lg:col-span-6' : 'col-span-12 md:col-span-6 lg:col-span-4';

            return (
              <div
                key={study.id}
                className={`${colSpan} group`}
              >
                <div
                  className="h-full glass-acrylic card-sheen p-6 sm:p-7 rounded-3xl flex flex-col justify-between border border-white/[0.08] hover:border-cyan-400/40 transition-all duration-300 shadow-xl"
                  style={{ borderTop: `3px solid ${study.accentColor}` }}
                >
                  <div>
                    {/* Header Badges */}
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider"
                          style={{ backgroundColor: `${study.accentColor}18`, color: study.accentColor }}
                        >
                          {study.category.toUpperCase()}
                        </span>
                        <span className="text-xs text-neutral-400 font-mono font-semibold">{study.role}</span>
                      </div>

                      {study.featuredAward && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/25">
                          <Award className="w-3 h-3 text-rose-400" />
                          <span>{study.featuredAward}</span>
                        </span>
                      )}
                    </div>

                    {/* Title & Accordion Trigger */}
                    <button
                      type="button"
                      aria-expanded={isExpanded}
                      onClick={() => toggleExpand(study.id)}
                      data-cursor="EXPAND"
                      className="w-full text-left cursor-pointer group-hover:text-cyan-300 transition-colors py-1"
                    >
                      <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight font-display mb-1">
                        {study.title}
                      </h3>
                      <p className="text-xs font-mono text-cyan-400/80 mt-0.5">{study.subtitle}</p>
                    </button>

                    {/* Quick Summary Preview */}
                    <p className="text-xs sm:text-sm text-neutral-300 leading-relaxed mt-3 mb-4">
                      {study.description}
                    </p>

                    {/* Key Metrics Scannable Preview Chips */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {study.impactMetrics.slice(0, 2).map((m, mIdx) => (
                        <span
                          key={mIdx}
                          className="text-[11px] font-mono text-emerald-300 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20"
                        >
                          ✓ {m}
                        </span>
                      ))}
                    </div>

                    {/* Expandable Architecture & Deep-Dive */}
                    {isExpanded && (
                      <div className="pt-4 border-t border-white/[0.08] space-y-4 animate-fadeIn">
                        <div>
                          <h4 className="text-xs font-mono uppercase text-neutral-400 mb-1 font-bold">
                            Problem Space &amp; Discovery
                          </h4>
                          <p className="text-xs sm:text-sm text-neutral-300 bg-black/40 p-3 rounded-2xl border border-white/[0.06]">
                            {study.problemStatement}
                          </p>
                        </div>

                        <div>
                          <h4 className="text-xs font-mono uppercase text-cyan-400 mb-1.5 font-bold flex items-center gap-1.5">
                            <Cpu className="w-3.5 h-3.5" />
                            <span>System Architecture &amp; Engineering Invariants</span>
                          </h4>
                          <div className="space-y-1.5">
                            {study.solutionArchitecture.map((arch, aIdx) => (
                              <div key={aIdx} className="flex items-start gap-2 text-xs text-neutral-200 bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.06]">
                                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                                <span>{arch}</span>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div>
                          <h4 className="text-xs font-mono uppercase text-emerald-400 mb-1.5 font-bold">
                            Quantified Performance &amp; Production Impact
                          </h4>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {study.impactMetrics.map((metric, metricIdx) => (
                              <div key={metricIdx} className="p-2.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-xs text-emerald-200">
                                <span className="font-bold mr-1">•</span>
                                {metric}
                              </div>
                            ))}
                          </div>
                        </div>

                        <div>
                          <h4 className="text-xs font-mono uppercase text-neutral-400 mb-1.5 font-bold">
                            Technology Stack
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {study.techStack.map((tech) => (
                              <span key={tech} className="px-2.5 py-1 rounded-lg text-[10px] font-mono bg-white/[0.04] text-neutral-300 border border-white/[0.08]">
                                {tech}
                              </span>
                            ))}
                          </div>
                        </div>

                        {(study.externalUrl || study.repoUrl) && (
                          <div className="pt-2 flex flex-wrap gap-3">
                            {study.externalUrl && (
                              <a
                                href={study.externalUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 text-xs font-bold hover:bg-cyan-500/20 hover:text-white transition-colors min-h-[44px]"
                              >
                                <span>Canonical Link</span>
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            )}
                            {study.repoUrl && (
                              <a
                                href={study.repoUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-xs font-bold hover:bg-indigo-500/20 hover:text-white transition-colors min-h-[44px]"
                              >
                                <span>Repository</span>
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Card Actions Footer */}
                  <div className="pt-4 border-t border-white/[0.08] mt-4 flex items-center justify-between gap-3">
                    <button
                      type="button"
                      onClick={() => onSelectCaseStudy(study)}
                      data-cursor="DRAWER"
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/[0.06] text-neutral-100 hover:text-white hover:bg-cyan-500/20 transition-all text-xs font-bold border border-white/10 hover:border-cyan-400/40 min-h-[44px] cursor-pointer"
                    >
                      <span>Inspect Drawer</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-cyan-400" />
                    </button>

                    <button
                      type="button"
                      onClick={() => toggleExpand(study.id)}
                      className="flex items-center gap-1 px-3 py-2 rounded-xl text-xs font-mono font-semibold text-cyan-400 hover:text-cyan-300 transition-colors min-h-[44px] cursor-pointer"
                    >
                      <span className="hidden sm:inline">{isExpanded ? 'Collapse' : 'Expand'}</span>
                      <ChevronDown
                        className={`w-4 h-4 text-neutral-400 transition-transform duration-200 ${
                          isExpanded ? 'rotate-180' : ''
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Dedicated EXPLODED STRATA STATUS • LIVE NODE Panel */}
        <div className="glass-acrylic card-sheen p-7 sm:p-8 rounded-3xl border border-cyan-500/30 shadow-[0_0_50px_rgba(0,242,254,0.08)] relative overflow-hidden space-y-6">
          <div
            className="absolute -top-24 -right-24 w-64 h-64 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none"
            aria-hidden="true"
          />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs mb-2.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
                <span className="font-bold uppercase tracking-wider">EXPLODED STRATA STATUS • LIVE NODE</span>
              </div>
              <h3 className="text-2xl sm:text-3xl font-black text-white tracking-tight font-display">
                Digital Wallet Core Architecture
              </h3>
              <p className="text-xs sm:text-sm text-neutral-300 leading-relaxed mt-1">
                3-tier decoupled fintech architecture powering Tier-1 enterprise banking super-apps across Southeast Asia.
              </p>
            </div>

            <div className="flex flex-col items-stretch sm:items-end gap-2 flex-shrink-0">
              <button
                type="button"
                onClick={handleExplodeStrata}
                data-cursor="STRATA"
                aria-label="Explode 3D Strata View"
                className="min-h-[48px] py-3 px-6 rounded-2xl bg-gradient-to-r from-cyan-400 to-blue-500 text-black hover:from-cyan-300 hover:to-blue-400 transition-all font-bold text-xs sm:text-sm flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-cyan-400/20 active:scale-95"
              >
                <Layers className="w-4 h-4 text-black" />
                <span>{isExploded ? 'Reset Strata View' : 'Explode 3D Strata View'}</span>
              </button>
              <span className="text-[10px] font-mono text-neutral-400 text-center sm:text-right">
                {isExploded ? '● 3D SCENE STATUS: STRATA EXPANDED' : '○ 3D SCENE STATUS: COMPACT CORE'}
              </span>
            </div>
          </div>

          {/* The 3 Strata Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Strata 01: Presentation & NFC */}
            <div className="p-4 sm:p-5 rounded-2xl bg-white/[0.03] border border-sky-500/20 hover:border-sky-500/40 transition-all space-y-2">
              <span className="text-[10px] font-mono font-bold text-sky-400 tracking-wider flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5" />
                STRATA 01 • PRESENTATION &amp; NFC
              </span>
              <span className="inline-block text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/25 font-bold">
                EMV L2 KERNEL
              </span>
              <div className="text-sm font-bold text-white font-display">
                Presentation &amp; NFC Antenna Loop
              </div>
              <p className="text-xs text-neutral-400 leading-relaxed">
                Sub-300ms tap-to-pay transaction latency, native biometric authentication, and tokenized NFC payload isolation.
              </p>
            </div>

            {/* Strata 02: Transaction Core */}
            <div className="p-4 sm:p-5 rounded-2xl bg-white/[0.03] border border-cyan-500/20 hover:border-cyan-500/40 transition-all space-y-2">
              <span className="text-[10px] font-mono font-bold text-cyan-400 tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                STRATA 02 • TRANSACTION CORE
              </span>
              <span className="inline-block text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/25 font-bold">
                0 DEFECT UAT
              </span>
              <div className="text-sm font-bold text-white font-display">
                Transaction Core &amp; Vector Matcher
              </div>
              <p className="text-xs text-neutral-400 leading-relaxed">
                Hardware-anchored AES-256 HSM signing, state-machine validation, and zero-defect enterprise UAT certification.
              </p>
            </div>

            {/* Strata 03: ISO 20022 Clearing */}
            <div className="p-4 sm:p-5 rounded-2xl bg-white/[0.03] border border-indigo-500/20 hover:border-indigo-500/40 transition-all space-y-2">
              <span className="text-[10px] font-mono font-bold text-indigo-400 tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" />
                STRATA 03 • ISO 20022 CLEARING
              </span>
              <span className="inline-block text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/25 font-bold">
                RTGS GATEWAY
              </span>
              <div className="text-sm font-bold text-white font-display">
                ISO 20022 Clearing &amp; Heatsink Settlement
              </div>
              <p className="text-xs text-neutral-400 leading-relaxed">
                ISO 8583 / ISO 20022 financial message translation, multi-rail settlement routing, and dual-audit compliance logging.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
