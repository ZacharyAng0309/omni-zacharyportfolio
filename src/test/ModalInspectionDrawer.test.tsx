import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModalInspectionDrawer } from '../components/ModalInspectionDrawer';
import { CaseStudyModal } from '../components/CaseStudyModal';
import { PressModal } from '../components/PressModal';
import { CASE_STUDIES } from '../data/caseStudies';

describe('Modal Components', () => {
  beforeEach(() => {
    document.body.style.overflow = '';
  });

  describe('ModalInspectionDrawer', () => {
    it('does not render when isOpen is false', () => {
      render(
        <ModalInspectionDrawer isOpen={false} onClose={vi.fn()} title="Test Modal">
          <p>Hidden Content</p>
        </ModalInspectionDrawer>
      );
      expect(screen.queryByText('Test Modal')).toBeNull();
    });

    it('renders and locks body scroll when isOpen is true, then closes on close button', () => {
      const handleClose = vi.fn();
      render(
        <ModalInspectionDrawer isOpen={true} onClose={handleClose} title="Test Modal">
          <p>Visible Content</p>
        </ModalInspectionDrawer>
      );

      expect(screen.getByText('Test Modal')).toBeDefined();
      expect(screen.getByText('Visible Content')).toBeDefined();
      expect(document.body.style.overflow).toBe('hidden');

      const closeBtn = screen.getByLabelText('Close modal');
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('closes on Escape key and closes on backdrop scrim click', () => {
      const handleClose = vi.fn();
      render(
        <ModalInspectionDrawer isOpen={true} onClose={handleClose} title="Test Modal">
          <p>Visible Content</p>
        </ModalInspectionDrawer>
      );

      // Press Escape
      fireEvent.keyDown(window, { key: 'Escape' });
      expect(handleClose).toHaveBeenCalledTimes(1);

      // Click outer backdrop
      const dialog = screen.getByRole('dialog');
      fireEvent.click(dialog);
      expect(handleClose).toHaveBeenCalledTimes(2);
    });
  });

  describe('CaseStudyModal', () => {
    it('renders full case study architecture invariants and impact metrics', () => {
      const handleClose = vi.fn();
      render(<CaseStudyModal caseStudy={CASE_STUDIES[0]} onClose={handleClose} />);

      expect(screen.getByText(CASE_STUDIES[0].title)).toBeDefined();
      expect(screen.getByText(/Problem Space & Discovery/i)).toBeDefined();
      expect(screen.getByText(/System Design & Architectural Invariants/i)).toBeDefined();

      const closeBtn = screen.getByLabelText('Close modal');
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('PressModal', () => {
    it('renders national press feature transcript and source article link', () => {
      const handleClose = vi.fn();
      render(<PressModal isOpen={true} onClose={handleClose} />);

      expect(screen.getByText(/National Press & Global Championship Verification/i)).toBeDefined();
      expect(screen.getByText(/"To the Land of the Alps, we go!"/i)).toBeDefined();

      const articleLink = screen.getByRole('link', { name: /view full the star article/i });
      expect(articleLink.getAttribute('href')).toContain('thestar.com.my');

      const closeBtn = screen.getByRole('button', { name: /^close$/i });
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });
});
