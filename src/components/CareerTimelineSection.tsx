import React, { useState, useMemo } from 'react';
import { TIMELINE_MILESTONES } from '../data/timeline';
import { Calendar, MapPin, ChevronDown, CheckCircle2, TrendingUp, Clock, Sparkles } from 'lucide-react';

export const CareerTimelineSection: React.FC = () => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<'storyline' | 'latest'>('storyline');

  const sortedMilestones = useMemo(() => {
    const items = [...TIMELINE_MILESTONES];
    if (sortMode === 'storyline') {
      return items.sort(
        (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
      );
    }
    return items.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }, [sortMode]);

  const dispatchTomeInspect = (milestoneId: string) => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action: 'tome_inspect', milestoneId },
        })
      );
    }
  };

  const toggleExpand = (id: string) => {
    dispatchTomeInspect(id);
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <section
      id="timeline"
      aria-label="Career Journey & Milestones"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 md:px-12 pt-28 sm:pt-32 pb-20 sm:pb-24 relative z-10 max-w-7xl mx-auto w-full"
    >
      <div data-peek-hide className="w-full">
        {/* Editorial Chapter Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b border-white/[0.08]">
          <div className="space-y-3 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-mono text-xs uppercase tracking-wider border border-emerald-500/20 font-bold">
                Act 02 • The Academy • Academic Foundations &amp; Career Ascent
              </span>
              <span className="text-neutral-400 text-[11px] sm:text-xs font-mono">
                UK FIRST-CLASS BSC (3.75) • APU SE DIPLOMA DISTINCTION (3.89)
              </span>
            </div>

            <h2 className="text-3xl sm:text-5xl md:text-6xl font-black tracking-tight text-white font-display">
              Calibrated Milestones &amp;{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-300">
                Growth Storyline
              </span>
            </h2>

            <p className="text-neutral-300 text-sm sm:text-base leading-relaxed">
              Trace Zachary’s chronological growth from 3.89 CGPA software engineering diploma and 3.75 First-Class BSc foundations at APU to enterprise fintech architecture at Soft Space.
            </p>
          </div>

          {/* Storyline Ascent vs Latest First Sort Toggle */}
          <div
            role="group"
            aria-label="Timeline Sort Order"
            className="inline-flex items-center p-1.5 rounded-2xl bg-white/[0.04] border border-white/10 backdrop-blur-xl self-start md:self-end"
          >
            <button
              type="button"
              data-testid="sort-storyline-btn"
              data-cursor="SORT"
              aria-pressed={sortMode === 'storyline'}
              onClick={() => {
                setSortMode('storyline');
                dispatchTomeInspect('sort-storyline');
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer min-h-[44px] ${
                sortMode === 'storyline'
                  ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/20'
                  : 'text-neutral-400 hover:text-white'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              <span>📈 Growth Storyline</span>
            </button>

            <button
              type="button"
              data-testid="sort-latest-btn"
              data-cursor="SORT"
              aria-pressed={sortMode === 'latest'}
              onClick={() => {
                setSortMode('latest');
                dispatchTomeInspect('sort-latest');
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer min-h-[44px] ${
                sortMode === 'latest'
                  ? 'bg-cyan-400 text-black shadow-lg shadow-cyan-400/20'
                  : 'text-neutral-400 hover:text-white'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>🕒 Latest First</span>
            </button>
          </div>
        </div>

        {/* 12-Column Editorial Bento Grid */}
        <div className="grid grid-cols-12 gap-5 sm:gap-6">
          {sortedMilestones.map((item, index) => {
            const isExpanded = expandedId === item.id;
            const stepNumber = sortMode === 'storyline' ? index + 1 : sortedMilestones.length - index;
            const isWide = item.isHero || index % 3 === 0;

            return (
              <div
                key={item.id}
                data-milestone-id={item.id}
                onMouseEnter={() => dispatchTomeInspect(item.id)}
                className={`col-span-12 ${
                  isWide ? 'lg:col-span-7' : 'lg:col-span-5'
                } group`}
              >
                <div
                  className={`h-full glass-acrylic card-sheen p-6 sm:p-7 rounded-3xl transition-all duration-300 flex flex-col justify-between ${
                    item.isHero
                      ? 'border-cyan-400/40 shadow-[0_0_30px_rgba(0,242,254,0.06)]'
                      : 'border-white/[0.08] hover:border-white/20'
                  }`}
                >
                  <div>
                    {/* Header Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-[10px] font-mono font-bold text-emerald-400">
                          STEP 0{stepNumber}
                        </span>
                        {item.isHero && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-[10px] font-mono font-bold text-cyan-300">
                            <Sparkles className="w-3 h-3" />
                            KEY MILESTONE
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-xs font-mono text-neutral-400">
                        <span className="flex items-center gap-1 text-cyan-400">
                          <Calendar className="w-3.5 h-3.5" />
                          {item.period}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-neutral-500" />
                          {item.location}
                        </span>
                      </div>
                    </div>

                    {/* Role & Org Trigger */}
                    <button
                      type="button"
                      aria-expanded={isExpanded}
                      onClick={() => toggleExpand(item.id)}
                      data-cursor="INSPECT"
                      className="w-full text-left cursor-pointer group-hover:text-cyan-300 transition-colors min-h-[44px] flex flex-col justify-center"
                    >
                      <h3 className="text-xl sm:text-2xl font-bold text-white mb-1 tracking-tight font-display">
                        {item.role}
                      </h3>
                      <div className="text-sm sm:text-base text-neutral-300 font-semibold mb-4">
                        {item.organization}
                      </div>
                    </button>

                    {/* Primary Impact Contract */}
                    <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/[0.06] mb-3">
                      <div className="flex items-start gap-2.5 text-xs sm:text-sm text-neutral-200 leading-relaxed">
                        <CheckCircle2 className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                        <span>{item.keyImpacts[0]}</span>
                      </div>
                    </div>

                    {/* Expandable Extended Impacts */}
                    {isExpanded && (
                      <div className="pt-3 border-t border-white/[0.08] space-y-2.5 animate-fadeIn">
                        {item.keyImpacts.slice(1).map((impact, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-xs sm:text-sm text-neutral-300">
                            <CheckCircle2 className="w-3.5 h-3.5 text-neutral-500 flex-shrink-0 mt-0.5" />
                            <span>{impact}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Footer & Domain Tags */}
                  <div className="pt-4 mt-4 border-t border-white/[0.06] flex items-center justify-between gap-2">
                    <div className="flex flex-wrap gap-1.5">
                      {item.techOrDomain?.slice(0, 3).map((domain) => (
                        <span
                          key={domain}
                          className="px-2.5 py-1 rounded-lg text-[10px] font-mono bg-white/[0.04] border border-white/[0.08] text-neutral-400"
                        >
                          {domain}
                        </span>
                      ))}
                    </div>

                    <button
                      type="button"
                      aria-expanded={isExpanded}
                      onClick={() => toggleExpand(item.id)}
                      className="min-h-[44px] flex items-center gap-1.5 text-xs font-mono font-semibold text-cyan-400 hover:text-cyan-300 flex-shrink-0 cursor-pointer"
                    >
                      <span>{isExpanded ? 'Collapse' : 'Expand Details'}</span>
                      <ChevronDown
                        className={`w-3.5 h-3.5 transition-transform duration-200 ${
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
      </div>
    </section>
  );
};
