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
      aria-label="Executive Introduction & Product Reveal"
      className="relative min-h-[140vh] sm:min-h-[160vh] flex flex-col items-center justify-start pt-24 sm:pt-32 pb-16 sm:pb-20 px-4 sm:px-6 hero-spotlight"
    >
      <div className="sticky top-20 sm:top-28 max-w-5xl mx-auto text-center flex flex-col items-center pointer-events-auto w-full">
        {/* Apple Keynote Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 sm:px-3.5 sm:py-1.5 rounded-full bg-white/5 border border-white/10 text-[11px] sm:text-xs font-medium text-neutral-300 mb-6 sm:mb-8 backdrop-blur-xl max-w-[90vw] text-center">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
          <span className="truncate">Global Grand Champion • Hilti IT Competition 2024</span>
        </div>

        {/* Monumental Responsive Headline */}
        <h1 className="text-3xl sm:text-5xl md:text-7xl lg:text-8xl font-bold tracking-tighter leading-[1.08] mb-4 sm:mb-6 headline-gradient max-w-4xl px-2">
          Architect of Enterprise Intelligence.
        </h1>

        {/* Sub-headline */}
        <p className="text-sm sm:text-lg md:text-2xl text-neutral-400 font-normal max-w-2xl mx-auto mb-8 sm:mb-10 leading-relaxed tracking-tight px-3">
          Ang Zi Yang (Zachary). Bridging cutting-edge Generative AI with disciplined product execution and scalable fintech systems.
        </p>

        {/* Keynote CTAs (Mobile Stacked / Desktop Inline) */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 w-full sm:w-auto px-4">
          <button
            onClick={onExploreClick}
            className="w-full sm:w-auto min-h-[48px] flex items-center justify-center gap-2 px-6 py-3.5 rounded-full bg-white text-black text-xs sm:text-sm font-semibold hover:bg-neutral-200 transition-all cursor-pointer shadow-lg hover:scale-102 active:scale-98"
          >
            <span>Explore The Journey</span>
            <ArrowDown className="w-4 h-4" />
          </button>

          <button
            onClick={onCaseStudiesClick}
            className="w-full sm:w-auto min-h-[48px] flex items-center justify-center gap-2 px-6 py-3.5 rounded-full apple-glass text-white text-xs sm:text-sm font-semibold hover:bg-white/10 transition-all cursor-pointer"
          >
            <span>Inspect Architecture</span>
            <ExternalLink className="w-4 h-4 text-cyan-400" />
          </button>
        </div>
      </div>
    </section>
  );
};
