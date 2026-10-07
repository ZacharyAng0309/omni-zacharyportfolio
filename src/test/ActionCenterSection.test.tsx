import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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
});
