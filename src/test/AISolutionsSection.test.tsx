import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AISolutionsSection } from '../components/AISolutionsSection';
import { CASE_STUDIES } from '../data/caseStudies';

describe('AISolutionsSection Component', () => {
  it('renders all 4 flagship case studies and category tags', () => {
    render(<AISolutionsSection onSelectCaseStudy={vi.fn()} />);

    expect(screen.getByText(/Chapter 02 • AI Solutions & Products/i)).toBeDefined();
    expect(screen.getByText('Hireti (Team Sweetzerland)')).toBeDefined();
    expect(screen.getByText('ChronoAI — Privacy-First AI Work Tracker')).toBeDefined();
    expect(screen.getByText('Digital Wallet Super-App Portfolio SDLC')).toBeDefined();
    expect(screen.getByText('Petronas PIES — Upstream Energy AI & Decarbonization System')).toBeDefined();
  });

  it('triggers onSelectCaseStudy with exact case study object on inspect click', () => {
    const handleSelect = vi.fn();
    render(<AISolutionsSection onSelectCaseStudy={handleSelect} />);

    const inspectButtons = screen.getAllByRole('button', { name: /inspect drawer/i });
    expect(inspectButtons.length).toBe(4);

    fireEvent.click(inspectButtons[0]);
    expect(handleSelect).toHaveBeenCalledWith(CASE_STUDIES[0]);

    fireEvent.click(inspectButtons[1]);
    expect(handleSelect).toHaveBeenCalledWith(CASE_STUDIES[1]);
  });

  it('handles rapid repeated accordion toggle clicks without crashing', () => {
    render(<AISolutionsSection onSelectCaseStudy={vi.fn()} />);

    const hiretiHeading = screen.getByText('Hireti (Team Sweetzerland)');
    const cardTrigger = hiretiHeading.closest('button');
    expect(cardTrigger).not.toBeNull();

    // Toggle 10 times rapidly
    for (let i = 0; i < 10; i++) {
      fireEvent.click(cardTrigger!);
    }
  });
});
