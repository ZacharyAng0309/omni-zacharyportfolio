export interface CanonicalStationProgress {
  stIdx: number;
  w: number;
  camProgress: number;
}

export interface CorridorTransitState extends CanonicalStationProgress {
  isInCorridor: boolean;
  corridorIndex: number;
  destActIndex: number;
  corridorBell: number;
}

const TOTAL_ACTS = 6;
const MAX_ACT_INDEX = TOTAL_ACTS - 1;
const DWELL_ENDS = [0.08, 0.28, 0.48, 0.68, 0.88] as const;
const WALK_SPAN = 0.08;

/**
 * Single authoritative scroll-to-station & inter-act Skybridge transit curve
 * shared across CameraRig, ParticleLattice, CinemaSetsBuilder, Act1–6 dioramas,
 * WhisperStageHUD, and useScrollProgress.
 */
export function getCanonicalStationProgress(sp: number): CanonicalStationProgress {
  const clamped = Number.isFinite(sp) ? Math.min(1, Math.max(0, sp)) : 0;
  let stIdx = MAX_ACT_INDEX;
  let w = 0;

  for (let i = 0; i < DWELL_ENDS.length; i++) {
    const dwellEnd = DWELL_ENDS[i]!;
    const walkEnd = dwellEnd + WALK_SPAN;
    if (clamped < dwellEnd) {
      stIdx = i;
      w = 0;
      break;
    }
    if (clamped < walkEnd) {
      stIdx = i;
      const u = (clamped - dwellEnd) / WALK_SPAN;
      w = u * u * (3 - 2 * u);
      break;
    }
  }

  const camProgress = (stIdx + w) / MAX_ACT_INDEX;
  return { stIdx, w, camProgress };
}

export function getCorridorTransitState(sp: number): CorridorTransitState {
  const base = getCanonicalStationProgress(sp);
  const isInCorridor = base.w > 0.04 && base.w < 0.96;
  const corridorIndex = base.stIdx;
  const destActIndex = Math.min(MAX_ACT_INDEX, base.stIdx + 1);
  const corridorBell = base.w > 0.005 && base.w < 0.995 ? Math.sin(base.w * Math.PI) : 0;

  return {
    ...base,
    isInCorridor,
    corridorIndex,
    destActIndex,
    corridorBell,
  };
}

export function isBackdropGroupVisible(actIndex: number, sp: number): boolean {
  if (actIndex <= 0) {
    return sp >= -0.05 && sp <= 0.155;
  }
  if (actIndex >= MAX_ACT_INDEX) {
    return sp >= 0.88 && sp <= 1.05;
  }
  const minSp = actIndex * 0.2 - 0.12;
  const maxSp = actIndex * 0.2 + 0.155;
  return sp >= minSp && sp <= maxSp;
}
