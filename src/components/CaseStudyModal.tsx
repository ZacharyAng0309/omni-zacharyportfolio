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
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center gap-2.5">
            <Award className="w-5 h-5 flex-shrink-0 text-rose-400" />
            <span className="font-semibold text-xs">{caseStudy.featuredAward}</span>
          </div>
        )}

        {/* Problem Statement */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-400" />
            Problem Space & Discovery
          </h4>
          <p className="text-slate-300 leading-relaxed bg-slate-950/50 p-4 rounded-xl border border-slate-800">
            {caseStudy.problemStatement}
          </p>
        </div>

        {/* Solution Architecture */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            System Design & Architectural Invariants
          </h4>
          <div className="space-y-2">
            {caseStudy.solutionArchitecture.map((arch, idx) => (
              <div key={idx} className="flex items-start gap-2.5 bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                <span className="text-xs text-slate-200 leading-relaxed">{arch}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quantified Impact Metrics */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            Measured Business & Engineering Impact
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {caseStudy.impactMetrics.map((metric, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-xs text-slate-200">
                • {metric}
              </div>
            ))}
          </div>
        </div>

        {/* Tech Stack */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2">
            Technology Stack
          </h4>
          <div className="flex flex-wrap gap-2">
            {caseStudy.techStack.map((tech, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-md text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-slate-800 flex justify-end gap-3">
          {caseStudy.repoUrl && (
            <a
              href={caseStudy.repoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-200 hover:text-white hover:bg-slate-700 transition-colors border border-slate-700"
            >
              <span>Explore GitHub Code</span>
              <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
            </a>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-colors cursor-pointer font-bold"
          >
            Done
          </button>
        </div>
      </div>
    </ModalInspectionDrawer>
  );
};
