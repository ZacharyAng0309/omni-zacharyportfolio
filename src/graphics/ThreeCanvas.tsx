import React, { useEffect, useRef } from 'react';
import { SceneController } from './SceneController';

interface ThreeCanvasProps {
  scrollProgress: number;
  isReducedMotion: boolean;
  onSelectSummitBeacon?: () => void;
  onSelectCaseStudyNode?: (slug: string) => void;
}

export const ThreeCanvas: React.FC<ThreeCanvasProps> = ({
  scrollProgress,
  isReducedMotion,
  onSelectSummitBeacon,
  onSelectCaseStudyNode,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<SceneController | null>(null);
  const callbacksRef = useRef({ onSelectSummitBeacon, onSelectCaseStudyNode });

  // Keep latest callbacks synchronized without re-initializing WebGL
  useEffect(() => {
    callbacksRef.current = { onSelectSummitBeacon, onSelectCaseStudyNode };
  });

  useEffect(() => {
    if (!containerRef.current) return;

    const controller = new SceneController(containerRef.current, {
      onSelectSummitBeacon: () => callbacksRef.current.onSelectSummitBeacon?.(),
      onSelectCaseStudyNode: (slug: string) => callbacksRef.current.onSelectCaseStudyNode?.(slug),
    });
    controllerRef.current = controller;

    const handleResize = () => {
      controller.resize();
    };

    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = (e.clientY / window.innerHeight) * 2 - 1;
      controller.updateParallax(x, y);
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      controller.dispose();
      controllerRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (controllerRef.current) {
      controllerRef.current.updateScroll(scrollProgress);
    }
  }, [scrollProgress]);

  useEffect(() => {
    if (controllerRef.current) {
      controllerRef.current.setReducedMotion(isReducedMotion);
    }
  }, [isReducedMotion]);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 pointer-events-none z-0"
      style={{ width: '100vw', height: '100vh', overflow: 'hidden' }}
      aria-label="3D WebGL Scene backdrop."
    />
  );
};
