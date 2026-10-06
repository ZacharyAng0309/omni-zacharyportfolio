import React from 'react';
import { ArrowDown, ExternalLink } from 'lucide-react';

interface HeroSectionProps {
  onExploreClick: () => void;
  onCaseStudiesClick: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onExploreClick,
  onCaseStudiesClick,
}) => {
  return (
    <section
      id="hero"
      aria-label="Apple Keynote Product Reveal"
      className="relative min-h-[160vh] flex flex-col items-center justify-start pt-32 pb-20 px-6 hero-spotlight"
    >
      <div className="sticky top-28 max-w-5xl mx-auto text-center flex flex-col items-center pointer-events-auto">
        {/* Apple Keynote Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-neutral-300 mb-8 backdrop-blur-xl">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Global Grand Champion • Hilti IT Competition 2024</span>
        </div>

        {/* Monumental Headline */}
        <h1 className="text-5xl sm:text-7xl md:text-8xl font-bold tracking-tighter leading-none mb-6 headline-gradient max-w-4xl">
          Architect of Enterprise Intelligence.
        </h1>

        {/* Sub-headline */}
        <p className="text-lg sm:text-2xl text-neutral-400 font-normal max-w-2xl mx-auto mb-10 leading-relaxed tracking-tight">
          Ang Zi Yang (Zachary). Bridging cutting-edge Generative AI with disciplined product execution and scalable fintech systems.
        </p>

        {/* Keynote CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
          <button
            onClick={onExploreClick}
            className="flex items-center gap-2 px-6 py-3.5 rounded-full bg-white text-black text-xs sm:text-sm font-semibold hover:bg-neutral-200 transition-all cursor-pointer shadow-lg hover:scale-102 active:scale-98"
          >
            <span>Explore The Journey</span>
            <ArrowDown className="w-4 h-4" />
          </button>

          <button
            onClick={onCaseStudiesClick}
            className="flex items-center gap-2 px-6 py-3.5 rounded-full apple-glass text-white text-xs sm:text-sm font-semibold hover:bg-white/10 transition-all cursor-pointer"
          >
            <span>Inspect Architecture</span>
            <ExternalLink className="w-4 h-4 text-cyan-400" />
          </button>
        </div>

        {/* Benchmark Bento Chips */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-4xl mx-auto">
          <div className="apple-glass p-5 sm:p-6 rounded-3xl text-left border-t border-rose-500/30">
            <div className="text-[11px] font-mono uppercase text-neutral-400 mb-1 tracking-wider">World Final</div>
            <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight mb-0.5">1st / 53</div>
            <div className="text-xs text-neutral-400">Teams Worldwide (Hilti)</div>
          </div>

          <div className="apple-glass p-5 sm:p-6 rounded-3xl text-left border-t border-cyan-500/30">
            <div className="text-[11px] font-mono uppercase text-neutral-400 mb-1 tracking-wider">Cloud Mastery</div>
            <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight mb-0.5">14 Quests</div>
            <div className="text-xs text-neutral-400">7 Vertex & Gemini Badges</div>
          </div>

          <div className="apple-glass p-5 sm:p-6 rounded-3xl text-left border-t border-indigo-500/30">
            <div className="text-[11px] font-mono uppercase text-neutral-400 mb-1 tracking-wider">Academic Merit</div>
            <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight mb-0.5">3.89 CGPA</div>
            <div className="text-xs text-neutral-400">APU Software Eng. Distinction</div>
          </div>

          <div className="apple-glass p-5 sm:p-6 rounded-3xl text-left border-t border-emerald-500/30">
            <div className="text-[11px] font-mono uppercase text-neutral-400 mb-1 tracking-wider">Ecosystem</div>
            <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight mb-0.5">500+</div>
            <div className="text-xs text-neutral-400">Engineers Mentored at GDSC</div>
          </div>
        </div>
      </div>
    </section>
  );
};
