import { useState, useEffect } from 'react';
import { getCanonicalStationProgress } from '../graphics/core/stationProgress';

const SECTIONS = ['hero', 'timeline', 'vault', 'summit', 'ai-solutions', 'contact'] as const;

export function useScrollProgress(): { scrollProgress: number; activeSection: string } {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [activeSection, setActiveSection] = useState('hero');

  useEffect(() => {
    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
      const currentScroll = window.scrollY;

      const sectionElements = SECTIONS.map((id) => document.getElementById(id));
      const hasAllElements = sectionElements.every((el) => el !== null);

      let progress = 0;
      if (hasAllElements && totalScroll > 0) {
        const tops = sectionElements.map((el) => el!.offsetTop);
        if (currentScroll <= tops[0]!) {
          progress = 0;
        } else if (currentScroll >= totalScroll || currentScroll >= tops[5]!) {
          progress = 1;
        } else {
          let segIndex = 0;
          for (let i = 0; i < tops.length - 1; i++) {
            if (currentScroll >= tops[i]! && currentScroll < tops[i + 1]!) {
              segIndex = i;
              break;
            }
          }
          const segStart = tops[segIndex]!;
          const segEnd = tops[segIndex + 1]!;
          const segSpan = Math.max(1, segEnd - segStart);
          const segFrac = Math.min(1, Math.max(0, (currentScroll - segStart) / segSpan));
          progress = (segIndex + segFrac) / (tops.length - 1);
        }
      } else {
        progress = totalScroll > 0 ? Math.min(1, Math.max(0, currentScroll / totalScroll)) : 0;
      }

      setScrollProgress(progress);

      // Section detection locked to canonical corridor curve when scroll continuum is active
      if (currentScroll <= 0 && progress === 0) {
        setActiveSection('hero');
        return;
      }

      if (totalScroll > 0) {
        const { stIdx, w } = getCanonicalStationProgress(progress);
        const canonicalIdx = Math.min(SECTIONS.length - 1, w >= 0.5 ? stIdx + 1 : stIdx);
        setActiveSection(SECTIONS[canonicalIdx]!);
        return;
      }

      const midY = window.innerHeight * 0.5;
      for (const id of SECTIONS) {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.height > 0 && rect.top <= midY && rect.bottom > midY) {
            setActiveSection(id);
            return;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return { scrollProgress, activeSection };
}
