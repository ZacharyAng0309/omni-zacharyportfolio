import React, { useState } from 'react';
import { Newspaper, ExternalLink, ChevronDown, Award, MapPin, Sparkles } from 'lucide-react';
import { PRESS_CITES } from '../data/pressCites';

interface SummitSectionProps {
  onInspectPressModal: () => void;
}

export const SummitSection: React.FC<SummitSectionProps> = ({ onInspectPressModal }) => {
  const [expandedCiteId, setExpandedCiteId] = useState<string | null>(null);

  const dispatchTrophyPresent = (citeId?: string) => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action: 'trophy_present', citeId },
        })
      );
    }
  };

  const toggleCite = (id: string) => {
    dispatchTrophyPresent(id);
    setExpandedCiteId((prev) => (prev === id ? null : id));
  };

  return (
    <section
      id="summit"
      aria-label="The Swiss Summit & Hilti Global Championship"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 md:px-12 py-20 sm:py-24 relative z-10 max-w-7xl mx-auto w-full"
    >
      <div data-peek-hide className="w-full">
        {/* Editorial Chapter Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b border-white/[0.08]">
          <div className="space-y-3 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 font-mono text-xs uppercase tracking-wider border border-rose-500/20 font-bold">
                Act 04 • The Alpine Summit • Hilti Global Championship Peak
              </span>
              <span className="text-neutral-400 text-[11px] sm:text-xs font-mono">
                LOC: MOUNT PILATUS (2,128M), SWITZERLAND &amp; SCHAAN, LIECHTENSTEIN
              </span>
            </div>

            <h2 className="text-3xl sm:text-5xl md:text-6xl font-black tracking-tight text-white font-display">
              Global Grand Championship:{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-400 via-amber-300 to-yellow-200">
                The Swiss Alps &amp; Hilti ITC 2024
              </span>
            </h2>

            <p className="text-neutral-300 text-sm sm:text-base leading-relaxed">
              Leading an international university engineering team to global victory. Team Sweetzerland engineered <strong className="text-white font-semibold">Hireti</strong>, an enterprise AI talent orchestration platform aligning sustainable green upskilling with global workforce planning, out-innovating 53 university teams worldwide.
            </p>
          </div>
        </div>

        {/* 8/4 Asymmetric Editorial Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 sm:gap-7 mb-10">
          {/* 8-Column Alpine Expedition Bento Card */}
          <div
            onMouseEnter={() => dispatchTrophyPresent('summit-story')}
            data-cursor="EXPEDITION"
            className="md:col-span-8 glass-acrylic card-sheen p-7 sm:p-8 rounded-3xl flex flex-col justify-between border border-white/[0.08] hover:border-rose-500/40 transition-all duration-300"
            style={{ borderTop: '3px solid #f43f5e' }}
          >
            <div>
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/30 mb-5">
                <Award className="w-4 h-4 text-rose-400" />
                <span className="font-bold">1st Place Worldwide • Team Sweetzerland</span>
              </div>

              <h3 className="text-2xl sm:text-3xl font-black text-white mb-4 tracking-tight font-display">
                To the Land of the Alps: Corporate IT Presentation &amp; Alpine Ascent
              </h3>

              <p className="text-neutral-300 text-sm sm:text-base leading-relaxed mb-6">
                Following competitive hackathon phases, Zachary pitched Hireti before Hilti's global corporate IT executive jury in Schaan, Liechtenstein. As Global Grand Champions, the team was awarded an all-expenses-paid expedition to Hilti Headquarters and an alpine ascent across Lucerne and Mount Pilatus (2,128m) in November 2024.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-6 border-t border-white/[0.08] text-xs text-neutral-400 font-mono">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <span>Schaan, Liechtenstein &amp; Mount Pilatus (2,128m), Switzerland</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  dispatchTrophyPresent('inspect-modal');
                  onInspectPressModal();
                }}
                data-cursor="INSPECT"
                className="w-full sm:w-auto min-h-[46px] flex items-center justify-center gap-2 px-5 py-2.5 rounded-2xl bg-rose-500/15 text-rose-200 border border-rose-500/30 hover:bg-rose-500/30 hover:text-white transition-all text-xs font-bold cursor-pointer shadow-lg shadow-rose-500/10"
              >
                <Newspaper className="w-4 h-4 text-rose-400" />
                <span>Inspect Trophy Proof &amp; Modal Drawer</span>
              </button>
            </div>
          </div>

          {/* 4-Column The Star Editorial Highlight Card */}
          <div
            onMouseEnter={() => dispatchTrophyPresent('the-star')}
            data-cursor="THE STAR"
            className="md:col-span-4 glass-acrylic card-sheen p-7 sm:p-8 rounded-3xl flex flex-col justify-between border border-white/[0.08] hover:border-amber-400/40 transition-all duration-300"
            style={{ borderTop: '3px solid #f59e0b' }}
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono uppercase text-amber-400 font-bold flex items-center gap-2 tracking-wider">
                  <Newspaper className="w-4 h-4" />
                  The Star (StarEdu)
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 font-bold">
                  VERIFIED
                </span>
              </div>

              <h4 className="text-xl sm:text-2xl font-black text-white mb-3 tracking-tight font-display">
                "To the Land of the Alps, we go!"
              </h4>

              <p className="text-xs sm:text-sm text-neutral-300 leading-relaxed mb-5">
                Front-page feature in Malaysia’s premier English daily newspaper. Chronicles Zachary’s product leadership and global championship win.
              </p>

              <blockquote className="p-4 rounded-2xl bg-black/40 border-l-2 border-amber-400 text-xs sm:text-sm text-neutral-300 italic mb-6">
                "Team Sweetzerland emerged global champions of the 13th Hilti IT Competition... pitching Hireti."
              </blockquote>
            </div>

            <a
              href="https://www.thestar.com.my/news/education/2024/08/18/to-the-land-of-the-alps-we-go"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => dispatchTrophyPresent('the-star-link')}
              data-cursor="READ"
              className="w-full min-h-[46px] py-2.5 px-4 rounded-2xl text-xs font-bold bg-white/[0.06] text-neutral-200 hover:text-white hover:bg-amber-500/20 transition-all border border-white/10 hover:border-amber-400/40 flex items-center justify-center gap-2"
            >
              <span>Read Article on The Star</span>
              <ExternalLink className="w-3.5 h-3.5 text-amber-400" />
            </a>
          </div>
        </div>

        {/* Extensive Press & Media Citations Accordion */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
            <h3 className="text-xs font-mono uppercase tracking-widest text-neutral-400 flex items-center gap-2 font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>Verified Press Citations, ACM Research &amp; Industry Records ({PRESS_CITES.length})</span>
            </h3>
            <span className="text-[11px] font-mono text-neutral-500">
              National Daily • ACM SIGCHI • AI Hackathon • Petronas Energy • Institutional
            </span>
          </div>

          <div className="space-y-3">
            {PRESS_CITES.map((cite) => {
              const isExpanded = expandedCiteId === cite.id;
              return (
                <div
                  key={cite.id}
                  onMouseEnter={() => dispatchTrophyPresent(cite.id)}
                  className="glass-acrylic rounded-2xl p-5 sm:p-6 border-l-4 border-amber-400/80 transition-all hover:border-amber-400"
                >
                  <button
                    type="button"
                    aria-expanded={isExpanded}
                    onClick={() => toggleCite(cite.id)}
                    data-cursor="TRANSCRIPT"
                    className="w-full text-left flex items-start sm:items-center justify-between gap-3 cursor-pointer min-h-[48px]"
                  >
                    <div className="flex items-start sm:items-center gap-3">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-400 flex-shrink-0 mt-1.5 sm:mt-0 shadow-[0_0_8px_rgba(245,158,11,0.6)]" />
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-amber-400/10 text-amber-300 border border-amber-400/25 uppercase font-bold">
                            {cite.badge}
                          </span>
                          <span className="text-xs text-neutral-400 font-mono">{cite.date}</span>
                        </div>
                        <h4 className="text-sm sm:text-base font-bold text-white mt-1">
                          {cite.source}: {cite.title}
                        </h4>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0 pt-1 sm:pt-0">
                      <span className="text-xs font-mono text-cyan-400 hidden sm:inline">
                        {isExpanded ? 'Collapse' : 'Read Transcript'}
                      </span>
                      <ChevronDown
                        className={`w-4 h-4 text-neutral-400 transition-transform duration-200 ${
                          isExpanded ? 'rotate-180' : ''
                        }`}
                      />
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="pt-4 mt-4 border-t border-white/[0.08] space-y-3 text-xs sm:text-sm text-neutral-300 leading-relaxed animate-fadeIn">
                      <blockquote className="p-4 rounded-2xl bg-black/40 border-l-2 border-amber-400 text-neutral-200 italic">
                        "{cite.quote}"
                      </blockquote>
                      <p>{cite.description}</p>
                      <div className="space-y-1.5 pt-1">
                        {cite.highlights.map((h, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs text-neutral-300">
                            <span className="text-amber-400 font-bold">•</span>
                            <span>{h}</span>
                          </div>
                        ))}
                      </div>
                      <div className="pt-2">
                        <a
                          href={cite.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          data-cursor="SOURCE"
                          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-500/15 text-amber-300 border border-amber-500/30 text-xs font-bold hover:bg-amber-500/25 hover:text-white transition-colors min-h-[44px]"
                        >
                          <span>Open Canonical Source</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};
