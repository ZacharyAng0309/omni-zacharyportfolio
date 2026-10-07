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

  it('validates APU media release points to live institutional release', () => {
    const apuCite = PRESS_CITES.find((c) => c.id === 'cite-apu-news');
    expect(apuCite).toBeDefined();
    expect(apuCite?.url).toBe(
      'https://apu.edu.my/news/back-back-wins-apu-students-hilti-it-competition'
    );
    // Invariant: no reference to stale Drupal 404 node
    expect(apuCite?.url).not.toContain('3218');
  });

  it('validates Hilti Competition citation points to active official portal', () => {
    const hiltiCite = PRESS_CITES.find((c) => c.id === 'cite-hilti-itc');
    expect(hiltiCite).toBeDefined();
    expect(hiltiCite?.url).toBe('https://itcompetition.hilti.group/');
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
