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
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 py-24 relative z-10 max-w-5xl mx-auto"
    >
      {/* Chapter Marker */}
      <div className="flex items-center gap-2 mb-3">
        <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 font-mono text-xs uppercase tracking-wider border border-emerald-500/20 font-bold">
          Chapter 04 • Career Journey &amp; Milestones
        </span>
        <span className="text-slate-500 text-xs font-mono">
          CALIBRATED ENTERPRISE &amp; COMMUNITY TRAJECTORY
        </span>
      </div>

      <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
        Calibrated Milestones &amp; <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-300">Leadership Trajectory</span>
      </h2>

      <p className="text-slate-300 text-base sm:text-lg max-w-3xl mb-10 leading-relaxed">
        Balancing autonomous Generative AI innovation, high-impact developer community leadership, and disciplined enterprise systems analysis.
      </p>

      {/* Vertical Interactive Timeline */}
      <div className="relative border-l-2 border-slate-800 ml-4 sm:ml-6 space-y-8">
        {TIMELINE_MILESTONES.map((item) => {
          const isExpanded = expandedId === item.id;
          return (
            <div key={item.id} className="relative pl-6 sm:pl-8 group">
              {/* Timeline Icon Node */}
              <div
                className={`absolute -left-[17px] top-1.5 w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                  item.isHero
                    ? 'bg-slate-900 border-cyan-400 text-cyan-300 shadow-md shadow-cyan-500/20'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                <Briefcase className="w-3.5 h-3.5" />
              </div>

              {/* Card Container */}
              <div
                className={`glass-panel p-6 rounded-2xl transition-all ${
                  item.isHero ? 'border-cyan-500/40' : 'border-slate-800/80'
                }`}
              >
                <div
                  className="flex flex-wrap items-center justify-between gap-2 cursor-pointer"
                  onClick={() => toggleExpand(item.id)}
                >
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono font-semibold text-cyan-400 flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        {item.period}
                      </span>
                      <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {item.location}
                      </span>
                    </div>

                    <h3 className="text-lg sm:text-xl font-bold text-white mb-0.5">
                      {item.role}
                    </h3>
                    <div className="text-sm text-slate-300 font-semibold">
                      {item.organization}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 text-xs font-mono text-cyan-400">
                    <span>{isExpanded ? 'Collapse' : 'Expand Details'}</span>
                    <ChevronDown
                      className={`w-4 h-4 text-slate-400 transition-transform ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </div>

                {/* Always-visible First Impact */}
                <div className="mt-4 pt-3 border-t border-slate-800/80">
                  <div className="flex items-start gap-2 text-xs text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                    <span>{item.keyImpacts[0]}</span>
                  </div>
                </div>

                {/* Collapsible Remaining Impacts */}
                {isExpanded && (
                  <div className="space-y-2 mt-3 pt-2 border-t border-slate-800/60 animate-fadeIn">
                    {item.keyImpacts.slice(1).map((impact, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                        <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{impact}</span>
                      </div>
                    ))}

                    {/* Tech & Domain Tags */}
                    <div className="flex flex-wrap gap-1.5 pt-3">
                      {item.techOrDomain.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-400 border border-slate-800"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
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
