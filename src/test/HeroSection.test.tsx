import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HeroSection } from '../components/HeroSection';

describe('HeroSection Component', () => {
  it('renders display typography and executive narrative', () => {
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    expect(screen.getByText(/Architect of Enterprise Intelligence/i)).toBeDefined();
    expect(screen.getByText(/Ang Zi Yang \(Zachary\)/i)).toBeDefined();
  });

  it('maintains a clean hero layout without cluttered telemetry benchmark chips', () => {
    render(<HeroSection onExploreClick={vi.fn()} onCaseStudiesClick={vi.fn()} />);

    expect(screen.queryByText('1st / 53')).toBeNull();
    expect(screen.queryByText('14 Quests')).toBeNull();
    expect(screen.queryByText('3.89 CGPA')).toBeNull();
    expect(screen.queryByText('500+')).toBeNull();
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
