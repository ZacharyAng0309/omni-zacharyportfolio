import React, { useEffect, useRef } from 'react';
import { SceneController } from './SceneController';

interface ThreeCanvasProps {
  scrollProgress: number;
  isReducedMotion: boolean;
  isSheetOpen?: boolean;
  onSelectSummitBeacon?: () => void;
  onSelectCaseStudyNode?: (slug: string) => void;
  onSelectSubTarget?: (actIndex: number, subTargetId: string) => void;
  onControllerReady?: (controller: SceneController | null) => void;
}

export const ThreeCanvas: React.FC<ThreeCanvasProps> = ({
  scrollProgress,
  isReducedMotion,
  isSheetOpen = false,
  onSelectSummitBeacon,
  onSelectCaseStudyNode,
  onSelectSubTarget,
  onControllerReady,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<SceneController | null>(null);
  const callbacksRef = useRef({ onSelectSummitBeacon, onSelectCaseStudyNode, onSelectSubTarget });
  const onControllerReadyRef = useRef(onControllerReady);

  // Keep latest callbacks synchronized without re-initializing WebGL
  useEffect(() => {
    callbacksRef.current = { onSelectSummitBeacon, onSelectCaseStudyNode, onSelectSubTarget };
    onControllerReadyRef.current = onControllerReady;
  });

  useEffect(() => {
    if (!containerRef.current) return;

    const controller = new SceneController(containerRef.current, {
      onSelectSummitBeacon: () => callbacksRef.current.onSelectSummitBeacon?.(),
      onSelectCaseStudyNode: (slug: string) => callbacksRef.current.onSelectCaseStudyNode?.(slug),
      onSelectSubTarget: (actIndex: number, subTargetId: string) =>
        callbacksRef.current.onSelectSubTarget?.(actIndex, subTargetId),
    });
    controllerRef.current = controller;
    if (typeof document !== 'undefined') {
      document.body.dataset.threeSceneReady = 'true';
    }
    onControllerReadyRef.current?.(controller);

    const handleResize = () => {
      controller.resize();
    };

    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = -(e.clientY / window.innerHeight) * 2 + 1;
      controller.updateParallax(x, y);
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    const resizeObserver =
      typeof ResizeObserver !== 'undefined'
        ? new ResizeObserver(() => {
            controller.resize();
          })
        : null;
    resizeObserver?.observe(containerRef.current);

    return () => {
      if (typeof document !== 'undefined') {
        delete document.body.dataset.threeSceneReady;
      }
      resizeObserver?.disconnect();
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      onControllerReadyRef.current?.(null);
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

  useEffect(() => {
    if (controllerRef.current) {
      controllerRef.current.setSheetOpen?.(isSheetOpen);
    }
  }, [isSheetOpen]);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-0"
      style={{ width: '100vw', height: '100vh', overflow: 'hidden' }}
      aria-label="3D WebGL Scene backdrop."
    />
  );
};
