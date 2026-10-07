import React, { useState } from 'react';
import { CASE_STUDIES } from '../data/caseStudies';
import type { CaseStudy } from '../domain/contracts';
import { ArrowUpRight, ChevronDown, CheckCircle2, Cpu, ExternalLink, Award } from 'lucide-react';

interface AISolutionsSectionProps {
  onSelectCaseStudy: (study: CaseStudy) => void;
}

export const AISolutionsSection: React.FC<AISolutionsSectionProps> = ({ onSelectCaseStudy }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <section
      id="ai-solutions"
      aria-label="Flagship Artificial Intelligence Systems & Case Studies"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 py-20 sm:py-24 relative z-10 max-w-6xl mx-auto"
    >
      {/* Chapter Marker */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-400 font-mono text-xs uppercase tracking-wider border border-cyan-500/20 font-bold">
          Chapter 02 • AI Solutions &amp; Products
        </span>
        <span className="text-slate-500 text-[11px] sm:text-xs font-mono">
          AUTONOMOUS MULTI-AGENT, VERTEX AI &amp; ON-DEVICE SYSTEMS
        </span>
      </div>

      <h2 className="text-2xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
        Flagship Products &amp; <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-300">Generative AI Systems</span>
      </h2>

      <p className="text-slate-300 text-sm sm:text-base md:text-lg max-w-3xl mb-8 sm:mb-10 leading-relaxed">
        Engineering production-grade AI solutions that balance deep model capability with strict privacy, low latency, and measurable business impact. Explore all 5 flagship systems below:
      </p>

      {/* Grid of 5 Comprehensive Case Studies */}
      <div className="space-y-4">
        {CASE_STUDIES.map((study) => {
          const isExpanded = expandedId === study.id;
          return (
            <div
              key={study.id}
              className="glass-panel p-5 sm:p-6 rounded-2xl transition-all border-l-4 hover:border-cyan-400"
              style={{ borderLeftColor: study.accentColor }}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <button
                  type="button"
                  aria-expanded={isExpanded}
                  onClick={() => toggleExpand(study.id)}
                  className="w-full text-left cursor-pointer flex-1 py-1"
                >
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <span
                      className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold"
                      style={{ backgroundColor: `${study.accentColor}18`, color: study.accentColor }}
                    >
                      {study.category.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">{study.role}</span>
                    {study.featuredAward && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20">
                        <Award className="w-3 h-3" />
                        <span>{study.featuredAward}</span>
                      </span>
                    )}
                  </div>

                  <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-white group-hover:text-cyan-300 transition-colors">
                    {study.title}
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{study.subtitle}</p>
                </button>

                <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800">
                  <button
                    onClick={() => onSelectCaseStudy(study)}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 text-slate-200 hover:text-white hover:bg-slate-700 transition-colors text-xs font-semibold border border-slate-700 min-h-[40px] cursor-pointer"
                  >
                    <span>Inspect Drawer</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>

                  <button
                    type="button"
                    onClick={() => toggleExpand(study.id)}
                    className="flex items-center gap-1 px-2.5 py-2 rounded-xl text-xs font-mono text-cyan-400 hover:bg-cyan-500/10 transition-colors min-h-[40px] cursor-pointer"
                  >
                    <span className="hidden sm:inline">{isExpanded ? 'Collapse' : 'Expand'}</span>
                    <ChevronDown
                      className={`w-4 h-4 text-slate-400 transition-transform ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Quick Summary Preview */}
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mt-3">
                {study.description}
              </p>

              {/* Expandable Architecture & Implementation Deep-Dive */}
              {isExpanded && (
                <div className="pt-4 mt-4 border-t border-slate-800 space-y-4 animate-fadeIn">
                  {/* Problem & Discovery */}
                  <div>
                    <h4 className="text-xs font-mono uppercase text-slate-400 mb-1 font-bold">
                      Problem Space &amp; Discovery
                    </h4>
                    <p className="text-xs sm:text-sm text-slate-300 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                      {study.problemStatement}
                    </p>
                  </div>

                  {/* Architecture & Engineering Invariants */}
                  <div>
                    <h4 className="text-xs font-mono uppercase text-cyan-400 mb-1.5 font-bold flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5" />
                      <span>System Architecture &amp; Engineering Invariants</span>
                    </h4>
                    <div className="space-y-1.5">
                      {study.solutionArchitecture.map((arch, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-xs text-slate-200 bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/60">
                          <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                          <span>{arch}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Quantified Business & System Impact */}
                  <div>
                    <h4 className="text-xs font-mono uppercase text-emerald-400 mb-1.5 font-bold">
                      Quantified Performance &amp; Production Impact
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {study.impactMetrics.map((metric, idx) => (
                        <div key={idx} className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/20 text-xs text-emerald-200">
                          <span className="font-bold mr-1">•</span>
                          {metric}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Tech Stack Chips */}
                  <div>
                    <h4 className="text-xs font-mono uppercase text-slate-400 mb-1.5 font-bold">
                      Technology Stack
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {study.techStack.map((tech) => (
                        <span key={tech} className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800/80 text-slate-300 border border-slate-700/60">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Reference Links */}
                  {(study.externalUrl || study.repoUrl) && (
                    <div className="pt-2 flex flex-wrap gap-3">
                      {study.externalUrl && (
                        <a
                          href={study.externalUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 text-xs font-semibold hover:bg-cyan-500/20 hover:text-white transition-colors min-h-[44px]"
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
                          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-xs font-semibold hover:bg-indigo-500/20 hover:text-white transition-colors min-h-[44px]"
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
          );
        })}
      </div>
    </section>
  );
};
