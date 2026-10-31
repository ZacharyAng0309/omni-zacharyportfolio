import React, { useState } from 'react';
import { CREDENTIALS } from '../data/credentials';
import { ExternalLink, ChevronDown, Award, Cloud, BookOpen, ShieldCheck } from 'lucide-react';

export const CredentialVaultSection: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'cloud' | 'pm' | 'academic'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filteredCredentials = CREDENTIALS.filter((cred) => {
    if (filter === 'all') return true;
    if (filter === 'cloud') return cred.badgeType.includes('Cloud') || cred.issuer.includes('Google') || cred.issuer.includes('Huawei') || cred.issuer.includes('Microsoft');
    if (filter === 'pm') return cred.badgeType.includes('PM') || cred.badgeType.includes('Business') || cred.badgeType.includes('Hackathon');
    if (filter === 'academic') return cred.badgeType.includes('Academic') || cred.badgeType.includes('Championship');
    return true;
  });

  const dispatchBadgeSurge = (credentialId?: string) => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action: 'badge_surge', credentialId },
        })
      );
    }
  };

  const toggleExpand = (id: string) => {
    dispatchBadgeSurge(id);
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <section
      id="vault"
      aria-label="Verified Credentials & Honors"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 md:px-12 py-20 sm:py-24 relative z-10 max-w-7xl mx-auto w-full"
    >
      <div data-peek-hide className="w-full">
        {/* Editorial Chapter Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b border-white/[0.08]">
          <div className="space-y-3 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 font-mono text-xs uppercase tracking-wider border border-indigo-500/20 font-bold">
                Act 03 • The Crucible • Cloud Mastery &amp; GDSC Leadership
              </span>
              <span className="text-neutral-400 text-[11px] sm:text-xs font-mono">
                GDSC APU PODIUM • 14 GOOGLE CLOUD QUESTS • 7 VERTEX AI BADGES
              </span>
            </div>

            <h2 className="text-3xl sm:text-5xl md:text-6xl font-black tracking-tight text-white font-display">
              Verified Credentials &amp;{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-300">
                Cloud Mastery
              </span>
            </h2>

            <p className="text-neutral-300 text-sm sm:text-base leading-relaxed">
              Every milestone is backed by verifiable institutional credentials, global hackathon trophies, and official Google Cloud, Microsoft Azure, and Huawei skill certifications.
            </p>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 self-start md:self-end">
            <button
              onClick={() => {
                setFilter('all');
                dispatchBadgeSurge('filter-all');
              }}
              data-cursor="FILTER"
              className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                filter === 'all'
                  ? 'bg-cyan-400 text-black font-bold shadow-lg shadow-cyan-400/20'
                  : 'glass-acrylic text-neutral-300 hover:text-white'
              }`}
            >
              All Credentials ({CREDENTIALS.length})
            </button>
            <button
              onClick={() => {
                setFilter('cloud');
                dispatchBadgeSurge('filter-cloud');
              }}
              data-cursor="FILTER"
              className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                filter === 'cloud'
                  ? 'bg-cyan-400 text-black font-bold shadow-lg shadow-cyan-400/20'
                  : 'glass-acrylic text-neutral-300 hover:text-white'
              }`}
            >
              <Cloud className="w-3.5 h-3.5" />
              <span>Cloud &amp; AI Badges</span>
            </button>
            <button
              onClick={() => {
                setFilter('pm');
                dispatchBadgeSurge('filter-pm');
              }}
              data-cursor="FILTER"
              className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                filter === 'pm'
                  ? 'bg-cyan-400 text-black font-bold shadow-lg shadow-cyan-400/20'
                  : 'glass-acrylic text-neutral-300 hover:text-white'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Product &amp; BA</span>
            </button>
            <button
              onClick={() => {
                setFilter('academic');
                dispatchBadgeSurge('filter-academic');
              }}
              data-cursor="FILTER"
              className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                filter === 'academic'
                  ? 'bg-cyan-400 text-black font-bold shadow-lg shadow-cyan-400/20'
                  : 'glass-acrylic text-neutral-300 hover:text-white'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Academic &amp; Global Wins</span>
            </button>
          </div>
        </div>

        {/* 12-Column Editorial Bento Grid */}
        <div className="grid grid-cols-12 gap-5 sm:gap-6">
          {filteredCredentials.map((cred) => {
            const isExpanded = expandedId === cred.id;
            return (
              <div
                key={cred.id}
                onMouseEnter={() => dispatchBadgeSurge(cred.id)}
                className="col-span-12 md:col-span-6 lg:col-span-4 group"
              >
                <div
                  className="h-full glass-acrylic card-sheen p-6 sm:p-7 rounded-3xl flex flex-col justify-between border border-white/[0.08] hover:border-cyan-400/40 transition-all duration-300"
                  style={{ borderTop: `2px solid ${cred.color}` }}
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span
                        className="text-[10px] font-mono px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider"
                        style={{ backgroundColor: `${cred.color}15`, color: cred.color }}
                      >
                        {cred.badgeType.toUpperCase()}
                      </span>
                      <span className="text-xs text-neutral-400 font-mono">{cred.issueDate}</span>
                    </div>

                    <h3 className="text-lg sm:text-xl font-bold text-white mb-1 tracking-tight font-display">
                      {cred.title}
                    </h3>
                    <div className="text-xs font-mono text-cyan-300 mb-3 font-semibold flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{cred.issuer}</span>
                    </div>

                    <p className="text-xs sm:text-sm text-neutral-300 leading-relaxed mb-4">
                      {cred.highlights[0]}
                    </p>

                    {isExpanded && cred.highlights.length > 1 && (
                      <div className="pt-3 border-t border-white/[0.08] space-y-2 mb-4 animate-fadeIn">
                        {cred.highlights.slice(1).map((h, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs text-neutral-300">
                            <span className="text-cyan-400 font-bold">•</span>
                            <span>{h}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-white/[0.08] mt-2">
                    <button
                      type="button"
                      onClick={() => toggleExpand(cred.id)}
                      aria-expanded={isExpanded}
                      data-cursor="SKILLS"
                      className="min-h-[44px] flex items-center gap-1.5 text-xs font-mono font-semibold text-cyan-400 hover:text-cyan-300 cursor-pointer"
                    >
                      <span>{isExpanded ? 'Hide Details' : 'View Skills'}</span>
                      <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
                    </button>

                    <a
                      href={cred.verificationUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      data-cursor="VERIFY"
                      className="min-h-[44px] px-3.5 py-1.5 rounded-xl bg-white/[0.06] text-neutral-200 hover:text-white hover:bg-cyan-500/20 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-white/10 hover:border-cyan-400/40"
                    >
                      <span>Verify</span>
                      <ExternalLink className="w-3 h-3 text-cyan-400" />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
