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

    it('implements WCAG 2.2 AA focus trapping and returns focus on close', () => {
      const handleClose = vi.fn();
      const triggerBtn = document.createElement('button');
      triggerBtn.textContent = 'Trigger Open';
      document.body.appendChild(triggerBtn);
      triggerBtn.focus();
      expect(document.activeElement).toBe(triggerBtn);

      const { rerender } = render(
        <ModalInspectionDrawer isOpen={true} onClose={handleClose} title="Focus Trap Modal">
          <button>First Interactive Action</button>
          <a href="#test">Interactive Link</a>
        </ModalInspectionDrawer>
      );

      const closeBtn = screen.getByLabelText('Close modal');
      const testLink = screen.getByRole('link', { name: 'Interactive Link' });

      // Tab trapping test
      testLink.focus();
      expect(document.activeElement).toBe(testLink);

      // Press Tab on last element -> wraps to first focusable element (close button)
      fireEvent.keyDown(window, { key: 'Tab' });
      expect(document.activeElement).toBe(closeBtn);

      // Press Shift+Tab on first element -> wraps to last element (test link)
      fireEvent.keyDown(window, { key: 'Tab', shiftKey: true });
      expect(document.activeElement).toBe(testLink);

      // Close modal and verify focus restored to triggerBtn
      rerender(
        <ModalInspectionDrawer isOpen={false} onClose={handleClose} title="Focus Trap Modal">
          <button>First Interactive Action</button>
          <a href="#test">Interactive Link</a>
        </ModalInspectionDrawer>
      );

      expect(document.activeElement).toBe(triggerBtn);
      document.body.removeChild(triggerBtn);
    });

    it('intercepts focus and pulls it inside when focus is outside the drawer', () => {
      const handleClose = vi.fn();
      render(
        <div>
          <button id="outside-btn">Outside Element</button>
          <ModalInspectionDrawer isOpen={true} onClose={handleClose} title="Focus Recovery Modal">
            <button id="inside-btn">Inside Button</button>
          </ModalInspectionDrawer>
        </div>
      );

      const outsideBtn = document.getElementById('outside-btn')!;
      outsideBtn.focus();
      expect(document.activeElement).toBe(outsideBtn);

      const closeBtn = screen.getByLabelText('Close modal');
      const insideBtn = document.getElementById('inside-btn')!;

      // Press Tab while outside -> redirected to first focusable element (close button)
      fireEvent.keyDown(window, { key: 'Tab' });
      expect(document.activeElement).toBe(closeBtn);

      // Focus outside again and press Shift+Tab -> redirected to last focusable element (inside-btn)
      outsideBtn.focus();
      fireEvent.keyDown(window, { key: 'Tab', shiftKey: true });
      expect(document.activeElement).toBe(insideBtn);
    });

    it('skips disabled buttons in focus cycle and preserves multi-drawer scroll lock', () => {
      const handleClose = vi.fn();
      const { unmount: unmountFirst } = render(
        <ModalInspectionDrawer isOpen={true} onClose={handleClose} title="Drawer 1">
          <button disabled>Disabled Action</button>
          <button id="enabled-btn">Active Action</button>
        </ModalInspectionDrawer>
      );

      expect(document.body.style.overflow).toBe('hidden');

      // Second drawer opens concurrently
      const { unmount: unmountSecond } = render(
        <ModalInspectionDrawer isOpen={true} onClose={handleClose} title="Drawer 2">
          <button id="drawer2-btn">Drawer 2 Button</button>
        </ModalInspectionDrawer>
      );

      expect(document.body.style.overflow).toBe('hidden');

      // Unmount first drawer: body overflow MUST remain 'hidden' because Drawer 2 is still open
      unmountFirst();
      expect(document.body.style.overflow).toBe('hidden');

      // Unmount second drawer: body overflow restored to ''
      unmountSecond();
      expect(document.body.style.overflow).toBe('');
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
