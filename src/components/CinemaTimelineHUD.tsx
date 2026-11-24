import React, { useCallback, useRef, useState } from 'react';
import { Film } from 'lucide-react';
import { WHISPER_ACTS, formatSmpteTimecode } from '../data/whisperActs';
import { scrollToProgressCinematic } from '../utils/cinematicScroll';

export interface CinemaTimelineHUDProps {
  scrollProgress: number;
  activeSection: string;
  isReducedMotion?: boolean;
  onSelectChapter: (sectionId: string) => void;
  onScrubStart?: () => void;
  onScrubProgress?: (nextProgress: number) => void;
}

export const CinemaTimelineHUD: React.FC<CinemaTimelineHUDProps> = ({
  scrollProgress,
  activeSection,
  isReducedMotion = false,
  onSelectChapter,
  onScrubStart,
  onScrubProgress,
}) => {
  const trackRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);
  const [hoverRatio, setHoverRatio] = useState<number | null>(null);

  const currentAct =
    WHISPER_ACTS.find((act) => act.sectionId === activeSection) ?? WHISPER_ACTS[0]!;
  const clampedProgress = Math.min(1, Math.max(0, scrollProgress));
  const timecode = formatSmpteTimecode(clampedProgress);

  const seekRatio = useCallback(
    (ratio: number, smooth: boolean = false) => {
      const clamped = Math.min(1, Math.max(0, ratio));
      onScrubStart?.();
      if (onScrubProgress) {
        onScrubProgress(clamped);
      } else {
        scrollToProgressCinematic(clamped, {
          smooth,
          reducedMotion: isReducedMotion,
        });
      }
    },
    [onScrubStart, onScrubProgress, isReducedMotion]
  );

  const seekFromClientX = useCallback(
    (clientX: number, smooth: boolean = false) => {
      const el = trackRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      if (rect.width <= 0) return;
      seekRatio((clientX - rect.left) / rect.width, smooth);
    },
    [seekRatio]
  );

  const handleTrackKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
        e.preventDefault();
        seekRatio(clampedProgress + 0.05, false);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
        e.preventDefault();
        seekRatio(clampedProgress - 0.05, false);
      } else if (e.key === 'Home') {
        e.preventDefault();
        seekRatio(0, true);
      } else if (e.key === 'End') {
        e.preventDefault();
        seekRatio(1, true);
      }
    },
    [clampedProgress, seekRatio]
  );

  const handlePointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      isDraggingRef.current = true;
      try {
        e.currentTarget.setPointerCapture?.(e.pointerId);
      } catch {
        // Ignore NotFoundError for synthetic or already-ended pointer IDs
      }
      seekFromClientX(e.clientX, true);
    },
    [seekFromClientX]
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const el = trackRef.current;
      if (el) {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0) {
          setHoverRatio(Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width)));
        }
      }
      if (!isDraggingRef.current) return;
      seekFromClientX(e.clientX, false);
    },
    [seekFromClientX]
  );

  const handlePointerUp = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    isDraggingRef.current = false;
    try {
      if (e.currentTarget.hasPointerCapture?.(e.pointerId)) {
        e.currentTarget.releasePointerCapture?.(e.pointerId);
      }
    } catch {
      // Ignore NotFoundError if capture was already released
    }
  }, []);

  const handlePointerLeave = useCallback(() => {
    if (!isDraggingRef.current) {
      setHoverRatio(null);
    }
  }, []);

  const hoveredAct =
    hoverRatio !== null
      ? (WHISPER_ACTS[Math.min(WHISPER_ACTS.length - 1, Math.max(0, Math.round(hoverRatio * 5)))] ??
        currentAct)
      : null;

  return (
    <>
      {/* Delicate 2.39:1 Anamorphic Camera Viewfinder Corner Brackets & Telemetry */}
      <div
        aria-hidden="true"
        data-peek-hide
        className="hidden sm:block fixed inset-4 z-20 pointer-events-none select-none"
      >
        <div
          className="absolute top-0 left-0 w-4 h-4 border-t border-l transition-colors duration-500"
          style={{ borderColor: `${currentAct.accentColor}40` }}
        />
        <span className="hidden min-[1440px]:inline absolute top-1 left-5 font-mono text-[8px] tracking-[0.22em] text-white/30 uppercase">
          REC ● 2.39:1
        </span>
        <div
          className="absolute top-0 right-0 w-4 h-4 border-t border-r transition-colors duration-500"
          style={{ borderColor: `${currentAct.accentColor}40` }}
        />
        <span className="hidden min-[1440px]:inline absolute top-1 right-5 font-mono text-[8px] tracking-[0.22em] text-white/30 uppercase">
          FOV 46MM • WEBGL2
        </span>
        <div
          className="absolute bottom-0 left-0 w-4 h-4 border-b border-l transition-colors duration-500"
          style={{ borderColor: `${currentAct.accentColor}40` }}
        />
        <div
          className="absolute bottom-0 right-0 w-4 h-4 border-b border-r transition-colors duration-500"
          style={{ borderColor: `${currentAct.accentColor}40` }}
        />
      </div>

      {/* Ultra-Slim Integrated SMPTE Timecode & Scrubbable 6-Chapter Ribbon */}
      <section
        aria-label="Director's Cut 6-Chapter Cinema Timeline"
        data-testid="cinema-timeline-hud"
        data-peek-hide
        className="fixed top-[66px] inset-x-0 z-30 flex justify-center px-3 pointer-events-none select-none"
      >
        <div className="pointer-events-auto w-full max-w-xl rounded-full bg-[#0a0908]/78 backdrop-blur-xl border border-white/12 px-3 py-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.12),0_8px_24px_rgba(0,0,0,0.6)] flex items-center gap-2.5 sm:gap-3">
          {/* Left Micro-Slate */}
          <div className="flex items-center gap-1.5 text-[10px] font-mono tracking-wider shrink-0">
            <span
              className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
              style={{ backgroundColor: currentAct.accentColor }}
              aria-hidden="true"
            />
            <Film className="w-3 h-3 text-neutral-400 shrink-0 hidden sm:inline" aria-hidden="true" />
            <span className="text-white font-semibold">{currentAct.sceneSlate} / 06</span>
            <span className="sr-only">{currentAct.stageName}</span>
          </div>

          {/* Center Integrated Scrub Track & Tick Dots (Touch & Pointer Scrubbable) */}
          <div className="relative flex flex-1 items-center h-4 touch-none">
            {/* Hover Timecode & Chapter Preview Slate Tooltip (anchored cleanly below the pill) */}
            {hoverRatio !== null && hoveredAct && (
              <div
                aria-hidden="true"
                data-testid="cinema-hover-preview"
                className="pointer-events-none absolute top-[calc(100%+10px)] z-40 -translate-x-1/2 px-2 py-0.5 rounded bg-[#07090f]/95 border border-white/15 text-[9px] font-mono text-[#F4F0EA] whitespace-nowrap shadow-lg"
                style={{ left: `${Math.min(92, Math.max(8, hoverRatio * 100))}%` }}
              >
                <span style={{ color: hoveredAct.accentColor }}>{hoveredAct.sceneSlate}</span>
                <span className="text-neutral-500 mx-1">•</span>
                <span>{formatSmpteTimecode(hoverRatio)}</span>
              </div>
            )}

            <div
              ref={trackRef}
              role="slider"
              aria-label="Scrub cinema timeline reel"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(clampedProgress * 100)}
              aria-valuetext={`${currentAct.sceneSlate} — ${currentAct.stageName} (${timecode})`}
              tabIndex={0}
              data-testid="cinema-timeline-track"
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerLeave={handlePointerLeave}
              onPointerCancel={handlePointerUp}
              onKeyDown={handleTrackKeyDown}
              className="relative h-1.5 w-full rounded-full bg-white/12 cursor-ew-resize touch-none overflow-visible flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F4F0EA]/80"
            >
              {/* Subtle film perforation ticks */}
              <div
                aria-hidden="true"
                className="absolute inset-0 opacity-25 rounded-full overflow-hidden"
                style={{
                  backgroundImage:
                    'repeating-linear-gradient(90deg, rgba(255,255,255,0.4) 0px, rgba(255,255,255,0.4) 1px, transparent 1px, transparent 12px)',
                }}
              />

              {/* Active reel progress fill */}
              <div
                aria-hidden="true"
                className="h-full rounded-l-full transition-[width] duration-75"
                style={{
                  width: `${clampedProgress * 100}%`,
                  background: `linear-gradient(90deg, rgba(255,255,255,0.22), ${currentAct.accentColor})`,
                }}
              />

              {/* Hover ghost reticle line */}
              {hoverRatio !== null && (
                <div
                  aria-hidden="true"
                  className="absolute top-0 bottom-0 w-px bg-white/45 pointer-events-none"
                  style={{ left: `${hoverRatio * 100}%` }}
                />
              )}

              {/* Playhead needle & tactile diamond reticle */}
              <div
                aria-hidden="true"
                className="absolute -top-0.5 -bottom-0.5 w-0.5 bg-white shadow-[0_0_10px_rgba(255,255,255,0.95)] pointer-events-none z-20"
                style={{ left: `calc(${clampedProgress * 100}% - 1px)` }}
              >
                <span
                  className="block w-1.5 h-1.5 rotate-45 -translate-x-[2px] -translate-y-0.5 rounded-[1px]"
                  style={{
                    backgroundColor: '#ffffff',
                    boxShadow: `0 0 8px ${currentAct.accentColor}`,
                  }}
                />
              </div>
            </div>

            {/* 6 Sleek Chapter Tick Dots with 32x44px Mobile / 44x44px sm+ Accessible Touch Hitboxes Anchored Along the Track */}
            {WHISPER_ACTS.map((act) => {
              const isActive = act.sectionId === currentAct.sectionId;
              const pct = (act.actIndex / 5) * 100;
              return (
                <button
                  key={act.sectionId}
                  type="button"
                  data-testid={`timeline-chapter-${act.sectionId}`}
                  title={`0${act.actIndex + 1} ${act.shortCutLabel}`}
                  aria-label={`Jump to Act 0${act.actIndex + 1} ${act.shortCutLabel}`}
                  onClick={() => onSelectChapter(act.sectionId)}
                  style={{ left: `${pct}%` }}
                  className="group absolute top-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-8 h-11 sm:w-11 sm:h-11 flex items-center justify-center rounded-full cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F4F0EA]/80"
                >
                  <span
                    aria-hidden="true"
                    style={{
                      backgroundColor: isActive ? act.accentColor : 'rgba(22, 24, 32, 0.92)',
                      borderColor: isActive ? '#ffffff' : 'rgba(255, 255, 255, 0.35)',
                    }}
                    className={`w-2.5 h-2.5 rounded-full border transition-transform ${
                      isActive
                        ? 'scale-125 shadow-[0_0_8px_rgba(255,255,255,0.65)]'
                        : 'group-hover:scale-125 group-hover:border-white/80'
                    }`}
                  />
                  <span className="sr-only">
                    0{act.actIndex + 1} {act.shortCutLabel}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Right Micro-Timecode */}
          <span
            data-testid="cinema-smpte-timecode"
            className="px-1.5 py-0.5 rounded-full bg-black/45 border border-white/10 text-[10px] font-mono text-[#F4F0EA] font-medium tabular-nums shrink-0"
          >
            {timecode}
          </span>
        </div>
      </section>
    </>
  );
};
