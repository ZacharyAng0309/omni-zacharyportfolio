import React, { useState, useEffect } from 'react';
import { Mail, EyeOff, Eye, Menu, X } from 'lucide-react';

interface NavbarHUDProps {
  activeSection: string;
  isReducedMotion: boolean;
  onToggleReducedMotion: () => void;
}

export const NavbarHUD: React.FC<NavbarHUDProps> = ({
  activeSection,
  isReducedMotion,
  onToggleReducedMotion,
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'hero', label: 'Overview' },
    { id: 'summit', label: 'The Summit' },
    { id: 'ai-solutions', label: 'AI Architecture' },
    { id: 'vault', label: 'Credentials' },
    { id: 'timeline', label: 'Specs' },
    { id: 'contact', label: 'Connect' },
  ];

  const scrollTo = (id: string) => {
    setIsMobileMenuOpen(false);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Close mobile menu on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsMobileMenuOpen(false);
    };
    if (isMobileMenuOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMobileMenuOpen]);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-3 py-2.5 sm:px-8 sm:py-3">
      <nav
        role="navigation"
        aria-label="Executive Portfolio Navigation"
        className="max-w-5xl mx-auto flex items-center justify-between px-4 py-2 sm:px-5 sm:py-2.5 rounded-full apple-glass transition-all duration-300 relative"
      >
        {/* Brand / Monogram */}
        <div
          onClick={() => scrollTo('hero')}
          className="flex items-center gap-2 sm:gap-2.5 cursor-pointer group min-h-[44px]"
        >
          <div className="w-7 h-7 rounded-full bg-white/10 border border-white/20 flex items-center justify-center font-bold text-xs tracking-tighter text-white group-hover:scale-105 transition-transform">
            ZA
          </div>
          <span className="font-semibold tracking-tight text-white text-sm">
            Zachary Ang
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-neutral-400 font-mono hidden xs:inline">
            Pro
          </span>
        </div>

        {/* Desktop Apple Style Section Pills */}
        <div className="hidden md:flex items-center gap-6 text-xs font-medium text-neutral-400">
          {navItems.map((item) => {
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => scrollTo(item.id)}
                className={`transition-colors cursor-pointer py-1 ${
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
        <div className="flex items-center gap-1.5 sm:gap-2">
          <button
            onClick={onToggleReducedMotion}
            title={isReducedMotion ? 'Enable 3D Animations' : 'Reduce 3D Motion'}
            aria-label={isReducedMotion ? 'Enable 3D Animations' : 'Reduce 3D Motion'}
            className="min-w-[40px] min-h-[40px] flex items-center justify-center rounded-full text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            {isReducedMotion ? <EyeOff className="w-4 h-4 text-amber-400" /> : <Eye className="w-4 h-4" />}
          </button>

          <a
            href="mailto:ziyang.ang02@gmail.com?subject=Strategic%20Inquiry%20-%20Ang%20Zi%20Yang%20(Zachary)"
            className="hidden sm:flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-full bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-sm hover:scale-102 active:scale-98 min-h-[36px]"
          >
            <Mail className="w-3 h-3 text-black" />
            <span>Get in Touch</span>
          </a>

          {/* Mobile Hamburger Toggle Button (min 44x44px touch target) */}
          <button
            onClick={() => setIsMobileMenuOpen((prev) => !prev)}
            aria-expanded={isMobileMenuOpen}
            aria-label={isMobileMenuOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
            className="md:hidden min-w-[44px] min-h-[44px] flex items-center justify-center rounded-full text-neutral-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5 text-cyan-400" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile Frosted Navigation Drawer / Dropdown */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden max-w-5xl mx-auto mt-2 p-3 rounded-3xl apple-glass shadow-2xl animate-fadeIn border border-white/10"
          role="dialog"
          aria-label="Mobile Navigation"
        >
          <div className="flex flex-col space-y-1">
            {navItems.map((item) => {
              const isActive = activeSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => scrollTo(item.id)}
                  className={`w-full text-left px-4 py-3 rounded-2xl text-xs font-medium flex items-center justify-between transition-colors min-h-[44px] ${
                    isActive
                      ? 'bg-cyan-500/15 text-cyan-300 font-semibold border border-cyan-500/30'
                      : 'text-neutral-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <span>{item.label}</span>
                  {isActive && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />}
                </button>
              );
            })}

            <div className="pt-2 mt-2 border-t border-white/10 flex items-center gap-2">
              <a
                href="mailto:ziyang.ang02@gmail.com?subject=Strategic%20Inquiry%20-%20Ang%20Zi%20Yang%20(Zachary)"
                onClick={() => setIsMobileMenuOpen(false)}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-full text-xs font-semibold bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-md min-h-[44px]"
              >
                <Mail className="w-3.5 h-3.5" />
                <span>Get in Touch (Email)</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
