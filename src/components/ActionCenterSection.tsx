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
      className="min-h-screen flex flex-col justify-center px-6 py-28 relative z-10 max-w-5xl mx-auto"
    >
      <div className="mb-12 text-center">
        <div className="text-xs font-mono uppercase tracking-widest text-neutral-400 mb-2">
          Strategic Engagement
        </div>
        <h2 className="text-4xl sm:text-6xl font-bold tracking-tighter headline-gradient mb-4">
          Initiate Collaboration.
        </h2>
        <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto">
          Available for high-stakes AI product strategy, enterprise solution architecture, and fintech advisory.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Direct Coordinates & Quick Actions */}
        <div className="apple-glass p-8 rounded-3xl border-t-2 border-cyan-400/40 space-y-6">
          <h3 className="text-xl font-bold text-white tracking-tight">
            Direct Executive Coordinates
          </h3>
          <p className="text-xs text-neutral-400 leading-relaxed">
            Open to fractional AI strategy, enterprise architecture reviews, and global leadership roles.
          </p>

          <div className="space-y-3">
            <a
              href="mailto:zacharyang0309@gmail.com"
              className="flex items-center gap-3 p-3.5 rounded-2xl bg-white/5 hover:bg-white/10 transition-colors border border-white/5 text-neutral-200 text-xs font-mono"
            >
              <div className="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400">
                <Mail className="w-4 h-4" />
              </div>
              <span>zacharyang0309@gmail.com</span>
            </a>

            <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-white/5 border border-white/5 text-neutral-300 text-xs font-mono">
              <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                <MapPin className="w-4 h-4" />
              </div>
              <span>Kuala Lumpur, Malaysia (Open to Global Remote)</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <button
              onClick={onResumeClick}
              className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-full text-xs font-semibold bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-md"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Resume (PDF)</span>
            </button>

            <div className="flex gap-2">
              <a
                href="https://www.linkedin.com/in/zacharyangziyang"
                target="_blank"
                rel="noopener noreferrer"
                className="p-3 rounded-full apple-glass text-neutral-300 hover:text-white hover:bg-white/10 transition-all border border-white/10 flex items-center justify-center"
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
                className="p-3 rounded-full apple-glass text-neutral-300 hover:text-white hover:bg-white/10 transition-all border border-white/10 flex items-center justify-center"
                title="Explore GitHub"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        {/* Quick Message Form */}
        <div className="apple-glass p-8 rounded-3xl border-t-2 border-white/20">
          <h3 className="text-xl font-bold text-white tracking-tight mb-1">
            Send Direct Brief
          </h3>
          <p className="text-xs text-neutral-400 mb-6">
            Leave a message and Zachary will reply within 24 hours.
          </p>

          {submitted ? (
            <div className="p-8 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <div className="text-sm font-bold text-white">Transmission Confirmed</div>
              <p className="text-xs text-neutral-300">
                Zachary will reach out shortly to {formData.email}.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-mono text-neutral-400 mb-1">YOUR NAME</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Elena Rostova"
                  className="w-full px-4 py-3 rounded-2xl bg-white/5 border border-white/10 text-neutral-200 text-xs focus:outline-none focus:border-white/30 transition-colors"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-neutral-400 mb-1">EMAIL ADDRESS</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="e.g. elena@partner.com"
                  className="w-full px-4 py-3 rounded-2xl bg-white/5 border border-white/10 text-neutral-200 text-xs focus:outline-none focus:border-white/30 transition-colors"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-neutral-400 mb-1">MESSAGE / INQUIRY</label>
                <textarea
                  rows={4}
                  required
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Describe your AI architecture, hackathon collaboration, or strategic initiative..."
                  className="w-full px-4 py-3 rounded-2xl bg-white/5 border border-white/10 text-neutral-200 text-xs focus:outline-none focus:border-white/30 transition-colors resize-none"
                />
              </div>

              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 py-3 rounded-full text-xs font-semibold bg-white text-black hover:bg-neutral-200 transition-all cursor-pointer shadow-md"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Transmit Message</span>
              </button>
            </form>
          )}
        </div>
      </div>

      <div className="pt-20 mt-20 border-t border-white/10 text-center sm:flex sm:justify-between sm:items-center text-xs text-neutral-500 font-mono space-y-2 sm:space-y-0">
        <div>
          © {CURRENT_YEAR} Zachary Ang Zi Yang.
        </div>
        <div className="flex justify-center gap-4 text-[11px]">
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
