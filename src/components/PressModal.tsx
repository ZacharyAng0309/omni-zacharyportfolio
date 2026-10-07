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
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Award className="w-6 h-6 text-rose-400 flex-shrink-0" />
            <div>
              <div className="font-bold text-white text-sm">Hilti IT Competition 2024 Global 1st Place</div>
              <div className="text-xs text-rose-300 font-mono">Team Sweetzerland (Team Lead: Zachary Ang)</div>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
            OFFICIAL RECORD
          </span>
        </div>

        {/* Newspaper Article Transcript */}
        <div className="bg-slate-950/60 p-5 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono pb-2 border-b border-slate-800">
            <span className="flex items-center gap-1.5">
              <Newspaper className="w-3.5 h-3.5 text-amber-400" />
              The Star (StarEdu Edition)
            </span>
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              18 August 2024
            </span>
          </div>

          <h4 className="text-base font-bold text-white">
            "To the Land of the Alps, we go!"
          </h4>

          <p className="text-xs text-slate-300 leading-relaxed">
            Team Sweetzerland from Asia Pacific University of Technology & Innovation (APU), led by Zachary Ang, was crowned global champion at the 13th Hilti IT Competition. Competing against 53 international universities from around the world, the Malaysian team pitched their solution "Hireti"—a cutting-edge AI platform engineered to revolutionize sustainable talent acquisition and corporate green skill gap resolution.
          </p>

          <p className="text-xs text-slate-300 leading-relaxed">
            As global grand champions, the team earned an all-expenses-paid expedition to Hilti Corporation's global headquarters in Schaan, Liechtenstein, along with an alpine journey across Lucerne and Mount Pilatus in Switzerland.
          </p>
        </div>

        {/* Expedition Timeline */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
            <div className="flex items-center gap-1.5 text-cyan-400 font-mono font-semibold mb-1">
              <MapPin className="w-3.5 h-3.5" />
              Hilti HQ, Schaan, Liechtenstein
            </div>
            <div className="text-slate-300">
              Executive presentation to Hilti CIO and Corporate IT Leadership Council.
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
            <div className="flex items-center gap-1.5 text-amber-400 font-mono font-semibold mb-1">
              <MapPin className="w-3.5 h-3.5" />
              Mount Pilatus & Lucerne, Switzerland
            </div>
            <div className="text-slate-300">
              Alpine expedition and high-altitude summit excursion (November 2024).
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-slate-800 flex justify-end gap-3">
          <a
            href="https://www.thestar.com.my/news/education/2024/08/18/to-the-land-of-the-alps-we-go"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-200 hover:text-white hover:bg-slate-700 transition-colors border border-slate-700"
          >
            <span>View Full The Star Article</span>
            <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
          </a>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-500 text-white hover:bg-rose-600 transition-colors cursor-pointer font-bold"
          >
            Close
          </button>
        </div>
      </div>
    </ModalInspectionDrawer>
  );
};
