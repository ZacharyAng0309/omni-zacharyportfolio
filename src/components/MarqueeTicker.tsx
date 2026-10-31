import React from 'react';

interface MarqueeTickerProps {
  className?: string;
}

const TICKER_ITEMS = [
  { icon: '🥇', label: 'HILTI GLOBAL IT CHAMPION', detail: '1st of 184 teams worldwide' },
  { icon: '⚡', label: '3.89 FIRST CLASS HONOURS', detail: 'Top 5% Academic Valedictorian' },
  { icon: '☁️', label: 'GOOGLE CLOUD ACE CERTIFIED', detail: 'Production Distributed Infrastructure' },
  { icon: '🏆', label: '4X GLOBAL HACKATHON WINNER', detail: 'APU, Hilti, Shell, AWS' },
  { icon: '🤖', label: 'ENTERPRISE AI PLATFORMS', detail: 'Autonomous Multi-Agent Architectures' },
  { icon: '🏔️', label: 'SWISS ALPS PILATUS EXPEDITION', detail: 'High-Altitude Keynote Presenter' },
];

export const MarqueeTicker: React.FC<MarqueeTickerProps> = ({ className = '' }) => {
  // Duplicate list twice for seamless 100% infinite translateX marquee
  const items = [...TICKER_ITEMS, ...TICKER_ITEMS];

  return (
    <div
      className={`relative w-full overflow-hidden border-y border-white/[0.06] bg-black/40 py-3.5 backdrop-blur-md ${className}`}
      data-peek-hide="true"
      aria-label="Accreditation Highlights Ticker"
    >
      {/* Side Vignette Fades */}
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-24 bg-gradient-to-r from-[#050507] to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-24 bg-gradient-to-l from-[#050507] to-transparent" />

      <div className="animate-marquee items-center gap-10">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="flex items-center gap-3 whitespace-nowrap px-2"
          >
            <span className="text-base">{item.icon}</span>
            <span className="font-mono text-xs font-bold tracking-wider text-white/90 uppercase">
              {item.label}
            </span>
            <span className="text-white/30">•</span>
            <span className="font-sans text-xs text-cyan-300/80">
              {item.detail}
            </span>
            <span className="ml-6 text-white/10">/</span>
          </div>
        ))}
      </div>
    </div>
  );
};
