import { useState } from 'react';
import { Download, Mail, Send, CheckCircle2, MapPin } from 'lucide-react';

interface ActionCenterSectionProps {
  onResumeClick: () => void;
}

const CURRENT_YEAR = new Date().getFullYear();

export const ActionCenterSection: React.FC<ActionCenterSectionProps> = ({ onResumeClick }) => {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.message) return;
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      setFormData({ name: '', email: '', message: '' });
    }, 4000);
  };

  return (
    <footer
      id="contact"
      role="contentinfo"
      aria-label="Executive Action Center"
      className="min-h-screen flex flex-col justify-center px-4 sm:px-6 py-20 sm:py-28 relative z-10 max-w-5xl mx-auto"
    >
      <div className="mb-10 sm:mb-12 text-center">
        <div className="text-xs font-mono uppercase tracking-widest text-neutral-400 mb-2">
          Strategic Engagement
        </div>
        <h2 className="text-3xl sm:text-5xl md:text-6xl font-bold tracking-tighter headline-gradient mb-3 sm:mb-4">
          Initiate Collaboration.
        </h2>
        <p className="text-neutral-400 text-xs sm:text-sm md:text-base max-w-xl mx-auto px-2">
          Available for high-stakes AI product strategy, enterprise solution architecture, and fintech advisory.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 items-start">
        {/* Direct Coordinates & Quick Actions */}
        <div className="apple-glass p-5 sm:p-8 rounded-2xl sm:rounded-3xl border-t-2 border-cyan-400/40 space-y-5 sm:space-y-6">
          <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight">
            Direct Executive Coordinates
          </h3>
          <p className="text-xs text-neutral-400 leading-relaxed">
            Open to fractional AI strategy, enterprise architecture reviews, and global leadership roles.
          </p>

          <div className="space-y-3">
            <a
              href="mailto:zacharyang0309@gmail.com"
              className="flex items-center gap-3 p-3.5 rounded-2xl bg-white/5 hover:bg-white/10 transition-colors border border-white/5 text-neutral-200 text-xs font-mono min-h-[48px]"
            >
              <div className="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 flex-shrink-0">
                <Mail className="w-4 h-4" />
              </div>
              <span className="truncate">zacharyang0309@gmail.com</span>
            </a>

            <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-white/5 border border-white/5 text-neutral-300 text-xs font-mono min-h-[48px]">
              <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 flex-shrink-0">
                <MapPin className="w-4 h-4" />
              </div>
              <span>Kuala Lumpur, Malaysia (Open to Global Remote)</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <button
              onClick={onResumeClick}
              className="w-full sm:flex-1 min-h-[48px] flex items-center justify-center gap-2 py-3 px-4 rounded-full text-xs font-semibold bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-md"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Resume (PDF)</span>
            </button>

            <div className="flex justify-center gap-2">
              <a
                href="https://www.linkedin.com/in/zacharyangziyang"
                target="_blank"
                rel="noopener noreferrer"
                className="w-12 h-12 rounded-full apple-glass text-neutral-300 hover:text-white hover:bg-white/10 transition-all border border-white/10 flex items-center justify-center cursor-pointer"
                title="Connect on LinkedIn"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 8.76a1.64 1.64 0 0 0 0-3.28 1.64 1.64 0 0 0 0 3.28m1.4 9.74v-8.37H5.06v8.37h2.8z" />
                </svg>
              </a>

              <a
                href="https://github.com/ZacharyAng0309"
                target="_blank"
                rel="noopener noreferrer"
                className="w-12 h-12 rounded-full apple-glass text-neutral-300 hover:text-white hover:bg-white/10 transition-all border border-white/10 flex items-center justify-center cursor-pointer"
                title="Explore GitHub"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        {/* Executive Direct Dispatch Form */}
        <div className="apple-glass p-5 sm:p-8 rounded-2xl sm:rounded-3xl border-t-2 border-indigo-400/40">
          <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight mb-2">
            Direct Dispatch
          </h3>
          <p className="text-xs text-neutral-400 mb-6">
            Leave a direct inquiry. Responses guaranteed within 24 hours.
          </p>

          {submitted ? (
            <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-center space-y-2 animate-fadeIn">
              <CheckCircle2 className="w-8 h-8 mx-auto" />
              <div className="font-semibold text-sm">Message Transmitted Successfully</div>
              <p className="text-xs text-neutral-400">
                Thank you. Zachary will review your inquiry promptly.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-bold">
                  Your Name / Organization
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Elena Rostova • Hilti Corporate IT"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs sm:text-sm placeholder:text-neutral-600 focus:outline-none focus:border-cyan-400 transition-colors min-h-[44px]"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-bold">
                  Corporate Email
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. elena.rostova@hilti.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs sm:text-sm placeholder:text-neutral-600 focus:outline-none focus:border-cyan-400 transition-colors min-h-[44px]"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-bold">
                  Executive Brief / Project Scope
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Outline key objectives, timeline, or collaboration scope..."
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs sm:text-sm placeholder:text-neutral-600 focus:outline-none focus:border-cyan-400 transition-colors resize-none"
                />
              </div>

              <button
                type="submit"
                className="w-full min-h-[48px] py-3.5 px-6 rounded-full bg-white text-black text-xs sm:text-sm font-semibold hover:bg-neutral-200 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg hover:scale-101 active:scale-99"
              >
                <span>Transmit Message</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          )}
        </div>
      </div>

      <div className="pt-16 sm:pt-20 mt-16 sm:mt-20 border-t border-white/10 text-center sm:flex sm:justify-between sm:items-center text-xs text-neutral-500 font-mono space-y-3 sm:space-y-0">
        <div>
          © {CURRENT_YEAR} Zachary Ang Zi Yang.
        </div>
        <div className="flex flex-wrap justify-center gap-3 text-[11px]">
          <span>APPLE KEYNOTE AESTHETIC</span>
          <span>•</span>
          <span>THREE.JS WEBGL</span>
          <span>•</span>
          <span>REACT 19</span>
        </div>
      </div>
    </footer>
  );
};
