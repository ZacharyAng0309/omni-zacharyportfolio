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

  useEffect(() => {
    if (!containerRef.current) return;

    const controller = new SceneController(containerRef.current, {
      onSelectSummitBeacon,
      onSelectCaseStudyNode,
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
  }, [onSelectSummitBeacon, onSelectCaseStudyNode]);

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
      className="fixed inset-0 pointer-events-auto z-0"
      style={{ width: '100vw', height: '100vh', overflow: 'hidden' }}
      aria-label="3D WebGL Scene. Drag to rotate, click beacons or nodes to inspect."
    />
  );
};
