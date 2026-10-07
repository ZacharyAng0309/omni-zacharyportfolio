import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HeroSection } from '../components/HeroSection';

describe('HeroSection Component', () => {
  it('renders display typography and executive narrative', () => {
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    expect(screen.getByText(/Architect of Enterprise Intelligence/i)).toBeDefined();
    expect(screen.getByText(/Ang Zi Yang \(Zachary\)/i)).toBeDefined();
  });

  it('renders all 4 benchmark bento telemetry metrics', () => {
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    expect(screen.getByText('1st / 53')).toBeDefined();
    expect(screen.getByText('14 Quests')).toBeDefined();
    expect(screen.getByText('3.89 CGPA')).toBeDefined();
    expect(screen.getByText('500+')).toBeDefined();
  });

  it('triggers onExploreClick and onCaseStudiesClick when CTA buttons are clicked', () => {
    const onExplore = vi.fn();
    const onCaseStudies = vi.fn();

    render(<HeroSection onExploreClick={onExplore} onCaseStudiesClick={onCaseStudies} />);

    const exploreBtn = screen.getByRole('button', { name: /explore the journey/i });
    const inspectBtn = screen.getByRole('button', { name: /inspect architecture/i });

    fireEvent.click(exploreBtn);
    expect(onExplore).toHaveBeenCalledTimes(1);

    fireEvent.click(inspectBtn);
    expect(onCaseStudies).toHaveBeenCalledTimes(1);
  });
});
