import React, { useState } from 'react';
import { Newspaper, ExternalLink, ChevronDown, Award, MapPin } from 'lucide-react';
import { PRESS_CITES } from '../data/pressCites';

interface SummitSectionProps {
  onInspectPressModal: () => void;
}

export const SummitSection: React.FC<SummitSectionProps> = ({ onInspectPressModal }) => {
  const [expandedCiteId, setExpandedCiteId] = useState<string | null>(null);

  const toggleCite = (id: string) => {
    setExpandedCiteId((prev) => (prev === id ? null : id));
  };

  return (
    <section
      id="summit"
      aria-label="The Swiss Summit & Hilti Global Championship"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 py-20 sm:py-24 relative z-10 max-w-6xl mx-auto"
    >
      {/* Chapter Marker */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="px-2.5 py-1 rounded-md bg-rose-500/10 text-rose-400 font-mono text-xs uppercase tracking-wider border border-rose-500/20 font-bold">
          Chapter 01 • The Summit
        </span>
        <span className="text-slate-500 text-[11px] sm:text-xs font-mono">
          LOC: SCHAAN, LIECHTENSTEIN &amp; MOUNT PILATUS, SWITZERLAND
        </span>
      </div>

      <h2 className="text-2xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
        Global Grand Championship: <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-400 to-amber-300">The Swiss Alps &amp; Hilti ITC 2024</span>
      </h2>

      <p className="text-slate-300 text-sm sm:text-base md:text-lg max-w-3xl mb-8 sm:mb-10 leading-relaxed">
        Leading an international university engineering team to global victory. Team Sweetzerland engineered <strong className="text-white font-semibold">Hireti</strong>, an enterprise AI talent orchestration platform aligning sustainable green upskilling with global workforce planning, out-innovating 53 university teams worldwide.
      </p>

      {/* Main Feature Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 sm:gap-6 mb-8 sm:mb-10">
        {/* Story Bento Card */}
        <div className="md:col-span-8 glass-panel p-5 sm:p-8 rounded-2xl flex flex-col justify-between border-t-2 border-rose-500/60">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 mb-4">
              <Award className="w-3.5 h-3.5" />
              <span>1st Place Worldwide • Team Sweetzerland</span>
            </div>
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-3">
              To the Land of the Alps: Corporate IT Presentation &amp; Alpine Ascent
            </h3>
            <p className="text-slate-300 text-xs sm:text-sm md:text-base leading-relaxed mb-6">
              Following competitive hackathon phases, Zachary pitched Hireti before Hilti's global corporate IT executive jury in Schaan, Liechtenstein. As Global Grand Champions, the team was awarded an all-expenses-paid expedition to Hilti Headquarters and an alpine ascent across Lucerne and Mount Pilatus (2,128m) in November 2024.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-4 border-t border-slate-800 text-xs text-slate-400 font-mono">
            <div className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
              <span>Schaan, Liechtenstein &amp; Mount Pilatus (2,128m), Switzerland</span>
            </div>
            <button
              onClick={onInspectPressModal}
              className="w-full sm:w-auto min-h-[44px] flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-rose-500/10 text-rose-300 border border-rose-500/30 hover:bg-rose-500/20 hover:text-white transition-all text-xs font-semibold cursor-pointer"
            >
              <Newspaper className="w-3.5 h-3.5" />
              <span>Inspect Trophy Proof &amp; Modal Drawer</span>
            </button>
          </div>
        </div>

        {/* The Star Highlight Card */}
        <div className="md:col-span-4 glass-panel p-5 sm:p-8 rounded-2xl flex flex-col justify-between border-t-2 border-amber-400">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono uppercase text-amber-400 font-semibold flex items-center gap-1.5">
                <Newspaper className="w-3.5 h-3.5" />
                The Star (StarEdu)
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                VERIFIED
              </span>
            </div>
            <h4 className="text-lg sm:text-xl font-bold text-white mb-2">
              "To the Land of the Alps, we go!"
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed mb-4">
              Front-page feature in Malaysia’s premier English daily newspaper. Chronicles Zachary’s product leadership and global championship win.
            </p>
            <blockquote className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-400 italic mb-4">
              "Team Sweetzerland emerged global champions of the 13th Hilti IT Competition... pitching Hireti."
            </blockquote>
          </div>

          <a
            href="https://www.thestar.com.my/news/education/2024/05/12/to-the-land-of-the-alps-we-go"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full min-h-[44px] py-2.5 px-4 rounded-xl text-xs font-semibold bg-slate-800 text-slate-200 hover:text-white hover:bg-slate-700 transition-colors border border-slate-700 flex items-center justify-center gap-1.5"
          >
            <span>Read Article on The Star</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* EXTENSIVE LIST OF VERIFIED NATIONAL PRESS & MEDIA CITATIONS (EXPANDABLE ACCORDIONS) */}
      <div className="space-y-4">
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Newspaper className="w-3.5 h-3.5 text-amber-400" />
          <span>Complete List of Verified Press Citations &amp; Institutional Records</span>
        </h3>

        <div className="space-y-3">
          {PRESS_CITES.map((cite) => {
            const isExpanded = expandedCiteId === cite.id;
            return (
              <div
                key={cite.id}
                className="glass-panel rounded-2xl p-4 sm:p-5 border-l-4 border-amber-400/80 transition-all hover:border-amber-400"
              >
                <button
                  type="button"
                  aria-expanded={isExpanded}
                  onClick={() => toggleCite(cite.id)}
                  className="w-full text-left flex items-start sm:items-center justify-between gap-3 cursor-pointer min-h-[48px] py-1"
                >
                  <div className="flex items-start sm:items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400 flex-shrink-0 mt-1 sm:mt-0" />
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-400/10 text-amber-400 border border-amber-400/20 uppercase font-bold">
                          {cite.badge}
                        </span>
                        <span className="text-xs text-slate-400 font-mono">{cite.date}</span>
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
                      className={`w-4 h-4 text-slate-400 transition-transform ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </button>

                {isExpanded && (
                  <div className="pt-4 mt-4 border-t border-slate-800 space-y-3 text-xs sm:text-sm text-slate-300 leading-relaxed animate-fadeIn">
                    <blockquote className="p-3.5 rounded-xl bg-slate-950/70 border-l-2 border-amber-400 text-slate-200 italic">
                      "{cite.quote}"
                    </blockquote>
                    <p>{cite.description}</p>
                    <div className="space-y-1.5 pt-1">
                      {cite.highlights.map((h, i) => (
                        <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
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
                        className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-semibold hover:bg-amber-500/20 hover:text-white transition-colors min-h-[44px]"
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
    </section>
  );
};
