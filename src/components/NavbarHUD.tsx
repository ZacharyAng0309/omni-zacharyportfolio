import React, { useState, useEffect } from 'react';
import { Mail, EyeOff, Eye, Menu, X, Volume2, VolumeX } from 'lucide-react';
import { scrollToSectionCinematic } from '../utils/cinematicScroll';
import { WHISPER_ACTS } from '../data/whisperActs';

interface NavbarHUDProps {
  activeSection: string;
  isReducedMotion: boolean;
  onToggleReducedMotion: () => void;
  isAudioEnabled?: boolean;
  onToggleAudio?: () => void;
  onSelectSection?: (sectionId: string) => void;
}

export const NavbarHUD: React.FC<NavbarHUDProps> = ({
  activeSection,
  isReducedMotion,
  onToggleReducedMotion,
  isAudioEnabled = false,
  onToggleAudio,
  onSelectSection,
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'hero', label: '01. Overview' },
    { id: 'timeline', label: '02. Growth' },
    { id: 'vault', label: '03. Mastery' },
    { id: 'summit', label: '04. Hilti Peak' },
    { id: 'ai-solutions', label: '05. Projects' },
    { id: 'contact', label: '06. Interests & Approach' },
  ];

  const scrollTo = (id: string) => {
    setIsMobileMenuOpen(false);
    if (onSelectSection) {
      onSelectSection(id);
    } else {
      scrollToSectionCinematic(id, { reducedMotion: isReducedMotion });
    }
  };

  // Close mobile menu on Escape key and lock body scroll
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsMobileMenuOpen(false);
    };
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isMobileMenuOpen]);

  return (
    <>
      {/* Full-Screen Mobile Backdrop Scrim to isolate menu from body content */}
      {isMobileMenuOpen && (
        <div
          data-testid="mobile-menu-backdrop"
          onClick={() => setIsMobileMenuOpen(false)}
          className="fixed inset-0 bg-black/85 backdrop-blur-xl z-[45] lg:hidden"
          aria-hidden="true"
        />
      )}

      <header
        data-peek-hide
        className="fixed top-0 left-0 right-0 z-50 px-3 pt-1.5 sm:px-8 sm:pt-1.5 pointer-events-none"
      >
        <nav
          role="navigation"
          aria-label="Executive Portfolio Navigation"
          className="pointer-events-auto max-w-5xl mx-auto flex items-center justify-between gap-2 px-4 py-1 sm:px-5 sm:py-1 rounded-full bg-[#0a0908]/82 backdrop-blur-2xl border border-white/12 shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_16px_36px_rgba(0,0,0,0.7)] transition-all duration-300 relative"
        >
          {/* Brand / Monogram */}
          <button
            type="button"
            onClick={() => scrollTo('hero')}
            className="flex items-center gap-2 sm:gap-2.5 cursor-pointer group min-h-[38px] shrink-0 text-left rounded-full pr-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F4F0EA]/80"
          >
            <div className="w-7 h-7 rounded-full bg-white/10 border border-white/20 flex items-center justify-center font-bold text-xs tracking-tighter text-white group-hover:scale-105 transition-transform">
              ZA
            </div>
            <span className="font-semibold tracking-tight text-white text-sm whitespace-nowrap">
              Zachary Ang
            </span>
          </button>

          {/* Desktop Apple Style Section Pills */}
          <div className="hidden lg:flex items-center lg:gap-4 xl:gap-6 text-xs font-medium text-neutral-400">
            {navItems.map((item) => {
              const isActive = activeSection === item.id;
              const actAccent =
                WHISPER_ACTS.find((a) => a.sectionId === item.id)?.accentColor ?? '#c8a97e';
              return (
                <button
                  key={item.id}
                  onClick={() => scrollTo(item.id)}
                  className={`relative transition-colors cursor-pointer py-1 whitespace-nowrap ${
                    isActive
                      ? 'text-white font-semibold'
                      : 'hover:text-white'
                  }`}
                >
                  {item.label}
                  {isActive && (
                    <span
                      aria-hidden="true"
                      className="absolute bottom-0 inset-x-0.5 h-[2px] rounded-full transition-colors duration-300"
                      style={{
                        backgroundColor: actAccent,
                        boxShadow: `0 0 8px ${actAccent}`,
                      }}
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Actions & Accessibility */}
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            {onToggleAudio && (
              <button
                onClick={onToggleAudio}
                title={isAudioEnabled ? 'Mute Procedural Web Audio' : 'Enable Procedural Web Audio'}
                aria-label={isAudioEnabled ? 'Mute Procedural Web Audio' : 'Enable Procedural Web Audio'}
                className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-full text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                {isAudioEnabled ? (
                  <Volume2 className="w-4 h-4 text-cyan-400 animate-pulse" />
                ) : (
                  <VolumeX className="w-4 h-4 text-neutral-400" />
                )}
              </button>
            )}

            <button
              onClick={onToggleReducedMotion}
              title={isReducedMotion ? 'Enable 3D Animations' : 'Reduce 3D Motion'}
              aria-label={isReducedMotion ? 'Enable 3D Animations' : 'Reduce 3D Motion'}
              className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-full text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              {isReducedMotion ? <EyeOff className="w-4 h-4 text-amber-400" /> : <Eye className="w-4 h-4" />}
            </button>

            <a
              href="mailto:ziyang.ang02@gmail.com?subject=Strategic%20Inquiry%20-%20Ang%20Zi%20Yang%20(Zachary)"
              className="hidden sm:flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-full bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-sm hover:scale-102 active:scale-98 min-h-[44px] whitespace-nowrap shrink-0"
            >
              <Mail className="w-3 h-3 text-black" />
              <span>Get in Touch</span>
            </a>

            {/* Mobile Hamburger Toggle Button (min 44x44px touch target) */}
            <button
              onClick={() => setIsMobileMenuOpen((prev) => !prev)}
              aria-expanded={isMobileMenuOpen}
              aria-label={isMobileMenuOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
              className="lg:hidden min-w-[44px] min-h-[44px] flex items-center justify-center rounded-full text-neutral-300 hover:text-white hover:bg-white/10 transition-colors"
            >
              {isMobileMenuOpen ? <X className="w-5 h-5 text-cyan-400" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </nav>

        {/* Mobile Frosted Navigation Drawer / Dropdown */}
        {isMobileMenuOpen && (
          <div
            className="pointer-events-auto lg:hidden max-w-5xl mx-auto mt-2 p-3.5 rounded-3xl bg-[#09090f]/95 backdrop-blur-2xl shadow-2xl animate-fadeIn border border-white/15 relative z-50 ring-1 ring-white/10"
            role="dialog"
            aria-label="Mobile Navigation"
          >
            <div className="flex flex-col space-y-1">
              {navItems.map((item) => {
                const isActive = activeSection === item.id;
                const actAccent =
                  WHISPER_ACTS.find((a) => a.sectionId === item.id)?.accentColor ?? '#c8a97e';
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => scrollTo(item.id)}
                    style={
                      isActive
                        ? {
                            backgroundColor: `${actAccent}1f`,
                            borderColor: `${actAccent}66`,
                            color: '#F4F0EA',
                          }
                        : undefined
                    }
                    className={`w-full text-left px-4 py-3 rounded-2xl text-xs font-medium flex items-center justify-between transition-colors min-h-[44px] border ${
                      isActive
                        ? 'font-semibold'
                        : 'text-[#D6D0C4] hover:bg-white/5 hover:text-[#F4F0EA] border-transparent'
                    }`}
                  >
                    <span>{item.label}</span>
                    {isActive && (
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ backgroundColor: actAccent }}
                      />
                    )}
                  </button>
                );
              })}

              <div className="pt-2 mt-2 border-t border-white/10 flex items-center gap-2">
                {onToggleAudio && (
                  <button
                    onClick={onToggleAudio}
                    className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-full text-xs font-semibold bg-white/10 text-white hover:bg-white/20 transition-all cursor-pointer min-h-[44px]"
                  >
                    {isAudioEnabled ? (
                      <>
                        <Volume2 className="w-4 h-4 text-cyan-400 animate-pulse" />
                        <span>Sound: On</span>
                      </>
                    ) : (
                      <>
                        <VolumeX className="w-4 h-4 text-neutral-400" />
                        <span>Sound: Off</span>
                      </>
                    )}
                  </button>
                )}

                <a
                  href="mailto:ziyang.ang02@gmail.com?subject=Strategic%20Inquiry%20-%20Ang%20Zi%20Yang%20(Zachary)"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-full text-xs font-semibold bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-md min-h-[44px]"
                >
                  <Mail className="w-3.5 h-3.5" />
                  <span>Get in Touch (Email)</span>
                </a>
              </div>
            </div>
          </div>
        )}
      </header>
    </>
  );
};
