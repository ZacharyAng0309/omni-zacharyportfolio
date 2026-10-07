import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CredentialVaultSection } from '../components/CredentialVaultSection';
import { CREDENTIALS } from '../data/credentials';

describe('CredentialVaultSection Component', () => {
  it('renders all credentials on initial load', () => {
    render(<CredentialVaultSection />);

    expect(screen.getByText(/Chapter 03 • Credential Vault/i)).toBeDefined();
    expect(screen.getByText(`All Credentials (${CREDENTIALS.length})`)).toBeDefined();
  });

  it('filters credentials when category filter pills are clicked', () => {
    render(<CredentialVaultSection />);

    const cloudPill = screen.getByRole('button', { name: /cloud & ai badges/i });
    const pmPill = screen.getByRole('button', { name: /product & ba/i });
    const academicPill = screen.getByRole('button', { name: /academic & global wins/i });
    const allPill = screen.getByRole('button', { name: /all credentials/i });

    // Click Cloud filter
    fireEvent.click(cloudPill);
    const cloudHeadings = screen.getAllByRole('heading', { level: 3 });
    expect(cloudHeadings.length).toBeGreaterThan(0);

    // Click PM filter
    fireEvent.click(pmPill);
    const pmHeadings = screen.getAllByRole('heading', { level: 3 });
    expect(pmHeadings.length).toBeGreaterThan(0);

    // Click Academic filter
    fireEvent.click(academicPill);
    const academicHeadings = screen.getAllByRole('heading', { level: 3 });
    expect(academicHeadings.length).toBeGreaterThan(0);

    // Return to All
    fireEvent.click(allPill);
    expect(screen.getByText(`All Credentials (${CREDENTIALS.length})`)).toBeDefined();
  });

  it('verifies all credentials have valid verification links and toggles skill details', () => {
    render(<CredentialVaultSection />);

    // Check verification links
    const verifyLinks = screen.getAllByRole('link', { name: /verify/i });
    expect(verifyLinks.length).toBeGreaterThan(0);
    verifyLinks.forEach((link) => {
      expect(link.getAttribute('href')).toMatch(/^https?:\/\//);
    });

    // Toggle skill details
    const viewSkillsButtons = screen.getAllByRole('button', { name: /view skills/i });
    expect(viewSkillsButtons.length).toBeGreaterThan(0);

    const firstButton = viewSkillsButtons[0];
    fireEvent.click(firstButton);
    expect(screen.getByText(/hide details/i)).toBeDefined();

    fireEvent.click(firstButton);
    expect(screen.queryByText(/hide details/i)).toBeNull();
  });
});
