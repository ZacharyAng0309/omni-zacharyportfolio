import React, { useState, useEffect, useCallback } from 'react';
import { Eye, Layers } from 'lucide-react';
import type { SceneController } from '../graphics/SceneController';
import { WHISPER_ACTS } from '../data/whisperActs';

interface SpatialStageControlDockProps {
  activeSection: string;
  controller?: SceneController | null;
  onOpenDispatch?: () => void;
}

interface StageActMetadata {
  actLabel: string;
  stageTitle: string;
  actionId: string;
  actionButtonLabel: string;
}

const STAGE_ACT_MAP: Record<string, StageActMetadata> = {
  hero: {
    actLabel: 'Act 01',
    stageTitle: 'Enterprise AI Core',
    actionId: 'explode_strata',
    actionButtonLabel: 'Explode Core',
  },
  timeline: {
    actLabel: 'Act 02',
    stageTitle: 'The Academy & Career Ascent',
    actionId: 'tome_inspect',
    actionButtonLabel: 'Inspect Tome',
  },
  vault: {
    actLabel: 'Act 03',
    stageTitle: 'The Crucible & Cloud Mastery',
    actionId: 'badge_surge',
    actionButtonLabel: 'Surge Badges',
  },
  summit: {
    actLabel: 'Act 04',
    stageTitle: 'Mount Pilatus Alpine Summit',
    actionId: 'pulse_summit',
    actionButtonLabel: 'Pulse Summit',
  },
  'ai-solutions': {
    actLabel: 'Act 05',
    stageTitle: 'The Frontier Exploded Core',
    actionId: 'explode_strata',
    actionButtonLabel: 'Explode Strata',
  },
  contact: {
    actLabel: 'Act 06',
    stageTitle: 'Horizon Interests & Portal',
    actionId: 'cosmic_pulse',
    actionButtonLabel: 'Initiate Dispatch',
  },
};

export const SpatialStageControlDock: React.FC<SpatialStageControlDockProps> = ({
  activeSection,
  controller,
  onOpenDispatch,
}) => {
  const [isPeekingStage, setIsPeekingStage] = useState(false);
  const [lastTriggeredAction, setLastTriggeredAction] = useState<string | null>(null);

  const currentStage =
    STAGE_ACT_MAP[activeSection] ??
    STAGE_ACT_MAP.hero ?? {
      actLabel: 'Act 01',
      stageTitle: 'Enterprise AI Core',
      actionId: 'explode_strata',
      actionButtonLabel: 'Explode Core',
    };

  const actAccent =
    WHISPER_ACTS.find((a) => a.sectionId === activeSection)?.accentColor ?? '#c8a97e';

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.body.dataset.stagePeek = isPeekingStage ? 'true' : 'false';
    }
    return () => {
      if (typeof document !== 'undefined') {
        delete document.body.dataset.stagePeek;
      }
    };
  }, [isPeekingStage]);

  const handleTogglePeek = useCallback(() => {
    setIsPeekingStage((prev) => !prev);
  }, []);

  const handleTriggerGesture = useCallback(() => {
    const action = currentStage.actionId;
    if (controller) {
      controller.triggerSceneAction(action, { section: activeSection });
    }
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action, section: activeSection },
        })
      );
      if (action === 'explode_strata' && !controller) {
        window.dispatchEvent(new CustomEvent('portfolio:explode_strata'));
      }
    }
    if (activeSection === 'contact') {
      onOpenDispatch?.();
    }
    setLastTriggeredAction(action);
  }, [controller, currentStage.actionId, activeSection, onOpenDispatch]);

  return (
    <aside
      aria-label="3D Spatial Stage Control Dock"
      data-testid="spatial-stage-control-dock"
      className="fixed bottom-3 left-1/2 -translate-x-1/2 sm:left-auto sm:translate-x-0 sm:bottom-8 sm:right-10 z-40 flex items-center gap-1 sm:gap-2 p-1 sm:p-1.5 rounded-full bg-[#12100e]/88 border border-white/14 shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_16px_40px_rgba(0,0,0,0.75)] backdrop-blur-2xl max-w-[calc(100vw-1.25rem)]"
    >
      {/* Accessible Stage Metadata (Visually hidden to prevent duplicating bottom-left Whisper HUD) */}
      <div className="sr-only">
        <span>{currentStage.actLabel} · 3D Stage</span>
        <span data-testid="dock-stage-title">{currentStage.stageTitle}</span>
      </div>

      {/* Peek 3D Stage Toggle Button */}
      <button
        type="button"
        data-testid="peek-stage-toggle"
        data-cursor="PEEK"
        aria-pressed={isPeekingStage}
        onClick={handleTogglePeek}
        className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-full text-[10px] sm:text-[11px] font-mono uppercase tracking-wider whitespace-nowrap transition-all cursor-pointer min-h-[38px] sm:min-h-[40px] ${
          isPeekingStage
            ? 'bg-[#F4F0EA] text-[#14110f] font-semibold'
            : 'text-[#D6D0C4] hover:text-[#F4F0EA] hover:bg-white/10'
        }`}
      >
        <Eye className="w-3.5 h-3.5 shrink-0" />
        <span>{isPeekingStage ? 'Exit 3D Peek' : 'Peek 3D Stage'}</span>
      </button>

      <span className="w-px h-4 bg-white/15 shrink-0" aria-hidden="true" />

      {/* Context-Aware 3D Gesture Trigger */}
      <button
        type="button"
        data-testid="trigger-3d-gesture-btn"
        data-cursor="TRIGGER"
        onClick={handleTriggerGesture}
        data-last-action={lastTriggeredAction ?? ''}
        style={{ color: actAccent }}
        className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-full text-[10px] sm:text-[11px] font-mono uppercase tracking-wider whitespace-nowrap bg-white/[0.05] hover:bg-white/[0.12] border border-white/10 hover:text-[#F4F0EA] transition-all cursor-pointer min-h-[38px] sm:min-h-[40px]"
      >
        <span
          aria-hidden="true"
          className="w-1.5 h-1.5 rounded-full shrink-0"
          style={{ backgroundColor: actAccent }}
        />
        <Layers className="w-3.5 h-3.5 shrink-0" />
        <span>{currentStage.actionButtonLabel}</span>
      </button>
    </aside>
  );
};
