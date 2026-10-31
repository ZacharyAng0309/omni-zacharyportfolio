import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act, within } from '@testing-library/react';
import App from '../App';

let capturedOnSelectCaseStudyNode: ((slug: string) => void) | undefined;
let capturedOnSelectSummitBeacon: (() => void) | undefined;

vi.mock('../graphics/ThreeCanvas', () => ({
  ThreeCanvas: ({
    onSelectCaseStudyNode,
    onSelectSummitBeacon,
  }: {
    onSelectCaseStudyNode?: (slug: string) => void;
    onSelectSummitBeacon?: () => void;
  }) => {
    capturedOnSelectCaseStudyNode = onSelectCaseStudyNode;
    capturedOnSelectSummitBeacon = onSelectSummitBeacon;
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

    expect(screen.getByText(/Architect of Enterprise Intelligence/i)).toBeDefined();
    expect(screen.getByText(/1st Place Worldwide • Team Sweetzerland/i)).toBeDefined();
    expect(screen.getByText(/Act 05 • The Frontier/i)).toBeDefined();
    expect(screen.getByText(/Act 02 • The Academy/i)).toBeDefined();
    expect(screen.getByText(/Act 03 • The Crucible/i)).toBeDefined();
    expect(screen.getByText(/Initiate Collaboration/i)).toBeDefined();
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
});

