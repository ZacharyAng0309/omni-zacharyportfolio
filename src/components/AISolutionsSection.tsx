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
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 py-24 relative z-10 max-w-6xl mx-auto"
    >
      {/* Chapter Marker */}
      <div className="flex items-center gap-2 mb-3">
        <span className="px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-400 font-mono text-xs uppercase tracking-wider border border-cyan-500/20 font-bold">
          Chapter 02 • AI Solutions &amp; Products
        </span>
        <span className="text-slate-500 text-xs font-mono">
          AUTONOMOUS MULTI-AGENT, VERTEX AI &amp; ON-DEVICE SYSTEMS
        </span>
      </div>

      <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
        Flagship Products &amp; <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-300">Generative AI Systems</span>
      </h2>

      <p className="text-slate-300 text-base sm:text-lg max-w-3xl mb-10 leading-relaxed">
        Engineering production-grade AI solutions that balance deep model capability with strict privacy, low latency, and measurable business impact. Explore all 5 flagship systems below:
      </p>

      {/* Grid of 5 Comprehensive Case Studies */}
      <div className="space-y-4">
        {CASE_STUDIES.map((study) => {
          const isExpanded = expandedId === study.id;
          return (
            <div
              key={study.id}
              className="glass-panel p-6 rounded-2xl transition-all border-l-4 hover:border-cyan-400"
              style={{ borderLeftColor: study.accentColor }}
            >
              <div
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer"
                onClick={() => toggleExpand(study.id)}
              >
                <div>
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

                  <h3 className="text-xl sm:text-2xl font-bold text-white group-hover:text-cyan-300 transition-colors">
                    {study.title}
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{study.subtitle}</p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectCaseStudy(study);
                    }}
                    className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 text-slate-200 hover:text-white hover:bg-slate-700 transition-colors text-xs font-semibold border border-slate-700"
                  >
                    <span>Full Modal Drawer</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                  <div className="flex items-center gap-1 text-xs font-mono text-cyan-400">
                    <span>{isExpanded ? 'Collapse' : 'Expand Architecture'}</span>
                    <ChevronDown
                      className={`w-4 h-4 text-slate-400 transition-transform ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </div>
              </div>

              {/* Quick Summary Preview */}
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mt-3">
                {study.description}
              </p>

              {/* Collapsible Deep Specs Drawer */}
              {isExpanded && (
                <div className="pt-5 mt-4 border-t border-slate-800 space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed animate-fadeIn">
                  <div>
                    <h5 className="text-xs font-mono uppercase font-bold text-rose-400 mb-1 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-rose-400" />
                      Problem Space &amp; Discovery
                    </h5>
                    <p className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-slate-300">
                      {study.problemStatement}
                    </p>
                  </div>

                  <div>
                    <h5 className="text-xs font-mono uppercase font-bold text-cyan-400 mb-2 flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5" />
                      System Design &amp; Architectural Invariants
                    </h5>
                    <div className="space-y-1.5">
                      {study.solutionArchitecture.map((arch, idx) => (
                        <div key={idx} className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/60 text-xs">
                          <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                          <span>{arch}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h5 className="text-xs font-mono uppercase font-bold text-emerald-400 mb-2">
                      Quantified Business &amp; Technical Impact
                    </h5>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      {study.impactMetrics.map((metric, idx) => (
                        <div key={idx} className="p-2.5 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-slate-200">
                          • {metric}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h5 className="text-xs font-mono uppercase font-bold text-slate-400 mb-1.5">
                      Technology Stack
                    </h5>
                    <div className="flex flex-wrap gap-1.5">
                      {study.techStack.map((tech, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-md text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2 flex flex-wrap gap-3">
                    {study.repoUrl && (
                      <a
                        href={study.repoUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 text-slate-200 border border-slate-700 text-xs font-semibold hover:text-white transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Open Canonical Source / Repository</span>
                      </a>
                    )}
                    <button
                      onClick={() => onSelectCaseStudy(study)}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 text-xs font-semibold hover:bg-cyan-500/25 transition-colors cursor-pointer"
                    >
                      <span>Open High-Res Inspection Modal</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};
