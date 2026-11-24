import React, { useEffect, useRef, useState } from 'react';

export interface MagneticCursorProps {
  accentColor?: string;
  isReducedMotion?: boolean;
}

export const MagneticCursor: React.FC<MagneticCursorProps> = ({
  accentColor = '#00f2fe',
  isReducedMotion = false,
}) => {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const [cursorText, setCursorText] = useState<string>('');
  const [isHovering, setIsHovering] = useState<boolean>(false);
  const [isVisible, setIsVisible] = useState<boolean>(false);
  const [isSupported] = useState<boolean>(() =>
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(hover: hover) and (pointer: fine)').matches
  );

  const mousePos = useRef({ x: -100, y: -100 });
  const ringPos = useRef({ x: -100, y: -100 });
  const ringVelocity = useRef({ x: 0, y: 0 });
  const rafId = useRef<number | null>(null);
  const isVisibleRef = useRef<boolean>(false);
  const isHoveringRef = useRef<boolean>(false);
  const cursorTextRef = useRef<string>('');

  useEffect(() => {
    if (!isSupported || isReducedMotion) return;

    const commitHover = (nextHover: boolean, nextText: string) => {
      if (isHoveringRef.current !== nextHover) {
        isHoveringRef.current = nextHover;
        setIsHovering(nextHover);
      }
      if (cursorTextRef.current !== nextText) {
        cursorTextRef.current = nextText;
        setCursorText(nextText);
      }
    };

    const onMouseMove = (e: MouseEvent) => {
      mousePos.current.x = e.clientX;
      mousePos.current.y = e.clientY;

      if (!isVisibleRef.current) {
        isVisibleRef.current = true;
        setIsVisible(true);
      }

      const target = e.target as HTMLElement | null;
      const cursorTarget = target?.closest('[data-cursor]') as HTMLElement | null;
      if (cursorTarget) {
        const text = cursorTarget.getAttribute('data-cursor') || '';
        commitHover(true, text);
      } else if (target?.closest('button, a, [role="button"]')) {
        commitHover(true, '');
      } else {
        const hoveredProp =
          typeof document !== 'undefined' ? document.body.dataset.hoveredProp || '' : '';
        if (hoveredProp && (!target || target.tagName === 'CANVAS' || target === document.body)) {
          commitHover(true, hoveredProp);
        } else {
          commitHover(false, '');
        }
      }
    };

    const onMouseLeave = () => {
      if (isVisibleRef.current) {
        isVisibleRef.current = false;
        setIsVisible(false);
      }
    };

    const onMouseEnter = () => {
      if (!isVisibleRef.current) {
        isVisibleRef.current = true;
        setIsVisible(true);
      }
    };

    window.addEventListener('mousemove', onMouseMove, { passive: true });
    document.addEventListener('mouseleave', onMouseLeave);
    document.addEventListener('mouseenter', onMouseEnter);

    const loop = () => {
      const springK = 0.24;
      const damping = 0.76;

      const ax = (mousePos.current.x - ringPos.current.x) * springK;
      const ay = (mousePos.current.y - ringPos.current.y) * springK;

      ringVelocity.current.x = (ringVelocity.current.x + ax) * damping;
      ringVelocity.current.y = (ringVelocity.current.y + ay) * damping;

      ringPos.current.x += ringVelocity.current.x;
      ringPos.current.y += ringVelocity.current.y;

      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${mousePos.current.x}px, ${mousePos.current.y}px, 0)`;
      }
      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${ringPos.current.x}px, ${ringPos.current.y}px, 0)`;
      }

      rafId.current = requestAnimationFrame(loop);
    };

    rafId.current = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseleave', onMouseLeave);
      document.removeEventListener('mouseenter', onMouseEnter);
      if (rafId.current !== null) {
        cancelAnimationFrame(rafId.current);
        rafId.current = null;
      }
    };
  }, [isSupported, isReducedMotion]);

  if (!isSupported || isReducedMotion || !isVisible) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden" aria-hidden="true">
      {/* High-precision Core Dot */}
      <div
        ref={dotRef}
        className="fixed top-0 left-0 -ml-1 -mt-1 h-2 w-2 rounded-full transition-opacity duration-200"
        style={{
          willChange: 'transform',
          backgroundColor: accentColor,
          boxShadow: `0 0 8px ${accentColor}e6`,
        }}
      />

      {/* Spring Ring with Contextual Badge (zero backdrop blur so underlying labels remain razor crisp) */}
      <div
        ref={ringRef}
        className={`fixed top-0 left-0 flex items-center justify-center rounded-full border transition-[width,height,margin] duration-200 ease-out ${
          isHovering ? 'h-14 w-14 -ml-7 -mt-7' : 'h-10 w-10 -ml-5 -mt-5'
        }`}
        style={{
          willChange: 'transform',
          borderColor: isHovering ? `${accentColor}cc` : `${accentColor}66`,
          backgroundColor: isHovering ? `${accentColor}16` : `${accentColor}0a`,
          boxShadow: isHovering
            ? `inset 0 0 14px ${accentColor}38, 0 0 20px ${accentColor}26`
            : `0 0 10px ${accentColor}1c`,
        }}
      >
        {cursorText && (
          <span
            className="font-mono text-[8px] font-bold tracking-widest uppercase drop-shadow-[0_1px_2px_rgba(0,0,0,0.85)]"
            style={{ color: accentColor }}
          >
            {cursorText}
          </span>
        )}
      </div>
    </div>
  );
};
