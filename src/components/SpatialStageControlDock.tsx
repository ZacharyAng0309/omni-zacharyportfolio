import React, { useState, useEffect, useCallback } from 'react';
import { Eye, Sparkles, Layers } from 'lucide-react';
import type { SceneController } from '../graphics/SceneController';

interface SpatialStageControlDockProps {
  activeSection: string;
  controller?: SceneController | null;
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
    actionButtonLabel: 'Cosmic Pulse',
  },
};

export const SpatialStageControlDock: React.FC<SpatialStageControlDockProps> = ({
  activeSection,
  controller,
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
      controller.triggerSceneAction(action);
    }
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action, section: activeSection },
        })
      );
      if (action === 'explode_strata') {
        window.dispatchEvent(new CustomEvent('portfolio:explode_strata'));
      }
    }
    setLastTriggeredAction(action);
  }, [controller, currentStage.actionId, activeSection]);

  return (
    <aside
      aria-label="3D Spatial Stage Control Dock"
      data-testid="spatial-stage-control-dock"
      className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-40 flex items-center gap-2 sm:gap-2.5 p-2 sm:px-3.5 sm:py-2 rounded-full apple-glass border border-white/15 shadow-2xl backdrop-blur-2xl"
    >
      {/* Active 3D Stage Indicator */}
      <div className="hidden lg:flex items-center gap-2 pr-2 border-r border-white/10">
        <span className="inline-flex items-center justify-center w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-400 leading-none">
            {currentStage.actLabel} · 3D Stage
          </span>
          <span
            data-testid="dock-stage-title"
            className="text-xs font-medium text-white tracking-tight leading-tight mt-0.5"
          >
            {currentStage.stageTitle}
          </span>
        </div>
      </div>

      {/* Peek 3D Stage Toggle Button */}
      <button
        type="button"
        data-testid="peek-stage-toggle"
        data-cursor="PEEK"
        aria-pressed={isPeekingStage}
        onClick={handleTogglePeek}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer min-h-[44px] ${
          isPeekingStage
            ? 'bg-cyan-400 text-black font-semibold shadow-[0_0_20px_rgba(0,242,254,0.45)]'
            : 'bg-white/10 text-neutral-200 hover:bg-white/20 hover:text-white border border-white/10'
        }`}
      >
        <Eye className="w-3.5 h-3.5" />
        <span>{isPeekingStage ? 'Exit 3D Peek' : 'Peek 3D Stage'}</span>
      </button>

      {/* Context-Aware 3D Gesture Trigger */}
      <button
        type="button"
        data-testid="trigger-3d-gesture-btn"
        data-cursor="TRIGGER"
        onClick={handleTriggerGesture}
        data-last-action={lastTriggeredAction ?? ''}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/25 hover:text-white border border-cyan-500/30 transition-all cursor-pointer min-h-[44px]"
      >
        {currentStage.actionId === 'explode_strata' ? (
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
        ) : (
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
        )}
        <span>{currentStage.actionButtonLabel}</span>
      </button>
    </aside>
  );
};
