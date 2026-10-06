import React from 'react';
import { Download, EyeOff, Eye } from 'lucide-react';

interface NavbarHUDProps {
  activeSection: string;
  isReducedMotion: boolean;
  onToggleReducedMotion: () => void;
  onResumeClick: () => void;
}

export const NavbarHUD: React.FC<NavbarHUDProps> = ({
  activeSection,
  isReducedMotion,
  onToggleReducedMotion,
  onResumeClick,
}) => {
  const navItems = [
    { id: 'hero', label: 'Overview' },
    { id: 'summit', label: 'The Summit' },
    { id: 'ai-solutions', label: 'AI Architecture' },
    { id: 'vault', label: 'Credentials' },
    { id: 'timeline', label: 'Specs' },
    { id: 'contact', label: 'Connect' },
  ];

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-4 py-3 sm:px-8">
      <nav
        role="navigation"
        aria-label="Apple Keynote Navigation"
        className="max-w-5xl mx-auto flex items-center justify-between px-5 py-2.5 rounded-full apple-glass transition-all duration-300"
      >
        {/* Brand / Monogram */}
        <div
          onClick={() => scrollTo('hero')}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-7 h-7 rounded-full bg-white/10 border border-white/20 flex items-center justify-center font-bold text-xs tracking-tighter text-white group-hover:scale-105 transition-transform">
            ZA
          </div>
          <span className="font-semibold tracking-tight text-white text-sm">
            Zachary Ang
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-neutral-400 font-mono">
            Pro
          </span>
        </div>

        {/* Apple Style Section Pills */}
        <div className="hidden md:flex items-center gap-6 text-xs font-medium text-neutral-400">
          {navItems.map((item) => {
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => scrollTo(item.id)}
                className={`transition-colors cursor-pointer ${
                  isActive
                    ? 'text-white font-semibold'
                    : 'hover:text-white'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Actions & Accessibility */}
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleReducedMotion}
            title={isReducedMotion ? 'Enable 3D Animations' : 'Reduce 3D Motion'}
            aria-label={isReducedMotion ? 'Enable 3D Animations' : 'Reduce 3D Motion'}
            className="p-1.5 rounded-full text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            {isReducedMotion ? <EyeOff className="w-3.5 h-3.5 text-amber-400" /> : <Eye className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={onResumeClick}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-full bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-sm hover:scale-102 active:scale-98"
          >
            <Download className="w-3 h-3" />
            <span>Resume</span>
          </button>
        </div>
      </nav>
    </header>
  );
};
