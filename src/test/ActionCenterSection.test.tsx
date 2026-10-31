import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { ActionCenterSection } from '../components/ActionCenterSection';

describe('ActionCenterSection Component', () => {
  it('renders direct executive coordinates with ziyang.ang02@gmail.com', () => {
    render(<ActionCenterSection />);

    const emailLinks = screen.getAllByRole('link', { name: /ziyang\.ang02@gmail\.com/i });
    expect(emailLinks.length).toBeGreaterThan(0);
    expect(emailLinks[0].getAttribute('href')).toBe('mailto:ziyang.ang02@gmail.com');
  });

  it('renders "Get in Touch via Email" link with pre-populated inquiry subject', () => {
    render(<ActionCenterSection />);

    const getInTouchLink = screen.getByRole('link', { name: /get in touch via email/i });
    expect(getInTouchLink).toBeDefined();
    expect(getInTouchLink.getAttribute('href')).toContain('mailto:ziyang.ang02@gmail.com');
  });

  it('renders "Request Executive CV" link with pre-populated CV request subject', () => {
    render(<ActionCenterSection />);

    const cvLink = screen.getByRole('link', { name: /request executive cv/i });
    expect(cvLink).toBeDefined();
    expect(cvLink.getAttribute('href')).toContain('mailto:ziyang.ang02@gmail.com');
    expect(cvLink.getAttribute('href')).toContain('Executive%20CV');
  });

  it('verifies LinkedIn and GitHub external social links', () => {
    render(<ActionCenterSection />);

    const linkedInLink = screen.getByTitle('Connect on LinkedIn');
    expect(linkedInLink.getAttribute('href')).toBe('https://www.linkedin.com/in/zacharyangziyang');

    const githubLink = screen.getByTitle('Explore GitHub');
    expect(githubLink.getAttribute('href')).toBe('https://github.com/ZacharyAng0309');
  });

  it('submits dispatch form and shows transmission confirmation', () => {
    render(<ActionCenterSection />);

    const nameInput = screen.getByPlaceholderText(/Elena Rostova/i);
    const emailInput = screen.getByPlaceholderText(/elena\.rostova@hilti\.com/i);
    const messageInput = screen.getByPlaceholderText(/Outline key objectives/i);
    const submitBtn = screen.getByRole('button', { name: /transmit message/i });

    fireEvent.change(nameInput, { target: { value: 'Elena Rostova' } });
    fireEvent.change(emailInput, { target: { value: 'elena.rostova@hilti.com' } });
    fireEvent.change(messageInput, { target: { value: 'Inquiry regarding enterprise AI architecture.' } });

    fireEvent.click(submitBtn);

    expect(screen.getByText(/Message Transmitted Successfully/i)).toBeDefined();
  });

  it('handles copying email to clipboard and renders < 24H SLA badge and concentric beacon', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    render(<ActionCenterSection />);

    // Concentric 2D radar pulse beacon & SLA badge
    expect(screen.getByText(/< 24H SLA/i)).toBeDefined();
    expect(screen.getByText(/Response Protocol Active/i)).toBeDefined();
    expect(screen.getByLabelText(/Concentric Radar Beacon/i)).toBeDefined();

    // Copy Email button
    const copyBtn = screen.getByRole('button', { name: /copy email address/i });
    expect(copyBtn).toBeDefined();

    fireEvent.click(copyBtn);
    expect(writeTextMock).toHaveBeenCalledWith('ziyang.ang02@gmail.com');
    await waitFor(() => {
      expect(screen.getByText(/Copied!/i)).toBeDefined();
    });
  });

  it('gracefully falls back to document.execCommand when navigator.clipboard rejects or is unavailable', async () => {
    (document as any).execCommand = vi.fn().mockReturnValue(true);
    const execCommandSpy = vi.spyOn(document, 'execCommand');
    // Simulate clipboard rejection (e.g. cross-origin iframe or permission denied)
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockRejectedValue(new Error('Permission denied')),
      },
    });

    render(<ActionCenterSection />);

    const copyBtn = screen.getByRole('button', { name: /copy email address/i });
    fireEvent.click(copyBtn);

    await waitFor(() => {
      expect(execCommandSpy).toHaveBeenCalledWith('copy');
      expect(screen.getByText(/Copied!/i)).toBeDefined();
    });

    execCommandSpy.mockRestore();
    delete (document as any).execCommand;
  });

  it('resets copied state timer properly on repeated rapid clicks', async () => {
    vi.useFakeTimers();
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    render(<ActionCenterSection />);
    const copyBtn = screen.getByRole('button', { name: /copy email address/i });

    // First click
    fireEvent.click(copyBtn);
    expect(screen.getByText(/Copied!/i)).toBeDefined();

    // Advance 2 seconds (less than 2.5s)
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByText(/Copied!/i)).toBeDefined();

    // Second click: resets timer for another full 2.5s
    fireEvent.click(copyBtn);
    expect(screen.getByText(/Copied!/i)).toBeDefined();

    // Advance 1 second (total 3s from start, but only 1s from second click)
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByText(/Copied!/i)).toBeDefined();

    // Advance remaining 1.6s (now 2.6s since second click)
    act(() => {
      vi.advanceTimersByTime(1600);
    });
    expect(screen.queryByText(/Copied!/i)).toBeNull();

    vi.useRealTimers();
  });
});
