# SceneController Modernization & 3D Persona Migration Plan
**Project**: ZacharyPortfolio (`d:\omni-workstation\projects\ZacharyPortfolio`)  
**Specification Reference**: `vault/01_Wiki/Projects/ZacharyPortfolio/03_Design/3d_persona_specification.md`  
**Three.js Skills Applied**: `threejs` (Invariants 1–12), `interactive-3d-avatar`  
**Status**: VERIFIED & REFINED  

---

## 1. Objectives & Goals (/goal)

1. **Onboard Useful MCPs & Tooling**:
   - Integrated `gemini-api-docs` MCP for current Three.js and Google GenAI API patterns.
   - Utilized `generate_image` tool to benchmark and generate Zachary's studio-grade 3D spatial persona bust (`persona_3d_refined_1791385205717.jpg`), grounded in his real portrait (`reference_portrait.jpg`).
2. **Persona Asset Benchmarking & 3D Realization**:
   - Grounded against un-Three.js concept assets (`reference_portrait.jpg`, `3d_persona_hoodie_concept.jpg`).
   - Generated high-fidelity 3D spatial bust asset exhibiting Space Black tech hoodie, parted bangs, titanium round glasses, and frosted plinth with glowing cyan neon halo ring.
   - Built smooth, detailed Three.js procedural model matching the visual ground truth with zero external asset dependencies.
3. **Structured Migration of `SceneController.ts`**:
   - **Unified Animation Loop (`renderer.setAnimationLoop`)**: Replaced legacy `requestAnimationFrame` with WebXR-compatible `renderer.setAnimationLoop` and clean teardown via `setAnimationLoop(null)`.
   - **Modern WebGPU / WebGL Fallback Architecture**: Built capability detection (`detectGraphicsBackend()`, `getBackend()`, `isWebGPUSupported()`) ensuring seamless WebGPU readiness and resilient WebGL2 execution.
   - **High-Volume Instancing & Batching (`InstancedMesh`)**: Collapsed 96 discrete neural constellation nodes into a single CPU draw call with dynamic instance matrices (`DynamicDrawUsage`).
   - **Zero-Allocation Render Loop (Invariant 11)**: Reused scratch math objects (`scratchMatrix`, `scratchVec`, `scratchQuat`, `scratchEuler`, `scratchScale`) to prevent GC frame drops.
   - **Procedural Option B 3D Spatial Persona**:
     - High-subdivision cranium (`SphereGeometry(0.25, 64, 48)`), cheeks, and oval jawline (`#f3d8c8`).
     - Sculpted lips and approachable smile (`UpperLip`, `LowerLip`, philtrum groove in `#c87d6b`).
     - Signature titanium round glasses with circular rims, curved nose pads, bridge, and AR physical lenses.
     - Curtain fringe hair cap with 5 sculpted parted bang ribbons and sideburns (`#1c1615`).
     - Space Black tech hoodie (`#141416`), crossover cowl collar, charcoal underlayer (`#27282c`), and drawstrings with titanium aglets.
     - Dual-layer eye tracking with espresso irises, sclera, and smooth cosine eyelid blinking every 3.8s.
   - **Performance & Accessibility Guardrails**: Clamped DPR (max 1.5), clamped delta (max 0.1s), and respected `prefers-reduced-motion` to bypass procedural oscillations.
   - **Interaction & Event Coordination**: Fixed NDC Y inversion bug in `ThreeCanvas.tsx` and filtered out DOM button/link clicks in raycasting.
   - **Invariant 1 Disposal**: Implemented full recursive traversal to dispose geometries, materials, texture channels, and force WebGL context loss.

---

## 2. Implementation Work Breakdown (/plan)

| Step | Component | Status | Details |
|---|---|---|---|
| **Step 1** | **Persona Asset Benchmarking** | COMPLETE | Generated `persona_3d_refined_1791385205717.jpg` using multimodal generation grounded in `reference_portrait.jpg`. |
| **Step 2** | **WebGPU/WebGL Fallback Architecture** | COMPLETE | Added capability detection and reporting (`getBackend()`, `isWebGPUSupported()`) in `SceneController.ts`. |
| **Step 3** | **Option B 3D Spatial Persona** | COMPLETE | Built high-subdivision cranium, sculpted lips/smile, titanium glasses with nose pads, 5-ribbon parted bangs, and tech hoodie with aglets. |
| **Step 4** | **InstancedMesh & Particle Engine** | COMPLETE | Batched 96 neural nodes into `InstancedMesh` with dynamic draw usage and scratch matrix transformations. |
| **Step 5** | **Event & Pointer Coordination** | COMPLETE | Fixed NDC Y inversion in `ThreeCanvas.tsx`; filtered interactive HTML elements in pointerdown raycasting. |
| **Step 6** | **Zero VRAM Leak Disposal** | COMPLETE | Deep recursive disposal of geometries, materials, and textures; cancellation of animation loop. |
| **Step 7** | **Multi-Perspective Verification (/boost)** | COMPLETE | Expanded unit test suite in `SceneController.test.ts` to 12 deep tests covering persona hierarchy, raycasting, and disposal. |
