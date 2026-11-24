/**
 * SoundEngine
 * Procedural Web Audio API synthesizer for tactile and spatial acoustic feedback:
 * - Ambient sub-bass 44-52Hz
 * - Tactile 2.4kHz clicks
 * - Act transition frequency sweeps
 * - Summit harmonic chimes (528Hz, 792Hz, 1056Hz)
 * Strictly muted by default to respect autoplay policies and WCAG accessibility.
 */
export class SoundEngine {
  private audioContext: AudioContext | null = null;
  private isAudioMuted: boolean = true;
  private subBassOsc: OscillatorNode | null = null;
  private subBassGain: GainNode | null = null;
  private masterGain: GainNode | null = null;
  private analyser: AnalyserNode | null = null;
  private energyBuffer: Uint8Array<ArrayBuffer> | null = null;
  private activeSynthUntilMs: number = 0;
  private activeSynthDurationMs: number = 0;
  private activeSynthPeak: number = 0;
  private unlockListenerAttached: boolean = false;
  private unlockHandler: (() => void) | null = null;

  constructor() {
    // Attach one-time window unlock listeners to unlock AudioContext on first mobile/browser gesture
    this.attachUnlockListeners();
  }

  private attachUnlockListeners(): void {
    if (typeof window === 'undefined' || this.unlockListenerAttached) return;
    this.unlockListenerAttached = true;

    this.unlockHandler = () => {
      if (!this.audioContext) {
        // AudioContext not yet initialized; preserve listener for when audio is activated
        return;
      }
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume().then(() => {
          this.removeUnlockListeners();
        }).catch(() => {});
      } else {
        this.removeUnlockListeners();
      }
    };

