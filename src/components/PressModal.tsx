import React from 'react';
import { ModalInspectionDrawer } from './ModalInspectionDrawer';
import { Newspaper, Award, MapPin, Calendar, ExternalLink } from 'lucide-react';

interface PressModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PressModal: React.FC<PressModalProps> = ({ isOpen, onClose }) => {
  return (
    <ModalInspectionDrawer
      isOpen={isOpen}
      onClose={onClose}
      title="National Press & Global Championship Verification"
      subtitle="The Star (StarEdu) • Front Page Feature • August 18, 2024"
    >
      <div className="space-y-6 text-sm">
        {/* Banner */}
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-400/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Award className="w-6 h-6 text-amber-400 flex-shrink-0" />
            <div>
              <div className="font-bold text-[#F4F0EA] text-sm">Hilti IT Competition 2024 Global 1st Place</div>
              <div className="text-xs text-amber-200/90 font-mono">Team Sweetzerland (Team Lead: Zachary Ang)</div>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/12 text-emerald-300 border border-emerald-500/25 font-bold">
            OFFICIAL RECORD
          </span>
        </div>

        {/* Newspaper Article Transcript */}
        <div className="bg-white/[0.03] p-5 rounded-2xl border border-white/10 space-y-3">
          <div className="flex items-center justify-between text-xs text-[#D6D0C4] font-mono pb-2 border-b border-white/10">
            <span className="flex items-center gap-1.5">
              <Newspaper className="w-3.5 h-3.5 text-amber-400" />
              The Star (StarEdu Edition)
            </span>
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              18 August 2024
            </span>
          </div>

          <h4 className="text-base font-bold text-[#F4F0EA]">
            "To the Land of the Alps, we go!"
          </h4>

          <p className="text-xs text-[#E6E0D6] leading-relaxed">
            Team Sweetzerland from Asia Pacific University of Technology &amp; Innovation (APU), led by Zachary Ang, was crowned global champion at the 13th Hilti IT Competition. Competing against 53 international universities from around the world, the Malaysian team pitched their solution "Hireti"—a cutting-edge AI platform engineered to revolutionize sustainable talent acquisition and corporate green skill gap resolution.
          </p>

          <p className="text-xs text-[#E6E0D6] leading-relaxed">
            As global grand champions, the team earned an all-expenses-paid expedition to Hilti Corporation's global headquarters in Schaan, Liechtenstein, along with an alpine journey across Lucerne and Mount Pilatus in Switzerland.
          </p>
        </div>

        {/* Expedition Timeline */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/10">
            <div className="flex items-center gap-1.5 text-[#c8a97e] font-mono font-semibold mb-1">
              <MapPin className="w-3.5 h-3.5" />
              Hilti HQ, Schaan, Liechtenstein
            </div>
            <div className="text-[#E6E0D6]">
              Executive presentation to Hilti CIO and Corporate IT Leadership Council.
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/10">
            <div className="flex items-center gap-1.5 text-amber-400 font-mono font-semibold mb-1">
              <MapPin className="w-3.5 h-3.5" />
              Mount Pilatus &amp; Lucerne, Switzerland
            </div>
            <div className="text-[#E6E0D6]">
              Alpine expedition and high-altitude summit excursion (November 2024).
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-white/10 flex justify-end gap-3">
          <a
            href="https://www.thestar.com.my/news/education/2024/08/18/to-the-land-of-the-alps-we-go"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold bg-white/[0.06] text-[#F4F0EA] hover:bg-white/[0.12] transition-colors border border-white/12"
          >
            <span>View Full The Star Article</span>
            <ExternalLink className="w-3.5 h-3.5 text-[#c8a97e]" />
          </a>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-full text-xs font-semibold bg-[#F4F0EA] text-[#14110f] hover:bg-white transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </ModalInspectionDrawer>
  );
};
