import { create } from 'zustand';

interface ScrollState {
  scrollProgress: number;   // Normalized 0.0 to 1.0
  scrollVelocity: number;   // Smoothed scroll speed for shader distortion
  activeSection: 'hero' | 'experience' | 'systems' | 'contact';
  pointer: [number, number]; // Normalized [-1, 1] cursor coords
  setScroll: (progress: number, velocity: number) => void;
  setActiveSection: (section: ScrollState['activeSection']) => void;
  setPointer: (x: number, y: number) => void;
}

export const useScrollStore = create<ScrollState>((set) => ({
  scrollProgress: 0,
  scrollVelocity: 0,
  activeSection: 'hero',
  pointer: [0, 0],
  setScroll: (scrollProgress, scrollVelocity) => set({ scrollProgress, scrollVelocity }),
  setActiveSection: (activeSection) => set({ activeSection }),
  setPointer: (x, y) => set({ pointer: [x, y] }),
}));
