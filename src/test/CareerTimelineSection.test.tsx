import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CareerTimelineSection } from '../components/CareerTimelineSection';
import { TIMELINE_MILESTONES } from '../data/timeline';

describe('CareerTimelineSection Component', () => {
  it('renders milestones across career journey', () => {
    render(<CareerTimelineSection />);

    expect(screen.getByText(/Chapter 04 • Career Journey & Milestones/i)).toBeDefined();
    TIMELINE_MILESTONES.forEach((item) => {
      expect(screen.getByText(item.organization)).toBeDefined();
    });
  });

  it('allows expanding and collapsing milestone details repeatedly', () => {
    render(<CareerTimelineSection />);

    const firstItem = TIMELINE_MILESTONES[0];
    const roleHeading = screen.getByText(firstItem.role);
    const trigger = roleHeading.closest('button');
    expect(trigger).not.toBeNull();

    // Expand
    fireEvent.click(trigger!);
    expect(screen.getByText(/collapse/i)).toBeDefined();

    // Collapse
    fireEvent.click(trigger!);
    expect(screen.queryByText(/collapse/i)).toBeNull();

    // Rapid stress toggling
    for (let i = 0; i < 8; i++) {
      fireEvent.click(trigger!);
    }
  });
});
