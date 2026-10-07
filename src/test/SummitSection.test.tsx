import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SummitSection } from '../components/SummitSection';

describe('SummitSection Component', () => {
  it('renders championship details and trophy inspection CTA', () => {
    const handleInspect = vi.fn();
    render(<SummitSection onInspectPressModal={handleInspect} />);

    expect(screen.getByText(/Chapter 01 • The Summit/i)).toBeDefined();
    expect(screen.getByText(/1st Place Worldwide • Team Sweetzerland/i)).toBeDefined();

    const inspectBtn = screen.getByRole('button', { name: /inspect trophy proof/i });
    fireEvent.click(inspectBtn);
    expect(handleInspect).toHaveBeenCalledTimes(1);
  });

  it('renders external canonical link to The Star article', () => {
    render(<SummitSection onInspectPressModal={vi.fn()} />);

    const theStarLink = screen.getByRole('link', { name: /read article on the star/i });
    expect(theStarLink).toBeDefined();
    expect(theStarLink.getAttribute('href')).toBe(
      'https://www.thestar.com.my/news/education/2024/05/12/to-the-land-of-the-alps-we-go'
    );
  });

  it('allows repeated accordion expansion and collapse without errors', () => {
    render(<SummitSection onInspectPressModal={vi.fn()} />);

    // Find the first accordion button
    const accordionTriggers = screen.getAllByRole('button', { name: /the star|the star online|hilti/i });
    expect(accordionTriggers.length).toBeGreaterThan(0);

    const firstTrigger = accordionTriggers[0];

    // Click to expand
    fireEvent.click(firstTrigger);
    expect(screen.getByText(/open canonical source/i)).toBeDefined();

    // Click to collapse
    fireEvent.click(firstTrigger);
    expect(screen.queryByText(/open canonical source/i)).toBeNull();

    // Rapid repeated clicks (stress testing toggles)
    for (let i = 0; i < 6; i++) {
      fireEvent.click(firstTrigger);
    }
  });
});
