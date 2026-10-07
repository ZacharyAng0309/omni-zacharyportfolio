import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import App from '../App';

vi.mock('../graphics/ThreeCanvas', () => ({
  ThreeCanvas: () => <div data-testid="webgl-canvas" />,
}));

describe('App Stability & Rapid Interactions Stress Test', () => {
  beforeEach(() => {
    document.body.style.overflow = '';
  });

  it('handles 50+ rapid item interactions without throwing errors or crashing', async () => {
    // Render the complete application
    const { container } = render(<App />);
    expect(container).toBeDefined();

    // 1. Rapidly toggle reduced motion 10 times
    const motionToggle = screen.getByTitle(/reduce 3d motion|enable 3d animations/i);
    for (let i = 0; i < 10; i++) {
      act(() => {
        fireEvent.click(motionToggle);
      });
    }

    // 2. Rapidly open and close mobile hamburger menu 10 times
    const hamburgerBtn = screen.getByLabelText(/open navigation menu|close navigation menu/i);
    for (let i = 0; i < 10; i++) {
      act(() => {
        fireEvent.click(hamburgerBtn);
      });
    }

    // 3. Rapidly open and close Case Study modals for each case study
    const inspectButtons = screen.getAllByRole('button', { name: /inspect drawer/i });
    for (const btn of inspectButtons) {
      act(() => {
        fireEvent.click(btn);
      });
      // Close via close button or escape
      const closeBtn = screen.getByLabelText('Close modal');
      act(() => {
        fireEvent.click(closeBtn);
      });
    }

    // 4. Rapidly open and close Press Modal 5 times
    const trophyInspectBtn = screen.getByRole('button', { name: /inspect trophy proof/i });
    for (let i = 0; i < 5; i++) {
      act(() => {
        fireEvent.click(trophyInspectBtn);
      });
      const closeBtn = screen.getByLabelText('Close modal');
      act(() => {
        fireEvent.click(closeBtn);
      });
    }

    // 5. Rapidly cycle through credential category filters 12 times
    const cloudFilter = screen.getByRole('button', { name: /cloud & ai badges/i });
    const pmFilter = screen.getByRole('button', { name: /product & ba/i });
    const academicFilter = screen.getByRole('button', { name: /academic & global wins/i });
    const allFilter = screen.getByRole('button', { name: /all credentials/i });

    for (let i = 0; i < 3; i++) {
      act(() => {
        fireEvent.click(cloudFilter);
        fireEvent.click(pmFilter);
        fireEvent.click(academicFilter);
        fireEvent.click(allFilter);
      });
    }

    // 6. Rapidly toggle press citation accordions 10 times
    const accordionTriggers = screen.getAllByRole('button', { name: /the star|the star online|hilti/i });
    if (accordionTriggers.length > 0) {
      for (let i = 0; i < 10; i++) {
        act(() => {
          fireEvent.click(accordionTriggers[0]);
        });
      }
    }

    // Confirm that the application is fully intact and healthy after 50+ actions
    expect(screen.getByText(/Architect of Enterprise Intelligence/i)).toBeDefined();
    expect(screen.getByText('Hireti (Team Sweetzerland)')).toBeDefined();
    expect(screen.getByText(/Initiate Collaboration/i)).toBeDefined();
  });
});