    window.addEventListener('pointerdown', this.unlockHandler, { passive: true });
    window.addEventListener('touchstart', this.unlockHandler, { passive: true });
    window.addEventListener('keydown', this.unlockHandler, { passive: true });
  }

  private removeUnlockListeners(): void {
    if (typeof window === 'undefined' || !this.unlockListenerAttached) return;
    if (this.unlockHandler) {
      window.removeEventListener('pointerdown', this.unlockHandler);
      window.removeEventListener('touchstart', this.unlockHandler);
      window.removeEventListener('keydown', this.unlockHandler);
      this.unlockHandler = null;
    }
    this.unlockListenerAttached = false;
  }

  private initAudioContext(): void {
    if (typeof window === 'undefined') return;
    if (!this.audioContext) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        this.audioContext = new AudioCtx();
      }
    }
    if (this.audioContext && !this.masterGain) {
      try {
        this.masterGain = this.audioContext.createGain();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 64;
        this.analyser.smoothingTimeConstant = 0.8;
        this.energyBuffer = new Uint8Array(new ArrayBuffer(this.analyser.frequencyBinCount));
        this.masterGain.connect(this.analyser);
        this.analyser.connect(this.audioContext.destination);
      } catch {
        // Graceful fallback for non-standard test runners
      }
    }
    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume().then(() => {
        if (this.audioContext?.state === 'running') {
          this.removeUnlockListeners();
        }
      }).catch(() => {});
      this.attachUnlockListeners();
    }
  }

  public getAudioContext(): AudioContext | null {
    return this.audioContext;
  }

  public isAudioEnabled(): boolean {
    return !this.isAudioMuted;
  }

  private triggerSynthEnvelope(peak: number, durationSeconds: number): void {
    const nowMs = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const durationMs = Math.max(40, durationSeconds * 1000);
    const currentEnv =
      nowMs < this.activeSynthUntilMs && this.activeSynthDurationMs > 0
        ? this.activeSynthPeak *
          Math.max(0.18, Math.min(1.0, (this.activeSynthUntilMs - nowMs) / this.activeSynthDurationMs))
        : 0;
    const newUntilMs = Math.max(this.activeSynthUntilMs, nowMs + durationMs);
    this.activeSynthDurationMs = Math.max(40, newUntilMs - nowMs);
    this.activeSynthUntilMs = newUntilMs;
    this.activeSynthPeak = Math.max(currentEnv, Math.min(1.0, peak));
  }

  public getAudioEnergy(): number {
    if (this.isAudioMuted || !this.audioContext || this.audioContext.state !== 'running') {
      return 0.0;
    }
    let fftEnergy = 0.0;
    if (this.analyser && this.energyBuffer) {
      try {
        this.analyser.getByteFrequencyData(this.energyBuffer);
        let sum = 0;
        let vocalSum = 0;
        const vocalBins = Math.min(4, this.energyBuffer.length);
        for (let i = 0; i < this.energyBuffer.length; i++) {
          const val = this.energyBuffer[i]!;
          sum += val;
          if (i < vocalBins) {
            vocalSum += val;
          }
        }
        const fullAvg = sum / (this.energyBuffer.length * 255.0);
        const vocalAvg = vocalBins > 0 ? vocalSum / (vocalBins * 255.0) : 0.0;
        fftEnergy = Math.max(fullAvg, vocalAvg * 0.65) * 3.5;
      } catch {
        fftEnergy = 0.0;
      }
    }

    const nowMs = typeof performance !== 'undefined' ? performance.now() : Date.now();
    let transientEnergy = 0.0;
    if (nowMs < this.activeSynthUntilMs && this.activeSynthDurationMs > 0) {
      const remaining = (this.activeSynthUntilMs - nowMs) / this.activeSynthDurationMs;
      transientEnergy = this.activeSynthPeak * Math.max(0.18, Math.min(1.0, remaining));
    }
    const subBassFloor = this.subBassOsc ? 0.24 : 0.0;
    const synthEnergy = Math.max(subBassFloor, transientEnergy);

    return Math.min(1.0, Math.max(fftEnergy, synthEnergy));
  }

  public toggleAudio(): boolean {
    this.initAudioContext();
    this.isAudioMuted = !this.isAudioMuted;

    if (!this.isAudioMuted) {
      this.startAmbientSubBass();
      this.playHapticClick(1200, 0.05);
    } else {
      this.stopAmbientSubBass();
      this.activeSynthUntilMs = 0;
      this.activeSynthDurationMs = 0;
      this.activeSynthPeak = 0;
    }

    return !this.isAudioMuted;
  }

  public playTactileClick(duration: number = 0.03): void {
    this.playHapticClick(2400, duration);
  }

  public playHapticClick(frequency: number = 2400, duration: number = 0.04): void {
    if (this.isAudioMuted || !this.audioContext || this.audioContext.state === 'closed') return;
    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume().catch(() => {});
    }
    this.triggerSynthEnvelope(0.45, Math.max(duration, 0.14));
    try {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(frequency, this.audioContext.currentTime);

      gain.gain.setValueAtTime(0.06, this.audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.audioContext.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.masterGain ?? this.audioContext.destination);

      osc.start();
      osc.stop(this.audioContext.currentTime + duration);
    } catch {
      // Graceful fallback
    }
  }

  public playHarmonicHum(frequency: number = 220, duration: number = 0.35): void {
    if (this.isAudioMuted || !this.audioContext || this.audioContext.state === 'closed') return;
    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume().catch(() => {});
    }
    this.triggerSynthEnvelope(0.68, duration);
    try {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
      osc.frequency.exponentialRampToValueAtTime(frequency * 0.5, this.audioContext.currentTime + duration);

      gain.gain.setValueAtTime(0.08, this.audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.audioContext.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.masterGain ?? this.audioContext.destination);

      osc.start();
      osc.stop(this.audioContext.currentTime + duration);
    } catch {
      // Graceful fallback
    }
  }

  public playTransitionSweep(startFreq: number = 140, endFreq: number = 480, duration: number = 0.45): void {
    if (this.isAudioMuted || !this.audioContext || this.audioContext.state === 'closed') return;
    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume().catch(() => {});
    }
    this.triggerSynthEnvelope(0.62, duration);
    try {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(startFreq, this.audioContext.currentTime);
      osc.frequency.exponentialRampToValueAtTime(endFreq, this.audioContext.currentTime + duration);

      gain.gain.setValueAtTime(0.04, this.audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.audioContext.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.masterGain ?? this.audioContext.destination);

      osc.start();
      osc.stop(this.audioContext.currentTime + duration);
    } catch {
      // Graceful fallback
    }
  }

  public playSummitChime(): void {
    if (this.isAudioMuted || !this.audioContext || this.audioContext.state === 'closed') return;
    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume().catch(() => {});
    }
    this.triggerSynthEnvelope(0.72, 0.45);
    const chords = [528, 792, 1056];
    chords.forEach((freq, idx) => {
      setTimeout(() => {
        this.playHapticClick(freq, 0.28);
      }, idx * 70);
    });
  }

  private startAmbientSubBass(): void {
    if (!this.audioContext || this.subBassOsc) return;
    try {
      this.subBassOsc = this.audioContext.createOscillator();
      this.subBassGain = this.audioContext.createGain();

      this.subBassOsc.type = 'sine';
      this.subBassOsc.frequency.setValueAtTime(48, this.audioContext.currentTime); // 48Hz Sub-bass

      this.subBassGain.gain.setValueAtTime(0.018, this.audioContext.currentTime);

      this.subBassOsc.connect(this.subBassGain);
      this.subBassGain.connect(this.masterGain ?? this.audioContext.destination);

      this.subBassOsc.start();
    } catch {
      // Graceful fallback
    }
  }

  private stopAmbientSubBass(): void {
    if (this.subBassOsc) {
      try {
        this.subBassOsc.stop();
        this.subBassOsc.disconnect();
      } catch {}
      this.subBassOsc = null;
    }
    if (this.subBassGain) {
      try {
        this.subBassGain.disconnect();
      } catch {}
      this.subBassGain = null;
    }
  }

  public dispose(): void {
    this.removeUnlockListeners();
    this.stopAmbientSubBass();
    if (this.masterGain) {
      try {
        this.masterGain.disconnect();
      } catch {}
      this.masterGain = null;
    }
    if (this.analyser) {
      try {
        this.analyser.disconnect();
      } catch {}
      this.analyser = null;
    }
    this.energyBuffer = null;
    this.activeSynthUntilMs = 0;
    this.activeSynthDurationMs = 0;
    this.activeSynthPeak = 0;
    if (this.audioContext) {
      try {
        this.audioContext.close();
      } catch {}
      this.audioContext = null;
    }
  }
}
