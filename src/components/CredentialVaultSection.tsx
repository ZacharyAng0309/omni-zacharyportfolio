import React, { useState } from 'react';
import { CREDENTIALS } from '../data/credentials';
import { ExternalLink, ChevronDown, Award, Cloud, BookOpen } from 'lucide-react';

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

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <section
      id="vault"
      aria-label="Verified Credentials & Honors"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-8 py-20 sm:py-24 relative z-10 max-w-6xl mx-auto"
    >
      {/* Chapter Marker */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-400 font-mono text-xs uppercase tracking-wider border border-indigo-500/20 font-bold">
          Chapter 03 • Credential Vault
        </span>
        <span className="text-slate-500 text-[11px] sm:text-xs font-mono">
          PRIMARY SOURCE GROUNDING &amp; OFFICIAL REGISTRIES
        </span>
      </div>

      <h2 className="text-2xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
        Verified Credentials &amp; <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-300">Academic Distinction</span>
      </h2>

      <p className="text-slate-300 text-sm sm:text-base md:text-lg max-w-3xl mb-8 leading-relaxed">
        Every milestone is backed by verifiable institutional credentials, global hackathon trophies, and official Google Cloud, Microsoft Azure, and Huawei skill certifications.
      </p>

      {/* Category Filter Pills (Mobile Touch Ergonomics >= 44px) */}
      <div className="flex flex-wrap items-center gap-2 mb-8">
        <button
          onClick={() => setFilter('all')}
          className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            filter === 'all'
              ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
              : 'glass-panel text-slate-300 hover:text-white'
          }`}
        >
          All Credentials ({CREDENTIALS.length})
        </button>
        <button
          onClick={() => setFilter('cloud')}
          className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
            filter === 'cloud'
              ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
              : 'glass-panel text-slate-300 hover:text-white'
          }`}
        >
          <Cloud className="w-3.5 h-3.5" />
          <span>Cloud &amp; AI Badges</span>
        </button>
        <button
          onClick={() => setFilter('pm')}
          className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
            filter === 'pm'
              ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
              : 'glass-panel text-slate-300 hover:text-white'
          }`}
        >
          <Award className="w-3.5 h-3.5" />
          <span>Product &amp; BA</span>
        </button>
        <button
          onClick={() => setFilter('academic')}
          className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
            filter === 'academic'
              ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
              : 'glass-panel text-slate-300 hover:text-white'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Academic &amp; Global Wins</span>
        </button>
      </div>

      {/* Grid of Credentials */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        {filteredCredentials.map((cred) => {
          const isExpanded = expandedId === cred.id;
          return (
            <div
              key={cred.id}
              className="glass-panel p-5 sm:p-6 rounded-2xl flex flex-col justify-between hover:border-indigo-500/40 transition-all border-t-2"
              style={{ borderTopColor: cred.color }}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span
                    className="text-[10px] font-mono px-2 py-0.5 rounded font-bold"
                    style={{ backgroundColor: `${cred.color}15`, color: cred.color }}
                  >
                    {cred.badgeType.toUpperCase()}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">{cred.issueDate}</span>
                </div>

                <h3 className="text-base sm:text-lg font-bold text-white mb-1">
                  {cred.title}
                </h3>
                <div className="text-xs font-mono text-slate-400 mb-3 font-semibold">
                  {cred.issuer}
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mb-4">
                  {cred.highlights[0]}
                </p>

                {isExpanded && cred.highlights.length > 1 && (
                  <div className="pt-3 border-t border-slate-800 space-y-1.5 mb-4 animate-fadeIn">
                    {cred.highlights.slice(1).map((h, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-xs text-slate-300">
                        <span className="text-cyan-400 font-bold">•</span>
                        <span>{h}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 mt-2">
                <button
                  type="button"
                  onClick={() => toggleExpand(cred.id)}
                  aria-expanded={isExpanded}
                  className="min-h-[40px] flex items-center gap-1 text-xs font-mono text-cyan-400 hover:underline cursor-pointer"
                >
                  <span>{isExpanded ? 'Hide Details' : 'View Skills'}</span>
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                </button>

                <a
                  href={cred.verificationUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="min-h-[40px] px-3 py-1.5 rounded-lg bg-slate-800/80 text-slate-200 hover:text-white hover:bg-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-700"
                >
                  <span>Verify</span>
                  <ExternalLink className="w-3 h-3 text-cyan-400" />
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
