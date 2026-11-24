import React, { useEffect, useRef, useState } from 'react';
import { SceneController, type ProjectedHotspot } from '../graphics/SceneController';
import { WHISPER_ACTS } from '../data/whisperActs';

export interface DiegeticHotspotLayerProps {
  activeSection: string;
  activeSubTargetId: string | null;
  isSheetOpen?: boolean;
  controller: SceneController | null;
  onSelectSubTarget: (actIndex: number, subTargetId: string) => void;
}

const FALLBACK_SCREEN_POSITIONS: ReadonlyArray<{ x: number; y: number }> = [
  { x: 34, y: 42 },
  { x: 52, y: 32 },
  { x: 64, y: 50 },
  { x: 74, y: 42 },
];

export const DiegeticHotspotLayer: React.FC<DiegeticHotspotLayerProps> = ({
  activeSection,
  activeSubTargetId,
  isSheetOpen = false,
  controller,
  onSelectSubTarget,
}) => {
  const currentAct =
    WHISPER_ACTS.find((a) => a.sectionId === activeSection) ?? WHISPER_ACTS[0]!;

  const [hotspots, setHotspots] = useState<ProjectedHotspot[]>(() => {
    const targets = SceneController.DIORAMA_SUB_TARGETS.filter(
      (t) => t.actIndex === currentAct.actIndex
    );
    return targets.map((t, idx) => {
      const pos = FALLBACK_SCREEN_POSITIONS[idx % FALLBACK_SCREEN_POSITIONS.length]!;
      return {
        id: t.id,
        actIndex: t.actIndex,
        label: t.label,
        badge: t.badge,
        accentColor: t.accentColor,
        xPercent: pos.x,
        yPercent: pos.y,
        visible: true,
      };
    });
  });

  const lastHotspotsRef = useRef<ProjectedHotspot[]>(hotspots);

  useEffect(() => {
    let rafId: number | null = null;
    let isCancelled = false;

    const commitIfChanged = (next: ProjectedHotspot[]) => {
      const prev = lastHotspotsRef.current;
      const unchanged =
        prev.length === next.length &&
        next.every((item, i) => {
          const p = prev[i];
          return (
            p !== undefined &&
            p.id === item.id &&
            p.actIndex === item.actIndex &&
            p.visible === item.visible &&
            Math.abs(p.xPercent - item.xPercent) < 0.05 &&
            Math.abs(p.yPercent - item.yPercent) < 0.05
          );
        });
      if (!unchanged) {
        lastHotspotsRef.current = next;
        setHotspots(next);
      }
    };

    const updatePositions = () => {
      if (isCancelled) return;
      if (controller) {
        const projected = controller.getProjectedHotspots(currentAct.actIndex);
        if (projected.length > 0) {
          commitIfChanged(projected);
        }
      } else {
        const targets = SceneController.DIORAMA_SUB_TARGETS.filter(
          (t) => t.actIndex === currentAct.actIndex
        );
        commitIfChanged(
          targets.map((t, idx) => {
            const pos = FALLBACK_SCREEN_POSITIONS[idx % FALLBACK_SCREEN_POSITIONS.length]!;
            return {
              id: t.id,
              actIndex: t.actIndex,
              label: t.label,
              badge: t.badge,
              accentColor: t.accentColor,
              xPercent: pos.x,
              yPercent: pos.y,
              visible: true,
            };
          })
        );
      }
      rafId = window.requestAnimationFrame(updatePositions);
    };

    updatePositions();
    return () => {
      isCancelled = true;
      if (rafId !== null) {
        window.cancelAnimationFrame(rafId);
      }
    };
  }, [controller, currentAct.actIndex]);

  return (
    <div
      aria-label="Diegetic 3D Spatial Target Reticles"
      data-testid="diegetic-hotspot-layer"
      data-peek-hide
      className="fixed inset-0 z-20 pointer-events-none overflow-hidden select-none"
    >
      {hotspots.map((hotspot, idx) => {
        if (!hotspot.visible) return null;
        const isSelected = activeSubTargetId === hotspot.id;
        const pinNum = `0${idx + 1}`;
        const cam = controller?.getCamera?.();
        const isPortrait = typeof cam?.aspect === 'number' ? cam.aspect < 1.0 : false;
        if (isSheetOpen && (isPortrait || hotspot.xPercent > 54)) {
          return null;
        }
        const safeYPercent = isPortrait
          ? Math.min(hotspot.yPercent, 54)
          : hotspot.xPercent < 44 && hotspot.yPercent > 64
            ? 62
            : hotspot.yPercent;
        const openLeft = hotspot.xPercent > 62;

        return (
          <button
            key={hotspot.id}
            type="button"
            data-testid={`diegetic-hotspot-${hotspot.id}`}
            data-cursor={hotspot.badge}
            aria-label={`Inspect 3D Prop: ${hotspot.label}`}
            onClick={() => onSelectSubTarget(hotspot.actIndex, hotspot.id)}
            style={{
              left: `${hotspot.xPercent}%`,
              top: `${safeYPercent}%`,
              transform: 'translate(-50%, -50%)',
            }}
            className="pointer-events-auto absolute group w-6 h-6 rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-[#F4F0EA] focus-visible:ring-offset-2 focus-visible:ring-offset-black/80 cursor-pointer"
          >
            {/* Minimal Architectural Numbered Pin Marker with Magnetic Halo & AR Reticle Ticks */}
            <span className="relative flex items-center justify-center w-6 h-6">
              <span
                aria-hidden="true"
                className="pointer-events-none absolute -top-1 left-1/2 -translate-x-1/2 w-[1px] h-1 opacity-70"
                style={{ backgroundColor: hotspot.accentColor }}
              />
              <span
                aria-hidden="true"
                className="pointer-events-none absolute -bottom-1 left-1/2 -translate-x-1/2 w-[1px] h-1 opacity-70"
                style={{ backgroundColor: hotspot.accentColor }}
              />
              <span
                aria-hidden="true"
                className="pointer-events-none absolute -left-1 top-1/2 -translate-y-1/2 w-1 h-[1px] opacity-70"
                style={{ backgroundColor: hotspot.accentColor }}
              />
              <span
                aria-hidden="true"
                className="pointer-events-none absolute -right-1 top-1/2 -translate-y-1/2 w-1 h-[1px] opacity-70"
                style={{ backgroundColor: hotspot.accentColor }}
              />
              {!isSelected && (
                <span
                  aria-hidden="true"
                  className="hotspot-pulse-ring absolute inset-0 rounded-full border pointer-events-none"
                  style={{ borderColor: `${hotspot.accentColor}99` }}
                />
              )}
              <span
                className={`relative flex items-center justify-center w-6 h-6 rounded-full text-[10px] font-mono transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] backdrop-blur-md border ${
                  isSelected
                    ? 'bg-[#F4F0EA] text-[#14110f] font-semibold border-[#F4F0EA] shadow-[0_0_16px_rgba(244,240,234,0.45)] scale-110'
                    : 'bg-[#14110f]/75 text-[#F4F0EA]/90 group-hover:border-[#F4F0EA] group-hover:scale-105'
                }`}
                style={isSelected ? undefined : { borderColor: `${hotspot.accentColor}8c` }}
              >
                {pinNum}
              </span>
            </span>

            {/* Hover & Keyboard-Focus Expandable Spatial Tag Anchored Off the Fixed Reticle Center */}
            <span
              className={`pointer-events-none absolute top-1/2 -translate-y-1/2 ${
                openLeft ? 'right-full mr-1.5' : 'left-full ml-1.5'
              } inline-flex items-center gap-1.5 rounded-full text-[10px] font-mono backdrop-blur-md transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] overflow-hidden whitespace-nowrap ${
                isSelected
                  ? 'max-w-[260px] opacity-100 px-2.5 py-0.5 bg-[#14110f]/85 text-[#F4F0EA] border'
                  : 'max-w-0 opacity-0 px-0 py-0 border-0 group-hover:max-w-[260px] group-hover:opacity-100 group-hover:px-2.5 group-hover:py-0.5 group-hover:bg-[#14110f]/85 group-hover:text-[#F4F0EA] group-hover:border group-hover:border-white/20 group-focus-visible:max-w-[260px] group-focus-visible:opacity-100 group-focus-visible:px-2.5 group-focus-visible:py-0.5 group-focus-visible:bg-[#14110f]/85 group-focus-visible:text-[#F4F0EA] group-focus-visible:border group-focus-visible:border-white/20'
              }`}
              style={isSelected ? { borderColor: `${hotspot.accentColor}99` } : undefined}
            >
              <span
                className="text-[8px] uppercase tracking-wider opacity-75"
                style={{ color: hotspot.accentColor }}
              >
                {hotspot.badge}
              </span>
              <span>{hotspot.label}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
};
