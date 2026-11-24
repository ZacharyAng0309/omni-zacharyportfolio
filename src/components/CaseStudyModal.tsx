import React from 'react';
import type { CaseStudy } from '../domain/contracts';
import { ModalInspectionDrawer } from './ModalInspectionDrawer';
import { CheckCircle2, Layers, Cpu, Award, ExternalLink } from 'lucide-react';

interface CaseStudyModalProps {
  caseStudy: CaseStudy | null;
  onClose: () => void;
}

export const CaseStudyModal: React.FC<CaseStudyModalProps> = ({ caseStudy, onClose }) => {
  if (!caseStudy) return null;

  return (
    <ModalInspectionDrawer
      isOpen={!!caseStudy}
      onClose={onClose}
      title={caseStudy.title}
      subtitle={`${caseStudy.category} • ${caseStudy.role}`}
    >
      <div className="space-y-6 text-sm">
        {/* Award Highlight */}
        {caseStudy.featuredAward && (
          <div
            className="p-3.5 rounded-2xl border flex items-center gap-2.5"
            style={{
              backgroundColor: `${caseStudy.accentColor}16`,
              borderColor: `${caseStudy.accentColor}4d`,
              color: '#F4F0EA',
            }}
          >
            <Award
              className="w-5 h-5 flex-shrink-0"
              style={{ color: caseStudy.accentColor }}
            />
            <span className="font-semibold text-xs">{caseStudy.featuredAward}</span>
          </div>
        )}

        {/* Problem Statement */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-[#D6D0C4] mb-2 flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: caseStudy.accentColor }}
            />
            Problem Space &amp; Discovery
          </h4>
          <p className="text-[#E6E0D6] leading-relaxed bg-white/[0.03] p-4 rounded-2xl border border-white/10">
            {caseStudy.problemStatement}
          </p>
        </div>

        {/* Solution Architecture */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-[#D6D0C4] mb-2 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[#c8a97e]" />
            System Design &amp; Architectural Invariants
          </h4>
          <div className="space-y-2">
            {caseStudy.solutionArchitecture.map((arch, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 bg-white/[0.03] p-3 rounded-xl border border-white/10"
              >
                <CheckCircle2 className="w-4 h-4 text-[#c8a97e] flex-shrink-0 mt-0.5" />
                <span className="text-xs text-[#E6E0D6] leading-relaxed">{arch}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quantified Impact Metrics */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-[#D6D0C4] mb-2 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            Measured Business &amp; Engineering Impact
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {caseStudy.impactMetrics.map((metric, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-emerald-500/8 border border-emerald-500/20 text-xs text-[#E6E0D6]"
              >
                • {metric}
              </div>
            ))}
          </div>
        </div>

        {/* Tech Stack */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-[#D6D0C4] mb-2">
            Technology Stack
          </h4>
          <div className="flex flex-wrap gap-2">
            {caseStudy.techStack.map((tech, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-md text-xs font-mono bg-white/[0.05] text-[#D6D0C4] border border-white/10"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-white/10 flex justify-end gap-3">
          {caseStudy.repoUrl && (
            <a
              href={caseStudy.repoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold bg-white/[0.06] text-[#F4F0EA] hover:bg-white/[0.12] transition-colors border border-white/12"
            >
              <span>Explore GitHub Code</span>
              <ExternalLink className="w-3.5 h-3.5 text-[#c8a97e]" />
            </a>
          )}
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-full text-xs font-semibold bg-[#F4F0EA] text-[#14110f] hover:bg-white transition-colors cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </ModalInspectionDrawer>
  );
};
