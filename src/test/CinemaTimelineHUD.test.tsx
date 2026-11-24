import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CinemaTimelineHUD } from '../components/CinemaTimelineHUD';
import { formatSmpteTimecode } from '../data/whisperActs';
import {
  animateCinematicScrollTo,
  cancelActiveScrollFlight,
  easeInOutQuint,
  scrollToProgressCinematic,
  scrollToSectionCinematic,
} from '../utils/cinematicScroll';

describe('CinemaTimelineHUD & SMPTE Timecode Formatter', () => {
  it('formats normalized scroll progress accurately into 24fps SMPTE timecodes', () => {
    expect(formatSmpteTimecode(0)).toBe('00:00:00:00');
    expect(formatSmpteTimecode(0.2)).toBe('00:00:18:00');
    expect(formatSmpteTimecode(0.5)).toBe('00:00:45:00');
    expect(formatSmpteTimecode(1.0)).toBe('00:01:30:00');
    expect(formatSmpteTimecode(-0.2)).toBe('00:00:00:00');
    expect(formatSmpteTimecode(1.4)).toBe('00:01:30:00');
  });

  it('displays active scene slate and SMPTE timecode for the current section', () => {
    const onSelectChapter = vi.fn();
    render(
      <CinemaTimelineHUD
        scrollProgress={0.6}
        activeSection="summit"
        onSelectChapter={onSelectChapter}
      />
    );

    const hud = screen.getByTestId('cinema-timeline-hud');
    expect(hud.textContent).toContain('SC 04 / 06');
    expect(hud.textContent).toMatch(/Pilatus Alpine Sunrise/i);
    expect(screen.getByTestId('cinema-smpte-timecode').textContent).toBe('00:00:54:00');
  });

  it('navigates directly to clicked chapter cut markers', () => {
    const onSelectChapter = vi.fn();
    render(
      <CinemaTimelineHUD
        scrollProgress={0}
        activeSection="hero"
        onSelectChapter={onSelectChapter}
      />
    );

    const chapterBtn = screen.getByTestId('timeline-chapter-vault');
    expect(chapterBtn.className).toContain('h-11');
    expect(chapterBtn.className).toContain('sm:w-11');
    fireEvent.click(chapterBtn);
    expect(onSelectChapter).toHaveBeenCalledWith('vault');
  });

  it('supports accessible keyboard and pointer scrubbing along the cinema filmstrip track and notifies onScrubStart', () => {
    const onSelectChapter = vi.fn();
    const onScrubStart = vi.fn();
    const onScrubProgress = vi.fn();
    render(
      <CinemaTimelineHUD
        scrollProgress={0.4}
        activeSection="vault"
        onSelectChapter={onSelectChapter}
        onScrubStart={onScrubStart}
        onScrubProgress={onScrubProgress}
      />
    );

    const hud = screen.getByTestId('cinema-timeline-hud');
    expect(hud.className).toContain('top-[66px]');

    const slider = screen.getByTestId('cinema-timeline-track');
    Object.defineProperty(slider, 'getBoundingClientRect', {
      value: () => ({ left: 0, width: 200, top: 0, right: 200, bottom: 10, height: 10 }),
    });

    fireEvent.keyDown(slider, { key: 'ArrowRight' });
    expect(onScrubStart).toHaveBeenCalledTimes(1);
    expect(onScrubProgress).toHaveBeenLastCalledWith(expect.closeTo(0.45, 5));

    fireEvent.keyDown(slider, { key: 'ArrowLeft' });
    expect(onScrubStart).toHaveBeenCalledTimes(2);
    expect(onScrubProgress).toHaveBeenLastCalledWith(expect.closeTo(0.35, 5));

    fireEvent.keyDown(slider, { key: 'Home' });
    expect(onScrubStart).toHaveBeenCalledTimes(3);
    expect(onScrubProgress).toHaveBeenLastCalledWith(0);

    fireEvent.keyDown(slider, { key: 'End' });
    expect(onScrubStart).toHaveBeenCalledTimes(4);
    expect(onScrubProgress).toHaveBeenLastCalledWith(1);

    fireEvent.pointerDown(slider, { clientX: 50, pointerId: 1 });
    expect(onScrubStart).toHaveBeenCalledTimes(5);
    expect(onScrubProgress).toHaveBeenLastCalledWith(expect.closeTo(0.25, 5));

    fireEvent.pointerMove(slider, { clientX: 120, pointerId: 1 });
    expect(onScrubStart).toHaveBeenCalledTimes(6);
    expect(onScrubProgress).toHaveBeenLastCalledWith(expect.closeTo(0.6, 5));
    fireEvent.pointerUp(slider, { pointerId: 1 });

    // Pointer capture throwing NotFoundError (e.g. cancelled touch/stylus or synthetic pointerId) must never break scrubbing
    slider.setPointerCapture = () => {
      throw new DOMException('No active pointer', 'NotFoundError');
    };
    slider.hasPointerCapture = () => true;
    slider.releasePointerCapture = () => {
      throw new DOMException('No active pointer', 'NotFoundError');
    };
    expect(() => {
      fireEvent.pointerDown(slider, { clientX: 150, pointerId: 99 });
      fireEvent.pointerUp(slider, { pointerId: 99 });
    }).not.toThrow();
    expect(onScrubProgress).toHaveBeenLastCalledWith(expect.closeTo(0.75, 5));
  });

  it('displays floating hover timecode & scene slate preview while moving pointer over timeline track', () => {
    const onSelectChapter = vi.fn();
    render(
      <CinemaTimelineHUD
        scrollProgress={0.2}
        activeSection="timeline"
        onSelectChapter={onSelectChapter}
      />
    );

    const slider = screen.getByTestId('cinema-timeline-track');
    Object.defineProperty(slider, 'getBoundingClientRect', {
      value: () => ({ left: 0, width: 200, top: 0, right: 200, bottom: 10, height: 10 }),
    });

    expect(screen.queryByTestId('cinema-hover-preview')).toBeNull();

    fireEvent.pointerMove(slider, { clientX: 100 });
    const preview = screen.getByTestId('cinema-hover-preview');
    expect(preview.textContent).toContain('00:00:45:00');
    expect(preview.className).toContain('top-[calc(100%+10px)]');

    fireEvent.pointerLeave(slider);
    expect(screen.queryByTestId('cinema-hover-preview')).toBeNull();
  });

  it('computes symmetric quintic easing, uses behavior instant to prevent CSS scroll-behavior smooth conflicts, ignores sheet-internal wheel, and falls back to scrollIntoView', () => {
    expect(easeInOutQuint(0)).toBe(0);
    expect(easeInOutQuint(0.5)).toBeCloseTo(0.5, 5);
    expect(easeInOutQuint(1)).toBe(1);
    expect(easeInOutQuint(0.25)).toBeLessThan(0.25);
    expect(easeInOutQuint(0.75)).toBeGreaterThan(0.75);

    const scrollIntoViewMock = vi.fn();
    const sectionEl = document.createElement('div');
    sectionEl.id = 'vault';
    sectionEl.scrollIntoView = scrollIntoViewMock;
    document.body.appendChild(sectionEl);

    scrollToSectionCinematic('vault', { reducedMotion: false });
    expect(scrollIntoViewMock).toHaveBeenCalledWith({ behavior: 'smooth' });
    sectionEl.remove();

    // Verify programmatic scrollTo uses behavior: 'instant' (never 'auto') so html { scroll-behavior: smooth } cannot stall RAF flights or lag drag scrubbing
    const origScrollHeightDesc = Object.getOwnPropertyDescriptor(document.documentElement, 'scrollHeight');
    const origInnerHeightDesc = Object.getOwnPropertyDescriptor(window, 'innerHeight');
    const origScrollYDesc = Object.getOwnPropertyDescriptor(window, 'scrollY');
    const origScrollTo = window.scrollTo;
    const origRaf = window.requestAnimationFrame;
    const origCancelRaf = window.cancelAnimationFrame;

    try {
      let currentY = 0;
      const scrollCalls: Array<{ top?: number; behavior?: ScrollBehavior }> = [];
      let scheduledCb: FrameRequestCallback | null = null;
      let rafId = 1;
      const cancelledIds: number[] = [];

      Object.defineProperty(document.documentElement, 'scrollHeight', { value: 4800, configurable: true });
      Object.defineProperty(window, 'innerHeight', { value: 800, configurable: true });
      Object.defineProperty(window, 'scrollY', { get: () => currentY, configurable: true });
      window.scrollTo = ((opts: ScrollToOptions | number) => {
        if (typeof opts === 'object' && opts !== null) {
          scrollCalls.push({ top: opts.top, behavior: opts.behavior });
          if (typeof opts.top === 'number') currentY = opts.top;
        }
      }) as typeof window.scrollTo;
      window.requestAnimationFrame = ((cb: FrameRequestCallback) => {
        scheduledCb = cb;
        return rafId++;
      }) as typeof window.requestAnimationFrame;
      window.cancelAnimationFrame = ((id: number) => {
        cancelledIds.push(id);
        scheduledCb = null;
      }) as typeof window.cancelAnimationFrame;

      // 1. Instant scrub seek must pass behavior: 'instant'
      scrollToProgressCinematic(0.25, { smooth: false, reducedMotion: false });
      expect(scrollCalls[scrollCalls.length - 1]).toEqual({ top: 1000, behavior: 'instant' });

      // 2. Smooth RAF flight steps must pass behavior: 'instant' and ignore wheel inside SlideOverInspectionSheet
      currentY = 0;
      animateCinematicScrollTo(2000, { durationMs: 700, reducedMotion: false });
      const sheet = document.createElement('aside');
      sheet.setAttribute('data-testid', 'slide-over-inspection-sheet');
      const innerChild = document.createElement('div');
      sheet.appendChild(innerChild);
      document.body.appendChild(sheet);

      innerChild.dispatchEvent(new WheelEvent('wheel', { deltaY: 100, bubbles: true }));
      expect(scheduledCb).not.toBeNull();

      // Advance one RAF step
      const stepCb = scheduledCb as FrameRequestCallback | null;
      if (stepCb) stepCb(350);
      const stepCb2 = scheduledCb as FrameRequestCallback | null;
      if (stepCb2) stepCb2(700);
      expect(scrollCalls.every((c) => c.behavior === 'instant')).toBe(true);
      expect(currentY).toBe(1000);

      // Page-level wheel outside sheet must cancel an active flight
      window.dispatchEvent(new WheelEvent('wheel', { deltaY: 120, bubbles: true }));
      expect(cancelledIds.length).toBeGreaterThan(0);

      sheet.remove();
      cancelActiveScrollFlight();
    } finally {
      window.scrollTo = origScrollTo;
      window.requestAnimationFrame = origRaf;
      window.cancelAnimationFrame = origCancelRaf;
      if (origScrollHeightDesc) Object.defineProperty(document.documentElement, 'scrollHeight', origScrollHeightDesc);
      if (origInnerHeightDesc) Object.defineProperty(window, 'innerHeight', origInnerHeightDesc);
      if (origScrollYDesc) Object.defineProperty(window, 'scrollY', origScrollYDesc);
    }
  });
});
