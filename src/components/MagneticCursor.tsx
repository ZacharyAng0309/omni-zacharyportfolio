import React, { useEffect, useRef, useState } from 'react';

export const MagneticCursor: React.FC = () => {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const [cursorText, setCursorText] = useState<string>('');
  const [isHovering, setIsHovering] = useState<boolean>(false);
  const [isVisible, setIsVisible] = useState<boolean>(false);
  const [isSupported, setIsSupported] = useState<boolean>(false);

  const mousePos = useRef({ x: -100, y: -100 });
  const ringPos = useRef({ x: -100, y: -100 });
  const ringVelocity = useRef({ x: 0, y: 0 });
  const rafId = useRef<number | null>(null);

  useEffect(() => {
    // Only enable on desktop/fine-pointer devices
    const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    if (!finePointer) return;
    setIsSupported(true);

    const onMouseMove = (e: MouseEvent) => {
      mousePos.current.x = e.clientX;
      mousePos.current.y = e.clientY;

      if (!isVisible) setIsVisible(true);

      // Check contextual cursor data
      const target = e.target as HTMLElement | null;
      const cursorTarget = target?.closest('[data-cursor]') as HTMLElement | null;
      if (cursorTarget) {
        const text = cursorTarget.getAttribute('data-cursor') || '';
        setCursorText(text);
        setIsHovering(true);
      } else if (target?.closest('button, a, [role="button"]')) {
        setCursorText('');
        setIsHovering(true);
      } else {
        setCursorText('');
        setIsHovering(false);
      }
    };

    const onMouseLeave = () => {
      setIsVisible(false);
    };

    const onMouseEnter = () => {
      setIsVisible(true);
    };

    window.addEventListener('mousemove', onMouseMove, { passive: true });
    document.addEventListener('mouseleave', onMouseLeave);
    document.addEventListener('mouseenter', onMouseEnter);

    const loop = () => {
      // Spring-damper physics simulation
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
      }
    };
  }, [isVisible]);

  if (!isSupported || !isVisible) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden" aria-hidden="true">
      {/* High-precision Core Dot */}
      <div
        ref={dotRef}
        className="fixed top-0 left-0 -ml-1 -mt-1 h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(0,242,254,0.9)] transition-opacity duration-200"
        style={{ willChange: 'transform' }}
      />

      {/* Spring Ring with Refraction Lens Magnification & Contextual Badge */}
      <div
        ref={ringRef}
        className={`fixed top-0 left-0 -ml-5 -mt-5 flex items-center justify-center rounded-full transition-all duration-200 ease-out ${
          isHovering
            ? 'h-16 w-16 -ml-8 -mt-8 border border-cyan-300/80 bg-cyan-900/25 backdrop-blur-[4px] shadow-[inset_0_0_16px_rgba(0,242,254,0.35),0_0_24px_rgba(0,242,254,0.2)]'
            : 'h-10 w-10 border border-cyan-400/40 bg-cyan-950/20 backdrop-blur-[2px] shadow-[0_0_12px_rgba(0,242,254,0.1)]'
        }`}
        style={{
          willChange: 'transform',
          backdropFilter: isHovering ? 'blur(3px) contrast(118%) brightness(112%)' : 'blur(2px)',
          WebkitBackdropFilter: isHovering ? 'blur(3px) contrast(118%) brightness(112%)' : 'blur(2px)',
        }}
      >
        {cursorText && (
          <span className="font-mono text-[9px] font-bold tracking-widest text-cyan-200 uppercase drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]">
            {cursorText}
          </span>
        )}
      </div>
    </div>
  );
};
