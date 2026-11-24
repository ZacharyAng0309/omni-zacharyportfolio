/**
 * Director's Eased Scroll Flight Helper
 * Replaces abrupt native jumps / linear scrollTo with weighted quintic ease-in-out
 * camera glide across chapters while honoring manual wheel/touch interruption and
 * prefers-reduced-motion accessibility.
 */

export interface CinematicScrollOptions {
  durationMs?: number;
  reducedMotion?: boolean;
}

export interface ProgressScrollOptions extends CinematicScrollOptions {
  smooth?: boolean;
}

let activeRafId: number | null = null;
let detachInterruptListeners: (() => void) | null = null;

/**
 * Quintic ease-in-out curve calibrated for silky long-throw camera acceleration
 * and zero mechanical sudden stops (Peach Worlds / Active Theory feel).
 */
export function easeInOutQuint(t: number): number {
  const x = Math.min(1, Math.max(0, t));
  return x < 0.5 ? 16 * x * x * x * x * x : 1 - Math.pow(-2 * x + 2, 5) / 2;
}

function resolveReducedMotion(explicit?: boolean): boolean {
  if (typeof explicit === 'boolean') return explicit;
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
  return false;
}

function clearInterruptListeners(): void {
  if (detachInterruptListeners) {
    detachInterruptListeners();
    detachInterruptListeners = null;
  }
}

/** Cancels any active eased scroll flight cleanly (called on manual wheel/touch or live drag scrub). */
export function cancelActiveScrollFlight(): void {
  if (activeRafId !== null && typeof window !== 'undefined' && typeof window.cancelAnimationFrame === 'function') {
    window.cancelAnimationFrame(activeRafId);
  }
  activeRafId = null;
  clearInterruptListeners();
}

/**
 * Animates `window.scrollY` smoothly to `targetScrollY` using quintic easing.
 * Returns `false` if the document is non-scrollable (e.g. JSDOM default height).
 */
export function animateCinematicScrollTo(
  targetScrollY: number,
  options: CinematicScrollOptions = {}
): boolean {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return false;
  }

  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  if (maxScroll <= 0) {
    return false;
  }

  cancelActiveScrollFlight();

  const clampedTarget = Math.max(0, Math.min(maxScroll, Math.round(targetScrollY)));
  const startY = window.scrollY;
  const deltaY = clampedTarget - startY;
  const isReduced = resolveReducedMotion(options.reducedMotion);

  if (
    isReduced ||
    Math.abs(deltaY) < 2 ||
    typeof window.requestAnimationFrame !== 'function'
  ) {
    window.scrollTo({ top: clampedTarget, behavior: 'instant' });
    window.dispatchEvent(new Event('scroll'));
    return true;
  }

  const distanceRatio = Math.min(1, Math.abs(deltaY) / Math.max(1, maxScroll));
  const durationMs =
    options.durationMs ?? Math.round(Math.min(1150, Math.max(680, 660 + distanceRatio * 490)));

  const onManualInterrupt = (e: Event) => {
    const target = e.target;
    if (
      typeof Element !== 'undefined' &&
      target instanceof Element &&
      target.closest('[data-testid="slide-over-inspection-sheet"], [role="dialog"]')
    ) {
      return;
    }
    cancelActiveScrollFlight();
  };

  window.addEventListener('wheel', onManualInterrupt, { passive: true });
  window.addEventListener('touchstart', onManualInterrupt, { passive: true });
  detachInterruptListeners = () => {
    window.removeEventListener('wheel', onManualInterrupt);
    window.removeEventListener('touchstart', onManualInterrupt);
  };

  let startTimestamp: number | null = null;

  const step = (timestamp: number) => {
    if (startTimestamp === null) {
      startTimestamp = timestamp;
    }
    const elapsed = timestamp - startTimestamp;
    const rawT = Math.min(1, elapsed / durationMs);
    const eased = easeInOutQuint(rawT);

    window.scrollTo({
      top: Math.round(startY + deltaY * eased),
      behavior: 'instant',
    });
    window.dispatchEvent(new Event('scroll'));

    if (rawT < 1) {
      activeRafId = window.requestAnimationFrame(step);
    } else {
      activeRafId = null;
      clearInterruptListeners();
    }
  };

  activeRafId = window.requestAnimationFrame(step);
  return true;
}

/**
 * Smoothly flies the viewport to a named spatial section (`hero`, `timeline`, etc.).
 * Preserves `el.scrollIntoView(...)` delegation when running in non-scrollable JSDOM layouts.
 */
export function scrollToSectionCinematic(
  sectionId: string,
  options: CinematicScrollOptions = {}
): void {
  if (typeof document === 'undefined' || typeof window === 'undefined') return;
  const el = document.getElementById(sectionId);
  if (!el) return;

  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  const isReduced = resolveReducedMotion(options.reducedMotion);

  if (maxScroll <= 0) {
    cancelActiveScrollFlight();
    if (typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: isReduced ? 'auto' : 'smooth' });
    }
    return;
  }

  const targetY = window.scrollY + el.getBoundingClientRect().top;
  animateCinematicScrollTo(targetY, {
    durationMs: options.durationMs,
    reducedMotion: isReduced,
  });
}

/**
 * Seeks normalized scroll progress `[0..1]`, using eased flight on single clicks or instant
 * seek while actively scrubbing the filmstrip scrubber.
 */
export function scrollToProgressCinematic(
  progress: number,
  options: ProgressScrollOptions = {}
): void {
  if (typeof document === 'undefined' || typeof window === 'undefined') return;
  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  if (maxScroll <= 0) return;

  const clamped = Math.min(1, Math.max(0, progress));
  const targetY = Math.round(clamped * maxScroll);
  const isReduced = resolveReducedMotion(options.reducedMotion);

  if (options.smooth && !isReduced) {
    animateCinematicScrollTo(targetY, {
      durationMs: options.durationMs ?? 720,
      reducedMotion: false,
    });
  } else {
    cancelActiveScrollFlight();
    window.scrollTo({ top: targetY, behavior: 'instant' });
    window.dispatchEvent(new Event('scroll'));
  }
}
