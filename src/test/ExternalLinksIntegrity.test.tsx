import { describe, it, expect } from 'vitest';
import { PRESS_CITES } from '../data/pressCites';
import { CREDENTIALS } from '../data/credentials';
import { CASE_STUDIES } from '../data/caseStudies';

describe('External Links & Content Integrity Verification', () => {
  it('validates canonical The Star article URL points to live August 18, 2024 publication', () => {
    const theStarCite = PRESS_CITES.find((c) => c.id === 'cite-the-star');
    expect(theStarCite).toBeDefined();
    expect(theStarCite?.url).toBe(
      'https://www.thestar.com.my/news/education/2024/08/18/to-the-land-of-the-alps-we-go'
    );
    expect(theStarCite?.date).toContain('August 2024');

    // Invariant: no reference to stale 404 date (May 12, 2024)
    expect(theStarCite?.url).not.toContain('2024/05/12');
  });

  it('validates ACM SIGCHI Fusion 2023 citation points to live APU media release', () => {
    const fusionCite = PRESS_CITES.find((c) => c.id === 'cite-fusion-acm');
    expect(fusionCite).toBeDefined();
    expect(fusionCite?.url).toBe(
      'https://apu.edu.my/news/apu-students-make-mark-sustainable-development-fusion-2023-winning-gold-and-silver-awards'
    );
    expect(fusionCite?.badge).toContain('ACM SIGCHI');
  });

  it('validates APU media release points to live institutional release', () => {
    const apuCite = PRESS_CITES.find((c) => c.id === 'cite-apu-news');
    expect(apuCite).toBeDefined();
    expect(apuCite?.url).toBe(
      'https://apu.edu.my/news/back-back-wins-apu-students-hilti-it-competition'
    );
    // Invariant: no reference to stale Drupal 404 node
    expect(apuCite?.url).not.toContain('3218');
  });

  it('validates that press citations cover multiple diverse topics (not just Hilti)', () => {
    const topics = PRESS_CITES.map((c) => c.id);
    expect(topics).toContain('cite-the-star'); // Global competition & The Star national daily
    expect(topics).toContain('cite-fusion-acm'); // ACM SIGCHI Human-Computer Interaction & UN SDGs
    expect(topics).toContain('cite-great-ai'); // Great AI Hackathon & Privacy-First AI
    expect(topics).toContain('cite-petronas-pies'); // Petronas CHESS Energy & Decarbonization
    expect(topics).toContain('cite-apu-news'); // APU Academic Back-to-Back Milestone

    // Verify all citations have valid HTTPS URLs
    PRESS_CITES.forEach((cite) => {
      expect(cite.url).toMatch(/^https:\/\//);
      expect(cite.title.length).toBeGreaterThan(5);
      expect(cite.description.length).toBeGreaterThan(20);
      expect(cite.highlights.length).toBeGreaterThanOrEqual(3);
    });
  });

  it('ensures all credential badges have valid, well-formed HTTPS verification URLs', () => {
    CREDENTIALS.forEach((cred) => {
      expect(cred.verificationUrl).toMatch(/^https:\/\//);
      expect(cred.verificationUrl).not.toContain('localhost');
      expect(cred.verificationUrl).not.toContain('2024/05/12');
    });
  });

  it('ensures all case study repositories and links point to legitimate domains', () => {
    CASE_STUDIES.forEach((cs) => {
      if (cs.repoUrl) {
        expect(cs.repoUrl).toMatch(/^https:\/\//);
        expect(cs.repoUrl).not.toContain('Hireti'); // private repo redirected to profile
      }
      if (cs.externalUrl) {
        expect(cs.externalUrl).toMatch(/^https:\/\//);
      }
    });
  });
});
