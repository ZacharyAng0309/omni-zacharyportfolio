import { useState, useEffect } from 'react';

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

      // Section detection (6-Act Growth Journey Storyline Sequence)
      if (progress >= 0.88) {
        setActiveSection('contact');
        return;
      }

      const contactEl = document.getElementById('contact');
      if (contactEl) {
        const contactRect = contactEl.getBoundingClientRect();
        if (contactRect.top <= window.innerHeight * 0.55 && contactRect.bottom >= 0) {
          setActiveSection('contact');
          return;
        }
      }

      for (const id of SECTIONS) {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= window.innerHeight * 0.45 && rect.bottom >= window.innerHeight * 0.2) {
            setActiveSection(id);
            break;
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
