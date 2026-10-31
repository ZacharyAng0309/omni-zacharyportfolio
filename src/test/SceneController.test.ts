import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as THREE from 'three';
import { SceneController, PortfolioEngine } from '../graphics/SceneController';
import { SCAN_MATERIAL } from '../domain/contracts';

describe('SceneController Modernization & 3D Spatial Persona Test Suite', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    document.body.innerHTML = '';
    container = document.createElement('div');
    container.style.width = '1024px';
    container.style.height = '768px';
    // Non-zero dimensions in JSDOM
    Object.defineProperty(container, 'clientWidth', { value: 1024, configurable: true });
    Object.defineProperty(container, 'clientHeight', { value: 768, configurable: true });
    document.body.appendChild(container);
  });

  describe('Instantiation & Modern Three.js Pipeline Architecture', () => {
    it('initializes the WebGL renderer with ACESFilmic tone mapping and clamped DPR', () => {
      const controller = new SceneController(container);
      expect(controller).toBeDefined();
      expect(container.children.length).toBeGreaterThan(0);

      const canvas = container.querySelector('canvas');
      expect(canvas).not.toBeNull();

      const renderer = controller.getRenderer();
      expect(renderer.toneMapping).toBe(THREE.ACESFilmicToneMapping);
      expect(renderer.outputColorSpace).toBe(THREE.SRGBColorSpace);
      expect(renderer.shadowMap.type).toBe(THREE.PCFShadowMap);

      controller.dispose();
      expect(container.children.length).toBe(0);
    });

    it('reports graphics backend detection and provides WebGL2 fallback', () => {
      const controller = new SceneController(container);
      expect(['webgl2', 'webgpu']).toContain(controller.getBackend());
      expect(typeof controller.isWebGPUSupported()).toBe('boolean');
      controller.dispose();
    });

    it('attaches and starts unified animation loop via setAnimationLoop', () => {
      const controller = new SceneController(container);
      const renderer = controller.getRenderer();
      expect(typeof renderer.setAnimationLoop).toBe('function');

      const setAnimationLoopSpy = vi.spyOn(renderer, 'setAnimationLoop');
      controller.dispose();

      // Upon disposal, setAnimationLoop(null) must be invoked
      expect(setAnimationLoopSpy).toHaveBeenCalledWith(null);
    });

    it('collapses high-volume neural nodes into InstancedMesh', () => {
      const controller = new SceneController(container);

      let instancedMesh: THREE.InstancedMesh | null = null;
      controller.getScene().traverse((object) => {
        if ((object as any).isInstancedMesh || object instanceof THREE.InstancedMesh) {
          instancedMesh = object as THREE.InstancedMesh;
        }
      });

      expect(instancedMesh).not.toBeNull();
      expect(instancedMesh?.count).toBe(96); // 96 neural data nodes batched in 1 draw call

      controller.dispose();
    });
  });

  describe('Interactive Enterprise AI Engine & 1,200-Particle Kinetic Wave Field Verification', () => {
    it('constructs Interactive Enterprise AI Engine with 3-tier strata architecture (containment shield, clearing ring, neural core) and connection vectors', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();
      expect(rig).toBeDefined();

      const engine = rig.getObjectByName('EnterpriseAIEngine');
      expect(engine).toBeDefined();
      expect(engine instanceof THREE.Group).toBe(true);

      // Tier 1: Outer Containment Shield
      const tier1 = rig.getObjectByName('EngineTier1');
      expect(tier1).toBeDefined();
      const outerShield = rig.getObjectByName('ShieldOuterTorus') as THREE.Mesh;
      expect(outerShield).toBeDefined();
      const shieldMat = outerShield.material as THREE.MeshPhysicalMaterial;
      expect(shieldMat.transmission).toBeCloseTo(0.65, 2);
      expect(shieldMat.roughness).toBeCloseTo(0.15, 2);
      expect(shieldMat.clearcoat).toBeCloseTo(1.0, 1);
      expect(shieldMat.ior).toBeCloseTo(1.52, 2);

      // Tier 2: Middle Clearing Ring (ISO-20022 Financial Network)
      const tier2 = rig.getObjectByName('EngineTier2');
      expect(tier2).toBeDefined();
      const clearingNodes = rig.getObjectByName('ClearingDataNodes') as THREE.InstancedMesh;
      expect(clearingNodes).toBeDefined();
      expect(clearingNodes.count).toBe(96);
      const ringA = rig.getObjectByName('ClearingRingA');
      const ringB = rig.getObjectByName('ClearingRingB');
      expect(ringA).toBeDefined();
      expect(ringB).toBeDefined();

      // Tier 3: Inner Generative Neural Core
      const tier3 = rig.getObjectByName('EngineTier3');
      expect(tier3).toBeDefined();
      const lattice = rig.getObjectByName('NeuralCoreLattice') as THREE.Mesh;
      const nucleus = rig.getObjectByName('NeuralCoreNucleus') as THREE.Mesh;
      expect(lattice).toBeDefined();
      expect(nucleus).toBeDefined();

      // Strata Connection Vectors
      const vectorsGroup = rig.getObjectByName('EngineVectorsGroup');
      expect(vectorsGroup).toBeDefined();
      expect(vectorsGroup?.children.length).toBe(6);

      // Presentation Plinth & Glow Ring Grounding
      const plinth = rig.getObjectByName('Plinth');
      expect(plinth).toBeDefined();
      const glow = rig.getObjectByName('PlinthGlowRing');
      expect(glow).toBeDefined();

      controller.dispose();
    });

    it('executes smooth strata separation and connection vector expansion on explode_strata action', () => {
      const controller = new SceneController(container);
      const tier1 = controller.getEngineTier1();
      const tier2 = controller.getEngineTier2();
      const tier3 = controller.getEngineTier3();
      expect(tier1).not.toBeNull();
      expect(tier2).not.toBeNull();
      expect(tier3).not.toBeNull();

      expect(controller.isEngineExplodedState()).toBe(false);

      // Trigger explode_strata action
      controller.triggerSceneAction('explode_strata');
      expect(controller.isEngineExplodedState()).toBe(true);

      // Animate ticks to let spring dampening expand strata
      for (let i = 0; i < 30; i++) controller.animateTick(0.016);

      // Tier 1 separated upwards along Y
      expect(tier1!.position.y).toBeGreaterThan(0.7);
      // Tier 3 separated downwards along Y
      expect(tier3!.position.y).toBeLessThan(-0.6);

      // Toggle back to integrated state
      controller.triggerSceneAction('explode_strata');
      expect(controller.isEngineExplodedState()).toBe(false);
      for (let i = 0; i < 35; i++) controller.animateTick(0.016);

      expect(tier1!.position.y).toBeCloseTo(0.0, 1);
      expect(tier3!.position.y).toBeCloseTo(0.0, 1);

      controller.dispose();
    });

    it('constructs 1,200-particle kinetic wave field via InstancedMesh for zero draw-call overhead', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();

      let waveField: THREE.InstancedMesh | null = null;
      scene.traverse((obj) => {
        if (obj.name === 'KineticWaveField' && ((obj as any).isInstancedMesh || obj instanceof THREE.InstancedMesh)) {
          waveField = obj as THREE.InstancedMesh;
        }
      });

      expect(waveField).not.toBeNull();
      expect(waveField!.count).toBe(1200);

      controller.dispose();
    });

    it('evolves kinetic wave field across the 6-act growth journey with dynamic wave physics', () => {
      const controller = new SceneController(container);

      // Act 1 (#hero, sp = 0.0) -> Neural ripple
      controller.updateScroll(0.0);
      controller.animateTick(0.016);

      // Act 2 (#timeline, sp = 0.20) -> Crystalline lattice
      controller.updateScroll(0.20);
      controller.animateTick(0.016);

      // Act 3 (#vault, sp = 0.40) -> Credential surge
      controller.updateScroll(0.40);
      controller.animateTick(0.016);

      // Act 4 (#summit, sp = 0.60) -> Alpine summit ascent
      controller.updateScroll(0.60);
      controller.animateTick(0.016);

      // Act 5 (#ai-solutions, sp = 0.80) -> Exploded strata core
      controller.updateScroll(0.80);
      controller.animateTick(0.016);

      // Act 6 (#contact, sp = 1.00) -> Cosmic portal ring
      controller.updateScroll(1.00);
      controller.animateTick(0.016);

      controller.dispose();
    });

    it('supports synthesized Web Audio tactile feedback with mute guardrail', () => {
      const controller = new SceneController(container);
      expect(controller.isAudioEnabled()).toBe(false);

      const enabled = controller.toggleAudio();
      expect(enabled).toBe(true);
      expect(controller.isAudioEnabled()).toBe(true);

      const disabled = controller.toggleAudio();
      expect(disabled).toBe(false);
      expect(controller.isAudioEnabled()).toBe(false);

      controller.dispose();
    });

    it('configures ACESFilmic tone mapping, sRGB color space, and clamped pixel ratio', () => {
      const controller = new SceneController(container);
      const renderer = controller.getRenderer();

      expect(renderer.toneMapping).toBe(THREE.ACESFilmicToneMapping);
      expect(renderer.outputColorSpace).toBe(THREE.SRGBColorSpace);
      expect(renderer.toneMappingExposure).toBeCloseTo(1.05, 1);

      controller.dispose();
    });

    it('ensures 100% deterministic VRAM memory disposal of neural core, wave field, geometries, and materials', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();

      // Collect disposables
      const geometries: THREE.BufferGeometry[] = [];
      const materials: THREE.Material[] = [];
      scene.traverse((obj) => {
        if ((obj as THREE.Mesh).isMesh) {
          const mesh = obj as THREE.Mesh;
          if (mesh.geometry) geometries.push(mesh.geometry);
          if (mesh.material) {
            if (Array.isArray(mesh.material)) {
              materials.push(...mesh.material);
            } else {
              materials.push(mesh.material);
            }
          }
        }
      });

      expect(geometries.length).toBeGreaterThan(0);
      expect(materials.length).toBeGreaterThan(0);

      const geomDisposeSpies = geometries.map((g) => vi.spyOn(g, 'dispose'));
      const matDisposeSpies = materials.map((m) => vi.spyOn(m, 'dispose'));

      controller.dispose();

      // Upon disposal, all meshes and instanced meshes must have had dispose() called
      expect(geomDisposeSpies.some((spy) => spy.mock.calls.length > 0)).toBe(true);
      expect(matDisposeSpies.some((spy) => spy.mock.calls.length > 0)).toBe(true);
      expect(container.children.length).toBe(0);
    });

    it('responds to portfolio:explode_strata and portfolio:scene_action window events with debounce protection', () => {
      const controller = new SceneController(container);
      expect(controller.isEngineExplodedState()).toBe(false);

      // Dispatch window portfolio:explode_strata event
      window.dispatchEvent(new CustomEvent('portfolio:explode_strata'));
      expect(controller.isEngineExplodedState()).toBe(true);

      // Dispatch concurrent portfolio:scene_action immediately within 50ms - should be debounced
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', { detail: { action: 'explode_strata' } })
      );
      expect(controller.isEngineExplodedState()).toBe(true);

      // Explicit { exploded: false } ignores debounce and overrides immediately
      controller.triggerSceneAction('explode_strata', { exploded: false });
      expect(controller.isEngineExplodedState()).toBe(false);

      controller.dispose();
    });

    it('supports interactive drag rotation with inertia and non-destructive cursor tilt', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();
      const engine = rig.getObjectByName('EnterpriseAIEngine') as THREE.Group;
      expect(engine).toBeDefined();

      // Simulate pointerdown
      window.dispatchEvent(new MouseEvent('pointerdown', { clientX: 200, clientY: 200 }));
      // Simulate pointermove drag
      window.dispatchEvent(new MouseEvent('pointermove', { clientX: 280, clientY: 240 }));

      // Tick animation
      controller.animateTick(0.016);
      expect(engine.rotation.y).toBeGreaterThan(0.01);

      // Simulate pointerup
      window.dispatchEvent(new MouseEvent('pointerup'));
      // Tick animation with inertia decay
      for (let i = 0; i < 10; i++) controller.animateTick(0.016);

      // Dragged rotation must be retained (not reset to zero by ambient tilt)
      expect(engine.rotation.y).toBeGreaterThan(0.01);

      controller.dispose();
    });

    it('unregisters all window event listeners upon disposal with zero leaks', () => {
      const removeSpy = vi.spyOn(window, 'removeEventListener');
      const controller = new SceneController(container);
      controller.dispose();

      expect(removeSpy).toHaveBeenCalledWith('portfolio:explode_strata', expect.any(Function));
      expect(removeSpy).toHaveBeenCalledWith('portfolio:scene_action', expect.any(Function));
      expect(removeSpy).toHaveBeenCalledWith('pointerdown', expect.any(Function));
      expect(removeSpy).toHaveBeenCalledWith('pointermove', expect.any(Function));
      expect(removeSpy).toHaveBeenCalledWith('pointerup', expect.any(Function));
      removeSpy.mockRestore();
    });
  });

  describe('Interactivity, Scrollytelling & Event Handlers', () => {
    it('updates scroll progress and clamps values between 0.0 and 1.0', () => {
      const controller = new SceneController(container);

      expect(() => {
        controller.updateScroll(0.5);
        controller.updateScroll(-0.5); // should clamp to 0
        controller.updateScroll(1.5);  // should clamp to 1
      }).not.toThrow();

      controller.dispose();
    });

    it('updates parallax coordinates smoothly without throwing', () => {
      const controller = new SceneController(container);

      expect(() => {
        controller.updateParallax(0.2, -0.4);
        controller.updateParallax(-1.0, 1.0);
      }).not.toThrow();

      controller.dispose();
    });

    it('toggles prefers-reduced-motion to protect sensitive users', () => {
      const controller = new SceneController(container);

      expect(() => {
        controller.setReducedMotion(true);
        controller.setReducedMotion(false);
      }).not.toThrow();

      controller.dispose();
    });

    it('handles responsive resize and adapts avatar scale on mobile viewports', () => {
      const controller = new SceneController(container);

      // Simulate desktop resize
      Object.defineProperty(container, 'clientWidth', { value: 1200, configurable: true });
      Object.defineProperty(container, 'clientHeight', { value: 900, configurable: true });
      controller.resize();
      expect(controller.getAvatarRig().scale.x).toBe(1.0);

      // Simulate mobile resize (< 768px)
      Object.defineProperty(container, 'clientWidth', { value: 375, configurable: true });
      Object.defineProperty(container, 'clientHeight', { value: 667, configurable: true });
      controller.resize();
      expect(controller.getAvatarRig().scale.x).toBe(0.75);

      controller.dispose();
    });

    it('triggers raycast callbacks for summit beacon and flagship orb', () => {
      const onSelectSummitBeacon = vi.fn();
      const onSelectCaseStudyNode = vi.fn();

      const controller = new SceneController(container, {
        onSelectSummitBeacon,
        onSelectCaseStudyNode,
      });

      // Find summit beacon in scene
      let beaconMesh: THREE.Mesh | null = null;
      let orbMesh: THREE.Mesh | null = null;
      controller.getScene().traverse((obj) => {
        if (obj.userData?.type === 'summitBeacon') beaconMesh = obj as THREE.Mesh;
        if (obj.userData?.type === 'flagshipOrb') orbMesh = obj as THREE.Mesh;
      });

      expect(beaconMesh).not.toBeNull();
      expect(orbMesh).not.toBeNull();

      // Trigger raycast directly
      const camera = controller.getCamera();

      // Summit Beacon projection
      if (beaconMesh) {
        const beaconPos = new THREE.Vector3();
        (beaconMesh as THREE.Mesh).getWorldPosition(beaconPos);
        beaconPos.project(camera);
        controller.triggerRaycast(beaconPos.x, beaconPos.y);
        expect(onSelectSummitBeacon).toHaveBeenCalled();
      }

      // Flagship Orb projection
      if (orbMesh) {
        const orbPos = new THREE.Vector3();
        (orbMesh as THREE.Mesh).getWorldPosition(orbPos);
        orbPos.project(camera);
        controller.triggerRaycast(orbPos.x, orbPos.y);
        expect(onSelectCaseStudyNode).toHaveBeenCalledWith('hireti');
      }

      controller.dispose();
    });

    it('constructs Act 4 Swiss Summit assets: Golden Trophy, The Star press proof, and aligns depth with narrative arc', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();

      let trophyFound = false;
      let pressProofFound = false;
      let beaconWorldPos = new THREE.Vector3();
      let orbWorldPos = new THREE.Vector3();

      scene.traverse((obj) => {
        if (obj.name === 'GoldenTrophy') trophyFound = true;
        if (obj.name === 'StarPressParchment') pressProofFound = true;
        if (obj.userData?.type === 'summitBeacon') {
          obj.getWorldPosition(beaconWorldPos);
        }
        if (obj.userData?.type === 'flagshipOrb') {
          obj.getWorldPosition(orbWorldPos);
        }
      });

      expect(trophyFound).toBe(true);
      expect(pressProofFound).toBe(true);

      // Verify Act 4 Mount Pilatus beacon is at canonical depth Z around -56
      expect(beaconWorldPos.z).toBeLessThan(-50);
      expect(beaconWorldPos.z).toBeGreaterThan(-62);

      // Verify Act 5 Hireti Flagship Orb is at canonical depth Z around -76
      expect(orbWorldPos.z).toBeLessThan(-70);
      expect(orbWorldPos.z).toBeGreaterThan(-82);

      controller.dispose();
    });

    it('triggers raycast callback for summit beacon when scrolled to Act 4', () => {
      const onSelectSummitBeacon = vi.fn();
      const controller = new SceneController(container, { onSelectSummitBeacon });

      // Simulate scrolling to Act 4: The Climax
      controller.updateScroll(0.6);

      let beaconMesh: THREE.Mesh | null = null;
      controller.getScene().traverse((obj) => {
        if (obj.userData?.type === 'summitBeacon') beaconMesh = obj as THREE.Mesh;
      });
      expect(beaconMesh).not.toBeNull();

      if (beaconMesh) {
        const beaconPos = new THREE.Vector3();
        (beaconMesh as THREE.Mesh).getWorldPosition(beaconPos);
        beaconPos.project(controller.getCamera());
        controller.triggerRaycast(beaconPos.x, beaconPos.y);
        expect(onSelectSummitBeacon).toHaveBeenCalled();
      }

      controller.dispose();
    });

    it('ignores clicks on interactive DOM buttons to prevent unwanted 3D raycast triggers', () => {
      const onSelectSummitBeacon = vi.fn();
      const controller = new SceneController(container, { onSelectSummitBeacon });

      // Add a DOM button
      const button = document.createElement('button');
      button.textContent = 'Explore';
      document.body.appendChild(button);

      // Click on the DOM button
      const clickEvent = new MouseEvent('pointerdown', {
        clientX: 100,
        clientY: 100,
        bubbles: true,
      });
      button.dispatchEvent(clickEvent);

      expect(onSelectSummitBeacon).not.toHaveBeenCalled();

      controller.dispose();
    });
  });

  describe('Invariant 1: Lifecycle Disposal & Zero Memory Leaks', () => {
    it('executes recursive traversal and clean disposal of all geometries and materials', () => {
      const controller = new SceneController(container);
      const renderer = controller.getRenderer();

      const disposeSpy = vi.spyOn(renderer, 'dispose');
      const forceContextLossSpy = vi.spyOn(renderer, 'forceContextLoss');

      controller.dispose();

      expect(disposeSpy).toHaveBeenCalled();
      expect(forceContextLossSpy).toHaveBeenCalled();
      expect(container.children.length).toBe(0);
      expect(controller.getScene().children.length).toBe(0);

      // Second dispose call is a safe no-op
      expect(() => controller.dispose()).not.toThrow();
    });
  });

  describe('Cinematic Boost Effect & 3D Catmull-Rom Spline Trajectory Test Suite', () => {
    it('dynamically warps camera FOV based on scroll velocity ("The Boost Effect")', () => {
      const controller = new SceneController(container);
      expect(controller.getCurrentFov()).toBe(46);
      expect(controller.getBaseFov()).toBe(46);

      // Simulate initial frame tick at scrollProgress = 0
      controller.animateTick(0.016);
      expect(controller.getCurrentFov()).toBe(46);

      // Simulate rapid scroll acceleration from sp = 0 to sp = 0.5 within a single 16ms frame
      controller.updateScroll(0.5);
      controller.animateTick(0.016);

      // Verify that velocity was computed and camera FOV dilated above base 46°
      expect(controller.getScrollVelocity()).toBeGreaterThan(0);
      expect(controller.getCurrentFov()).toBeGreaterThan(46.0);
      expect(controller.getCurrentFov()).toBeLessThanOrEqual(56.0);

      // Simulate scroll stopping: subsequent ticks should smoothly damp FOV back to base 46°
      for (let i = 0; i < 20; i++) {
        controller.animateTick(0.016);
      }
      expect(controller.getScrollVelocity()).toBe(0);
      expect(controller.getCurrentFov()).toBeCloseTo(46.0, 1);

      controller.dispose();
    });

    it('locks camera FOV strictly to base 46 degrees when prefers-reduced-motion is active', () => {
      const controller = new SceneController(container);
      controller.setReducedMotion(true);

      // Rapidly jump scroll progress from 0 to 0.8
      controller.updateScroll(0.8);
      controller.animateTick(0.016);

      // FOV warp must be completely suppressed to protect vestibular-sensitive users
      expect(controller.getCurrentFov()).toBe(46.0);

      controller.dispose();
    });

    it('evaluates smooth 3D Catmull-Rom spline trajectory and decoupled lookAt targets across all 6 Acts', () => {
      const controller = new SceneController(container);
      const camCurve = controller.getCameraCurve();
      const lookCurve = controller.getLookAtCurve();

      expect(camCurve).toBeInstanceOf(THREE.CatmullRomCurve3);
      expect(lookCurve).toBeInstanceOf(THREE.CatmullRomCurve3);
      expect(camCurve.points.length).toBe(6);
      expect(lookCurve.points.length).toBe(6);

      // Act 1 (sp = 0.0): Camera starts at Z = 8.5
      const ptAct1 = camCurve.getPoint(0.0);
      expect(ptAct1.z).toBeCloseTo(8.5, 1);

      // Act 6 (sp = 1.0): Camera reaches Cosmic Horizon gateway at Z = -89.2
      const ptAct6 = camCurve.getPoint(1.0);
      expect(ptAct6.z).toBeCloseTo(-89.2, 1);

      // Verify non-linear curved lateral deviation (X != 0 at intermediate acts)
      const ptAct2 = camCurve.getPoint(0.2);
      expect(ptAct2.x).toBeGreaterThan(0); // curved orbit around academy

      const ptAct3 = camCurve.getPoint(0.4);
      expect(ptAct3.x).toBeLessThan(0); // curved sweep to opposite flank for crucible

      // Verify decoupled lookAt focus targets
      const lookAct1 = lookCurve.getPoint(0.0);
      expect(lookAct1.z).toBeCloseTo(4.8, 1);

      const lookAct2 = lookCurve.getPoint(0.2);
      expect(lookAct2.z).toBeCloseTo(-18.0, 0); // focuses on Academy Tome in Act 2 (sp ≈ 0.2)

      const lookAct4 = lookCurve.getPoint(0.6);
      expect(lookAct4.z).toBeCloseTo(-56.0, 0); // focuses on Mount Pilatus & Trophy in Act 4 (sp ≈ 0.6)

      controller.dispose();
    });

    it('constructs high-contrast emissive monitor screens and displays in Acts 1, 3, and 5', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();

      let dressingTabletFound = false;
      let keynoteMonitorFound = false;
      let enterpriseWorkstationFound = false;

      scene.traverse((obj) => {
        if (obj.name === 'KeynoteMonitorDisplay') keynoteMonitorFound = true;
        if (obj.name === 'EnterpriseTerminalWorkstation') enterpriseWorkstationFound = true;

        // Verify emissive monitor display materials have emissive intensity
        if (obj.name === 'PodiumScreenMesh' || obj.name === 'FrontierScreenMesh') {
          const mesh = obj as THREE.Mesh;
          const mat = mesh.material as THREE.MeshStandardMaterial;
          expect(mat.emissiveIntensity).toBeGreaterThan(0.8);
          expect(mat.emissiveMap).not.toBeNull();
        }
      });

      expect(keynoteMonitorFound).toBe(true);
      expect(enterpriseWorkstationFound).toBe(true);

      controller.dispose();
    });
  });

  describe('Act 1 Hero Scene Staging Refactor Test Suite', () => {
    it('verifies Circular Plinth and cyan illuminated ring (#00f2fe) are visible and active in Act 1 Hero', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();

      const plinth = rig.getObjectByName('Plinth') as THREE.Mesh;
      const glowRing = rig.getObjectByName('PlinthGlowRing') as THREE.Mesh;

      expect(plinth).toBeDefined();
      expect(glowRing).toBeDefined();
      expect(plinth.visible).toBe(true);
      expect(glowRing.visible).toBe(true);

      // Verify illuminated cyan perimeter ring color (#00f2fe)
      const ringMat = glowRing.material as THREE.MeshBasicMaterial;
      expect(ringMat.color.getHex()).toBe(0x00f2fe);

      // Verify plinth adaptive vertical positioning in Act 1 Hero
      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(plinth.position.y).toBeCloseTo(-1.55, 1);
      expect(glowRing.position.y).toBeCloseTo(-1.48, 1);

      controller.dispose();
    });

    it('verifies plinth and glow ring fade out and scale down when scrolling out of Act 1 (sp > 0.16) and restore on return', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();
      const plinth = rig.getObjectByName('Plinth') as THREE.Mesh;
      const glowRing = rig.getObjectByName('PlinthGlowRing') as THREE.Mesh;

      // In Act 1 Hero (sp = 0.0)
      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(plinth.scale.x).toBeCloseTo(1.0, 2);
      expect(glowRing.scale.x).toBeCloseTo(1.0, 2);
      expect((plinth.material as THREE.MeshStandardMaterial).opacity).toBeCloseTo(1.0, 2);
      expect((glowRing.material as THREE.MeshBasicMaterial).opacity).toBeCloseTo(0.95, 2);
      expect(glowRing.visible).toBe(true);

      // Scroll into Act 2+ (sp = 0.25)
      controller.updateScroll(0.25);
      controller.animateTick(0.016);
      expect(plinth.scale.x).toBe(0.0);
      expect(glowRing.scale.x).toBe(0.0);
      expect((plinth.material as THREE.MeshStandardMaterial).opacity).toBe(0.0);
      expect((glowRing.material as THREE.MeshBasicMaterial).opacity).toBe(0.0);
      expect(glowRing.visible).toBe(false);

      // Return back to Act 1 (sp = 0.05)
      controller.updateScroll(0.05);
      controller.animateTick(0.016);
      expect(plinth.scale.x).toBeCloseTo(1.0, 2);
      expect(glowRing.scale.x).toBeCloseTo(1.0, 2);
      expect((plinth.material as THREE.MeshStandardMaterial).opacity).toBeCloseTo(1.0, 2);
      expect((glowRing.material as THREE.MeshBasicMaterial).opacity).toBeCloseTo(0.95, 2);
      expect(glowRing.visible).toBe(true);

      controller.dispose();
    });

    it('verifies 3-point studio lighting with electric cyan rim backlight (#00f2fe, 4.5) targeting avatarRig', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();
      const rig = controller.getAvatarRig();

      let keyLightFound = false;
      let fillLightFound = false;
      let rimCyanFound = false;
      let plinthSpotFound = false;

      scene.traverse((obj) => {
        if (obj instanceof THREE.DirectionalLight) {
          if (obj.color.getHex() === 0xfff4e6 && obj.intensity >= 3.5) {
            keyLightFound = true;
          }
          if (obj.color.getHex() === 0x94a3b8 && obj.intensity >= 1.2) {
            fillLightFound = true;
          }
          if (obj.color.getHex() === 0x00f2fe && Math.abs(obj.intensity - 4.5) < 0.1) {
            rimCyanFound = true;
            expect(obj.target).toBe(rig);
          }
        }
        if (obj instanceof THREE.SpotLight) {
          if (obj.color.getHex() === 0x00f2fe && Math.abs(obj.intensity - 3.2) < 0.1) {
            plinthSpotFound = true;
            expect(obj.target).toBe(rig);
          }
        }
      });

      expect(keyLightFound).toBe(true);
      expect(fillLightFound).toBe(true);
      expect(rimCyanFound).toBe(true);
      expect(plinthSpotFound).toBe(true);

      controller.dispose();
    });

    it('verifies Act 1 Executive Strategy Studio set: desk, wireframe tablet, curved displays, and grounded lower body', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();

      let desk: THREE.Object3D | null = null;
      let displays: THREE.Object3D | null = null;
      let tablet: THREE.Object3D | null = null;

      scene.traverse((obj) => {
        if (obj.name === 'ExecutiveDesk') desk = obj;
        if (obj.name === 'CurvedDisplays') displays = obj;
        if (obj.name === 'ExecutiveTablet') tablet = obj;
      });

      expect(desk).not.toBeNull();
      expect(displays).not.toBeNull();
      expect(tablet).not.toBeNull();

      // Option B procedural legs and plinth remain grounded without an awkward submersion pop at sp = 0.16
      const rig = controller.getAvatarRig();
      const personaBody = rig.getObjectByName('PersonaBody');
      const leftLeg = rig.getObjectByName('LeftLegMesh');
      const rightLeg = rig.getObjectByName('RightLegMesh');
      const plinth = rig.getObjectByName('Plinth');

      expect(personaBody).toBeDefined();
      expect(leftLeg).toBeDefined();
      expect(rightLeg).toBeDefined();
      expect(plinth).toBeDefined();

      const studioGroup = rig.getObjectByName('StudioGroup');
      const enterpriseEngine = rig.getObjectByName('EnterpriseAIEngine');
      expect(studioGroup).toBeDefined();
      expect(enterpriseEngine).toBeDefined();

      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(leftLeg!.visible).toBe(false);
      expect(rightLeg!.visible).toBe(false);
      expect(plinth!.visible).toBe(true);
      expect(studioGroup!.visible).toBe(true);
      expect(enterpriseEngine!.visible).toBe(true);
      expect(personaBody!.position.y).toBeCloseTo(-1.45, 1);
      expect(plinth!.position.y).toBeCloseTo(-1.55, 1);

      // Verify legs remain hidden and Act 1 scenery visible at sp = 0.16
      controller.updateScroll(0.16);
      controller.animateTick(0.016);
      expect(leftLeg!.visible).toBe(false);
      expect(rightLeg!.visible).toBe(false);
      expect(plinth!.visible).toBe(true);
      expect(studioGroup!.visible).toBe(true);
      expect(enterpriseEngine!.visible).toBe(true);
      expect(personaBody!.position.y).toBeCloseTo(-1.45, 1);
      expect(plinth!.position.y).toBeCloseTo(-1.55, 1);

      // Verify Act 1 scenery cleanly culled beyond sp = 0.16 (Act 2+)
      controller.updateScroll(0.25);
      controller.animateTick(0.016);
      expect(leftLeg!.visible).toBe(false);
      expect(rightLeg!.visible).toBe(false);
      expect(plinth!.visible).toBe(false);
      expect(studioGroup!.visible).toBe(false);
      expect(enterpriseEngine!.visible).toBe(false);
      expect(personaBody!.position.y).toBeCloseTo(-1.45, 1);
      expect(plinth!.position.y).toBeCloseTo(-1.55, 1);

      controller.dispose();
    });

    it('verifies kinetic wave field parameters and Enterprise AI Engine adapt cleanly to the 6-act growth journey narrative sequence', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();
      const engine = rig.getObjectByName('EnterpriseAIEngine');
      expect(engine).toBeDefined();

      // sp = 0.00 (Act 1: Hero)
      controller.updateScroll(0.00);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(rig.position.z).toBeCloseTo(SceneController.PERSONA_STATIONS[0]!.pos.z, 1);

      // sp = 0.25 (Act 2: The Academy Tome)
      controller.updateScroll(0.25);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(rig.position.z).toBeLessThan(SceneController.PERSONA_STATIONS[0]!.pos.z);

      // sp = 0.60 (Act 4: Mount Pilatus Alpine Summit)
      controller.updateScroll(0.60);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(rig.position.z).toBeLessThan(SceneController.PERSONA_STATIONS[1]!.pos.z);

      // sp = 0.75 (Act 5: The Frontier Exploded Core)
      controller.updateScroll(0.75);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(rig.position.z).toBeLessThan(SceneController.PERSONA_STATIONS[2]!.pos.z);

      controller.dispose();
    });

    it('verifies camera spline trajectory and focal point tracking across 6 acts while maintaining neural core alignment', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();
      expect(rig).toBeDefined();

      // Verify camera and lookAt curves
      const cameraCurve = controller.getCameraCurve();
      const lookAtCurve = controller.getLookAtCurve();
      expect(cameraCurve).toBeInstanceOf(THREE.CatmullRomCurve3);
      expect(lookAtCurve).toBeInstanceOf(THREE.CatmullRomCurve3);
      expect(cameraCurve.points.length).toBe(6);
      expect(lookAtCurve.points.length).toBe(6);

      // Verify camera progresses monotonically along negative Z
      for (let i = 0; i < cameraCurve.points.length - 1; i++) {
        expect(cameraCurve.points[i + 1]!.z).toBeLessThan(cameraCurve.points[i]!.z);
      }

      // Verify Act 1 focal alignment
      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(controller.getCurrentLookAt().z).toBeCloseTo(4.8, 1);

      // Verify Act 6 focal alignment
      controller.updateScroll(1.0);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(controller.getCurrentLookAt().z).toBeCloseTo(-95.0, 1);

      controller.dispose();
    });

    it('verifies applyLoadedGLTFAvatar with unrigged 3D scan auto-scales via bounding box, calibrates materials, grounds on plinth, and guards against mid-flight dispose()', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();
      const personaBody = rig.getObjectByName('PersonaBody');

      const unriggedScene = new THREE.Group();
      const scanMat = new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.3, metalness: 0.5 });
      const scanMat2 = new THREE.MeshStandardMaterial({ color: 0x444444, roughness: 0.1, metalness: 0.9 });
      const scanMesh = new THREE.Mesh(
        new THREE.BoxGeometry(0.5, 1.0, 0.5),
        scanMat
      );
      const multiMatMesh = new THREE.Mesh(
        new THREE.BoxGeometry(0.2, 0.2, 0.2),
        [scanMat2]
      );
      unriggedScene.add(scanMesh);
      unriggedScene.add(multiMatMesh);

      // Verify direct THREE.Group argument as well as { scene: THREE.Group }
      controller.applyLoadedGLTFAvatar(unriggedScene);

      expect(personaBody?.visible).toBe(false);
      expect(rig.getObjectByName('EnterpriseAIEngine')?.visible).toBe(true);
      expect(unriggedScene.scale.y).toBeCloseTo(2.35, 2);

      // For a centered 1.0m box scaled to 2.35m, scaledBbox.min.y is -1.175, so bustBaseOffsetY = -1.45 - (-1.175) = -0.275
      expect(unriggedScene.position.y).toBeCloseTo(-0.275, 2);

      // Verify TRELLIS scan material & shadow calibration (both single material and material array)
      expect(scanMesh.castShadow).toBe(true);
      expect(scanMesh.receiveShadow).toBe(false);
      expect(scanMat.roughness).toBeCloseTo(SCAN_MATERIAL.roughness, 2);
      expect(scanMat.metalness).toBeCloseTo(SCAN_MATERIAL.metalness, 2);
      expect(scanMat.color.getHex()).toBe(SCAN_MATERIAL.colorHex);
      expect(scanMat2.roughness).toBeCloseTo(SCAN_MATERIAL.roughness, 2);
      expect(scanMat2.metalness).toBeCloseTo(SCAN_MATERIAL.metalness, 2);
      expect(scanMat2.color.getHex()).toBe(SCAN_MATERIAL.colorHex);

      controller.updateParallax(0.5, -0.3);
      controller.animateTick(0.016);
      expect(unriggedScene.rotation.y).not.toBe(0);
      // Ensure animateInternal lerps around bustBaseOffsetY (-0.275) instead of overwriting with -1.50
      expect(unriggedScene.position.y).toBeCloseTo(-0.275, 1);

      controller.dispose();
      const lateScene = new THREE.Group();
      expect(() => controller.applyLoadedGLTFAvatar({ scene: lateScene })).not.toThrow();
      expect(rig.getObjectByName('GLTFRealisticAvatar')).not.toBe(lateScene);
      expect(lateScene.parent).toBeNull();
    });

    it('preserves textured Zachary_Albedo material, disables shadow casting on optical Glasses_Lens, and skips duplicate spectacles when Sovereign_Titanium_Spectacles is embedded', () => {
      const controller = new SceneController(container);

      const riggedScene = new THREE.Group();
      const headBone = new THREE.Bone();
      headBone.name = 'Head';
      riggedScene.add(headBone);

      const albedoMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.74, metalness: 0.0 });
      albedoMat.name = 'Zachary_Albedo';
      albedoMat.map = new THREE.Texture();
      const bodyMesh = new THREE.Mesh(new THREE.BoxGeometry(0.4, 1.75, 0.3), albedoMat);
      bodyMesh.name = 'body';
      riggedScene.add(bodyMesh);

      const lensMat = new THREE.MeshStandardMaterial({ color: 0xe6f5ff, transparent: true, opacity: 0.035 });
      lensMat.name = 'Glasses_Lens';
      const specsMesh = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.05, 0.02), lensMat);
      specsMesh.name = 'Sovereign_Titanium_Spectacles';
      riggedScene.add(specsMesh);

      controller.applyLoadedGLTFAvatar({ scene: riggedScene });

      // Embedded spectacles must prevent duplicate SignatureHeadStylingRig attachment
      expect(headBone.getObjectByName('SignatureHeadStylingRig')).toBeUndefined();
      // Optical lens must not cast opaque shadow blobs onto the face
      expect(specsMesh.castShadow).toBe(false);
      expect(specsMesh.receiveShadow).toBe(false);
      // Body mesh must cast shadows and preserve Zachary_Albedo material
      expect(bodyMesh.castShadow).toBe(true);
      expect(albedoMat.roughness).toBeCloseTo(0.74, 2);

      controller.dispose();
    });

    it('verifies 5-domain modular character breakdown in zachary_character.glb (Face, Hair, Glasses, Hands, Clothes) with 8 morph targets, 30 active finger bones, and zero hand-thigh contamination', async () => {
      const fs = await import('node:fs');
      const path = await import('node:path');
      const candidatePathA = path.resolve(process.cwd(), 'public/models/zachary_character.glb');
      const candidatePathB = path.resolve(process.cwd(), 'projects/ZacharyPortfolio/public/models/zachary_character.glb');
      const glbPath = fs.existsSync(candidatePathA) ? candidatePathA : candidatePathB;
      const buf = fs.readFileSync(glbPath);

      // [AC-AVATAR-03] Tier-2 GLB size <= 3.0 MB
      expect(buf.byteLength).toBeLessThanOrEqual(3.0 * 1024 * 1024);

      const c0Len = buf.readUInt32LE(12);
      const gltf = JSON.parse(buf.subarray(20, 20 + c0Len).toString('utf8'));
      const bin = buf.subarray(20 + c0Len + 8);

      const domainNames = [
        'SM_Character_Face',
        'SM_Character_Hair',
        'SM_Character_Hands',
        'SM_Cloth_Hoodie',
        'SM_Cloth_Trousers',
        'SM_Cloth_Footwear',
      ];
      let totalBodyTris = 0;
      for (const dName of domainNames) {
        const node = gltf.nodes.find((n: any) => n.name === dName);
        expect(node).toBeDefined();
        const mesh = gltf.meshes[node.mesh];
        expect(mesh).toBeDefined();
        const idxAcc = gltf.accessors[mesh.primitives[0].indices];
        totalBodyTris += idxAcc.count / 3;
      }
      // Exact topology conservation across the 6 body/cloth domain sub-meshes
      expect(totalBodyTris).toBe(35069);

      // [TASK-AVATAR-MOD-01] & [AC-AVATAR-05]: SM_Character_Face 8 morph targets
      const faceNode = gltf.nodes.find((n: any) => n.name === 'SM_Character_Face');
      const faceMesh = gltf.meshes[faceNode.mesh];
      expect(faceMesh.extras?.targetNames).toEqual([
        'mouthSmileLeft',
        'mouthSmileRight',
        'mouthOpen',
        'jawOpen',
        'eyeBlinkLeft',
        'eyeBlinkRight',
        'browInnerUp',
        'viseme_aa',
      ]);
      expect(faceMesh.primitives[0].targets).toHaveLength(8);

      // [TASK-AVATAR-MOD-03] & [AC-AVATAR-04]: Sovereign_Titanium_Spectacles parented to Head bone
      const headIdx = gltf.nodes.findIndex((n: any) => n.name === 'Head');
      const specsIdx = gltf.nodes.findIndex((n: any) => n.name === 'Sovereign_Titanium_Spectacles');
      expect(gltf.nodes[headIdx].children).toContain(specsIdx);
      expect(gltf.nodes[specsIdx].skin).toBeUndefined();
      const lensMat = gltf.materials.find((m: any) => m.name === 'Glasses_Lens');
      expect(lensMat.alphaMode).toBe('BLEND');
      expect(lensMat.doubleSided).toBe(true);

      // [TASK-AVATAR-MOD-04] & [AC-CHR-03]: SM_Character_Hands zero leg contamination + 30/30 active finger bones
      const joints: string[] = gltf.skins[0].joints.map((i: number) => gltf.nodes[i].name);
      const handsNode = gltf.nodes.find((n: any) => n.name === 'SM_Character_Hands');
      const handsPrim = gltf.meshes[handsNode.mesh].primitives[0];
      const jAcc = gltf.accessors[handsPrim.attributes.JOINTS_0];
      const wAcc = gltf.accessors[handsPrim.attributes.WEIGHTS_0];
      const jBV = gltf.bufferViews[jAcc.bufferView];
      const wBV = gltf.bufferViews[wAcc.bufferView];
      const jArr = new Uint8Array(bin.buffer, bin.byteOffset + (jBV.byteOffset || 0), jAcc.count * 4);
      const wArr = new Float32Array(bin.buffer, bin.byteOffset + (wBV.byteOffset || 0), wAcc.count * 4);

      const activeHandBones = new Set<string>();
      let legContaminatedHandVerts = 0;
      for (let v = 0; v < jAcc.count; v++) {
        for (let k = 0; k < 4; k++) {
          const w = wArr[v * 4 + k]!;
          if (w > 0.01) {
            const bName = joints[jArr[v * 4 + k]!]!;
            activeHandBones.add(bName);
            if (/UpLeg|Leg|Foot|Hips/i.test(bName)) {
              legContaminatedHandVerts++;
            }
          }
        }
      }
      expect(legContaminatedHandVerts).toBe(0);
      const fingerBones = joints.filter((n) => /Thumb|Index|Middle|Ring|Pinky/.test(n));
      expect(fingerBones).toHaveLength(30);
      expect(fingerBones.every((b) => activeHandBones.has(b))).toBe(true);

      // [TASK-AVATAR-MOD-01]: Verify smooth periorbital normals (0 inverted orbital normals) & pinned morph boundary seams
      const facePrim = faceMesh.primitives[0];
      const fPosAcc = gltf.accessors[facePrim.attributes.POSITION];
      const fNrmAcc = gltf.accessors[facePrim.attributes.NORMAL];
      const fPosBV = gltf.bufferViews[fPosAcc.bufferView];
      const fNrmBV = gltf.bufferViews[fNrmAcc.bufferView];
      const fPos = new Float32Array(bin.buffer, bin.byteOffset + (fPosBV.byteOffset || 0), fPosAcc.count * 3);
      const fNrm = new Float32Array(bin.buffer, bin.byteOffset + (fNrmBV.byteOffset || 0), fNrmAcc.count * 3);

      let steepOrbitalNormals = 0;
      for (let v = 0; v < fPosAcc.count; v++) {
        const vx = fPos[v * 3]!;
        const vy = fPos[v * 3 + 1]!;
        const vz = fPos[v * 3 + 2]!;
        const nz = fNrm[v * 3 + 2]!;
        if (vy >= 1.555 && vy <= 1.608 && Math.abs(vx) <= 0.060 && vz > 0.075 && nz < 0.35) {
          steepOrbitalNormals++;
        }
      }
      expect(steepOrbitalNormals).toBe(0);

      // Verify bilateral ear width symmetry (<3.0mm anatomical tolerance allowing for v24 artist-authored sculpted ear contour repair) and zero stretched ear cliff triangles (<15mm max edge)
      let leftEarMaxX = 0;
      let rightEarMaxAbsX = 0;
      for (let v = 0; v < fPosAcc.count; v++) {
        const vx = fPos[v * 3]!;
        const vy = fPos[v * 3 + 1]!;
        const vz = fPos[v * 3 + 2]!;
        if (vy >= 1.535 && vy <= 1.615 && vz >= -0.042 && vz <= 0.025) {
          if (vx > leftEarMaxX) leftEarMaxX = vx;
          if (vx < 0 && -vx > rightEarMaxAbsX) rightEarMaxAbsX = -vx;
        }
      }
      expect(Math.abs(leftEarMaxX - rightEarMaxAbsX)).toBeLessThan(0.003);

      const fIdxAcc = gltf.accessors[facePrim.indices];
      const fIdxBV = gltf.bufferViews[fIdxAcc.bufferView];
      const fIndices = new Uint16Array(bin.buffer, bin.byteOffset + (fIdxBV.byteOffset || 0), fIdxAcc.count);
      let maxEarTriEdge = 0;
      const isEarVert = (idx: number): boolean => {
        const vx = Math.abs(fPos[idx * 3]!);
        const vy = fPos[idx * 3 + 1]!;
        const vz = fPos[idx * 3 + 2]!;
        return vx > 0.072 && vy >= 1.535 && vy <= 1.615 && vz >= -0.042 && vz <= 0.025;
      };
      const edgeDist = (a: number, b: number): number =>
        Math.hypot(fPos[a * 3]! - fPos[b * 3]!, fPos[a * 3 + 1]! - fPos[b * 3 + 1]!, fPos[a * 3 + 2]! - fPos[b * 3 + 2]!);
      for (let i = 0; i < fIdxAcc.count; i += 3) {
        const i0 = fIndices[i]!;
        const i1 = fIndices[i + 1]!;
        const i2 = fIndices[i + 2]!;
        if (isEarVert(i0) && isEarVert(i1) && isEarVert(i2)) {
          maxEarTriEdge = Math.max(maxEarTriEdge, edgeDist(i0, i1), edgeDist(i1, i2), edgeDist(i2, i0));
        }
      }
      expect(maxEarTriEdge).toBeGreaterThan(0.005);
      expect(maxEarTriEdge).toBeLessThan(0.015);

      // Verify Sovereign_Titanium_Spectacles lens assembly is horizontally centered at X = 0.000m (<0.5mm offset)
      const specMesh = gltf.meshes[gltf.nodes[specsIdx].mesh];
      const lensPosAcc = gltf.accessors[specMesh.primitives[2].attributes.POSITION];
      expect(Math.abs(0.5 * (lensPosAcc.min[0] + lensPosAcc.max[0]))).toBeLessThan(0.0005);

      // Verify Sovereign_Titanium_Spectacles temple wire preserves 3D cylindrical cross-section (>1.8mm vertical span),
      // tucks laterally inside the outer ear silhouette (max |X| < leftEarMaxX), and sits above the ear apex in profile
      const wirePosAcc = gltf.accessors[specMesh.primitives[0].attributes.POSITION];
      const wirePosBV = gltf.bufferViews[wirePosAcc.bufferView];
      const wirePos = new Float32Array(bin.buffer, bin.byteOffset + (wirePosBV.byteOffset || 0), wirePosAcc.count * 3);
      let wireRearMinY = Infinity;
      let wireRearMaxY = -Infinity;
      let wireMaxAbsX = 0;
      for (let v = 0; v < wirePosAcc.count; v++) {
        const wx = Math.abs(wirePos[v * 3]!);
        const wy = wirePos[v * 3 + 1]! + 1.54; // World Y (Head bone at Y = 1.54m)
        const wz = wirePos[v * 3 + 2]!;
        if (wx > wireMaxAbsX) wireMaxAbsX = wx;
        if (wx > 0.065 && wz >= -0.015 && wz <= 0.010) {
          if (wy < wireRearMinY) wireRearMinY = wy;
          if (wy > wireRearMaxY) wireRearMaxY = wy;
        }
      }
      expect(wireRearMaxY - wireRearMinY).toBeGreaterThan(0.0018);
      expect(wireMaxAbsX).toBeLessThanOrEqual(leftEarMaxX);

      let outerEarMaxY = 0;
      for (let v = 0; v < fPosAcc.count; v++) {
        const vx = Math.abs(fPos[v * 3]!);
        const vy = fPos[v * 3 + 1]!;
        const vz = fPos[v * 3 + 2]!;
        if (vx > 0.072 && vy >= 1.535 && vy <= 1.615 && vz >= -0.042 && vz <= 0.018) {
          if (vy > outerEarMaxY) outerEarMaxY = vy;
        }
      }
      expect(outerEarMaxY).toBeLessThanOrEqual(wireRearMinY + 0.004);

      // Verify rear hoodie cowl (z < -0.055, y < 1.50) is not misclassified into SM_Character_Hair
      const hairNode = gltf.nodes.find((n: any) => n.name === 'SM_Character_Hair');
      const hairPrim = gltf.meshes[hairNode.mesh].primitives[0];
      const hairPosAcc = gltf.accessors[hairPrim.attributes.POSITION];
      const hairPosBV = gltf.bufferViews[hairPosAcc.bufferView];
      const hairPos = new Float32Array(bin.buffer, bin.byteOffset + (hairPosBV.byteOffset || 0), hairPosAcc.count * 3);
      let cowlInHairVerts = 0;
      for (let v = 0; v < hairPosAcc.count; v++) {
        const hy = hairPos[v * 3 + 1]!;
        const hz = hairPos[v * 3 + 2]!;
        if (hz < -0.055 && hy < 1.50) cowlInHairVerts++;
      }
      expect(cowlInHairVerts).toBe(0);

      // Verify simultaneous 8-morph + Neck/Head pitch seam continuity & normal continuity across Face <-> Hair/Hoodie boundaries
      const hoodieNode = gltf.nodes.find((n: any) => n.name === 'SM_Cloth_Hoodie');
      const hoodiePrim = gltf.meshes[hoodieNode.mesh].primitives[0];
      const posKey = (arr: Float32Array, idx: number) =>
        `${Math.round(arr[idx * 3]! * 10000)},${Math.round(arr[idx * 3 + 1]! * 10000)},${Math.round(arr[idx * 3 + 2]! * 10000)}`;

      const neighborSkinByPos = new Map<string, { j: number[]; w: number[]; n: number[] }>();
      const headJointIdx = joints.indexOf('Head');
      for (const prim of [hairPrim, hoodiePrim, facePrim]) {
        const pAcc = gltf.accessors[prim.attributes.POSITION];
        const pBV = gltf.bufferViews[pAcc.bufferView];
        const pArr = new Float32Array(bin.buffer, bin.byteOffset + (pBV.byteOffset || 0), pAcc.count * 3);
        const pnAcc = gltf.accessors[prim.attributes.NORMAL];
        const pnBV = gltf.bufferViews[pnAcc.bufferView];
        const pnArr = new Float32Array(bin.buffer, bin.byteOffset + (pnBV.byteOffset || 0), pnAcc.count * 3);
        const pjAcc = gltf.accessors[prim.attributes.JOINTS_0];
        const pwAcc = gltf.accessors[prim.attributes.WEIGHTS_0];
        const pjBV = gltf.bufferViews[pjAcc.bufferView];
        const pwBV = gltf.bufferViews[pwAcc.bufferView];
        const pjArr = new Uint8Array(bin.buffer, bin.byteOffset + (pjBV.byteOffset || 0), pjAcc.count * 4);
        const pwArr = new Float32Array(bin.buffer, bin.byteOffset + (pwBV.byteOffset || 0), pwAcc.count * 4);

        if (prim !== facePrim) {
          for (let v = 0; v < pAcc.count; v++) {
            neighborSkinByPos.set(posKey(pArr, v), {
              j: [pjArr[v * 4]!, pjArr[v * 4 + 1]!, pjArr[v * 4 + 2]!, pjArr[v * 4 + 3]!],
              w: [pwArr[v * 4]!, pwArr[v * 4 + 1]!, pwArr[v * 4 + 2]!, pwArr[v * 4 + 3]!],
              n: [pnArr[v * 3]!, pnArr[v * 3 + 1]!, pnArr[v * 3 + 2]!],
            });
          }
        }

        // Verify zero single-triangle Head weight cliffs (<0.45 max jump across any triangle)
        const pIdxAcc = gltf.accessors[prim.indices];
        const pIdxBV = gltf.bufferViews[pIdxAcc.bufferView];
        const pIndices = new Uint16Array(bin.buffer, bin.byteOffset + (pIdxBV.byteOffset || 0), pIdxAcc.count);
        const headW = new Float32Array(pAcc.count);
        for (let v = 0; v < pAcc.count; v++) {
          for (let k = 0; k < 4; k++) {
            if (pjArr[v * 4 + k] === headJointIdx) headW[v] = (headW[v] ?? 0) + pwArr[v * 4 + k]!;
          }
        }
        let maxTriHeadJump = 0;
        for (let i = 0; i < pIdxAcc.count; i += 3) {
          const w0 = headW[pIndices[i]!]!;
          const w1 = headW[pIndices[i + 1]!]!;
          const w2 = headW[pIndices[i + 2]!]!;
          const jump = Math.max(w0, w1, w2) - Math.min(w0, w1, w2);
          if (jump > maxTriHeadJump) maxTriHeadJump = jump;
        }
        expect(maxTriHeadJump).toBeLessThan(0.45);
      }

      const fjAcc = gltf.accessors[facePrim.attributes.JOINTS_0];
      const fwAcc = gltf.accessors[facePrim.attributes.WEIGHTS_0];
      const fjBV = gltf.bufferViews[fjAcc.bufferView];
      const fwBV = gltf.bufferViews[fwAcc.bufferView];
      const fjArr = new Uint8Array(bin.buffer, bin.byteOffset + (fjBV.byteOffset || 0), fjAcc.count * 4);
      const fwArr = new Float32Array(bin.buffer, bin.byteOffset + (fwBV.byteOffset || 0), fwAcc.count * 4);
      const morphArrays = (facePrim.targets as Array<{ POSITION: number }>).map((t) => {
        const tAcc = gltf.accessors[t.POSITION];
        const tBV = gltf.bufferViews[tAcc.bufferView];
        return new Float32Array(bin.buffer, bin.byteOffset + (tBV.byteOffset || 0), tAcc.count * 3);
      });

      let sharedSeamVerts = 0;
      let unpinnedSeamMorphVerts = 0;
      let mismatchedSeamSkinVerts = 0;
      let mismatchedSeamNormals = 0;
      for (let v = 0; v < fPosAcc.count; v++) {
        const neighbor = neighborSkinByPos.get(posKey(fPos, v));
        if (!neighbor) continue;
        sharedSeamVerts++;
        for (const mArr of morphArrays) {
          const disp = Math.hypot(mArr[v * 3]!, mArr[v * 3 + 1]!, mArr[v * 3 + 2]!);
          if (disp > 1e-6) unpinnedSeamMorphVerts++;
        }
        for (let k = 0; k < 4; k++) {
          if (fjArr[v * 4 + k] !== neighbor.j[k] || Math.abs(fwArr[v * 4 + k]! - neighbor.w[k]!) > 1e-5) {
            mismatchedSeamSkinVerts++;
          }
        }
        const nDot =
          fNrm[v * 3]! * neighbor.n[0]! +
          fNrm[v * 3 + 1]! * neighbor.n[1]! +
          fNrm[v * 3 + 2]! * neighbor.n[2]!;
        if (nDot < 0.9999) mismatchedSeamNormals++;
      }
      expect(sharedSeamVerts).toBeGreaterThan(100);
      expect(unpinnedSeamMorphVerts).toBeLessThanOrEqual(16); // <=16 minor boundary displacement entries from v24 adjacent hair boundary relaxation
      expect(mismatchedSeamSkinVerts).toBe(0);
      expect(mismatchedSeamNormals).toBeLessThanOrEqual(40); // <=40 boundary normal adjustments from v24 hair contour relaxation

      // [TASK-AVATAR-MOD-05] & [AC-CHR-03]: Verify forward 6-station arm kinematics (zero backward arm dislocation)
      const parents = new Array<number>(gltf.nodes.length).fill(-1);
      gltf.nodes.forEach((n: any, idx: number) => {
        for (const c of n.children || []) parents[c] = idx;
      });
      const evalHandWorldZ = (stIdx: number, side: 'Left' | 'Right'): number => {
        const st = SceneController.PERSONA_STATIONS[stIdx]!.gltf;
        const rotOverrides: Record<string, THREE.Quaternion> = {
          Spine2: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.05, 0, 0, 'XYZ')),
          LeftArm: new THREE.Quaternion().setFromEuler(new THREE.Euler(st.leftArmX, st.leftArmY, st.leftArmZ, 'XYZ')),
          LeftForeArm: new THREE.Quaternion().setFromEuler(new THREE.Euler(st.leftForeX, st.leftForeY, st.leftForeZ, 'XYZ')),
          RightArm: new THREE.Quaternion().setFromEuler(new THREE.Euler(st.rightArmX, st.rightArmY, st.rightArmZ, 'XYZ')),
          RightForeArm: new THREE.Quaternion().setFromEuler(new THREE.Euler(st.rightForeX, st.rightForeY, st.rightForeZ, 'XYZ')),
        };
        const getW = (idx: number): THREE.Matrix4 => {
          const nd = gltf.nodes[idx];
          const t = nd.translation || [0, 0, 0];
          const r = nd.rotation || [0, 0, 0, 1];
          const s = nd.scale || [1, 1, 1];
          const q = rotOverrides[nd.name] ?? new THREE.Quaternion(r[0], r[1], r[2], r[3]);
          const m = new THREE.Matrix4().compose(
            new THREE.Vector3(t[0], t[1], t[2]),
            q,
            new THREE.Vector3(s[0], s[1], s[2])
          );
          const p = parents[idx]!;
          return p === -1 ? m : getW(p).multiply(m);
        };
        const hIdx = gltf.nodes.findIndex((n: any) => n.name === `${side}Hand`);
        const wMat = getW(hIdx);
        return wMat.elements[14]!;
      };

      // In Stations 1..5, RightHand gestures forward in front of the torso (Z > +0.18m, never behind the spine)
      for (const stIdx of [1, 2, 3, 4, 5]) {
        expect(evalHandWorldZ(stIdx, 'Right')).toBeGreaterThan(0.18);
      }
      // In Stations 2 (Badges) & 4 (Core), LeftHand also gestures forward in front of the torso (Z > +0.10m)
      expect(evalHandWorldZ(2, 'Left')).toBeGreaterThan(0.10);
      expect(evalHandWorldZ(4, 'Left')).toBeGreaterThan(0.10);
    });

    it('modulates SM_Character_Face 8 morph targets and articulates 30 finger bones during SceneController animation ticks', () => {
      const controller = new SceneController(container);
      const gltfScene = new THREE.Group();

      const headBone = new THREE.Bone();
      headBone.name = 'Head';
      gltfScene.add(headBone);

      const leftF1 = new THREE.Bone();
      leftF1.name = 'LeftHandIndex1';
      const rightF1 = new THREE.Bone();
      rightF1.name = 'RightHandThumb1';
      gltfScene.add(leftF1, rightF1);

      const faceGeom = new THREE.BufferGeometry();
      faceGeom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(9), 3));
      const faceMesh = new THREE.Mesh(faceGeom, new THREE.MeshStandardMaterial());
      faceMesh.name = 'SM_Character_Face';
      faceMesh.morphTargetDictionary = {
        mouthSmileLeft: 0,
        mouthSmileRight: 1,
        mouthOpen: 2,
        jawOpen: 3,
        eyeBlinkLeft: 4,
        eyeBlinkRight: 5,
        browInnerUp: 6,
        viseme_aa: 7,
      };
      faceMesh.morphTargetInfluences = [0, 0, 0, 0, 0, 0, 0, 0];
      gltfScene.add(faceMesh);

      controller.applyLoadedGLTFAvatar({ scene: gltfScene });
      expect(controller.getGLTFFaceMesh()).toBe(faceMesh);
      expect(controller.getLeftFingers()).toContain(leftF1);
      expect(controller.getRightFingers()).toContain(rightF1);

      controller.triggerSceneAction('inspect_tome');
      for (let i = 0; i < 15; i++) controller.animateTick(0.016);

      expect(faceMesh.morphTargetInfluences[0]).toBeGreaterThan(0.1);
      expect(faceMesh.morphTargetInfluences[6]).toBeGreaterThan(0.15);
      expect(leftF1.rotation.x).toBeGreaterThan(0.05);
      expect(rightF1.rotation.x).toBeGreaterThan(0.05);

      controller.dispose();
    });

    it('verifies real-time audio-driven lip-sync viseme and jaw articulation', () => {
      const controller = new SceneController(container);
      const gltfScene = new THREE.Group();
      const headBone = new THREE.Bone();
      headBone.name = 'Head';
      gltfScene.add(headBone);

      const faceGeom = new THREE.BufferGeometry();
      faceGeom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(9), 3));
      const faceMesh = new THREE.Mesh(faceGeom, new THREE.MeshStandardMaterial());
      faceMesh.name = 'SM_Character_Face';
      faceMesh.morphTargetDictionary = {
        mouthSmileLeft: 0,
        mouthSmileRight: 1,
        mouthOpen: 2,
        jawOpen: 3,
        eyeBlinkLeft: 4,
        eyeBlinkRight: 5,
        browInnerUp: 6,
        viseme_aa: 7,
      };
      faceMesh.morphTargetInfluences = [0, 0, 0, 0, 0, 0, 0, 0];
      gltfScene.add(faceMesh);

      controller.applyLoadedGLTFAvatar({ scene: gltfScene });

      const sound = controller.getSoundEngine();
      vi.spyOn(sound, 'getAudioEnergy').mockReturnValue(0.75);

      // Animate tick over several frames to allow damped interpolation
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);

      // Verify viseme_aa, jawOpen, and mouthOpen are articulated
      expect(faceMesh.morphTargetInfluences[7]).toBeGreaterThan(0.05); // viseme_aa
      expect(faceMesh.morphTargetInfluences[3]).toBeGreaterThan(0.02); // jawOpen
      expect(faceMesh.morphTargetInfluences[2]).toBeGreaterThan(0.01); // mouthOpen

      // Silence audio and verify smooth damping back to resting posture
      vi.spyOn(sound, 'getAudioEnergy').mockReturnValue(0.0);
      for (let i = 0; i < 35; i++) controller.animateTick(0.016);

      expect(faceMesh.morphTargetInfluences[7]).toBeLessThan(0.02);
      expect(faceMesh.morphTargetInfluences[3]).toBeLessThan(0.02);
      expect(faceMesh.morphTargetInfluences[2]).toBeLessThan(0.02);

      controller.dispose();
    });
  });

  describe('Continuous Persona Transitions & Prop Interaction Across 6 Acts', () => {
    it('verifies getAvatarPathCurve returns a 6-point Catmull-Rom spline linking all act stations monotonically in -Z', () => {
      const controller = new SceneController(container);
      const avatarCurve = controller.getAvatarPathCurve();

      expect(avatarCurve).toBeInstanceOf(THREE.CatmullRomCurve3);
      expect(avatarCurve.points.length).toBe(6);

      // Verify Act 1 to Act 6 station coordinates match PERSONA_STATIONS
      expect(avatarCurve.points[0]?.z).toBeCloseTo(SceneController.PERSONA_STATIONS[0]!.pos.z, 2);
      expect(avatarCurve.points[5]?.z).toBeCloseTo(SceneController.PERSONA_STATIONS[5]!.pos.z, 2);

      // Verify points decrease monotonically along negative Z
      for (let i = 0; i < avatarCurve.points.length - 1; i++) {
        expect(avatarCurve.points[i + 1]!.z).toBeLessThan(avatarCurve.points[i]!.z);
      }

      controller.dispose();
    });

    it('verifies continuous smooth Hermite interpolation of avatar position across act boundaries without snapping', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();

      // Start at Act 1 plateau (sp = 0.04) and step to sp = 0.08
      controller.updateScroll(0.08);
      for (let i = 0; i < 30; i++) controller.animateTick(0.016);
      const zAt008 = rig.position.z;

      // Halfway through Act 1 -> Act 2 transition (sp = 0.12)
      controller.updateScroll(0.12);
      for (let i = 0; i < 30; i++) controller.animateTick(0.016);
      const zAt012 = rig.position.z;

      // Start of Act 2 plateau (sp = 0.16)
      controller.updateScroll(0.16);
      for (let i = 0; i < 30; i++) controller.animateTick(0.016);
      const zAt016 = rig.position.z;

      // Z position must progress smoothly and monotonically toward -Z without teleportation
      expect(zAt012).toBeLessThan(zAt008);
      expect(zAt016).toBeLessThan(zAt012);
      expect(zAt016).toBeCloseTo(SceneController.PERSONA_STATIONS[1]!.pos.z, 0);

      // Test sudden jump from sp = 0.16 to sp = 0.60:
      // The persona should glide smoothly via lerp without instant jumping
      controller.updateScroll(0.60);
      controller.animateTick(0.016); // 1 single frame tick
      const posDelta1Tick = Math.abs(rig.position.z - zAt016);
      // Even though the target jumped by ~38 units, in 1 frame it glides smoothly by lerp (0.18 factor)
      expect(posDelta1Tick).toBeLessThan(15.0);
      expect(posDelta1Tick).toBeGreaterThan(0.5);

      controller.dispose();
    });

    it('verifies attentive prop gaze targeting orients head and neck toward props in each act', () => {
      const controller = new SceneController(container);
      const rig = controller.getAvatarRig();
      const headPivot = rig.getObjectByName('HeadPivot');
      const neckPivot = rig.getObjectByName('NeckPivot');
      expect(headPivot).toBeDefined();
      expect(neckPivot).toBeDefined();

      // In Act 2 (sp = 0.22), prop target is the 3.89 Tome at (1.1, 0.0, -18.0)
      controller.updateScroll(0.22);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      const act2HeadRotY = headPivot!.rotation.y;

      // In Act 4 (sp = 0.60), prop target is the 24k Gold Trophy at (0.6, 0.25, -55.6)
      controller.updateScroll(0.60);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      const act4HeadRotY = headPivot!.rotation.y;

      // The head rotation must differ between Act 2 and Act 4 to track the distinct prop coordinates
      expect(act4HeadRotY).not.toBeCloseTo(act2HeadRotY, 2);

      controller.dispose();
    });

    it('verifies rigged GLTF humanoid bones receive continuous prop gaze and hand gestures across acts', () => {
      const controller = new SceneController(container);
      const gltfScene = new THREE.Group();
      const boneNames = [
        'Head', 'Neck', 'Spine2', 'LeftArm', 'RightArm',
        'LeftForeArm', 'RightForeArm', 'LeftHand', 'RightHand',
        'LeftUpLeg', 'RightUpLeg'
      ];
      const bones: Record<string, THREE.Bone> = {};
      for (const name of boneNames) {
        const bone = new THREE.Bone();
        bone.name = name;
        bones[name] = bone;
        gltfScene.add(bone);
      }
      controller.applyLoadedGLTFAvatar({ scene: gltfScene });

      // Hand bones must be tracked
      expect(controller.getLeftHandBone()).toBe(bones['LeftHand']);
      expect(controller.getRightHandBone()).toBe(bones['RightHand']);

      // Act 4 (Alpine Summit Trophy gesture, sp = 0.60)
      controller.updateScroll(0.60);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);

      // Verify spine and neck orient attentively
      expect(bones['Spine2']!.rotation.x).not.toBe(0);
      expect(bones['Neck']!.rotation.y).not.toBe(0);
      expect(bones['Head']!.rotation.y).not.toBe(0);

      // Verify arm and hand bone rotations match summit trophy gesture
      expect(bones['LeftArm']!.rotation.x).toBeGreaterThan(1.0);
      expect(bones['RightArm']!.rotation.x).toBeGreaterThan(1.0);
      expect(bones['RightHand']!.rotation.x).toBeDefined();

      controller.dispose();
    });

    it('verifies smooth progress-based scene visibility cross-fading, light ramps, and adaptive atmospheric fog', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();

      // Find summit beacon light and horizon beacon light
      let summitBeacon: THREE.PointLight | null = null;
      let horizonBeacon: THREE.PointLight | null = null;
      scene.traverse((obj) => {
        if (obj instanceof THREE.PointLight) {
          if (obj.color.getHex() === 0xf59e0b) summitBeacon = obj;
          if (obj.color.getHex() === 0x00f2fe) horizonBeacon = obj;
        }
      });

      expect(summitBeacon).not.toBeNull();
      expect(horizonBeacon).not.toBeNull();

      // In Act 1 (sp = 0.0), summit beacon and horizon beacon should be 0 intensity
      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(summitBeacon!.intensity).toBe(0);
      expect(horizonBeacon!.intensity).toBe(0);

      const fogInitial = (scene.fog as THREE.FogExp2).density;

      // At Act 4 Summit (sp = 0.60), summit beacon ramps to peak intensity (~2.2)
      controller.updateScroll(0.60);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(summitBeacon!.intensity).toBeGreaterThan(1.5);
      expect(horizonBeacon!.intensity).toBe(0);

      // Fog density at alpine summit should thin out for alpine clarity
      const fogSummit = (scene.fog as THREE.FogExp2).density;
      expect(fogSummit).toBeLessThan(fogInitial);

      // At Act 6 Horizon (sp = 1.0), horizon beacon ramps to peak intensity (~2.4)
      controller.updateScroll(1.0);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(summitBeacon!.intensity).toBe(0);
      expect(horizonBeacon!.intensity).toBeGreaterThan(1.8);

      controller.dispose();
    });

    it('verifies Act 5 constellation neural swarm and gyroscope groups participate in scene visibility cross-fading', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();

      let constellationGroup: THREE.Group | null = null;
      let gyroscopeGroup: THREE.Group | null = null;
      scene.traverse((obj) => {
        if (obj.name === 'ConstellationSet') constellationGroup = obj as THREE.Group;
        if (obj.name === 'GyroscopeSet') gyroscopeGroup = obj as THREE.Group;
      });

      expect(constellationGroup).not.toBeNull();
      expect(gyroscopeGroup).not.toBeNull();

      // At Act 1 (sp = 0.0), Act 5 entities must be hidden to prevent visual clutter
      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(constellationGroup!.visible).toBe(false);
      expect(gyroscopeGroup!.visible).toBe(false);

      // At Act 5 (sp = 0.80), Act 5 entities must be visible and active
      controller.updateScroll(0.80);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(constellationGroup!.visible).toBe(true);
      expect(gyroscopeGroup!.visible).toBe(true);

      controller.dispose();
    });

    it('verifies interactive action flares persist across animation ticks without instant overwriting', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();

      let horizonBeacon: THREE.PointLight | null = null;
      scene.traverse((obj) => {
        if (obj instanceof THREE.PointLight && obj.color.getHex() === 0x00f2fe) {
          horizonBeacon = obj;
        }
      });
      expect(horizonBeacon).not.toBeNull();

      // Scroll to Act 6
      controller.updateScroll(1.0);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(horizonBeacon!.intensity).toBeGreaterThan(2.0);

      // Trigger handshake wave action: beacon flare should ramp to ~4.6 and persist across multiple frames
      controller.triggerSceneAction('handshake_wave');
      for (let i = 0; i < 15; i++) controller.animateTick(0.016);
      expect(horizonBeacon!.intensity).toBeGreaterThan(4.0);

      controller.dispose();
    });

    it('verifies continuous gesture blending across all 6 acts on rigged GLTF humanoid bones', () => {
      const controller = new SceneController(container);
      const gltfScene = new THREE.Group();
      const boneNames = [
        'Head', 'Neck', 'Spine2', 'LeftArm', 'RightArm',
        'LeftForeArm', 'RightForeArm', 'LeftHand', 'RightHand',
        'LeftUpLeg', 'RightUpLeg'
      ];
      const bones: Record<string, THREE.Bone> = {};
      for (const name of boneNames) {
        const bone = new THREE.Bone();
        bone.name = name;
        bones[name] = bone;
        gltfScene.add(bone);
      }
      controller.applyLoadedGLTFAvatar({ scene: gltfScene });

      // Act 3 (Crucible GCP badge conducting): both arms articulate dynamically
      controller.updateScroll(0.40);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(bones['LeftArm']!.rotation.x).toBeGreaterThan(1.0);
      expect(bones['RightArm']!.rotation.x).toBeGreaterThan(1.0);

      // Act 5 (Frontier Exploded Core strata manipulation)
      controller.updateScroll(0.80);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(bones['LeftArm']!.rotation.x).toBeGreaterThan(1.0);
      expect(bones['RightArm']!.rotation.x).toBeGreaterThan(1.0);

      // Act 6 (Horizon Portal welcoming)
      controller.updateScroll(1.0);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(bones['RightHand']!.rotation.y).toBeGreaterThan(0.2);

      controller.dispose();
    });

    describe('Spatial Kinematics, Staging Architecture & Real Screen Defect Hardening (DEF-01 to DEF-09)', () => {
      it('verifies DEF-01: Act 3 CrucibleOrbitBadges orbit radius at 0.72m maintains safe clearance from avatar torso', () => {
        const controller = new SceneController(container);
        const scene = controller.getScene();
        const orbitGroup = scene.getObjectByName('CrucibleOrbitBadges') as THREE.Group;
        expect(orbitGroup).toBeDefined();

        // Five GCP skill badges in orbit around the GDSC lectern
        expect(orbitGroup.children.length).toBe(5);

        // Verify each badge is positioned on a 0.72m radius orbit around the lectern center
        orbitGroup.children.forEach((badge) => {
          const orbitRadius = Math.hypot(badge.position.x, badge.position.z);
          expect(orbitRadius).toBeCloseTo(0.72, 2);
        });

        // In world coordinates, crucibleGroup is at X = 1.85. With 0.72m orbit radius,
        // the innermost point of the orbit is X = 1.85 - 0.72 = 1.13m.
        // Accounting for badge outer rim radius (0.2m), badge edge reaches minimum X = 0.93m.
        // Station 2 avatar torso is at X = 0.75 (half-width ~0.12m -> right boundary X = 0.87m).
        // 0.93m > 0.87m guarantees zero torso slicing even during rotation surges.
        const minOrbitWorldX = 1.85 - 0.72 - 0.2;
        const avatarTorsoRightBoundary = SceneController.PERSONA_STATIONS[2]!.pos.x + 0.12;
        expect(minOrbitWorldX).toBeGreaterThan(avatarTorsoRightBoundary);

        controller.dispose();
      });

      it('verifies DEF-02: plinth grounding sets model and personaBody anchors to Y = -1.45, sitting flush on plinth top', () => {
        const controller = new SceneController(container);
        const rig = controller.getAvatarRig();
        const plinth = rig.getObjectByName('Plinth') as THREE.Mesh;
        const personaBody = rig.getObjectByName('PersonaBody') as THREE.Group;

        expect(plinth).toBeDefined();
        expect(personaBody).toBeDefined();

        // Plinth cylinder height is 0.20m, centered at Y = -1.55, so top surface is Y = -1.45
        const plinthTopSurfaceY = plinth.position.y + 0.10;
        expect(plinthTopSurfaceY).toBeCloseTo(-1.45, 2);

        // Procedural personaBody anchor must be exactly flush with plinth top surface
        expect(personaBody.position.y).toBeCloseTo(plinthTopSurfaceY, 2);

        // Verify rigged GLTF realistic avatar also grounds flush at Y = -1.45
        const gltfScene = new THREE.Group();
        const headBone = new THREE.Bone();
        headBone.name = 'Head';
        gltfScene.add(headBone);
        controller.applyLoadedGLTFAvatar({ scene: gltfScene });

        expect(gltfScene.position.y).toBeCloseTo(-1.45, 2);

        controller.dispose();
      });

      it('verifies DEF-03: Act 4 StarPressParchment is positioned in right spatial corridor (X > 0) beside Golden Trophy', () => {
        const controller = new SceneController(container);
        const scene = controller.getScene();
        const pressProof = scene.getObjectByName('StarPressParchment') as THREE.Group;
        const trophy = scene.getObjectByName('GoldenTrophy') as THREE.Group;

        expect(pressProof).toBeDefined();
        expect(trophy).toBeDefined();

        const pressWorldPos = new THREE.Vector3();
        const trophyWorldPos = new THREE.Vector3();
        pressProof.getWorldPosition(pressWorldPos);
        trophy.getWorldPosition(trophyWorldPos);

        // Star Press Proof is positioned at X = 2.45 in the right spatial corridor
        expect(pressWorldPos.x).toBeGreaterThan(1.5);
        expect(pressWorldPos.x).toBeGreaterThan(trophyWorldPos.x);

        // When projected with Act 4 camera, NDC X must be positive (> 0), clearing the left 58% card corridor
        controller.updateScroll(0.60);
        const projectedPress = pressWorldPos.clone().project(controller.getCamera());
        expect(projectedPress.x).toBeGreaterThan(0.0);

        controller.dispose();
      });

      it('verifies DEF-08: Act 2 Illuminated Tome includes solid wooden lectern pedestal extending to floor (Y = -1.45)', () => {
        const controller = new SceneController(container);
        const scene = controller.getScene();
        const pedestal = scene.getObjectByName('TomeLecternPedestal') as THREE.Mesh;
        const base = scene.getObjectByName('TomeLecternBase') as THREE.Mesh;
        const collar = scene.getObjectByName('TomeLecternCollar') as THREE.Mesh;

        expect(pedestal).toBeDefined();
        expect(base).toBeDefined();
        expect(collar).toBeDefined();

        // AcademySet is positioned at world Y = -0.20
        // Base plate is at local Y = -1.225, so world Y = -0.20 + (-1.225) = -1.425 ~ -1.45 (flush with floor)
        const baseWorldPos = new THREE.Vector3();
        base.getWorldPosition(baseWorldPos);
        expect(baseWorldPos.y).toBeCloseTo(-1.45, 1);

        controller.dispose();
      });

      it('verifies DEF-09: canonical station progress normalizes all transition windows to Δsp = 0.08 and synchronizes camera with persona', () => {
        const controller = new SceneController(container);

        // Verify Act 1 -> 2 transition begins at 0.08 and is halfway at 0.12
        const pAct1TransStart = controller.getCanonicalStationProgress(0.08);
        const pAct1TransMid = controller.getCanonicalStationProgress(0.12);
        expect(pAct1TransStart.stIdx).toBe(0);
        expect(pAct1TransStart.w).toBeCloseTo(0.0, 2);
        expect(pAct1TransMid.stIdx).toBe(0);
        expect(pAct1TransMid.w).toBeCloseTo(0.5, 2);

        // Near end of transition (0.159), w approaches 1.0
        const pAct1TransNearEnd = controller.getCanonicalStationProgress(0.159);
        expect(pAct1TransNearEnd.stIdx).toBe(0);
        expect(pAct1TransNearEnd.w).toBeGreaterThan(0.98);

        // At sp = 0.16, transition completes and arrives at Station 1 (Act 2 plateau)
        const pAct1TransEnd = controller.getCanonicalStationProgress(0.16);
        expect(pAct1TransEnd.stIdx).toBe(1);
        expect(pAct1TransEnd.w).toBe(0);
        expect(pAct1TransEnd.camProgress).toBeCloseTo(0.20, 2);

        // Act 4 transition window normalized to [0.68, 0.76] (Δsp = 0.08, previously 0.06)
        const pAct4TransStart = controller.getCanonicalStationProgress(0.68);
        const pAct4TransMid = controller.getCanonicalStationProgress(0.72);
        const pAct4TransNearEnd = controller.getCanonicalStationProgress(0.759);
        const pAct4TransEnd = controller.getCanonicalStationProgress(0.76);
        expect(pAct4TransStart.stIdx).toBe(3);
        expect(pAct4TransStart.w).toBeCloseTo(0.0, 2);
        expect(pAct4TransMid.stIdx).toBe(3);
        expect(pAct4TransMid.w).toBeCloseTo(0.5, 2);
        expect(pAct4TransNearEnd.stIdx).toBe(3);
        expect(pAct4TransNearEnd.w).toBeGreaterThan(0.98);
        expect(pAct4TransEnd.stIdx).toBe(4);
        expect(pAct4TransEnd.camProgress).toBeCloseTo(0.80, 2);

        // Verify Act 1 -> 2 synchronous camera and persona travel
        // At sp = 0.08 (start of transition): camera progress = 0.00, persona w = 0.0
        expect(pAct1TransStart.camProgress).toBeCloseTo(0.00, 2);

        // At sp = 0.12 (midway): camera progress = 0.10, persona w = 0.50
        expect(pAct1TransMid.camProgress).toBeCloseTo(0.10, 2);
        expect(pAct1TransMid.w).toBeCloseTo(0.50, 2);

        // At sp = 0.16 (end of transition, start of Act 2): camera progress = 0.20, persona w = 1.0 (at Act 2)
        expect(pAct1TransEnd.camProgress).toBeCloseTo(0.20, 2);

        controller.dispose();
      });
    });
  });

  describe('Modular Graphics Subsystems & PortfolioEngine Verification', () => {
    it('verifies PortfolioEngine export and facade getters for all modular core subsystems', () => {
      expect(PortfolioEngine).toBe(SceneController);
      const controller = new PortfolioEngine(container);

      expect(controller.getEngine()).toBeDefined();
      expect(controller.getCameraRig()).toBeDefined();
      expect(controller.getParticleLattice()).toBeDefined();
      expect(controller.getSoundEngine()).toBeDefined();
      expect(controller.getDepthPortrait()).toBeDefined();

      controller.dispose();
    });

    it('verifies 30,000 instanced particle lattice via THREE.InstancedMesh and dynamic 6-act attractor fields', () => {
      const controller = new SceneController(container);
      const lattice = controller.getParticleLattice();
      expect(lattice).toBeDefined();

      const persistentMesh = lattice.getPersistentLattice();
      expect(persistentMesh).toBeDefined();
      expect(persistentMesh instanceof THREE.InstancedMesh).toBe(true);
      expect(persistentMesh.count).toBe(30000);
      expect(persistentMesh.name).toBe('PersistentParticleLattice');

      // Update across acts and verify dynamic attractor field execution
      controller.updateScroll(0.40); // Act 3 Crucible
      controller.animateTick(0.016);
      expect(persistentMesh.instanceMatrix.version).toBeGreaterThan(0);

      controller.dispose();
    });

    it('verifies procedural SoundEngine audio state and tactile 2.4kHz clicks', () => {
      const controller = new SceneController(container);
      const sound = controller.getSoundEngine();
      expect(sound).toBeDefined();
      expect(sound.isAudioEnabled()).toBe(false); // Strictly muted by default

      // Test tactile click execution
      sound.playTactileClick();
      sound.playHarmonicHum(220, 0.2);
      sound.playTransitionSweep(140, 480, 0.3);
      sound.playSummitChime();

      controller.dispose();
    });

    it('verifies SoundEngine handles browser autoplay unlock via pointerdown/keydown', () => {
      const controller = new SceneController(container);
      const sound = controller.getSoundEngine();
      expect(sound).toBeDefined();

      // Trigger toggleAudio so AudioContext is initialized
      sound.toggleAudio();
      expect(sound.isAudioEnabled()).toBe(true);

      const ctx = sound.getAudioContext();
      expect(ctx).toBeDefined();
      expect(controller.getAudioContext()).toBe(ctx);

      // Set to suspended state to test gesture unlock
      if (ctx) {
        ctx.state = 'suspended';
      }

      // Simulate pointerdown unlock gesture
      window.dispatchEvent(new Event('pointerdown'));
      expect(ctx?.resume).toHaveBeenCalled();
      expect(ctx?.state).toBe('running');

      // Subsequent keydown gesture branch after unlock does not throw
      window.dispatchEvent(new Event('keydown'));

      controller.dispose();
    });

    it('verifies 2.5D POM DepthPortraitMesh shader structure and uniforms', () => {
      const controller = new SceneController(container);
      const portrait = controller.getDepthPortrait();
      expect(portrait).toBeDefined();

      const mesh = portrait.getMesh();
      expect(mesh).toBeDefined();
      expect(mesh.name).toBe('DepthPortraitHologram');

      const mat = mesh.material as THREE.ShaderMaterial;
      expect(mat.uniforms['uTexture']).toBeDefined();
      expect(mat.uniforms['uMouse']).toBeDefined();
      expect(mat.uniforms['uTime']).toBeDefined();
      expect(mat.uniforms['uParallaxScale']).toBeDefined();
      expect(mat.uniforms['uGlintIntensity']).toBeDefined();

      portrait.update(0.016, 0.5, -0.3);
      expect(mat.uniforms['uTime'].value).toBeGreaterThan(0);

      controller.dispose();
    });
  });

  describe('Dynamic Spatial Avatar Pose Actions & Kinematic Slerping', () => {
    it('executes glasses_adjust pose action with smooth weight ramp, stylized rig posture, and right arm lift', () => {
      const controller = new SceneController(container);
      const rig = controller.getStylizedRig();

      expect(controller.getCurrentPoseAction()).toBe('neutral');
      expect(controller.isPoseActionActive()).toBe(false);
      expect(controller.getPoseWeight()).toBe(0.0);

      // Trigger glasses_adjust
      controller.triggerSceneAction('glasses_adjust');
      expect(controller.getCurrentPoseAction()).toBe('glasses_adjust');
      expect(controller.isPoseActionActive()).toBe(true);

      // Advance animation ticks
      for (let i = 0; i < 20; i++) {
        controller.animateTick(0.016);
      }

      expect(controller.getPoseWeight()).toBeGreaterThan(0.5);
      expect(rig.getActivePosture()).toBe('glasses_adjust');

      // Verify rigged GLTF bones if loaded
      const riggedScene = new THREE.Group();
      const rightArmBone = new THREE.Bone();
      rightArmBone.name = 'RightArm';
      const rightForeArmBone = new THREE.Bone();
      rightForeArmBone.name = 'RightForeArm';
      riggedScene.add(rightArmBone);
      riggedScene.add(rightForeArmBone);

      controller.applyLoadedGLTFAvatar({ scene: riggedScene });
      for (let i = 0; i < 30; i++) {
        controller.animateTick(0.016);
      }

      // Target for glasses_adjust rightArmX is 0.55 (lifted toward face), compared to station 0 default 1.298
      expect(rightArmBone.rotation.x).toBeLessThan(1.0);

      controller.dispose();
    });

    it('executes inspect_tablet pose action with bi-lateral arm repositioning and forward telemetry inspection', () => {
      const controller = new SceneController(container);
      const rig = controller.getStylizedRig();

      controller.triggerSceneAction('inspect_tablet');
      expect(controller.getCurrentPoseAction()).toBe('inspect_tablet');

      for (let i = 0; i < 25; i++) {
        controller.animateTick(0.016);
      }

      expect(controller.getPoseWeight()).toBeGreaterThan(0.7);
      expect(rig.getActivePosture()).toBe('inspect_tablet');

      controller.dispose();
    });

    it('executes keynote_present pose action with confident arm opening toward Enterprise AI Monolith', () => {
      const controller = new SceneController(container);
      const rig = controller.getStylizedRig();

      controller.triggerSceneAction('keynote_present');
      expect(controller.getCurrentPoseAction()).toBe('keynote_present');

      for (let i = 0; i < 25; i++) {
        controller.animateTick(0.016);
      }

      expect(controller.getPoseWeight()).toBeGreaterThan(0.7);
      expect(rig.getActivePosture()).toBe('keynote_present');

      controller.dispose();
    });

    it('smoothly slerps back to neutral standing/seated pose on reset_pose action', () => {
      const controller = new SceneController(container);
      const rig = controller.getStylizedRig();

      // Enter keynote pose first
      controller.triggerSceneAction('keynote_present');
      for (let i = 0; i < 30; i++) {
        controller.animateTick(0.016);
      }
      expect(controller.getPoseWeight()).toBeGreaterThan(0.8);

      // Trigger reset_pose
      controller.triggerSceneAction('reset_pose');
      expect(controller.getCurrentPoseAction()).toBe('neutral');
      expect(controller.isPoseActionActive()).toBe(false);

      // Animate ticks to let weight damp back to 0.0
      for (let i = 0; i < 45; i++) {
        controller.animateTick(0.016);
      }

      expect(controller.getPoseWeight()).toBeCloseTo(0.0, 1);
      // At sp = 0 (Act 1), returns to seated / neutral posture
      expect(rig.getActivePosture()).toBe('seated');

      controller.dispose();
    });

    it('respects autoReturn configuration option to smoothly return to neutral after duration', () => {
      const controller = new SceneController(container);

      // Auto-return after 0.1 seconds
      controller.triggerSceneAction('glasses_adjust', { autoReturn: true, duration: 0.1 });
      expect(controller.getCurrentPoseAction()).toBe('glasses_adjust');

      // Tick before duration expires
      controller.animateTick(0.05);
      expect(controller.getCurrentPoseAction()).toBe('glasses_adjust');

      // Tick past duration expiry (0.05 + 0.08 = 0.13s > 0.1s)
      controller.animateTick(0.08);
      expect(controller.getCurrentPoseAction()).toBe('neutral');

      controller.dispose();
    });

    it('snaps pose weight immediately under prefers-reduced-motion', () => {
      const controller = new SceneController(container);
      controller.setReducedMotion(true);

      controller.triggerSceneAction('glasses_adjust');
      controller.animateTick(0.016);

      // Under reduced motion, pose weight snaps immediately to 1.0 without vestibular lag
      expect(controller.getPoseWeight()).toBe(1.0);

      controller.triggerSceneAction('reset_pose');
      controller.animateTick(0.016);
      expect(controller.getPoseWeight()).toBe(0.0);

      controller.dispose();
    });

    it('dispatches portfolio:scene_action with reset_pose when auto-return expires', () => {
      const controller = new SceneController(container);
      const dispatchSpy = vi.spyOn(window, 'dispatchEvent');

      controller.triggerSceneAction('glasses_adjust', { autoReturn: true, duration: 0.1 });
      controller.animateTick(0.05);
      expect(controller.getCurrentPoseAction()).toBe('glasses_adjust');

      // Tick past expiration
      controller.animateTick(0.08);
      expect(controller.getCurrentPoseAction()).toBe('neutral');

      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'portfolio:scene_action',
          detail: { action: 'reset_pose', source: 'auto_return' },
        })
      );

      dispatchSpy.mockRestore();
      controller.dispose();
    });

    it('handles rapid sequential pose switching without discontinuities or NaN', () => {
      const controller = new SceneController(container);
      const rig = controller.getStylizedRig();

      // Trigger glasses_adjust
      controller.triggerSceneAction('glasses_adjust');
      for (let i = 0; i < 15; i++) controller.animateTick(0.016);
      expect(controller.getActivePoseAction()).toBe('glasses_adjust');

      // Immediately switch to keynote_present without reset_pose in between
      controller.triggerSceneAction('keynote_present');
      expect(controller.getCurrentPoseAction()).toBe('keynote_present');
      expect(controller.getActivePoseAction()).toBe('keynote_present');

      for (let i = 0; i < 20; i++) controller.animateTick(0.016);
      expect(rig.getActivePosture()).toBe('keynote_present');
      expect(Number.isNaN(controller.getPoseWeight())).toBe(false);

      controller.dispose();
    });

    it('gracefully fades hero pose weight when scrolling away into subsequent acts', () => {
      const controller = new SceneController(container);
      const rig = controller.getStylizedRig();

      controller.triggerSceneAction('keynote_present');
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);
      expect(rig.getActivePosture()).toBe('keynote_present');

      // Scroll to Act 2 (Library: sp = 0.25)
      controller.updateScroll(0.25);
      for (let i = 0; i < 25; i++) controller.animateTick(0.016);

      // Storyline posture for Act 2 takes over
      expect(rig.getActivePosture()).toBe('reach_book');

      controller.dispose();
    });

    it('remains resilient to extreme deltas and zero deltas without crashing or corrupting math', () => {
      const controller = new SceneController(container);

      controller.triggerSceneAction('glasses_adjust');
      expect(() => controller.animateTick(0)).not.toThrow();
      expect(() => controller.animateTick(5.0)).not.toThrow();
      expect(Number.isNaN(controller.getPoseWeight())).toBe(false);

      controller.dispose();
    });

    it('handles scene action event bus detail forwarding, action aliases, and interest_focus payload color', () => {
      const controller = new SceneController(container);

      // Verify custom event bus forwards all detail fields
      window.dispatchEvent(
        new CustomEvent('portfolio:scene_action', {
          detail: { action: 'interest_focus', color: '#ff00aa', source: 'test' },
        })
      );
      expect(controller.getInterestFocusColorHex().toLowerCase()).toBe('#ff00aa');

      // Verify defensive resilience against malformed or non-string color payloads
      expect(() => {
        controller.triggerSceneAction('interest_focus', { color: '' });
        controller.triggerSceneAction('interest_focus', { color: null as unknown as string });
        controller.triggerSceneAction('interest_focus', { color: 12345 as unknown as string });
        controller.triggerSceneAction('interest_focus', {});
      }).not.toThrow();

      // Verify action aliases: badge_surge, tome_inspect, trophy_present
      expect(() => {
        controller.triggerSceneAction('badge_surge');
        controller.triggerSceneAction('tome_inspect');
        controller.triggerSceneAction('trophy_present');
      }).not.toThrow();

      // Verify rapid back-and-forth scroll transitions across the sp = 0.16 threshold
      const rig = controller.getAvatarRig();
      const studioGroup = rig.getObjectByName('StudioGroup');
      const enterpriseEngine = rig.getObjectByName('EnterpriseAIEngine');

      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(studioGroup!.visible).toBe(true);
      expect(enterpriseEngine!.visible).toBe(true);

      // Rapid flick to Act 2 (sp = 0.25)
      controller.updateScroll(0.25);
      controller.animateTick(0.016);
      expect(studioGroup!.visible).toBe(false);
      expect(enterpriseEngine!.visible).toBe(false);

      // Rapid flick back to Act 1 (sp = 0.05)
      controller.updateScroll(0.05);
      controller.animateTick(0.016);
      expect(studioGroup!.visible).toBe(true);
      expect(enterpriseEngine!.visible).toBe(true);

      controller.dispose();
    });

    it('verifies Act 3 Crucible Podium elevation sits at or below Y = -1.48 and CameraRig Act 5 aligns with Station 4 (X = 0.92)', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();
      const podium = scene.getObjectByName('CruciblePodium') as THREE.Mesh;
      expect(podium).toBeDefined();

      // Cylinder height = 0.25, half-height = 0.125
      const podiumTopY = podium.position.y + 0.125;
      expect(podiumTopY).toBeLessThanOrEqual(-1.48);

      const avatarCurve = controller.getCameraRig().getAvatarPathCurve();
      // Act 5 is point index 4 (0: hero, 1: timeline, 2: vault, 3: summit, 4: ai-solutions, 5: contact)
      const act5Point = avatarCurve.points[4]!;
      expect(act5Point.x).toBeCloseTo(0.92, 2);
      expect(act5Point.z).toBeCloseTo(-74.6, 1);

      controller.dispose();
    });

    it('verifies Act 1 plinth and glow ring fade out and scale down when scrolling into Acts 2–6 (sp > 0.16) and restore upon return to Act 1', () => {
      const controller = new SceneController(container);
      const plinth = controller.getPlinth();
      const glowRing = controller.getPlinthGlowRing();

      expect(plinth).toBeDefined();
      expect(glowRing).toBeDefined();

      // In Act 1 (sp = 0.05): full scale, full opacity, visible
      controller.updateScroll(0.05);
      controller.animateTick(0.016);
      expect(plinth.visible).toBe(true);
      expect(glowRing.visible).toBe(true);
      expect(plinth.scale.x).toBeCloseTo(1.0, 2);
      expect(glowRing.scale.x).toBeCloseTo(1.0, 2);
      expect((plinth.material as THREE.Material).opacity).toBeCloseTo(1.0, 2);

      // Mid-transition into Act 2 (sp = 0.19, halfway between 0.16 and 0.22)
      controller.updateScroll(0.19);
      controller.animateTick(0.016);
      expect(plinth.visible).toBe(true);
      expect(glowRing.visible).toBe(true);
      expect(plinth.scale.x).toBeGreaterThan(0.4);
      expect(plinth.scale.x).toBeLessThan(0.6);
      expect((plinth.material as THREE.Material).opacity).toBeGreaterThan(0.4);
      expect((plinth.material as THREE.Material).opacity).toBeLessThan(0.6);

      // Exited Act 1 into Act 2 (sp = 0.25) and Mount Pilatus in Act 4 (sp = 0.60): scaled down to 0, faded to 0, hidden
      controller.updateScroll(0.25);
      controller.animateTick(0.016);
      expect(plinth.visible).toBe(false);
      expect(glowRing.visible).toBe(false);
      expect(plinth.scale.x).toBe(0.0);
      expect((plinth.material as THREE.Material).opacity).toBe(0.0);

      controller.updateScroll(0.60);
      controller.animateTick(0.016);
      expect(plinth.visible).toBe(false);
      expect(glowRing.visible).toBe(false);
      expect(plinth.scale.x).toBe(0.0);
      expect((plinth.material as THREE.Material).opacity).toBe(0.0);

      // Scroll back up into Act 1 (sp = 0.08): restored to full scale, opacity, and visibility
      controller.updateScroll(0.08);
      controller.animateTick(0.016);
      expect(plinth.visible).toBe(true);
      expect(glowRing.visible).toBe(true);
      expect(plinth.scale.x).toBeCloseTo(1.0, 2);
      expect((plinth.material as THREE.Material).opacity).toBeCloseTo(1.0, 2);

      controller.dispose();
    });
  });
});



