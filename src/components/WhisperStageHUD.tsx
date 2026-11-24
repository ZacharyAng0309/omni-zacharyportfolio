import React from 'react';
import { ArrowUpRight, Eye } from 'lucide-react';
import { SceneController } from '../graphics/SceneController';
import { getCorridorTransitState } from '../graphics/core/stationProgress';
import { WHISPER_ACTS } from '../data/whisperActs';

export interface WhisperStageHUDProps {
  activeSection: string;
  scrollProgress?: number;
  activeSubTargetId: string | null;
  isSheetOpen: boolean;
  onSelectSubTarget: (actIndex: number, subTargetId: string) => void;
  onToggleSheet: (actIndex: number) => void;
  onClearFocus: () => void;
}

export const WhisperStageHUD: React.FC<WhisperStageHUDProps> = ({
  activeSection,
  scrollProgress = 0,
  activeSubTargetId,
  isSheetOpen,
  onSelectSubTarget,
  onToggleSheet,
  onClearFocus,
}) => {
  const currentAct =
    WHISPER_ACTS.find((a) => a.sectionId === activeSection) ?? WHISPER_ACTS[0]!;

  const clampedScroll = Math.min(1, Math.max(0, scrollProgress));
  const { isInCorridor, destActIndex } = getCorridorTransitState(clampedScroll);
  const corridorDestAct = isInCorridor
    ? (WHISPER_ACTS[destActIndex] ?? currentAct)
    : currentAct;

  const subTargets = SceneController.DIORAMA_SUB_TARGETS.filter(
    (item) => item.actIndex === currentAct.actIndex
  );

  return (
    <aside
      aria-label="Active 3D Scene Whisper Narrative & Sub-Target Controls"
      data-testid="whisper-stage-hud"
      data-peek-hide
      className={`fixed bottom-[76px] left-3.5 right-3.5 sm:right-auto sm:bottom-8 sm:left-10 z-30 max-w-none sm:max-w-xl pointer-events-none select-none transition-opacity duration-300 ${
        isSheetOpen
          ? 'max-sm:opacity-0 max-sm:pointer-events-none'
          : isInCorridor
            ? 'opacity-82'
            : 'opacity-100'
      }`}
    >
      {/* Unboxed Feathered Radial Atmospheric Vignette Scrim (closest-side at 50% 50% guarantees 0 alpha at all 4 box edges) */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-24 -bottom-20 -right-32 -top-24 -z-10"
        style={{
          background:
            'radial-gradient(closest-side at 50% 50%, rgba(5, 6, 9, 0.82) 0%, rgba(5, 6, 9, 0.56) 48%, rgba(5, 6, 9, 0.20) 78%, rgba(5, 6, 9, 0) 100%)',
        }}
      />
      <div
        className="pointer-events-auto pl-3.5 sm:pl-5 border-l transition-colors duration-500 flex flex-col gap-1 sm:gap-2.5 drop-shadow-[0_2px_16px_rgba(0,0,0,0.95)] [text-shadow:0_1px_8px_rgba(0,0,0,0.95)]"
        style={{ borderColor: `${currentAct.accentColor}66` }}
      >
        {/* Staggered Editorial Reveal Keyed by Active Act (Peach Worlds Cubic-Bezier Choreography) */}
        <div key={currentAct.sectionId} className="flex flex-col">
          {/* Top Row: High-Contrast Frosted Eyebrow Capsule + Active Camera Focus Reset */}
          <div className="cinema-reveal flex flex-wrap items-center gap-2.5">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-[#07080c]/84 backdrop-blur-md border border-white/14 shadow-[0_2px_10px_rgba(0,0,0,0.65)]">
              <span
                className="text-[11px] font-mono uppercase tracking-[0.2em] font-semibold transition-colors duration-500"
                style={{ color: currentAct.accentColor }}
              >
                {currentAct.actBadge}
              </span>
              <span className="text-[10px] font-mono text-[#E6E0D6] hidden sm:inline">
                — {currentAct.stageName}
              </span>
            </div>
            <span
              aria-hidden={!isInCorridor}
              className={`rounded-full bg-[#07080c]/84 text-[9px] font-mono uppercase tracking-widest text-[#F4F0EA]/90 overflow-hidden whitespace-nowrap transition-all duration-300 ${
                isInCorridor
                  ? 'max-w-[120px] opacity-100 px-2 py-0.5 border border-white/15'
                  : 'max-w-0 max-h-0 opacity-0 px-0 py-0 border-0 pointer-events-none'
              }`}
            >
              IN TRANSIT
            </span>

            {activeSubTargetId && (
              <button
                type="button"
                data-testid="whisper-reset-camera-btn"
                onClick={onClearFocus}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono text-[#F4F0EA] bg-white/10 hover:bg-white/20 border border-white/15 cursor-pointer transition-colors"
              >
                <Eye className="w-3 h-3" />
                <span>Reset View</span>
              </button>
            )}
          </div>

          {/* Unboxed Monumental Editorial Title & Concise Hook */}
          <div className="mt-1 sm:mt-2 flex flex-col gap-0.5 sm:gap-1">
            <h2 className="cinema-reveal-delay-1 text-[17px] sm:text-[26px] font-medium tracking-[-0.025em] text-[#F4F0EA] font-display leading-[1.12] text-balance">
              {currentAct.title}
            </h2>
            <p className="cinema-reveal-delay-2 text-[11px] sm:text-xs text-[#E6E0D6]/90 leading-snug sm:leading-relaxed max-w-md line-clamp-2 sm:line-clamp-none">
              {currentAct.hook}
            </p>
            <p
              data-testid="companion-whisper-caption"
              className="cinema-reveal-delay-2 flex items-start gap-2 pt-0.5 text-[10px] sm:text-[11px] leading-snug text-[#F4F0EA]/80 italic max-w-md"
            >
              <span
                className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0"
                style={{ backgroundColor: currentAct.accentColor }}
                aria-hidden="true"
              />
              <span className="line-clamp-2 sm:line-clamp-none">
                <span className="not-italic font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6D0C4]/85 mr-1.5">
                  Zachary
                </span>
                {isInCorridor ? corridorDestAct.transitWhisper : currentAct.companionWhisper}
              </span>
            </p>
          </div>

          <div
            aria-hidden={!isInCorridor}
            data-testid="whisper-corridor-status"
            className={`flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.18em] text-[#F4F0EA]/85 overflow-hidden transition-all duration-300 ease-out ${
              isInCorridor
                ? 'mt-1.5 sm:mt-2 max-h-8 opacity-100'
                : 'max-h-0 opacity-0 pointer-events-none'
            }`}
          >
            <span
              className="w-1.5 h-1.5 rounded-full animate-pulse shrink-0"
              style={{ backgroundColor: corridorDestAct.accentColor }}
              aria-hidden="true"
            />
            <span className="truncate">Skybridge Transit • Approaching {corridorDestAct.actBadge}</span>
          </div>
        </div>

        {/* Tactile Numbered Architectural Sub-Target Pills */}
        <div
          role="group"
          aria-label="3D Scene Sub-Target Switcher"
          className={`flex flex-wrap items-center gap-1 sm:gap-1.5 pt-0.5 sm:pt-1 max-w-full transition-opacity duration-300 ${
            isInCorridor ? 'opacity-90' : 'opacity-100'
          }`}
        >
          {subTargets.map((target, idx) => {
            const isSelected = activeSubTargetId === target.id;
            const indexNum = `0${idx + 1}`;
            return (
              <button
                key={target.id}
                type="button"
                data-testid={`whisper-subtarget-${target.id}`}
                data-cursor={target.badge}
                aria-pressed={isSelected}
                onClick={() => onSelectSubTarget(currentAct.actIndex, target.id)}
                style={
                  isSelected
                    ? {
                        borderColor: `${currentAct.accentColor}cc`,
                        backgroundColor: 'rgba(14, 16, 22, 0.92)',
                      }
                    : undefined
                }
                className={`group shrink-0 inline-flex items-center gap-1.5 px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full text-[10px] sm:text-[11px] backdrop-blur-md transition-all cursor-pointer border ${
                  isSelected
                    ? 'text-[#F4F0EA] font-medium shadow-[inset_0_1px_0_rgba(255,255,255,0.16),0_4px_14px_rgba(0,0,0,0.65)]'
                    : 'bg-[#08090d]/84 text-[#F4F0EA]/95 hover:text-white hover:bg-[#12141c]/92 border-white/15 shadow-[inset_0_1px_0_rgba(255,255,255,0.10),0_4px_12px_rgba(0,0,0,0.5)]'
                }`}
              >
                <span
                  className="font-mono text-[10px]"
                  style={{ color: isSelected ? currentAct.accentColor : '#d6d0c4' }}
                >
                  {indexNum}
                </span>
                <span className="tracking-wide">{target.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tactile Editorial Dossier Trigger */}
        <div className="pt-0.5 sm:pt-1">
          <button
            type="button"
            data-testid="whisper-open-dossier-btn"
            data-cursor="DOSSIER"
            onClick={() => onToggleSheet(currentAct.actIndex)}
            style={{ borderColor: `${currentAct.accentColor}88` }}
            className="inline-flex items-center gap-2 px-3 py-1 sm:px-3.5 sm:py-1.5 rounded-full text-[10px] sm:text-[11px] font-mono uppercase tracking-[0.14em] text-[#F4F0EA] bg-[#08090d]/86 backdrop-blur-md hover:bg-[#141620]/94 border transition-all cursor-pointer shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_6px_16px_rgba(0,0,0,0.6)]"
          >
            <span>
              {isSheetOpen ? 'Close Chapter Dossier' : 'Inspect Chapter Dossier'}
            </span>
            <ArrowUpRight
              className="w-3.5 h-3.5"
              style={{ color: currentAct.accentColor }}
            />
          </button>
        </div>
      </div>
    </aside>
  );
};
