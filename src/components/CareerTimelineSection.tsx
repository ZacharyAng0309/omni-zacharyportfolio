import React, { useState } from 'react';
import { TIMELINE_MILESTONES } from '../data/timeline';
import { Briefcase, Calendar, MapPin, ChevronDown, CheckCircle2 } from 'lucide-react';

export const CareerTimelineSection: React.FC = () => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <section
      id="timeline"
      aria-label="Career Journey & Milestones"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 py-20 sm:py-24 relative z-10 max-w-5xl mx-auto"
    >
      {/* Chapter Marker */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 font-mono text-xs uppercase tracking-wider border border-emerald-500/20 font-bold">
          Chapter 04 • Career Journey &amp; Milestones
        </span>
        <span className="text-slate-500 text-[11px] sm:text-xs font-mono">
          CALIBRATED ENTERPRISE &amp; COMMUNITY TRAJECTORY
        </span>
      </div>

      <h2 className="text-2xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
        Calibrated Milestones &amp; <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-300">Leadership Trajectory</span>
      </h2>

      <p className="text-slate-300 text-sm sm:text-base md:text-lg max-w-3xl mb-8 sm:mb-10 leading-relaxed">
        Balancing autonomous Generative AI innovation, high-impact developer community leadership, and disciplined enterprise systems analysis.
      </p>

      {/* Vertical Interactive Timeline (Optimized Indentation on Mobile) */}
      <div className="relative border-l-2 border-slate-800 ml-2 sm:ml-6 space-y-6 sm:space-y-8">
        {TIMELINE_MILESTONES.map((item) => {
          const isExpanded = expandedId === item.id;
          return (
            <div key={item.id} className="relative pl-5 sm:pl-8 group">
              {/* Timeline Icon Node */}
              <div
                className={`absolute -left-[14px] sm:-left-[17px] top-2 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center border-2 ${
                  item.isHero
                    ? 'bg-slate-900 border-cyan-400 text-cyan-300 shadow-md shadow-cyan-500/20'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                <Briefcase className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
              </div>

              {/* Card Container */}
              <div
                className={`glass-panel p-4 sm:p-6 rounded-2xl transition-all ${
                  item.isHero ? 'border-cyan-500/40' : 'border-slate-800/80'
                }`}
              >
                <button
                  type="button"
                  aria-expanded={isExpanded}
                  onClick={() => toggleExpand(item.id)}
                  className="w-full text-left flex flex-wrap items-center justify-between gap-2 cursor-pointer min-h-[44px]"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="text-xs font-mono font-semibold text-cyan-400 flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        {item.period}
                      </span>
                      <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {item.location}
                      </span>
                    </div>

                    <h3 className="text-base sm:text-xl font-bold text-white mb-0.5">
                      {item.role}
                    </h3>
                    <div className="text-xs sm:text-sm text-slate-300 font-semibold">
                      {item.organization}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 text-xs font-mono text-cyan-400 flex-shrink-0">
                    <span className="hidden sm:inline">{isExpanded ? 'Collapse' : 'Expand Details'}</span>
                    <ChevronDown
                      className={`w-4 h-4 text-slate-400 transition-transform ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </button>

                {/* Always-visible First Impact */}
                <div className="mt-3 sm:mt-4 pt-3 border-t border-slate-800/80">
                  <div className="flex items-start gap-2 text-xs text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                    <span>{item.keyImpacts[0]}</span>
                  </div>
                </div>

                {/* Expandable Extended Impacts */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-800 space-y-2 animate-fadeIn">
                    {item.keyImpacts.slice(1).map((impact, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                        <CheckCircle2 className="w-3.5 h-3.5 text-slate-500 flex-shrink-0 mt-0.5" />
                        <span>{impact}</span>
                      </div>
                    ))}
                    {item.techOrDomain && (
                      <div className="pt-2 flex flex-wrap gap-1.5">
                        {item.techOrDomain.map((domain) => (
                          <span
                            key={domain}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 border border-slate-800 text-slate-400"
                          >
                            {domain}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
