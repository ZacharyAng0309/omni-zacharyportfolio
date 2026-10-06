import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalInspectionDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

export const ModalInspectionDrawer: React.FC<ModalInspectionDrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/85 backdrop-blur-xl animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl max-h-[90vh] overflow-y-auto apple-glass p-6 sm:p-10 rounded-3xl border border-white/10 shadow-2xl relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-4 mb-6 border-b border-white/10">
          <div>
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-1 tracking-tight">{title}</h3>
            {subtitle && <p className="text-xs sm:text-sm font-mono text-cyan-400">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-2 rounded-full text-neutral-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="text-neutral-200">{children}</div>
      </div>
    </div>
  );
};
