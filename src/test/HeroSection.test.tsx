import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HeroSection } from '../components/HeroSection';

describe('HeroSection Component', () => {
  it('renders display typography and executive narrative', () => {
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    expect(screen.getByText(/Architect of Enterprise Intelligence/i)).toBeDefined();
    expect(screen.getAllByText(/Ang Zi Yang \(Zachary\)/i).length).toBeGreaterThanOrEqual(1);
  });

  it('renders the canonical 4-column hardware benchmark telemetry bar', () => {
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    expect(screen.getAllByText(/1st \/ 53 Teams/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/3\.75 BSc/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/14 Quests & 7 Badges/i)).toBeDefined();
    expect(screen.getByText(/0 Defect UAT/i)).toBeDefined();
  });

  it('triggers onExploreClick and onCaseStudiesClick when CTA buttons are clicked', () => {
    const onExplore = vi.fn();
    const onCaseStudies = vi.fn();

    render(<HeroSection onExploreClick={onExplore} onCaseStudiesClick={onCaseStudies} />);

    const exploreBtn = screen.getByRole('button', { name: /^explore case studies$/i });
    const inspectBtn = screen.getByRole('button', { name: /^executive inquiries$/i });

    fireEvent.click(exploreBtn);
    expect(onExplore).toHaveBeenCalledTimes(1);

    fireEvent.click(inspectBtn);
    expect(onCaseStudies).toHaveBeenCalledTimes(1);
  });

  it('triggers modern onExploreCaseStudies and onExecutiveInquiries props when provided', () => {
    const onCaseStudies = vi.fn();
    const onInquiries = vi.fn();

    render(
      <HeroSection
        onExploreCaseStudies={onCaseStudies}
        onExecutiveInquiries={onInquiries}
      />
    );

    const exploreBtn = screen.getByRole('button', { name: /^explore case studies$/i });
    const inquiriesBtn = screen.getByRole('button', { name: /^executive inquiries$/i });

    fireEvent.click(exploreBtn);
    expect(onCaseStudies).toHaveBeenCalledTimes(1);

    fireEvent.click(inquiriesBtn);
    expect(onInquiries).toHaveBeenCalledTimes(1);
  });

  it('renders Zachary authentic portrait and credentials inside Executive Keynote Dossier drawer', () => {
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    // Role, Peak Accolade & Key Domains
    expect(screen.getByText('AI Product Strategist & Solutions Architect')).toBeDefined();
    expect(screen.getByText(/Soft Space Fintech & Multi-Modal Agentic Systems/i)).toBeDefined();
    expect(screen.getByText(/Global Grand Champion • Hilti IT Competition 2024/i)).toBeDefined();
    expect(screen.getByText(/Enterprise AI Systems • Soft Space Fintech • Vertex AI/i)).toBeDefined();

    // Open Executive Keynote Dossier
    const dossierBtn = screen.getByRole('button', { name: /executive.*dossier/i });
    expect(dossierBtn).toBeDefined();
    fireEvent.click(dossierBtn);

    // Authentic portrait inside hero showcase card & drawer
    const portraitImgs = screen.getAllByRole('img', {
      name: /Ang Zi Yang \(Zachary\) — AI Product Strategist & Solutions Architect/i,
    });
    expect(portraitImgs.length).toBeGreaterThanOrEqual(1);
    expect(portraitImgs[0]?.getAttribute('src')).toBe('/images/zachary_editorial_portrait.webp');
  });

  it('renders spatial 3D enterprise engine floating HUD frame with explode architecture action and executive dossier trigger', () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent');
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    // Spatial Enterprise AI Engine HUD frame elements
    expect(screen.getByText(/ENTERPRISE AI ENGINE • LIVE ARCHITECTURE • ACT 01/i)).toBeDefined();
    expect(screen.getByText(/Multi-Tiered Production AI & Fintech Core/i)).toBeDefined();

    // Explode Architecture Button
    const explodeBtn = screen.getByRole('button', { name: /explode architecture/i });
    expect(explodeBtn).toBeDefined();
    fireEvent.click(explodeBtn);
    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'portfolio:scene_action',
      })
    );

    // Inspect Keynote Dossier Button (Right column HUD trigger)
    const inspectDossierBtn = screen.getByRole('button', { name: /inspect keynote dossier/i });
    expect(inspectDossierBtn).toBeDefined();
    fireEvent.click(inspectDossierBtn);

    // Verify modal dossier drawer opened
    const drawerTitle = screen.getByText(/EXECUTIVE KEYNOTE DOSSIER/i);
    expect(drawerTitle).toBeDefined();

    dispatchSpy.mockRestore();
  });

  it('renders spatial avatar poses action dock and dispatches dynamic scene action events for all poses', () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent');
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    expect(screen.getByText(/Spatial Avatar Poses/i)).toBeDefined();
    expect(screen.getByText(/Live Kinematics/i)).toBeDefined();

    // 1. Glasses adjust action
    const glassesBtn = screen.getByRole('button', { name: /glasses adjust pose/i });
    expect(glassesBtn).toBeDefined();
    fireEvent.click(glassesBtn);
    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'portfolio:scene_action',
        detail: { action: 'glasses_adjust', source: 'hero' },
      })
    );

    // 2. Inspect tablet action
    const tabletBtn = screen.getByRole('button', { name: /inspect tablet pose/i });
    expect(tabletBtn).toBeDefined();
    fireEvent.click(tabletBtn);
    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'portfolio:scene_action',
        detail: { action: 'inspect_tablet', source: 'hero' },
      })
    );

    // 3. Keynote present action
    const keynoteBtn = screen.getByRole('button', { name: /keynote present pose/i });
    expect(keynoteBtn).toBeDefined();
    fireEvent.click(keynoteBtn);
    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'portfolio:scene_action',
        detail: { action: 'keynote_present', source: 'hero' },
      })
    );

    // 4. Reset pose action
    const resetBtn = screen.getByRole('button', { name: /reset pose/i });
    expect(resetBtn).toBeDefined();
    fireEvent.click(resetBtn);
    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'portfolio:scene_action',
        detail: { action: 'reset_pose', source: 'hero' },
      })
    );

    dispatchSpy.mockRestore();
  });

  it('synchronizes active pose button styling when portfolio:scene_action events are dispatched externally', () => {
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    const spectaclesBtn = screen.getByRole('button', { name: /glasses adjust pose/i });
    expect(spectaclesBtn.className).toContain('bg-white/5');

    // External dispatch (e.g. from script or another component)
    fireEvent(
      window,
      new CustomEvent('portfolio:scene_action', {
        detail: { action: 'glasses_adjust', source: 'external' },
      })
    );

    // Should now be highlighted
    expect(spectaclesBtn.className).toContain('bg-cyan-500/30');

    // External auto-return or reset dispatch
    fireEvent(
      window,
      new CustomEvent('portfolio:scene_action', {
        detail: { action: 'reset_pose', source: 'auto_return' },
      })
    );

    // Should return to unselected style
    expect(spectaclesBtn.className).toContain('bg-white/5');
  });

  it('structures mobile & tablet layout hierarchy so 3D spatial stage is surfaced directly below headline', () => {
    const { container } = render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    const peekHideContainer = container.querySelector('[data-peek-hide]');
    expect(peekHideContainer).toBeDefined();
    expect(peekHideContainer?.className).toContain('flex flex-col lg:grid lg:grid-cols-12');

    const children = peekHideContainer?.children;
    expect(children?.length).toBe(3);

    // Block 1: Headline & Identity
    const block1 = children?.[0];
    expect(block1?.className).toContain('lg:col-span-7');
    expect(block1?.textContent).toContain('Architect of Enterprise Intelligence');

    // Block 2: 3D Stage Reticle & Kinematics Dock
    const block2 = children?.[1];
    expect(block2?.className).toContain('lg:col-span-5');
    expect(block2?.textContent).toContain('3D SPATIAL STAGE');
    expect(block2?.textContent).toContain('Live Kinematics');

    // Block 3: Narrative, CTAs & Telemetry
    const block3 = children?.[2];
    expect(block3?.className).toContain('lg:col-span-7');
    expect(block3?.textContent).toContain('Begin Growth Journey');
    expect(block3?.textContent).toContain('GLOBAL RANK');
  });
});
