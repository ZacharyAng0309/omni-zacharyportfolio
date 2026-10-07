# Ang Zi Yang (Zachary) — 3D Storyline Portfolio

> **Live Deployment**: [https://zacharyang0309.github.io/omni-zacharyportfolio/](https://zacharyang0309.github.io/omni-zacharyportfolio/)  
> **Global Grand Champion** — Hilti IT Competition 2024 (Liechtenstein & Switzerland)  
> **Finalist** — Great AI Hackathon 2025

---

## Overview
A high-performance scrollytelling personal portfolio built with **React 19**, **Three.js WebGL**, and **Tailwind CSS**. Designed to bridge spatial 3D presence with ultra-responsive executive readability.

### Key Features
- **High-Fidelity 3D Avatar**: Lightweight rigged humanoid model (`Asian_M_3_Busi.glb`, 1.74 MB) with dynamic cursor gaze tracking, sinus spine breathing oscillation, and procedurally attached titanium wireframe glasses.
- **Interactive Scrollytelling Choreography**: Smooth waypoint-interpolated camera transitions across 6 thematic acts.
- **Collapsible Architecture Deep Dives**: Expandable accordions for 5 flagship enterprise & AI case studies (*Hireti*, *ChronoAI*, *Soft Space Payment Platform*, *Petronas PIES*, *GDSC Bot*).
- **Verified National Press Vault**: Full citations with transcripts and canonical links from *The Star* ("To the Land of the Alps, we go!"), *APU Media News*, and *EasyUni*.
- **Comprehensive Credentials**: Complete suite of all 7 Google Cloud GCPBoleh Skill Badges, Microsoft Azure AZ-900, Huawei Cloud HCCDA, and Google Project Management.
- **Enterprise-Grade Performance**: Sub-1.5s initial paint, clamped DPR, code-split vendor chunks (`three`, `react`, `lucide`), and full `prefers-reduced-motion` WCAG 2.1 AA accessibility support.

---

## Tech Stack
- **UI Framework**: React 19 + TypeScript
- **3D Graphics Engine**: Three.js (r186) + GLTFLoader
- **Styling**: Tailwind CSS v4 + Lucide Icons
- **Build & Bundler**: Vite v8 + Rolldown engine
- **Code Quality**: Oxlint (0 warnings, 0 errors across all 21 source files)
- **Deployment**: GitHub Pages via automated GitHub Actions CI/CD (`.github/workflows/deploy.yml`)

---

## Development

```bash
# Install dependencies
npm install

# Start local dev server (port 5173)
npm run dev

# Run static analysis
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```
