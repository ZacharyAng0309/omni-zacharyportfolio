import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act, within } from '@testing-library/react';
import App from '../App';

import { useEffect as mockUseEffect } from 'react';
import type { PortfolioEngine as MockPortfolioEngine } from '../graphics/SceneController';

let capturedOnSelectCaseStudyNode: ((slug: string) => void) | undefined;
let capturedOnSelectSummitBeacon: (() => void) | undefined;
let activeMockController: MockPortfolioEngine | null = null;

vi.mock('../graphics/ThreeCanvas', () => ({
  ThreeCanvas: ({
    onSelectCaseStudyNode,
    onSelectSummitBeacon,
    onControllerReady,
  }: {
    onSelectCaseStudyNode?: (slug: string) => void;
    onSelectSummitBeacon?: () => void;
    onControllerReady?: (controller: MockPortfolioEngine) => void;
  }) => {
    capturedOnSelectCaseStudyNode = onSelectCaseStudyNode;
    capturedOnSelectSummitBeacon = onSelectSummitBeacon;
    mockUseEffect(() => {
      if (activeMockController) {
        onControllerReady?.(activeMockController);
      }
    }, [onControllerReady]);
    return <div data-testid="webgl-canvas" />;
  },
}));

describe('App Component Integration & Modal Raycasting Triggers', () => {
  beforeEach(() => {
    document.body.style.overflow = '';
    capturedOnSelectCaseStudyNode = undefined;
    capturedOnSelectSummitBeacon = undefined;
  });

  it('renders all primary portfolio sections and navigation HUD', () => {
    render(<App />);

    expect(screen.getAllByText(/Architect of Enterprise Intelligence/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/1st Place Worldwide • Team Sweetzerland/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Act 05 • The Frontier/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Act 02 • The Academy/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Act 03 • The Crucible/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Initiate Collaboration/i).length).toBeGreaterThan(0);

    // Verify new MOD-11 Diegetic Whisper HUD, 3D Hotspot Reticles, and Slide-Over Sheet
    expect(screen.getByTestId('whisper-stage-hud')).toBeDefined();
    expect(screen.getByTestId('diegetic-hotspot-layer')).toBeDefined();
    const sheet = screen.getByTestId('slide-over-inspection-sheet');
    expect(sheet.getAttribute('data-sheet-open')).toBe('false');
  });

  it('opens and closes SlideOverInspectionSheet when clicking a Diegetic 3D Hotspot or Whisper Sub-Target Pill', () => {
    render(<App />);

    const sheet = screen.getByTestId('slide-over-inspection-sheet');
    expect(sheet.getAttribute('data-sheet-open')).toBe('false');

    // Click a diegetic 3D hotspot reticle
    const hotspotBtn = screen.getByTestId('diegetic-hotspot-strategy-table');
    act(() => {
      fireEvent.click(hotspotBtn);
    });
    expect(sheet.getAttribute('data-sheet-open')).toBe('true');

    // Close the inspection sheet
    const closeSheetBtn = screen.getByTestId('close-inspection-sheet-btn');
    act(() => {
      fireEvent.click(closeSheetBtn);
    });
    expect(sheet.getAttribute('data-sheet-open')).toBe('false');
  });

  it('resets activeSubTargetId, selectedActOverride, and camera focus when closing SlideOverInspectionSheet via WhisperStageHUD toggle', () => {
    const clearSubTargetFocus = vi.fn();
    const focusSubTarget = vi.fn();
    const getProjectedHotspots = vi.fn(() => []);
    const fnCache = new Map<string | symbol, ReturnType<typeof vi.fn>>();
    activeMockController = new Proxy(
      { clearSubTargetFocus, focusSubTarget, getProjectedHotspots },
      {
        get(target, prop) {
          if (prop in target) return target[prop as keyof typeof target];
          if (prop === 'then') return undefined;
          let fn = fnCache.get(prop);
          if (!fn) {
            fn = vi.fn();
            fnCache.set(prop, fn);
          }
          return fn;
        },
      }
    ) as unknown as MockPortfolioEngine;

    try {
      render(<App />);

      const sheet = screen.getByTestId('slide-over-inspection-sheet');
      const toggleBtn = screen.getByTestId('whisper-open-dossier-btn');
      const subtargetBtn = screen.getByTestId('whisper-subtarget-strategy-table');

      // Select a sub-target (opens sheet and sets activeSubTargetId + selectedActOverride)
      act(() => {
        fireEvent.click(subtargetBtn);
      });
      expect(sheet.getAttribute('data-sheet-open')).toBe('true');
      expect(subtargetBtn.getAttribute('aria-pressed')).toBe('true');
      expect(screen.getByTestId('whisper-reset-camera-btn')).toBeDefined();
      expect(clearSubTargetFocus).not.toHaveBeenCalled();

      // Switch chapter inside sheet to Act 3 (sets selectedActOverride = 2 and releases stale Act 0 camera focus)
      act(() => {
        fireEvent.click(screen.getByTestId('sheet-tab-act-2'));
      });
      expect(sheet.textContent?.startsWith('Act 03 • The Crucible')).toBe(true);
      expect(clearSubTargetFocus).toHaveBeenCalledTimes(1);

      // Toggle closed via WhisperStageHUD button -> must clear sheet, activeSubTargetId, selectedActOverride, and camera focus
      act(() => {
        fireEvent.click(toggleBtn);
      });
      expect(sheet.getAttribute('data-sheet-open')).toBe('false');
      expect(screen.queryByTestId('whisper-reset-camera-btn')).toBeNull();
      expect(clearSubTargetFocus).toHaveBeenCalledTimes(2);

      // Active act falls back to scroll section (Act 0), so strategy-table subtarget is visible again & unpressed
      const resetSubtargetBtn = screen.getByTestId('whisper-subtarget-strategy-table');
      expect(resetSubtargetBtn.getAttribute('aria-pressed')).toBe('false');

      // Re-opening via WhisperStageHUD opens back at scroll Act 0 (not stale Act 03)
      act(() => {
        fireEvent.click(toggleBtn);
      });
      expect(sheet.getAttribute('data-sheet-open')).toBe('true');
      expect(sheet.textContent?.startsWith('Act 01 • Titanium Atelier')).toBe(true);
    } finally {
      activeMockController = null;
    }
  });

  it('renders warm editorial SlideOverInspectionSheet header, dispatches handshake_wave on submit, and cleans up timers on unmount', () => {
    vi.useFakeTimers();
    const clearTimeoutSpy = vi.spyOn(globalThis, 'clearTimeout');
    const dispatchedActions: string[] = [];
    const listener = (e: Event) => {
      const detail = (e as CustomEvent<{ action?: string }>).detail;
      if (detail?.action) dispatchedActions.push(detail.action);
    };
    window.addEventListener('portfolio:scene_action', listener);

    const { unmount } = render(<App />);

    // Open sheet
    act(() => {
      fireEvent.click(screen.getByTestId('whisper-open-dossier-btn'));
    });

    const sheet = screen.getByTestId('slide-over-inspection-sheet');
    expect(sheet.textContent).not.toMatch(/Left 60% Live Stage/i);

    // Copy email & submit dispatch form
    const copyBtn = within(sheet).getByRole('button', { name: /copy/i });
    act(() => {
      fireEvent.click(copyBtn);
    });
    expect(within(sheet).getByText('Copied')).toBeDefined();

    const nameInput = within(sheet).getByPlaceholderText('Your Name / Organization');
    const emailInput = within(sheet).getByPlaceholderText('Corporate Email');
    const msgInput = within(sheet).getByPlaceholderText('Project scope or collaboration topic...');
    act(() => {
      fireEvent.change(nameInput, { target: { value: 'Ada Lovelace' } });
      fireEvent.change(emailInput, { target: { value: 'ada@analytical.org' } });
      fireEvent.change(msgInput, { target: { value: 'Exploring multi-agent systems.' } });
    });
    const submitBtn = within(sheet).getByRole('button', { name: /transmit direct dispatch/i });
    act(() => {
      fireEvent.click(submitBtn);
    });

    expect(dispatchedActions).toContain('handshake_wave');
    expect(within(sheet).getByText('Dispatch Prepared')).toBeDefined();

    const callsBeforeUnmount = clearTimeoutSpy.mock.calls.length;
    unmount();
    expect(clearTimeoutSpy.mock.calls.length).toBeGreaterThanOrEqual(callsBeforeUnmount + 2);

    window.removeEventListener('portfolio:scene_action', listener);
    clearTimeoutSpy.mockRestore();
    vi.useRealTimers();
  });

  it('opens Hireti modal when 3D flagshipOrb triggers onSelectCaseStudyNode with "hireti"', () => {
    render(<App />);

    expect(capturedOnSelectCaseStudyNode).toBeDefined();

    // 3D scene raycast hit triggers onSelectCaseStudyNode('hireti')
    act(() => {
      capturedOnSelectCaseStudyNode!('hireti');
    });

    // Hireti modal should now be open
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeDefined();
    expect(within(dialog).getByText('Hireti (Team Sweetzerland)')).toBeDefined();
    expect(within(dialog).getByText(/Flagship AI • Team Lead & Product Strategist/i)).toBeDefined();
    expect(within(dialog).getByText(/Global Grand Champion/i)).toBeDefined();

    // Close modal
    const closeBtn = within(dialog).getByLabelText('Close modal');
    act(() => {
      fireEvent.click(closeBtn);
    });

    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('opens Omni-Workstation modal when onSelectCaseStudyNode is triggered with "omni-workstation"', () => {
    render(<App />);

    expect(capturedOnSelectCaseStudyNode).toBeDefined();

    act(() => {
      capturedOnSelectCaseStudyNode!('omni-workstation');
    });

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeDefined();
    expect(within(dialog).getByText('Omni-Workstation — Autonomous Multi-Modal Agentic Factory')).toBeDefined();
    expect(within(dialog).getByText(/Agentic Systems • Lead Architect & Systems Designer/i)).toBeDefined();
    expect(within(dialog).getByText(/Autonomous Multi-Modal Engineering Framework/i)).toBeDefined();

    // Close via close button
    const closeBtn = within(dialog).getByLabelText('Close modal');
    act(() => {
      fireEvent.click(closeBtn);
    });

    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('opens PressModal when 3D summit beacon callback is triggered', () => {
    render(<App />);

    expect(capturedOnSelectSummitBeacon).toBeDefined();

    act(() => {
      capturedOnSelectSummitBeacon!();
    });

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeDefined();
    expect(within(dialog).getByText(/National Press & Global Championship Verification/i)).toBeDefined();
    expect(within(dialog).getByText(/"To the Land of the Alps, we go!"/i)).toBeDefined();

    const closeBtn = within(dialog).getByLabelText('Close modal');
    act(() => {
      fireEvent.click(closeBtn);
    });

    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('keeps SlideOverInspectionSheet sticky header unclipped via overflow-clip and inner container scrollTo (never calling Element.scrollIntoView), clears CinemaTimelineHUD & bottom dock, supports 3D Peek fade, and syncs cross-act navigation', () => {
    const scrollIntoViewSpy = vi.spyOn(Element.prototype, 'scrollIntoView');
    const clearSubTargetFocus = vi.fn();
    const selectSubTarget = vi.fn();
    const getProjectedHotspots = vi.fn(() => []);
    const getActiveSubTarget = vi.fn(() => null);
    const fnCache = new Map<string | symbol, ReturnType<typeof vi.fn>>();
    activeMockController = new Proxy(
      { clearSubTargetFocus, selectSubTarget, getProjectedHotspots, getActiveSubTarget },
      {
        get(target, prop) {
          if (prop in target) return target[prop as keyof typeof target];
          if (prop === 'then') return undefined;
          let fn = fnCache.get(prop);
          if (!fn) {
            fn = vi.fn();
            fnCache.set(prop, fn);
          }
          return fn;
        },
      }
    ) as unknown as MockPortfolioEngine;

    try {
      render(<App />);

      const sheet = screen.getByTestId('slide-over-inspection-sheet');
      const timelineHud = screen.getByTestId('cinema-timeline-hud');
      expect(timelineHud.className).toContain('top-[66px]');
      expect(sheet.className).toContain('overflow-clip');
      expect(sheet.className).toContain('top-[110px]');
      expect(sheet.className).toContain('sm:top-[132px]');
      expect(sheet.className).toContain('sm:bottom-[92px]');
      expect(sheet.hasAttribute('data-peek-sheet')).toBe(true);

      const scroller = sheet.querySelector('.overflow-y-auto') as HTMLElement;
      const scrollerScrollToSpy = vi.fn();
      scroller.scrollTo = scrollerScrollToSpy;

      // Open sheet via sub-target pill and switch chapter tabs
      act(() => {
        fireEvent.click(screen.getByTestId('whisper-subtarget-optical-core'));
      });
      const scrollCallsAfterOpen = scrollerScrollToSpy.mock.calls.length;

      // Clicking another sub-target within the SAME chapter must not yank the inner drawer scroll position
      act(() => {
        fireEvent.click(screen.getByTestId('sheet-subtarget-strategy-table'));
      });
      expect(scrollerScrollToSpy.mock.calls.length).toBe(scrollCallsAfterOpen);

      // Switching chapter tab clears stale focus and scrolls drawer to Act 04
      act(() => {
        fireEvent.click(screen.getByTestId('sheet-tab-act-3'));
      });
      expect(clearSubTargetFocus).toHaveBeenCalledTimes(1);
      expect(scrollerScrollToSpy.mock.calls.length).toBe(scrollCallsAfterOpen + 1);

      // Cross-act Focus 3D Core click inside Act 05 section scrolls page to #ai-solutions so the target act is visible
      const act5Section = sheet.querySelector('[data-sheet-chapter="4"]') as HTMLElement;
      const focusCoreBtn = within(act5Section).getAllByRole('button', { name: /focus 3d core/i })[0]!;
      scrollIntoViewSpy.mockClear();
      act(() => {
        fireEvent.click(focusCoreBtn);
      });
      expect(selectSubTarget).toHaveBeenCalledWith(4, 'hireti-sweetzerland', { emitCallback: false });
      const aiSolutionsEl = document.getElementById('ai-solutions');
      expect(scrollIntoViewSpy.mock.instances).toContain(aiSolutionsEl);

      // Clicking top NavbarHUD clears active focus & resets sheet chapter override
      const navGrowthBtn = screen.getByRole('button', { name: '02. Growth' });
      act(() => {
        fireEvent.click(navGrowthBtn);
      });
      expect(clearSubTargetFocus).toHaveBeenCalledTimes(2);

      // SlideOverInspectionSheet must scroll only its inner scrollContainerRef (scrollTo), never scrollIntoView on chapter sections
      const sheetSectionScrollCalls = scrollIntoViewSpy.mock.instances.filter(
        (inst) => inst instanceof Element && inst.hasAttribute('data-sheet-chapter')
      );
      expect(sheetSectionScrollCalls).toHaveLength(0);
    } finally {
      activeMockController = null;
      scrollIntoViewSpy.mockRestore();
    }
  });

  it('releases active CameraRig focus when scrubbing CinemaTimelineHUD (keyboard & pointer) and avoids arming stale pendingNavAct when clicking the already-active chapter tab', () => {
    const clearSubTargetFocus = vi.fn();
    const selectSubTarget = vi.fn();
    const getProjectedHotspots = vi.fn(() => []);
    const getActiveSubTarget = vi.fn(() => null);
    const fnCache = new Map<string | symbol, ReturnType<typeof vi.fn>>();
    activeMockController = new Proxy(
      { clearSubTargetFocus, selectSubTarget, getProjectedHotspots, getActiveSubTarget },
      {
        get(target, prop) {
          if (prop in target) return target[prop as keyof typeof target];
          if (prop === 'then') return undefined;
          let fn = fnCache.get(prop);
          if (!fn) {
            fn = vi.fn();
            fnCache.set(prop, fn);
          }
          return fn;
        },
      }
    ) as unknown as MockPortfolioEngine;

    const origScrollHeightDesc = Object.getOwnPropertyDescriptor(document.documentElement, 'scrollHeight');
    const origInnerHeightDesc = Object.getOwnPropertyDescriptor(window, 'innerHeight');
    const origScrollYDesc = Object.getOwnPropertyDescriptor(window, 'scrollY');
    const origScrollTo = window.scrollTo;

    try {
      let currentScrollY = 0;
      Object.defineProperty(document.documentElement, 'scrollHeight', { value: 4800, configurable: true });
      Object.defineProperty(window, 'innerHeight', { value: 800, configurable: true });
      Object.defineProperty(window, 'scrollY', { get: () => currentScrollY, configurable: true });
      window.scrollTo = ((optsOrX: ScrollToOptions | number, y?: number) => {
        if (typeof optsOrX === 'number') {
          currentScrollY = y ?? 0;
        } else if (optsOrX && typeof optsOrX.top === 'number') {
          currentScrollY = optsOrX.top;
        }
      }) as typeof window.scrollTo;

      render(<App />);

      // Configure deterministic section offsets & rects for scroll synchronization
      const sectionIds = ['hero', 'timeline', 'vault', 'summit', 'ai-solutions', 'contact'];
      sectionIds.forEach((id, idx) => {
        const el = document.getElementById(id)!;
        Object.defineProperty(el, 'offsetTop', { value: idx * 800, configurable: true });
        el.getBoundingClientRect = () =>
          ({
            top: idx * 800 - currentScrollY,
            bottom: (idx + 1) * 800 - currentScrollY,
            height: 800,
            left: 0,
            right: 1280,
            width: 1280,
            x: 0,
            y: idx * 800 - currentScrollY,
            toJSON: () => {},
          }) as DOMRect;
      });

      const sheet = screen.getByTestId('slide-over-inspection-sheet');
      const slider = screen.getByTestId('cinema-timeline-track');
      Object.defineProperty(slider, 'getBoundingClientRect', {
        value: () => ({ left: 0, width: 400, top: 0, right: 400, bottom: 10, height: 10 }),
      });

      // 1. Focus Act 1 Optical Neural Core, then scrub via keyboard ArrowRight (stays within Act 1)
      const opticalCoreBtn = screen.getByTestId('whisper-subtarget-optical-core');
      act(() => {
        fireEvent.click(opticalCoreBtn);
      });
      expect(opticalCoreBtn.getAttribute('aria-pressed')).toBe('true');
      expect(screen.getByTestId('whisper-reset-camera-btn')).toBeDefined();

      act(() => {
        fireEvent.keyDown(slider, { key: 'ArrowRight' });
      });
      expect(clearSubTargetFocus).toHaveBeenCalledTimes(1);
      expect(opticalCoreBtn.getAttribute('aria-pressed')).toBe('false');
      expect(screen.queryByTestId('whisper-reset-camera-btn')).toBeNull();

      // 2. Re-focus Optical Neural Core, then scrub via pointerDown on timeline track
      currentScrollY = 0;
      act(() => {
        window.dispatchEvent(new Event('scroll'));
        fireEvent.click(opticalCoreBtn);
      });
      expect(opticalCoreBtn.getAttribute('aria-pressed')).toBe('true');

      act(() => {
        fireEvent.pointerDown(slider, { clientX: 20, pointerId: 1 });
        fireEvent.pointerUp(slider, { pointerId: 1 });
      });
      expect(clearSubTargetFocus).toHaveBeenCalledTimes(2);
      expect(opticalCoreBtn.getAttribute('aria-pressed')).toBe('false');
      expect(screen.queryByTestId('whisper-reset-camera-btn')).toBeNull();

      // 3. Click already-active chapter tab (01 Studio while on #hero), then immediately scroll to Act 2 (#timeline)
      // Must NOT leave a stale pendingNavAct that blocks the sheet from syncing to Act 02
      currentScrollY = 0;
      act(() => {
        window.dispatchEvent(new Event('scroll'));
        fireEvent.click(screen.getByTestId('sheet-tab-act-0'));
      });
      expect(sheet.textContent?.startsWith('Act 01 • Titanium Atelier')).toBe(true);

      currentScrollY = 800;
      act(() => {
        window.dispatchEvent(new Event('scroll'));
      });
      expect(sheet.textContent?.startsWith('Act 02 • The Academy')).toBe(true);

      // 4. Cross-act Focus 3D Core interrupted mid-flight by page wheel in Act 2 clears focus & syncs sheet to Act 02,
      //    whereas scrolling inside the sheet itself does NOT cancel pending cross-act focus
      currentScrollY = 0;
      act(() => {
        window.dispatchEvent(new Event('scroll'));
      });
      const act5Section = sheet.querySelector('[data-sheet-chapter="4"]') as HTMLElement;
      const focusCoreBtn = within(act5Section).getAllByRole('button', { name: /focus 3d core/i })[0]!;
      clearSubTargetFocus.mockClear();
      act(() => {
        fireEvent.click(focusCoreBtn);
      });
      expect(sheet.textContent?.startsWith('Act 05 • The Frontier')).toBe(true);

      // Mid-flight arrival in Act 2 (scrollY = 800) while pendingNavAct = 4
      currentScrollY = 800;
      act(() => {
        window.dispatchEvent(new Event('scroll'));
      });
      // Scrolling inside the inspection sheet must NOT interrupt the cross-act focus
      act(() => {
        fireEvent.wheel(act5Section, { deltaY: 120 });
      });
      expect(clearSubTargetFocus).not.toHaveBeenCalled();
      expect(sheet.textContent?.startsWith('Act 05 • The Frontier')).toBe(true);

      // Manual wheel on the page (outside sheet) cancels the cross-act jump and syncs back to Act 02
      act(() => {
        window.dispatchEvent(new WheelEvent('wheel', { deltaY: 120, bubbles: true }));
      });
      expect(clearSubTargetFocus).toHaveBeenCalledTimes(1);
      expect(sheet.textContent?.startsWith('Act 02 • The Academy')).toBe(true);
    } finally {
      activeMockController = null;
      window.scrollTo = origScrollTo;
      if (origScrollHeightDesc) Object.defineProperty(document.documentElement, 'scrollHeight', origScrollHeightDesc);
      if (origInnerHeightDesc) Object.defineProperty(window, 'innerHeight', origInnerHeightDesc);
      if (origScrollYDesc) Object.defineProperty(window, 'scrollY', origScrollYDesc);
    }
  });

  it('keeps WhisperStageHUD corridor status mounted without layout jump and highlights active sub-target cards in SlideOverInspectionSheet', () => {
    const clearSubTargetFocus = vi.fn();
    const selectSubTarget = vi.fn();
    const getProjectedHotspots = vi.fn(() => []);
    const getActiveSubTarget = vi.fn(() => null);
    const fnCache = new Map<string | symbol, ReturnType<typeof vi.fn>>();
    activeMockController = new Proxy(
      { clearSubTargetFocus, selectSubTarget, getProjectedHotspots, getActiveSubTarget },
      {
        get(target, prop) {
          if (prop in target) return target[prop as keyof typeof target];
          if (prop === 'then') return undefined;
          let fn = fnCache.get(prop);
          if (!fn) {
            fn = vi.fn();
            fnCache.set(prop, fn);
          }
          return fn;
        },
      }
    ) as unknown as MockPortfolioEngine;

    const origScrollHeightDesc = Object.getOwnPropertyDescriptor(document.documentElement, 'scrollHeight');
    const origInnerHeightDesc = Object.getOwnPropertyDescriptor(window, 'innerHeight');
    const origScrollYDesc = Object.getOwnPropertyDescriptor(window, 'scrollY');

    try {
      let currentScrollY = 0;
      Object.defineProperty(document.documentElement, 'scrollHeight', { value: 4800, configurable: true });
      Object.defineProperty(window, 'innerHeight', { value: 800, configurable: true });
      Object.defineProperty(window, 'scrollY', { get: () => currentScrollY, configurable: true });

      render(<App />);

      const sectionIds = ['hero', 'timeline', 'vault', 'summit', 'ai-solutions', 'contact'];
      sectionIds.forEach((id, idx) => {
        const el = document.getElementById(id)!;
        Object.defineProperty(el, 'offsetTop', { value: idx * 800, configurable: true });
        el.getBoundingClientRect = () =>
          ({
            top: idx * 800 - currentScrollY,
            bottom: (idx + 1) * 800 - currentScrollY,
            height: 800,
            left: 0,
            right: 1280,
            width: 1280,
            x: 0,
            y: idx * 800 - currentScrollY,
            toJSON: () => {},
          }) as DOMRect;
      });

      const corridorStatus = screen.getByTestId('whisper-corridor-status');
      expect(corridorStatus).toBeDefined();
      expect(corridorStatus.className).toContain('max-h-0 opacity-0');

      currentScrollY = 400;
      act(() => {
        window.dispatchEvent(new Event('scroll'));
      });
      expect(corridorStatus.className).toContain('max-h-8 opacity-100');

      const sheet = screen.getByTestId('slide-over-inspection-sheet');
      expect(sheet.getAttribute('aria-hidden')).toBe('true');
      expect(sheet.hasAttribute('inert') || sheet.inert).toBe(true);

      currentScrollY = 0;
      act(() => {
        window.dispatchEvent(new Event('scroll'));
      });
      act(() => {
        fireEvent.click(screen.getByTestId('whisper-subtarget-optical-core'));
      });

      expect(sheet.getAttribute('aria-hidden')).toBe('false');
      expect(sheet.hasAttribute('inert')).toBe(false);
      const opticalBtn = within(sheet).getByRole('button', { name: 'Inspect Optical Nucleus' });
      expect(opticalBtn.getAttribute('data-subtarget-active')).toBe('true');

      // Verify inner drawer scroll spy highlights the scrolled-into chapter tab cleanly
      vi.useFakeTimers();
      try {
        act(() => {
          vi.advanceTimersByTime(600);
        });
        const scrollBody = sheet.querySelector('.overflow-y-auto') as HTMLElement;
        expect(scrollBody).not.toBeNull();
        scrollBody.getBoundingClientRect = () =>
          ({ top: 100, bottom: 700, height: 600, left: 700, right: 1200, width: 500, x: 700, y: 100, toJSON: () => {} }) as DOMRect;
        Array.from(scrollBody.querySelectorAll('[data-sheet-chapter]')).forEach((sec) => {
          const idx = Number(sec.getAttribute('data-sheet-chapter'));
          const topVal = idx <= 2 ? 120 - (2 - idx) * 600 : 120 + (idx - 2) * 600;
          (sec as HTMLElement).getBoundingClientRect = () =>
            ({ top: topVal, bottom: topVal + 580, height: 580, left: 700, right: 1200, width: 500, x: 700, y: topVal, toJSON: () => {} }) as DOMRect;
        });
        act(() => {
          fireEvent.scroll(scrollBody);
        });
        const activeTab03 = screen.getByTestId('sheet-tab-act-2');
        expect(activeTab03.className).toContain('font-semibold');
      } finally {
        vi.useRealTimers();
      }

      act(() => {
        fireEvent.click(screen.getByTestId('sheet-tab-act-4'));
      });
      const act5Section = sheet.querySelector('[data-sheet-chapter="4"]') as HTMLElement;
      const focusCoreBtn = within(act5Section).getAllByRole('button', { name: /focus 3d core/i })[0]!;
      act(() => {
        fireEvent.click(focusCoreBtn);
      });
      const highlightedCards = act5Section.querySelectorAll('[data-subtarget-active="true"]');
      expect(highlightedCards.length).toBe(1);
    } finally {
      activeMockController = null;
      if (origScrollHeightDesc) Object.defineProperty(document.documentElement, 'scrollHeight', origScrollHeightDesc);
      if (origInnerHeightDesc) Object.defineProperty(window, 'innerHeight', origInnerHeightDesc);
      if (origScrollYDesc) Object.defineProperty(window, 'scrollY', origScrollYDesc);
    }
  });
});

