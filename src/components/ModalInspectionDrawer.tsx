import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

interface ModalInspectionDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

let activeDrawersCount = 0;

const lockBodyScroll = () => {
  activeDrawersCount++;
  document.body.style.overflow = 'hidden';
};

const unlockBodyScroll = () => {
  activeDrawersCount = Math.max(0, activeDrawersCount - 1);
  if (activeDrawersCount === 0) {
    document.body.style.overflow = '';
  }
};

const FOCUSABLE_SELECTOR = [
  'button:not([disabled])',
  '[href]:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"]):not([disabled])',
].join(', ');

export const ModalInspectionDrawer: React.FC<ModalInspectionDrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
}) => {
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement | null;
      lockBodyScroll();

      // Focus close button on open immediately (WCAG 2.2 AA) with fallback
      if (closeBtnRef.current) {
        closeBtnRef.current.focus();
      }
      const timer = setTimeout(() => {
        if (drawerRef.current && !drawerRef.current.contains(document.activeElement)) {
          closeBtnRef.current?.focus();
        }
      }, 30);

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onClose();
          return;
        }

        if (e.key === 'Tab') {
          if (!drawerRef.current) return;
          const focusable = drawerRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
          if (focusable.length === 0) {
            e.preventDefault();
            return;
          }

          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (!first || !last) return;

          // If focus is currently outside the drawer, redirect into the drawer
          if (!drawerRef.current.contains(document.activeElement)) {
            e.preventDefault();
            if (e.shiftKey) {
              last.focus();
            } else {
              first.focus();
            }
            return;
          }

          if (e.shiftKey) {
            if (document.activeElement === first) {
              e.preventDefault();
              last.focus();
            }
          } else {
            if (document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          }
        }
      };

      window.addEventListener('keydown', handleKeyDown);

      return () => {
        clearTimeout(timer);
        unlockBodyScroll();
        window.removeEventListener('keydown', handleKeyDown);
        if (
          previousFocusRef.current &&
          typeof previousFocusRef.current.focus === 'function' &&
          document.body.contains(previousFocusRef.current)
        ) {
          previousFocusRef.current.focus();
        }
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-50 flex justify-end bg-black/75 backdrop-blur-sm animate-fadeIn"
      onClick={onClose}
    >
      <div
        ref={drawerRef}
        className="fixed inset-y-0 right-0 w-full max-w-xl h-full bg-[#090d14]/95 border-l border-white/10 shadow-2xl backdrop-blur-2xl p-6 sm:p-8 flex flex-col z-50 animate-slideInRight"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Mobile Drag / Status Indicator Bar */}
        <div className="w-12 h-1 rounded-full bg-white/20 mx-auto mb-4 sm:hidden flex-shrink-0" />

        {/* Header */}
        <div className="flex items-start justify-between pb-4 mb-6 border-b border-white/10 flex-shrink-0">
          <div className="pr-4">
            <h3 className="text-lg sm:text-2xl font-bold text-white mb-1 tracking-tight leading-snug font-display">
              {title}
            </h3>
            {subtitle && <p className="text-xs sm:text-sm font-mono text-cyan-400">{subtitle}</p>}
          </div>
          <button
            ref={closeBtnRef}
            onClick={onClose}
            aria-label="Close modal"
            className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-full text-neutral-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer flex-shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto pr-1 text-neutral-200">{children}</div>
      </div>
    </div>
  );
};
