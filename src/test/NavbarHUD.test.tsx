import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NavbarHUD } from '../components/NavbarHUD';

describe('NavbarHUD Component', () => {
  beforeEach(() => {
    document.body.style.overflow = '';
  });

  it('renders brand monogram and navigation items', () => {
    render(
      <NavbarHUD
        activeSection="hero"
        isReducedMotion={false}
        onToggleReducedMotion={vi.fn()}
      />
    );

    expect(screen.getByText('Zachary Ang')).toBeDefined();
    expect(screen.getByText('Overview')).toBeDefined();
    expect(screen.getByText('The Summit')).toBeDefined();
    expect(screen.getByText('AI Architecture')).toBeDefined();
    expect(screen.getByText('Credentials')).toBeDefined();
    expect(screen.getByText('Specs')).toBeDefined();
    expect(screen.getByText('Connect')).toBeDefined();
  });

  it('contains desktop "Get in Touch" link routed to ziyang.ang02@gmail.com', () => {
    render(
      <NavbarHUD
        activeSection="hero"
        isReducedMotion={false}
        onToggleReducedMotion={vi.fn()}
      />
    );

    const getInTouchLink = screen.getByRole('link', { name: /get in touch/i });
    expect(getInTouchLink).toBeDefined();
    expect(getInTouchLink.getAttribute('href')).toContain('mailto:ziyang.ang02@gmail.com');
  });

  it('triggers onToggleReducedMotion on motion button click', () => {
    const handleToggle = vi.fn();
    render(
      <NavbarHUD
        activeSection="hero"
        isReducedMotion={false}
        onToggleReducedMotion={handleToggle}
      />
    );

    const toggleBtn = screen.getByTitle('Reduce 3D Motion');
    fireEvent.click(toggleBtn);
    expect(handleToggle).toHaveBeenCalledTimes(1);
  });

  it('expands mobile menu with backdrop scrim, locks scroll, and renders mobile contact email', () => {
    render(
      <NavbarHUD
        activeSection="hero"
        isReducedMotion={false}
        onToggleReducedMotion={vi.fn()}
      />
    );

    // Initial state: backdrop scrim does not exist
    expect(screen.queryByTestId('mobile-menu-backdrop')).toBeNull();

    // Click hamburger button to open mobile menu
    const menuBtn = screen.getByLabelText('Open Navigation Menu');
    fireEvent.click(menuBtn);

    // Backdrop scrim must be rendered
    const backdrop = screen.getByTestId('mobile-menu-backdrop');
    expect(backdrop).toBeDefined();

    // Body scroll must be locked to prevent collapsing/bleeding through body content
    expect(document.body.style.overflow).toBe('hidden');

    // Drawer dialog must be visible
    const drawer = screen.getByRole('dialog', { name: 'Mobile Navigation' });
    expect(drawer).toBeDefined();

    // Mobile email link must be routed to ziyang.ang02@gmail.com
    const mobileEmailLink = screen.getByText('Get in Touch (Email)').closest('a');
    expect(mobileEmailLink).not.toBeNull();
    expect(mobileEmailLink?.getAttribute('href')).toContain('mailto:ziyang.ang02@gmail.com');

    // Clicking backdrop must close the drawer and restore scroll
    fireEvent.click(backdrop);
    expect(screen.queryByTestId('mobile-menu-backdrop')).toBeNull();
    expect(document.body.style.overflow).toBe('');
  });

  it('closes mobile menu on Escape key press and restores body scroll', () => {
    render(
      <NavbarHUD
        activeSection="hero"
        isReducedMotion={false}
        onToggleReducedMotion={vi.fn()}
      />
    );

    const menuBtn = screen.getByLabelText('Open Navigation Menu');
    fireEvent.click(menuBtn);
    expect(document.body.style.overflow).toBe('hidden');

    // Press Escape
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByTestId('mobile-menu-backdrop')).toBeNull();
    expect(document.body.style.overflow).toBe('');
  });

  it('closes mobile menu and scrolls to section when nav item is tapped', () => {
    const scrollMock = vi.fn();
    const heroEl = document.createElement('div');
    heroEl.id = 'summit';
    heroEl.scrollIntoView = scrollMock;
    document.body.appendChild(heroEl);

    render(
      <NavbarHUD
        activeSection="hero"
        isReducedMotion={false}
        onToggleReducedMotion={vi.fn()}
      />
    );

    // Open mobile menu
    fireEvent.click(screen.getByLabelText('Open Navigation Menu'));
    expect(screen.getByTestId('mobile-menu-backdrop')).toBeDefined();

    // Click "The Summit" inside the drawer
    const drawer = screen.getByRole('dialog', { name: 'Mobile Navigation' });
    const allButtons = drawer.querySelectorAll('button');
    const summitItem = Array.from(allButtons).find((b) => b.textContent?.includes('The Summit'));
    expect(summitItem).toBeDefined();
    fireEvent.click(summitItem!);

    expect(scrollMock).toHaveBeenCalled();
    expect(screen.queryByTestId('mobile-menu-backdrop')).toBeNull();
    expect(document.body.style.overflow).toBe('');

    document.body.removeChild(heroEl);
  });
});
