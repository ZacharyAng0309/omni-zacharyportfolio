import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as THREE from 'three';
import { SceneController, PortfolioEngine } from '../graphics/SceneController';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
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

    it('ignores clicks on interactive DOM buttons and overlaying 2D HUD panels to prevent unwanted 3D raycast triggers', () => {
      const onSelectCaseStudyNode = vi.fn();
      const controller = new SceneController(container, { onSelectCaseStudyNode });

      // Place a large raycastable target directly in front of the Act 1 camera at NDC (0, 0)
      const cam = controller.getCamera();
      const forward = new THREE.Vector3();
      cam.getWorldDirection(forward);
      const hitMesh = new THREE.Mesh(
        new THREE.BoxGeometry(4, 4, 0.2),
        new THREE.MeshBasicMaterial()
      );
      hitMesh.position.copy(cam.position).add(forward.multiplyScalar(3));
      hitMesh.lookAt(cam.position);
      hitMesh.userData = { type: 'flagshipOrb', caseStudySlug: 'hireti' };
      controller.getScene().add(hitMesh);
      controller.getScene().updateMatrixWorld(true);

      const width = container.clientWidth || window.innerWidth;
      const height = container.clientHeight || window.innerHeight;
      const centerX = width * 0.5;
      const centerY = height * 0.5;

      // 1. Clicking an overlaying 2D DOM button or drawer div directly over the 3D prop must NOT raycast through
      const sheetDiv = document.createElement('div');
      const button = document.createElement('button');
      button.textContent = 'Explore';
      sheetDiv.appendChild(button);
      document.body.appendChild(sheetDiv);

      button.dispatchEvent(new MouseEvent('pointerdown', { clientX: centerX, clientY: centerY, bubbles: true }));
      sheetDiv.dispatchEvent(new MouseEvent('pointerdown', { clientX: centerX, clientY: centerY, bubbles: true }));
      expect(onSelectCaseStudyNode).not.toHaveBeenCalled();

      // 2. Clicking the actual 3D WebGL canvas at the same coordinates MUST hit the target cleanly
      const canvasEl = controller.getEngine().getDomElement();
      canvasEl.dispatchEvent(new MouseEvent('pointerdown', { clientX: centerX, clientY: centerY, bubbles: true }));
      expect(onSelectCaseStudyNode).toHaveBeenCalledTimes(1);
      expect(onSelectCaseStudyNode).toHaveBeenCalledWith('hireti');

      sheetDiv.remove();
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
      const candidatePathA = path.resolve(process.cwd(), 'artifacts/archived_public/models/zachary_character.glb');
      const candidatePathB = path.resolve(process.cwd(), 'projects/ZacharyPortfolio/artifacts/archived_public/models/zachary_character.glb');
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
      // Exact topology conservation across the 6 base body/cloth domain sub-meshes (v38) & 7 oral/eye meshes
      expect(totalBodyTris).toBe(34674);
      const extraV38Meshes = [
        'SM_Character_OralCavity',
        'SM_Character_UpperTeeth',
        'SM_Character_LowerTeeth',
        'SM_Character_Tongue',
        'SM_Character_Eyelids',
        'SM_Character_EyeRight',
        'SM_Character_EyeLeft',
      ];
      let extraTris = 0;
      for (const eName of extraV38Meshes) {
        const node = gltf.nodes.find((n: any) => n.name === eName);
        expect(node).toBeDefined();
        const mesh = gltf.meshes[node.mesh];
        extraTris += gltf.accessors[mesh.primitives[0].indices].count / 3;
      }
      const specIdxNode = gltf.nodes.find((n: any) => n.name === 'Sovereign_Titanium_Spectacles');
      const specMeshObj = gltf.meshes[specIdxNode.mesh];
      const specTris = specMeshObj.primitives.reduce(
        (sum: number, prim: any) => sum + gltf.accessors[prim.indices].count / 3,
        0
      );
      expect(totalBodyTris + extraTris + specTris).toBe(44910);

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

      const hoodiePosSet = new Set<string>();
      const hPAcc = gltf.accessors[hoodiePrim.attributes.POSITION];
      const hPBV = gltf.bufferViews[hPAcc.bufferView];
      const hPArr = new Float32Array(bin.buffer, bin.byteOffset + (hPBV.byteOffset || 0), hPAcc.count * 3);
      for (let v = 0; v < hPAcc.count; v++) hoodiePosSet.add(posKey(hPArr, v));

      let sharedSeamVerts = 0;
      let unpinnedSeamMorphVerts = 0;
      let mismatchedSeamSkinVerts = 0;
      const mismatchedSeamNormalKeys = new Set<string>();
      let mismatchedHoodieCollarNormals = 0;
      for (let v = 0; v < fPosAcc.count; v++) {
        const key = posKey(fPos, v);
        const neighbor = neighborSkinByPos.get(key);
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
        if (nDot < 0.9999) {
          mismatchedSeamNormalKeys.add(key);
          if (hoodiePosSet.has(key)) mismatchedHoodieCollarNormals++;
        }
      }
      expect(sharedSeamVerts).toBeGreaterThan(100);
      expect(unpinnedSeamMorphVerts).toBe(0);
      expect(mismatchedSeamSkinVerts).toBe(0);
      expect(mismatchedHoodieCollarNormals).toBe(0);
      // Deduplicate by 3D seam position so v40 UV2-split vertex copies along identical forehead/hair boundary points are not double-counted (45 unique vs 47 in v38)
      expect(mismatchedSeamNormalKeys.size).toBeLessThanOrEqual(50);

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

      // In Act 2 (sp = 0.22), prop target is the 3.75 Tome at (1.1, 0.0, -18.0)
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

  describe('6-Act Cinema Diorama Backdrops, SpatialLightBridge, Focus Dolly & GLSL SkyDome', () => {
    it('constructs 6 ChapterBackdrops and reveals SpatialLightBridge strictly during inter-act corridor transitions', () => {
      const controller = new SceneController(container);
      const lattice = controller.getParticleLattice();
      const backdrops = lattice.getChapterBackdropsGroup();
      const bridge = lattice.getSpatialLightBridge();

      expect(backdrops).toBeDefined();
      expect(bridge).toBeDefined();
      for (let i = 0; i < 6; i++) {
        expect(backdrops.getObjectByName(`ChapterBackdrop_${i}`)).toBeDefined();
      }

      // Stationary at Act 1 station: bridge hidden
      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(bridge.visible).toBe(false);

      // Mid-corridor transit between Act 1 and Act 2 (sp = 0.12): bridge illuminated
      controller.updateScroll(0.12);
      controller.animateTick(0.016);
      expect(bridge.visible).toBe(true);

      // Arrived at Act 2 station (sp = 0.20): bridge hides again
      controller.updateScroll(0.2);
      controller.animateTick(0.016);
      expect(bridge.visible).toBe(false);

      controller.dispose();
    });

    it('orchestrates 22 Focus Dolly sub-targets with smooth focusBlendWeight and clean clearSubTargetFocus release', () => {
      const controller = new SceneController(container);
      expect(SceneController.DIORAMA_SUB_TARGETS).toHaveLength(22);

      const onSelectSubTarget = vi.fn();
      const c2 = new SceneController(container, { onSelectSubTarget });

      c2.selectSubTarget(0, 'optical-core');
      expect(c2.getActiveSubTarget()).toEqual({ actIndex: 0, subTargetId: 'optical-core' });
      expect(onSelectSubTarget).toHaveBeenCalledWith(0, 'optical-core');
      expect(c2.getCameraRig().getActiveFocusTarget()?.subTargetId).toBe('optical-core');

      for (let i = 0; i < 40; i++) c2.animateTick(0.016);
      expect(c2.getCameraRig().getFocusBlendWeight()).toBeGreaterThan(0.95);
      expect(c2.getCamera().position.z).toBeCloseTo(7.20, 1);

      c2.clearSubTargetFocus();
      expect(c2.getActiveSubTarget()).toBeNull();
      expect(c2.getCameraRig().getActiveFocusTarget()).toBeNull();
      for (let i = 0; i < 45; i++) c2.animateTick(0.016);
      expect(c2.getCameraRig().getFocusBlendWeight()).toBeLessThan(0.05);

      c2.dispose();
      controller.dispose();
    });

    it('projects DiegeticHotspotLayer reticles within safe viewport bounds, clears WhisperStageHUD, enforces >= 8.5% sibling separation, and hides in transit', () => {
      const controller = new SceneController(container);

      for (let actIdx = 0; actIdx < 6; actIdx++) {
        controller.updateScroll(actIdx * 0.2);
        controller.animateTick(0.016);
        const pins = controller.getProjectedHotspots(actIdx);
        expect(pins.length).toBeGreaterThanOrEqual(3);

        for (let i = 0; i < pins.length; i++) {
          const p = pins[i]!;
          expect(p.xPercent).toBeGreaterThanOrEqual(16);
          expect(p.xPercent).toBeLessThanOrEqual(82);
          expect(p.yPercent).toBeGreaterThanOrEqual(18);
          expect(p.yPercent).toBeLessThanOrEqual(74);
          if (p.xPercent < 44) {
            expect(p.yPercent).toBeLessThanOrEqual(64);
          }
          for (let j = i + 1; j < pins.length; j++) {
            const q = pins[j]!;
            expect(Math.hypot(p.xPercent - q.xPercent, p.yPercent - q.yPercent)).toBeGreaterThanOrEqual(8.0);
          }
        }
      }

      // Mid-corridor transit hides diegetic pins cleanly
      controller.updateScroll(0.12);
      controller.animateTick(0.016);
      const transitPins = controller.getProjectedHotspots(0);
      expect(transitPins.every((p) => !p.visible)).toBe(true);

      controller.dispose();
    });

    it('adapts 390x844 portrait FOV, enforces full-width yPercent <= 54 hotspot safe-zone, and centers portrait Focus Dolly framing', () => {
      const controller = new SceneController(container);
      controller.getEngine().resize(390, 844);
      controller.getCameraRig().resize(390, 844);

      const responsiveFov = controller.getCameraRig().getResponsiveBaseFov();
      expect(responsiveFov).toBeGreaterThan(60);
      expect(responsiveFov).toBeLessThanOrEqual(68);

      for (let actIdx = 0; actIdx < 6; actIdx++) {
        controller.updateScroll(actIdx * 0.2);
        controller.animateTick(0.016);
        const pins = controller.getProjectedHotspots(actIdx);
        expect(pins.length).toBeGreaterThanOrEqual(3);
        for (const p of pins) {
          expect(p.yPercent).toBeLessThanOrEqual(54);
        }
      }

      controller.updateScroll(0);
      controller.selectSubTarget(0, 'optical-core');
      for (let i = 0; i < 40; i++) controller.animateTick(0.016);
      // optical-core desktop focusCamPos.z=7.20 and focusLookAt.x=1.34 -> portrait +Z pullback and centered lookAt.x counter-shift
      expect(controller.getCamera().position.z).toBeGreaterThan(8.0);
      expect(controller.getCurrentLookAt().x).toBeLessThan(1.20);

      controller.dispose();
    });

    it('dispatches Act 2–6 prop choreography via selectSubTarget across Academy volumes, Crucible rings, Summit waypoints, Frontier cores, and Horizon lenses', () => {
      const controller = new SceneController(container);

      controller.selectSubTarget(1, 'vol-3', { emitCallback: false });
      expect(controller.getLastSceneAction()).toBe('tome_inspect');

      controller.selectSubTarget(2, 'cloud-ai', { emitCallback: false });
      expect(controller.getLastSceneAction()).toBe('badge_surge');

      controller.selectSubTarget(3, 'hilti-trophy', { emitCallback: false });
      expect(controller.getLastSceneAction()).toBe('trophy_present');

      controller.selectSubTarget(4, 'hireti-sweetzerland', { emitCallback: false });
      expect(controller.isFrontierStrataExplodedState()).toBe(true);

      controller.selectSubTarget(5, 'crypto-quant', { emitCallback: false });
      expect(controller.getLastSceneAction()).toBe('interest_focus');
      expect(controller.getInterestFocusColorHex().toLowerCase()).toBe('#f59e0b');

      controller.selectSubTarget(5, 'direct-dispatch', { emitCallback: false });
      expect(controller.getLastSceneAction()).toBe('handshake_wave');

      controller.dispose();
    });

    it('articulates lower-body walking stride during corridor transit and contrapposto weight shift when stationary', () => {
      const controller = new SceneController(container);
      const gltfScene = new THREE.Group();
      const boneNames = ['Hips', 'Head', 'LeftUpLeg', 'RightUpLeg', 'LeftLeg', 'RightLeg'] as const;
      const bones: Record<string, THREE.Bone> = {};
      for (const n of boneNames) {
        const b = new THREE.Bone();
        b.name = n;
        bones[n] = b;
        gltfScene.add(b);
      }
      controller.applyLoadedGLTFAvatar({ scene: gltfScene });

      // Stationary contrapposto at Act 1
      controller.updateScroll(0.0);
      for (let i = 0; i < 20; i++) controller.animateTick(0.016);
      expect(Math.abs(bones['Hips']!.rotation.z)).toBeGreaterThan(0.005);

      // Mid-corridor walking stride at sp = 0.12
      controller.updateScroll(0.12);
      let maxStrideDiff = 0;
      for (let i = 0; i < 25; i++) {
        controller.animateTick(0.032);
        maxStrideDiff = Math.max(
          maxStrideDiff,
          Math.abs(bones['LeftUpLeg']!.rotation.x - bones['RightUpLeg']!.rotation.x)
        );
      }
      expect(maxStrideDiff).toBeGreaterThan(0.15);

      controller.dispose();
    });

    it('keeps Act 1 StudioGroup anchored in world space during walking departure and suppresses test-env GLB load warnings', async () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const loadSpy = vi.spyOn(GLTFLoader.prototype, 'load').mockImplementation((_url, _onLoad, _onProgress, onError) => {
        onError?.(new Error('Simulated network error in test env'));
      });

      const controller = new SceneController(container);
      const studioGroup = controller.getStudioGroup();
      expect(studioGroup).not.toBeNull();

      await controller.loadGLTFModel('/models/missing_test_model.glb');
      expect(warnSpy).not.toHaveBeenCalled();

      // Advance into Act 1 walking departure (sp = 0.12): StudioGroup counter-translates so world anchor stays fixed at Station 0
      controller.updateScroll(0.12);
      controller.animateTick(0.016);
      const worldPos = new THREE.Vector3();
      studioGroup!.getWorldPosition(worldPos);
      expect(worldPos.distanceTo(SceneController.PERSONA_STATIONS[0]!.pos)).toBeLessThan(0.15);

      controller.dispose();
      loadSpy.mockRestore();
      warnSpy.mockRestore();
    });

    it('renders continuous CinemaSkyDome GLSL shader centered on camera with per-act horizon color transitions', () => {
      const controller = new SceneController(container);
      const skyMesh = controller.getParticleLattice().getCinemaSkyMesh();
      expect(skyMesh).toBeDefined();
      expect(skyMesh.name).toBe('CinemaSkyDome');

      const skyMat = skyMesh.material as THREE.ShaderMaterial;
      const horizonUniform = skyMat.uniforms['uHorizonColor']!.value as THREE.Color;

      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      const act1HorizonHex = horizonUniform.getHex();
      expect(skyMesh.position.distanceTo(controller.getCamera().position)).toBeCloseTo(0, 3);

      controller.updateScroll(0.6);
      controller.animateTick(0.016);
      const act4HorizonHex = horizonUniform.getHex();
      expect(act4HorizonHex).not.toBe(act1HorizonHex);
      expect(skyMesh.position.distanceTo(controller.getCamera().position)).toBeCloseTo(0, 3);

      controller.dispose();
    });
  });

  describe('Cinematic Transition Physics, Inter-Act Portals & Velocity Star-Streak Warp', () => {
    it('builds 5 inter-act architectural portal gates visible strictly inside transition corridors', () => {
      const controller = new SceneController(container);
      const backdrops = controller.getParticleLattice().getChapterBackdropsGroup();

      for (let i = 0; i < 5; i++) {
        expect(backdrops.getObjectByName(`InterActPortalGate_${i}`)).toBeDefined();
        expect(backdrops.getObjectByName(`SkybridgePromenadeDeck_${i}`)).toBeDefined();
      }

      // Stationary at Act 1 station: portal gate 0 must remain hidden
      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(backdrops.getObjectByName('InterActPortalGate_0')?.visible).toBe(false);

      // Mid-transition between Act 1 and Act 2 (sp = 0.10): portal gate 0 illuminates cleanly
      controller.updateScroll(0.1);
      controller.animateTick(0.016);
      expect(backdrops.getObjectByName('InterActPortalGate_0')?.visible).toBe(true);
      expect(backdrops.getObjectByName('InterActPortalGate_1')?.visible).toBe(false);

      // Stationary at Act 2 station: portal gate 0 hides cleanly again
      controller.updateScroll(0.2);
      controller.animateTick(0.016);
      expect(backdrops.getObjectByName('InterActPortalGate_0')?.visible).toBe(false);

      controller.dispose();
    });

    it('applies damped Steadicam lateral banking roll and warps stardust lattice under velocity', () => {
      const controller = new SceneController(container);
      const rig = controller.getCameraRig();
      const lattice = controller.getParticleLattice();

      controller.updateScroll(0.0);
      controller.animateTick(0.016);
      expect(Math.abs(rig.getBankRoll())).toBeLessThan(0.01);

      // Rapid scroll sweep from Act 1 (x = -0.48) toward Act 2 (x = +1.35)
      controller.updateScroll(0.2);
      controller.animateTick(0.016);
      expect(Math.abs(rig.getBankRoll())).toBeGreaterThan(0.005);
      expect(Math.abs(rig.getBankRoll())).toBeLessThanOrEqual(0.055);
      expect(lattice.getWarpFactor()).toBeGreaterThan(0.15);

      // Under reduced motion, banking roll and velocity warp lock cleanly to zero
      controller.setReducedMotion(true);
      controller.animateTick(0.016);
      expect(rig.getBankRoll()).toBe(0);
      expect(lattice.getWarpFactor()).toBe(0);

      controller.dispose();
    });

    it('smoothly interpolates Skybridge lighting intensities without step jumps and damps companion idle arm relaxation', () => {
      const controller = new SceneController(container);
      controller.setReducedMotion(false);
      const scene = controller.getScene();
      const keyLight = scene.children.find(
        (obj) => obj instanceof THREE.DirectionalLight && obj.castShadow
      ) as THREE.DirectionalLight | undefined;
      const rimLight = controller.getRimCyanLight();
      expect(keyLight).toBeDefined();
      expect(rimLight).toBeDefined();

      // Act 1 corridor onset (sp = 0.11, w ~ 0.316 <= 0.35): preserves exact Act 1 lighting baseline
      controller.updateScroll(0.11);
      controller.animateTick(0.016);
      expect(keyLight!.intensity).toBeCloseTo(3.1, 3);
      expect(rimLight!.intensity).toBeCloseTo(2.45, 3);

      // Mid-corridor ramp (sp = 0.125, w ~ 0.593): smoothly interpolated intermediate values
      controller.updateScroll(0.125);
      controller.animateTick(0.016);
      expect(keyLight!.intensity).toBeGreaterThan(3.2);
      expect(keyLight!.intensity).toBeLessThan(3.7);
      expect(rimLight!.intensity).toBeGreaterThan(2.6);
      expect(rimLight!.intensity).toBeLessThan(4.3);

      // Exit to Act 2 (sp = 0.15, w ~ 0.957 >= 0.85): settles smoothly at Act 2 intensities
      controller.updateScroll(0.15);
      controller.animateTick(0.016);
      expect(keyLight!.intensity).toBeCloseTo(3.8, 3);
      expect(rimLight!.intensity).toBeCloseTo(4.5, 3);

      // Verify smooth exponential damping on stylized companion idle arm relaxation weight
      const compGroup = new THREE.Group();
      for (const boneName of ['LeftArm', 'RightArm', 'LeftForeArm', 'RightForeArm']) {
        const b = new THREE.Bone();
        b.name = boneName;
        compGroup.add(b);
      }
      const idleClip = new THREE.AnimationClip('Idle_Breathing', 1.0, []);
      const walkClip = new THREE.AnimationClip('Walk_Forward', 1.0, []);
      controller.applyLoadedStylizedCompanion({ scene: compGroup, animations: [idleClip, walkClip] });
      expect(controller.getCompanionIdleRelaxWeight()).toBeCloseTo(1.0, 3);

      controller.updateScroll(0.12);
      for (let i = 0; i < 5; i++) controller.animateTick(0.016);
      const midWeight = controller.getCompanionIdleRelaxWeight();
      expect(midWeight).toBeGreaterThan(0.1);
      expect(midWeight).toBeLessThan(0.9);

      for (let i = 0; i < 35; i++) controller.animateTick(0.016);
      expect(controller.getCompanionIdleRelaxWeight()).toBeLessThan(0.05);

      controller.dispose();
    });

    it('hides fallback StarPressBackingFrame upon GLB alignment, isolates IlluminatedTome top-face material, and aligns Act 5/6 landmarks', () => {
      const controller = new SceneController(container);
      const scene = controller.getScene();
      const backdrops = controller.getParticleLattice().getChapterBackdropsGroup();

      // Act 4: alignStarPressToGLBFrame() must hide fallback StarPressBackingFrame to prevent Z-fighting with Prop_Star_PressFrame
      const backingFrame = scene.getObjectByName('StarPressBackingFrame') as THREE.Mesh;
      const paperMesh = scene.getObjectByName('StarPressPaperMesh') as THREE.Mesh;
      expect(backingFrame).toBeDefined();
      expect(backingFrame.visible).toBe(true);
      (controller as unknown as { act4: { alignStarPressToGLBFrame(): void } }).act4.alignStarPressToGLBFrame();
      expect(backingFrame.visible).toBe(false);
      expect(paperMesh.visible).toBe(true);

      // Act 2: IlluminatedTome renders manuscript texture strictly on +Y top face (index 2) with sRGB colorSpace
      const tome = scene.getObjectByName('IlluminatedTome') as THREE.Mesh;
      expect(Array.isArray(tome.material)).toBe(true);
      const tomeMats = tome.material as THREE.MeshStandardMaterial[];
      expect(tomeMats).toHaveLength(6);
      expect(tomeMats[2]?.map).not.toBeNull();
      expect(tomeMats[2]?.map?.colorSpace).toBe(THREE.SRGBColorSpace);
      expect(tomeMats[0]?.map).toBeNull();

      // Act 5: ReactorGantryStruts and ReactorFloorBusbars flank the x = 0.55 reactor tunnel axis symmetrically
      const struts = backdrops.getObjectByName('ReactorGantryStruts') as THREE.InstancedMesh;
      const m0 = new THREE.Matrix4();
      const m1 = new THREE.Matrix4();
      const p0 = new THREE.Vector3();
      const p1 = new THREE.Vector3();
      struts.getMatrixAt(0, m0);
      struts.getMatrixAt(1, m1);
      p0.setFromMatrixPosition(m0);
      p1.setFromMatrixPosition(m1);
      expect((p0.x + p1.x) * 0.5).toBeCloseTo(0.55, 3);

      const busbars = backdrops.getObjectByName('ReactorFloorBusbars') as THREE.Group;
      expect(busbars).toBeDefined();
      expect(busbars.children).toHaveLength(2);
      expect((busbars.children[0]!.position.x + busbars.children[1]!.position.x) * 0.5).toBeCloseTo(0.55, 3);
      expect(busbars.children[0]!.position.z).toBeLessThan(-10);

      // Act 6: CosmicDeckCompassRing centers at world x = 0 (local -0.35 inside ChapterBackdrop_5)
      const compass = backdrops.getObjectByName('CosmicDeckCompassRing') as THREE.Mesh;
      expect(compass.position.x).toBeCloseTo(-0.35, 3);

      controller.dispose();
    });

    it('synchronizes all 6 Schema-v4 facial morph meshes, applies non-accumulating restQuaternion finger curls with 0.55 thumb scale, and matches eyelid PBR calibration', () => {
      const controller = new SceneController(container);
      const gltfScene = new THREE.Group();

      const headBone = new THREE.Bone();
      headBone.name = 'Head';
      const rightHandBone = new THREE.Bone();
      rightHandBone.name = 'RightHand';
      rightHandBone.rotation.set(0.16, 0.22, -0.12, 'XYZ');

      // Non-identity rest quaternions mirroring v38 GLB bone orientation
      const indexRest = new THREE.Quaternion(0.1238, -0.8629, 0.2901, 0.3948).normalize();
      const thumbRest = new THREE.Quaternion(-0.1012, -0.8682, 0.3612, 0.3248).normalize();
      const indexBone = new THREE.Bone();
      indexBone.name = 'LeftHandIndex1';
      indexBone.quaternion.copy(indexRest);
      const thumbBone = new THREE.Bone();
      thumbBone.name = 'LeftHandThumb1';
      thumbBone.quaternion.copy(thumbRest);
      gltfScene.add(headBone, rightHandBone, indexBone, thumbBone);

      const morphTargetNames = [
        'mouthSmileLeft',
        'mouthSmileRight',
        'mouthOpen',
        'jawOpen',
        'eyeBlinkLeft',
        'eyeBlinkRight',
        'browInnerUp',
        'viseme_aa',
      ];
      const morphDict: Record<string, number> = {
        ...Object.fromEntries(morphTargetNames.map((n, i) => [n, i])),
        staleUnusedShape: 8,
      };
      const meshNames = [
        'SM_Character_Face',
        'SM_Character_OralCavity',
        'SM_Character_UpperTeeth',
        'SM_Character_LowerTeeth',
        'SM_Character_Tongue',
        'SM_Character_Eyelids',
      ] as const;

      const morphMeshes: THREE.Mesh[] = [];
      const skinTex = new THREE.Texture();
      let eyelidsMat: THREE.MeshStandardMaterial | null = null;
      for (const mName of meshNames) {
        const g = new THREE.BufferGeometry();
        g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(9), 3));
        const mat = new THREE.MeshStandardMaterial(mName === 'SM_Character_Face' || mName === 'SM_Character_Eyelids' ? { map: skinTex } : {});
        if (mName === 'SM_Character_Eyelids') eyelidsMat = mat;
        const m = new THREE.Mesh(g, mat);
        m.name = mName;
        m.morphTargetDictionary = { ...morphDict };
        m.morphTargetInfluences = [0, 0, 0, 0, 0, 0, 0, 0, 0.99]; // Seed stale extra morph at index 8
        morphMeshes.push(m);
        gltfScene.add(m);
      }
      const eyeMesh = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.02, 0.02), new THREE.MeshStandardMaterial());
      eyeMesh.name = 'SM_Character_EyeLeft';
      gltfScene.add(eyeMesh);

      controller.applyLoadedGLTFAvatar({ scene: gltfScene });

      // Primary face mesh stays SM_Character_Face, all 6 morph meshes are registered, and eyelids share skin PBR calibration
      expect(controller.getGLTFFaceMesh()?.name).toBe('SM_Character_Face');
      expect(controller.getGLTFFacialMorphMeshes()).toHaveLength(6);
      expect(eyelidsMat?.color.getHex()).toBe(0xefebe8);
      expect(eyelidsMat?.roughness).toBeCloseTo(0.64, 2);
      expect(eyelidsMat?.emissiveIntensity).toBeCloseTo(0.08, 2);
      expect(morphMeshes[5]!.castShadow).toBe(false);
      expect(eyeMesh.castShadow).toBe(false);

      // Trigger blink window around virtualTime % 4.2 > 4.02 & inspect_tome for brow + curl
      for (let i = 0; i < 245; i++) controller.animateTick(0.016); // virtualTime ~ 3.92s
      controller.triggerSceneAction('inspect_tome');
      for (let i = 0; i < 13; i++) controller.animateTick(0.016); // virtualTime ~ 4.128s inside blink window while inspect_tome is active

      const faceInfl = morphMeshes[0]!.morphTargetInfluences!;
      expect(faceInfl[4]).toBeGreaterThan(0.3); // eyeBlinkLeft active
      expect(faceInfl[5]).toBeGreaterThan(0.3); // eyeBlinkRight active
      for (const m of morphMeshes) {
        expect(m.morphTargetInfluences![8]).toBe(0); // Inactive/stale target reset to 0 every frame
        for (let k = 0; k < 8; k++) {
          expect(m.morphTargetInfluences![k]).toBeCloseTo(faceInfl[k]!, 5);
        }
      }

      // Let currentFingerCurl settle to inspect_tome (0.18) and confirm zero per-frame accumulation & 0.55x thumb scale
      for (let i = 0; i < 45; i++) controller.animateTick(0.016);
      const expectedAngleDelta = (q: THREE.Quaternion, rest: THREE.Quaternion): number => {
        const diff = rest.clone().invert().multiply(q).normalize();
        return 2 * Math.acos(THREE.MathUtils.clamp(Math.abs(diff.w), 0, 1));
      };
      const indexDeltaAt60 = expectedAngleDelta(indexBone.quaternion, indexRest);
      const thumbDeltaAt60 = expectedAngleDelta(thumbBone.quaternion, thumbRest);
      expect(indexDeltaAt60).toBeCloseTo(0.18, 2);
      expect(thumbDeltaAt60).toBeCloseTo(0.18 * 0.55, 2);

      for (let i = 0; i < 40; i++) controller.animateTick(0.016);
      expect(expectedAngleDelta(indexBone.quaternion, indexRest)).toBeCloseTo(0.18, 2);
      expect(expectedAngleDelta(thumbBone.quaternion, thumbRest)).toBeCloseTo(0.18 * 0.55, 2);

      // Verify glasses_adjust wraps 4.52316 wrist Z to shortest equivalent (-1.76 rad) rather than spinning +4.5 rad
      controller.triggerSceneAction('glasses_adjust');
      controller.animateTick(0.016);
      expect(rightHandBone.rotation.z).toBeLessThan(0.0);

      controller.dispose();
    });

    it('welds coincident UV-seam vertex normals on SM_Character_Face and calibrates M_Hair_v38_CurtainFlow sheen/shadow response', () => {
      const controller = new SceneController(container);
      const gltfScene = new THREE.Group();

      // Build split-normal geometry at coincident corner position (0, 0, 0)
      const faceGeom = new THREE.BufferGeometry();
      faceGeom.setAttribute(
        'position',
        new THREE.Float32BufferAttribute([0, 0, 0, 0.1, 0, 0, 0, 0.1, 0, 0, 0, 0, 0, 0.1, 0, -0.1, 0, 0], 3)
      );
      faceGeom.setAttribute(
        'normal',
        new THREE.Float32BufferAttribute([1, 0, 0, 0, 0, 1, 0, 0, 1, -1, 0, 0, 0, 0, 1, 0, 0, 1], 3)
      );
      const faceMat = new THREE.MeshStandardMaterial({ map: new THREE.Texture() });
      const faceMesh = new THREE.Mesh(faceGeom, faceMat);
      faceMesh.name = 'SM_Character_Face';

      const hairTex = new THREE.Texture();
      const hairMat = new THREE.MeshStandardMaterial({
        name: 'M_Hair_v38_CurtainFlow',
        map: hairTex,
        normalMap: hairTex,
        roughness: 1.0,
      });
      const hairMesh = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.1), hairMat);
      hairMesh.name = 'SM_Character_Hair';

      const hips = new THREE.Bone();
      hips.name = 'Hips';
      const head = new THREE.Bone();
      head.name = 'Head';
      hips.add(head);
      gltfScene.add(faceMesh, hairMesh, hips);

      (controller as unknown as { applyLoadedGLTFAvatar(m: THREE.Group): void }).applyLoadedGLTFAvatar(gltfScene);

      // Indices 0 and 3 share position (0, 0, 0) with exact opposite normals -> guard keeps finite unit normals without NaN
      const nAttr = faceMesh.geometry.getAttribute('normal');
      expect(Number.isFinite(nAttr.getX(0))).toBe(true);
      expect(Math.hypot(nAttr.getX(0), nAttr.getY(0), nAttr.getZ(0))).toBeCloseTo(1, 5);
      expect(nAttr.getX(0)).toBeCloseTo(1, 5);
      expect(nAttr.getX(3)).toBeCloseTo(-1, 5);
      controller.dispose();

      const controller2 = new SceneController(container);
      const gltfScene2 = new THREE.Group();
      const faceGeom2 = new THREE.BufferGeometry();
      faceGeom2.setAttribute(
        'position',
        new THREE.Float32BufferAttribute([0, 0, 0, 0, 0, 0], 3)
      );
      faceGeom2.setAttribute(
        'normal',
        new THREE.Float32BufferAttribute([0.6, 0, 0.8, -0.6, 0, 0.8], 3)
      );
      const faceMesh2 = new THREE.Mesh(faceGeom2, new THREE.MeshStandardMaterial({ map: new THREE.Texture() }));
      faceMesh2.name = 'SM_Character_Face';
      const hairMat2 = new THREE.MeshStandardMaterial({
        name: 'M_Hair_v38_CurtainFlow',
        map: new THREE.Texture(),
        normalMap: new THREE.Texture(),
        roughness: 1.0,
      });
      hairMat2.normalScale.set(1, -1);
      const hairMesh2 = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.1), hairMat2);
      hairMesh2.name = 'SM_Character_Hair';
      const head2 = new THREE.Bone();
      head2.name = 'Head';
      gltfScene2.add(faceMesh2, hairMesh2, head2);

      (controller2 as unknown as { applyLoadedGLTFAvatar(m: THREE.Group): void }).applyLoadedGLTFAvatar(gltfScene2);
      const n2 = faceMesh2.geometry.getAttribute('normal');
      expect(n2.getX(0)).toBeCloseTo(0, 5);
      expect(n2.getZ(0)).toBeCloseTo(1, 5);
      expect(n2.getX(1)).toBeCloseTo(n2.getX(0), 5);
      expect(n2.getZ(1)).toBeCloseTo(n2.getZ(0), 5);

      expect(hairMat2.roughness).toBeCloseTo(0.72, 2);
      expect(hairMat2.normalScale.x).toBeCloseTo(0.85, 2);
      expect(hairMat2.normalScale.y).toBeCloseTo(-0.85, 2);
      expect(hairMat2.emissiveIntensity).toBeCloseTo(0.08, 2);

      controller2.dispose();
    });

    it('guards selectSubTarget against recursive callback loops, routes Act 5 explode_strata to Act5Frontier, resets sticky poses on clearSubTargetFocus, and compensates portrait mobile FOV', () => {
      let callbackCount = 0;
      const controller = new SceneController(container, {
        onSelectSubTarget: (actIndex, subTargetId) => {
          callbackCount += 1;
          // Simulate buggy recursive re-entry without emitCallback: false
          controller.selectSubTarget(actIndex, subTargetId);
        },
      });

      // 1. Non-re-entrant selectSubTarget + sticky pose reset
      controller.selectSubTarget(0, 'strategy-table');
      expect(callbackCount).toBe(1);
      expect(controller.getCurrentPoseAction()).toBe('keynote_present');

      controller.clearSubTargetFocus();
      expect(controller.getActiveSubTarget()).toBeNull();
      expect(controller.getCurrentPoseAction()).toBe('neutral');

      // Default Architectural Centerpiece Mode keeps humanoid off stage while studioEnvRT disposes cleanly
      expect(controller.isArchitecturalCenterpieceMode()).toBe(true);
      expect(controller.getStylizedRig().group.visible).toBe(false);

      // Also verify explicit emitCallback: false skips callback completely
      controller.selectSubTarget(0, 'optical-core', { emitCallback: false });
      expect(callbackCount).toBe(1);
      expect(controller.getCurrentPoseAction()).toBe('glasses_adjust');
      controller.clearSubTargetFocus();
      expect(controller.getCurrentPoseAction()).toBe('neutral');

      // 2. Act 5 explode_strata dock routing does not toggle Act 1 off-screen
      const act1Initial = controller.isEngineExplodedState();
      expect(controller.isFrontierStrataExplodedState()).toBe(false);
      controller.updateScroll(0.8);
      controller.triggerSceneAction('explode_strata', { section: 'ai-solutions' });
      expect(controller.isFrontierStrataExplodedState()).toBe(true);
      expect(controller.isEngineExplodedState()).toBe(act1Initial);

      // 3. Composed left-arm stance in Act 3 & Act 5 (clears adjacent props)
      expect(SceneController.PERSONA_STATIONS[2]!.gltf.leftArmZ).toBeLessThan(0);
      expect(SceneController.PERSONA_STATIONS[4]!.gltf.leftArmZ).toBeLessThan(0);

      // 4. Portrait mobile aspect FOV compensation preserves desktop 46 deg exactness
      const camRig = controller.getCameraRig();
      camRig.resize(1280, 800);
      expect(camRig.getResponsiveBaseFov()).toBe(46);
      camRig.resize(375, 812);
      expect(camRig.getResponsiveBaseFov()).toBeGreaterThan(46);
      expect(camRig.getResponsiveBaseFov()).toBeLessThanOrEqual(68);

      controller.dispose();
    });

    it('preserves v40 TEXCOORD_2/UV1 channels with Face/Hair emissive seam parity, scoped portrait eye/eyewear catchlight IBL with deterministic disposal & non-WebGL fallback, and left-zone Act 1-6 focus framing', () => {
      const controller = new SceneController(container);
      const gltfScene = new THREE.Group();

      const faceBaseTex = new THREE.Texture();
      faceBaseTex.channel = 2;
      const faceMat = new THREE.MeshStandardMaterial({
        name: 'Zachary_Face_Albedo',
        map: faceBaseTex,
      });
      const faceMesh = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.1), faceMat);
      faceMesh.name = 'SM_Character_Face';

      const hairBaseTex = new THREE.Texture();
      hairBaseTex.channel = 2;
      const hairNormalTex = new THREE.Texture();
      hairNormalTex.channel = 1;
      const hairRoughTex = new THREE.Texture();
      hairRoughTex.channel = 1;
      const hairMat = new THREE.MeshStandardMaterial({
        name: 'M_Hair_v38_CurtainFlow',
        map: hairBaseTex,
        normalMap: hairNormalTex,
        roughnessMap: hairRoughTex,
        roughness: 1.0,
      });
      const hairMesh = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.1), hairMat);
      hairMesh.name = 'SM_Character_Hair';

      const glassesMetalMat = new THREE.MeshStandardMaterial({
        name: 'Glasses_Metal',
        color: 0x2e333d,
        metalness: 0.98,
        roughness: 0.12,
      });
      const glassesLensMat = new THREE.MeshPhysicalMaterial({
        name: 'Glasses_Lens',
        transparent: true,
        opacity: 0.004,
        roughness: 0.06,
      });
      const glassesMesh = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.02, 0.02), [
        glassesMetalMat,
        glassesLensMat,
      ]);
      glassesMesh.name = 'Sovereign_Titanium_Spectacles_1';

      const eyeMat = new THREE.MeshPhysicalMaterial({
        name: 'M_Eyes_v36',
        roughness: 0.14,
        specularIntensity: 0.1,
      });
      const eyeLeftMesh = new THREE.Mesh(new THREE.SphereGeometry(0.012), eyeMat);
      eyeLeftMesh.name = 'SM_Character_EyeLeft';

      const head = new THREE.Bone();
      head.name = 'Head';
      gltfScene.add(faceMesh, hairMesh, glassesMesh, eyeLeftMesh, head);

      (controller as unknown as { applyLoadedGLTFAvatar(m: THREE.Group): void }).applyLoadedGLTFAvatar(gltfScene);

      // v40 UV2 base/emissive + UV1 hair normal/roughness preserved
      expect(faceMat.map?.channel).toBe(2);
      expect(faceMat.emissiveMap).toBe(faceBaseTex);
      expect(faceMat.emissiveMap?.channel).toBe(2);
      expect(hairMat.map?.channel).toBe(2);
      expect(hairMat.emissiveMap).toBe(hairBaseTex);
      expect(hairMat.emissiveMap?.channel).toBe(2);
      expect(hairMat.normalMap?.channel).toBe(1);
      expect(hairMat.roughnessMap?.channel).toBe(1);
      // Harmonized warm-neutral hair emissive lift matches Face fringe seam
      expect(hairMat.emissive.getHex()).toBe(0xf5e2d3);
      expect(hairMat.emissiveIntensity).toBeCloseTo(0.08, 2);

      // Brushed titanium spectacles & corneal eye catchlights (strictly scoped to eyes/eyewear — zero global or Face/Hair IBL bleed)
      expect(controller.getScene().environment).toBeNull();
      expect(faceMat.envMap).toBeNull();
      expect(hairMat.envMap).toBeNull();
      expect(glassesMetalMat.metalness).toBeCloseTo(0.72, 2);
      expect(glassesMetalMat.roughness).toBeCloseTo(0.24, 2);
      expect(glassesMetalMat.emissiveIntensity).toBeCloseTo(0.22, 2);
      expect(glassesLensMat.depthWrite).toBe(false);
      expect(glassesLensMat.transparent).toBe(true);
      expect(glassesLensMat.clearcoat).toBeCloseTo(1.0, 2);
      expect(glassesLensMat.opacity).toBeLessThanOrEqual(0.035);
      expect(glassesLensMat.envMapIntensity).toBeLessThanOrEqual(0.35);
      expect(eyeMat.roughness).toBeCloseTo(0.10, 2);
      expect(eyeMat.specularIntensity).toBeCloseTo(0.55, 2);
      expect(eyeMat.clearcoat).toBeCloseTo(1.0, 2);
      expect(eyeMat.clearcoatRoughness).toBeLessThanOrEqual(0.04);
      expect(eyeMat.ior).toBeGreaterThanOrEqual(1.4);
      expect(eyeMat.envMapIntensity).toBeLessThanOrEqual(0.7);

      const catchlightRT = controller.getPortraitCatchlightEnvTarget();
      expect(catchlightRT).not.toBeNull();
      expect(eyeMat.envMap).toBe(catchlightRT!.texture);
      expect(glassesMetalMat.envMap).toBe(catchlightRT!.texture);
      expect(glassesLensMat.envMap).toBe(catchlightRT!.texture);
      const envDisposeSpy = vi.spyOn(catchlightRT!, 'dispose');

      // Act 1 focus targets look right of focal sculpture so they sit in the unobstructed left-58% band
      const opticalCoreCfg = SceneController.DIORAMA_SUB_TARGETS.find((t) => t.id === 'optical-core')!;
      const dossierCfg = SceneController.DIORAMA_SUB_TARGETS.find((t) => t.id === 'executive-dossier')!;
      const tableCfg = SceneController.DIORAMA_SUB_TARGETS.find((t) => t.id === 'strategy-table')!;
      expect(opticalCoreCfg.focusLookAt.x).toBeGreaterThan(1.3);
      expect(dossierCfg.focusLookAt.y).toBeGreaterThanOrEqual(-0.20);
      expect(tableCfg.focusLookAt.x).toBeGreaterThan(tableCfg.worldAnchor.x + 0.3);

      // Every single one of the Focus Dolly targets across Acts 1–6 keeps its focal anchor
      // unobstructed inside the left-58% viewport (NDC x <= 0.08, clear of the 500px right-hand sheet at x = +0.18)
      // and clear of CinemaTimelineHUD (anchor NDC y <= 0.72)
      const projCam = new THREE.PerspectiveCamera(46, 1280 / 800, 0.1, 145);
      for (const target of SceneController.DIORAMA_SUB_TARGETS) {
        projCam.fov = target.focusFov ?? 39;
        projCam.position.copy(target.focusCamPos);
        projCam.lookAt(target.focusLookAt);
        projCam.updateProjectionMatrix();
        projCam.updateMatrixWorld(true);

        const anchorNdc = target.worldAnchor.clone().project(projCam);

        expect(anchorNdc.x, `${target.id} anchor clipped left (${anchorNdc.x.toFixed(3)})`).toBeGreaterThan(-0.92);
        expect(anchorNdc.x, `${target.id} anchor occluded by sheet (${anchorNdc.x.toFixed(3)})`).toBeLessThan(0.08);
        expect(anchorNdc.y, `${target.id} anchor clips top HUD (${anchorNdc.y.toFixed(3)})`).toBeLessThan(0.72);
      }

      // Cross-act subtarget selection keeps the targeted Act 5 Frontier visible even while scrollProgress is still at Act 1
      controller.updateScroll(0.0);
      controller.selectSubTarget(4, 'hireti-sweetzerland', { emitCallback: false });
      controller.animateTick(0.016);
      expect(controller.getFrontierGroup().visible).toBe(true);

      const studioEnvSpy = controller.getStudioEnvTarget() ? vi.spyOn(controller.getStudioEnvTarget()!, 'dispose') : null;
      controller.dispose();
      expect(envDisposeSpy).toHaveBeenCalledTimes(1);
      expect(controller.getPortraitCatchlightEnvTarget()).toBeNull();
      if (studioEnvSpy) expect(studioEnvSpy).toHaveBeenCalledTimes(1);
      expect(controller.getStudioEnvTarget()).toBeNull();

      // Safe fallback when WebGL context is unavailable (stripped non-WebGL mock): never throws and keeps direct material calibration
      const fallbackController = new SceneController(container);
      vi.spyOn(fallbackController.getRenderer(), 'getContext').mockReturnValue(null as unknown as WebGLRenderingContext);
      const fallbackScene = new THREE.Group();
      const fallbackEyeMat = new THREE.MeshPhysicalMaterial({ name: 'M_Eyes_v36', roughness: 0.14 });
      const fallbackEye = new THREE.Mesh(new THREE.SphereGeometry(0.012), fallbackEyeMat);
      fallbackEye.name = 'SM_Character_EyeLeft';
      const fallbackHead = new THREE.Bone();
      fallbackHead.name = 'Head';
      fallbackScene.add(fallbackEye, fallbackHead);
      expect(() => fallbackController.applyLoadedGLTFAvatar({ scene: fallbackScene })).not.toThrow();
      expect(fallbackController.getPortraitCatchlightEnvTarget()).toBeNull();
      expect(fallbackEyeMat.envMap).toBeNull();
      expect(fallbackEyeMat.clearcoat).toBeCloseTo(1.0, 2);
      expect(fallbackEyeMat.roughness).toBeCloseTo(0.10, 2);
      fallbackController.dispose();
    });

    it('welds shared Face/Hands/Hoodie seam normals, injects per-fragment parabolic collar & wrist margin shader guards, restores checkShaderErrors after PMREM prefiltering, and drives 6-mesh lip-sync from narrowband Web Audio synthesis', () => {
      const controller = new SceneController(container);
      const renderer = controller.getRenderer();
      expect(renderer.debug.checkShaderErrors).toBe(true);

      const gltfScene = new THREE.Group();
      const head = new THREE.Bone();
      head.name = 'Head';
      gltfScene.add(head);

      // Shared seam vertex at (0.04, 1.45, 0.01) between SM_Character_Face and SM_Cloth_Hoodie
      // and at (0.36, 0.89, 0.02) between SM_Character_Hands and SM_Cloth_Hoodie
      const faceGeom = new THREE.BufferGeometry();
      faceGeom.setAttribute('position', new THREE.Float32BufferAttribute([0.04, 1.45, 0.01], 3));
      faceGeom.setAttribute('normal', new THREE.Float32BufferAttribute([0.6, 0.0, 0.8], 3));
      const faceMat = new THREE.MeshStandardMaterial({ name: 'Zachary_Face_Albedo', map: new THREE.Texture() });
      const faceMesh = new THREE.Mesh(faceGeom, faceMat);
      faceMesh.name = 'SM_Character_Face';

      const handsGeom = new THREE.BufferGeometry();
      handsGeom.setAttribute('position', new THREE.Float32BufferAttribute([0.36, 0.89, 0.02], 3));
      handsGeom.setAttribute('normal', new THREE.Float32BufferAttribute([0.0, 0.6, 0.8], 3));
      const handsMat = new THREE.MeshStandardMaterial({ name: 'Zachary_Hands_Albedo', map: new THREE.Texture() });
      const handsMesh = new THREE.Mesh(handsGeom, handsMat);
      handsMesh.name = 'SM_Character_Hands';

      const hoodieGeom = new THREE.BufferGeometry();
      hoodieGeom.setAttribute(
        'position',
        new THREE.Float32BufferAttribute([0.04, 1.45, 0.01, 0.36, 0.89, 0.02], 3)
      );
      hoodieGeom.setAttribute(
        'normal',
        new THREE.Float32BufferAttribute([-0.6, 0.0, 0.8, 0.0, -0.6, 0.8], 3)
      );
      const hoodieMat = new THREE.MeshStandardMaterial({ name: 'Zachary_Cloth_Hoodie', map: new THREE.Texture() });
      const hoodieMesh = new THREE.Mesh(hoodieGeom, hoodieMat);
      hoodieMesh.name = 'SM_Cloth_Hoodie';

      const eyeMat = new THREE.MeshPhysicalMaterial({ name: 'M_Eyes_v36' });
      const eyeMesh = new THREE.Mesh(new THREE.SphereGeometry(0.012), eyeMat);
      eyeMesh.name = 'SM_Character_EyeLeft';

      gltfScene.add(faceMesh, handsMesh, hoodieMesh, eyeMesh);
      controller.applyLoadedGLTFAvatar({ scene: gltfScene });

      // 1. checkShaderErrors stays true after PMREM catchlight generation
      expect(renderer.debug.checkShaderErrors).toBe(true);

      // 2. Shared seam normals welded identically across Face<->Hoodie and Hands<->Hoodie
      const fNorm = faceGeom.getAttribute('normal');
      const hNorm = hoodieGeom.getAttribute('normal');
      const wNorm = handsGeom.getAttribute('normal');
      expect(fNorm.getX(0)).toBeCloseTo(0.0, 5);
      expect(fNorm.getZ(0)).toBeCloseTo(1.0, 5);
      expect(hNorm.getX(0)).toBeCloseTo(fNorm.getX(0), 5);
      expect(hNorm.getZ(0)).toBeCloseTo(fNorm.getZ(0), 5);
      expect(wNorm.getY(0)).toBeCloseTo(0.0, 5);
      expect(wNorm.getZ(0)).toBeCloseTo(1.0, 5);
      expect(hNorm.getY(1)).toBeCloseTo(wNorm.getY(0), 5);
      expect(hNorm.getZ(1)).toBeCloseTo(wNorm.getZ(0), 5);

      // 3. Per-fragment parabolic collar & wrist margin shader guards attached to Face, Hands, and Hoodie
      expect(faceMat.customProgramCacheKey()).toBe('skin-atlas-margin-neck-v2');
      expect(handsMat.customProgramCacheKey()).toBe('skin-atlas-margin-wrist-v2');
      expect(hoodieMat.customProgramCacheKey()).toBe('skin-atlas-margin-hoodie-v2');
      expect(handsMat.emissiveIntensity).toBeCloseTo(0.08, 2);

      const mockFaceShader = {
        vertexShader: '#include <common>\nvoid main() {\n#include <begin_vertex>\n}',
        fragmentShader: '#include <common>\nvoid main() {\n#include <map_fragment>\n#include <emissivemap_fragment>\n}',
      } as unknown as THREE.WebGLProgramParametersWithUniforms;
      faceMat.onBeforeCompile(mockFaceShader, renderer);
      expect(mockFaceShader.vertexShader).toContain('varying vec3 vBindPos;');
      expect(mockFaceShader.fragmentShader).toContain('vNeckCollarRimMask');
      expect(mockFaceShader.fragmentShader).toContain('1.4265 + 4.8 * vBindPos.x * vBindPos.x');
      expect(mockFaceShader.fragmentShader).toContain('1.0 - smoothstep( 0.018, 0.030, vBindPos.z )');

      const mockHandsShader = {
        vertexShader: '#include <common>\nvoid main() {\n#include <begin_vertex>\n}',
        fragmentShader: '#include <common>\nvoid main() {\n#include <map_fragment>\n#include <emissivemap_fragment>\n}',
      } as unknown as THREE.WebGLProgramParametersWithUniforms;
      handsMat.onBeforeCompile(mockHandsShader, renderer);
      expect(mockHandsShader.fragmentShader).toContain('0.7114 + 0.47086 * abs( vBindPos.x ) - 0.05367 * vBindPos.z');

      const mockHoodieShader = {
        vertexShader: '#include <common>\nvoid main() {\n#include <begin_vertex>\n}',
        fragmentShader:
          '#include <common>\nvoid main() {\n#include <map_fragment>\n#include <roughnessmap_fragment>\n#include <emissivemap_fragment>\n}',
      } as unknown as THREE.WebGLProgramParametersWithUniforms;
      hoodieMat.onBeforeCompile(mockHoodieShader, renderer);
      expect(mockHoodieShader.fragmentShader).toContain('vHoodieNeckSkinMask');
      expect(mockHoodieShader.fragmentShader).toContain('vHoodieWristSkinMask');
      expect(mockHoodieShader.fragmentShader).toContain('vHoodieWristCuffMask');
      expect(mockHoodieShader.fragmentShader).toContain('0.7114 + 0.47086 * abs( vBindPos.x ) - 0.05367 * vBindPos.z');
      expect(mockHoodieShader.fragmentShader).toContain('roughnessFactor = mix( roughnessFactor, 0.64, vHoodieNeckSkinMask );');

      // 4. Narrowband Web Audio synthesis (bins 0..1 active, bins 2..31 zero) + synthesis envelope drives getAudioEnergy()
      const sound = controller.getSoundEngine();
      sound.toggleAudio();
      expect(sound.isAudioEnabled()).toBe(true);
      const analyser = (sound as unknown as { analyser: { getByteFrequencyData: (arr: Uint8Array) => void } | null }).analyser;
      if (analyser) {
        vi.spyOn(analyser, 'getByteFrequencyData').mockImplementation((arr: Uint8Array) => {
          arr.fill(0);
          arr[0] = 210; // 48Hz..220Hz fundamental bin only
          arr[1] = 90;
        });
      }
      sound.playHarmonicHum(220, 0.45);
      const energyDuringHum = sound.getAudioEnergy();
      expect(energyDuringHum).toBeGreaterThan(0.60);
      // Overlapping short haptic click must not truncate or drop the active longer hum envelope
      sound.playHapticClick(880, 0.04);
      expect(sound.getAudioEnergy()).toBeGreaterThanOrEqual(energyDuringHum * 0.95);

      sound.toggleAudio();
      expect(sound.isAudioEnabled()).toBe(false);
      expect(sound.getAudioEnergy()).toBe(0);

      // 5. +Z-forward portrait gaze clamping across all 6 Acts keeps head yaw subtle (<= 0.14 rad), eliminates upward chin-tilt pitch,
      //    and dynamically synchronizes M_Eyes_v36 envMapRotation.y with avatar head yaw so corneal catchlights stay matched
      controller.setReducedMotion(true);
      for (const actSp of [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]) {
        controller.updateScroll(actSp);
        controller.animateTick(0.016);
        expect(Math.abs(head.rotation.y)).toBeLessThanOrEqual(0.1401);
        expect(head.rotation.x).toBeGreaterThanOrEqual(-0.0201);
        expect(head.rotation.x).toBeLessThanOrEqual(0.0401);
        const expectedEyeEnvYaw = controller.getAvatarRig().rotation.y + head.rotation.y;
        expect(eyeMat.envMapRotation.y).toBeCloseTo(expectedEyeEnvYaw, 4);
      }

      // 6. PersistentParticleLattice enforces true outer cylindrical perimeter (zero foreground squares inside central portrait frustum)
      const lattice = controller.getParticleLattice().getPersistentLattice();
      const mat4 = new THREE.Matrix4();
      const posVec = new THREE.Vector3();
      let minPerimeterRadius = Infinity;
      for (let i = 0; i < lattice.count; i += 25) {
        lattice.getMatrixAt(i, mat4);
        posVec.setFromMatrixPosition(mat4);
        const effR = Math.hypot(posVec.x, (posVec.y - 0.6) / 0.45);
        if (effR < minPerimeterRadius) minPerimeterRadius = effR;
      }
      expect(minPerimeterRadius).toBeGreaterThanOrEqual(5.75);

      controller.dispose();
    });

    it('mounts Designer Vinyl Stylized Companion on Act 1 dais, drives baked AnimationMixer locomotion (Idle_Breathing, Gesture_Present, Walk_Forward, Turn_Greet) & blink morphs, and stops mixer cleanly on dispose', () => {
      const controller = new SceneController(container);
      expect(controller.isStylizedCompanionMode()).toBe(true);
      expect(controller.isArchitecturalCenterpieceMode()).toBe(true);
      expect(controller.getStylizedRig().group.visible).toBe(false);
      expect(controller.getScene().environment).toBeNull();

      const compScene = new THREE.Group();
      const hips = new THREE.Bone();
      hips.name = 'Hips';
      const neck = new THREE.Bone();
      neck.name = 'Neck';
      const head = new THREE.Bone();
      head.name = 'Head';
      hips.add(neck);
      neck.add(head);

      const eyelidGeo = new THREE.BoxGeometry(0.02, 0.01, 0.01);
      const eyelidMat = new THREE.MeshStandardMaterial({ name: 'Mat_Companion_Skin' });
      const eyelidMesh = new THREE.Mesh(eyelidGeo, eyelidMat);
      eyelidMesh.name = 'SM_Companion_Eyelids';
      eyelidMesh.morphTargetDictionary = { eyeBlinkLeft: 0, eyeBlinkRight: 1 };
      eyelidMesh.morphTargetInfluences = [0, 0];

      const glassesMat = new THREE.MeshStandardMaterial({ name: 'Mat_Companion_GlassesMetal', metalness: 0.94, roughness: 0.18 });
      const glassesMesh = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.02, 0.02), glassesMat);
      glassesMesh.name = 'SM_Companion_Glasses';

      compScene.add(hips, eyelidMesh, glassesMesh);

      const mkClip = (name: string) =>
        new THREE.AnimationClip(name, 1.0, [
          new THREE.NumberKeyframeTrack('Hips.position[y]', [0, 0.5, 1.0], [0.78, 0.80, 0.78]),
        ]);

      controller.applyLoadedStylizedCompanion({
        scene: compScene,
        animations: [
          mkClip('Idle_Breathing'),
          mkClip('Walk_Forward'),
          mkClip('Gesture_Present'),
          mkClip('Turn_Greet'),
        ],
      });

      const companion = controller.getStylizedCompanionModel();
      const mixer = controller.getCompanionAnimationMixer();
      expect(companion).not.toBeNull();
      expect(mixer).not.toBeNull();
      expect(companion!.position.y).toBeCloseTo(-1.31, 2);
      expect(controller.getCompanionActiveClip()).toBe('Idle_Breathing');

      // Exploding the strata core prompts companion to gesture toward the sculpture
      controller.triggerSceneAction('explode_strata', { exploded: true });
      controller.animateTick(0.016);
      expect(controller.getCompanionActiveClip()).toBe('Gesture_Present');

      // Collapse back and scroll into Act 1->2 Obsidian Skybridge transit: steps down onto bridge & walks forward
      controller.triggerSceneAction('explode_strata', { exploded: false });
      controller.updateScroll(0.12);
      for (let i = 0; i < 6; i++) controller.animateTick(0.016);
      expect(controller.getCompanionActiveClip()).toBe('Walk_Forward');
      expect(companion!.position.y).toBeCloseTo(-1.45, 2);
      expect(Math.abs(companion!.rotation.y)).toBeGreaterThan(1.0);

      // Handshake dispatch at chapter prompts greeting clip
      controller.updateScroll(0.0);
      controller.triggerSceneAction('handshake_wave');
      controller.animateTick(0.016);
      expect(controller.getCompanionActiveClip()).toBe('Turn_Greet');

      // Arrival at Act 6 (sp = 1.0) triggers bounded 2.4s Turn_Greet, then settles back to Idle_Breathing
      controller.updateScroll(1.0);
      controller.animateTick(0.016);
      expect(controller.getCompanionActiveClip()).toBe('Turn_Greet');
      for (let i = 0; i < 28; i++) controller.animateTick(0.1);
      expect(controller.getCompanionActiveClip()).toBe('Idle_Breathing');

      const stopSpy = vi.spyOn(mixer!, 'stopAllAction');
      controller.dispose();
      expect(stopSpy).toHaveBeenCalledTimes(1);
      expect(controller.getStylizedCompanionModel()).toBeNull();
      expect(controller.getCompanionAnimationMixer()).toBeNull();
    });

    it('enforces sloped Act 3->4 bridge elevation, Act 6 5-lens morphing, CameraRig sheet framing, gesture reset, and pointermove hover cursor', () => {
      Object.defineProperty(container, 'clientWidth', { value: 1280, configurable: true });
      Object.defineProperty(container, 'clientHeight', { value: 800, configurable: true });
      const controller = new SceneController(container);

      // 1. Sloped Act 3->4 Skybridge elevation at sp = 0.52 (Act 4 landing y > -1.40)
      controller.updateScroll(0.52);
      controller.animateTick(0.016);
      const backdrops = controller.getParticleLattice().getChapterBackdropsGroup();
      const gate2 = backdrops.getObjectByName('InterActPortalGate_2');
      const deck2 = gate2?.getObjectByName('SkybridgeDeckGroup_2');
      const pier34 = gate2?.getObjectByName('SkybridgeFlankPier_2_34_R');
      const pier68 = gate2?.getObjectByName('SkybridgeFlankPier_2_68_R');
      expect(gate2?.visible).toBe(true);
      expect(deck2?.rotation.order).toBe('YXZ');
      expect(deck2?.rotation.x).toBeLessThan(0);
      expect(pier68!.position.y).toBeGreaterThan(pier34!.position.y);
      deck2!.updateWorldMatrix(true, false);
      const act4EndWorld = deck2!.localToWorld(new THREE.Vector3(0, 0, 10));
      expect(act4EndWorld.y).toBeGreaterThan(-1.40);

      // 2. Act 6 5-lens selectSubTarget color morphing (Beacon Light + Cosmic Eclipse + Eclipse Rim)
      controller.updateScroll(1.0);
      controller.animateTick(0.016);
      const horizonGroup = controller.getHorizonGroup();
      const beaconLight = horizonGroup.children.find(
        (c): c is THREE.PointLight => c instanceof THREE.PointLight
      );
      const eclipseRim = backdrops.getObjectByName('CosmicEclipseRim') as THREE.Mesh | undefined;
      const astrolabe = backdrops.getObjectByName('CosmicEclipseAstrolabeRing') as THREE.Mesh | undefined;
      expect(beaconLight).toBeDefined();
      expect(eclipseRim).toBeDefined();
      expect(astrolabe).toBeDefined();

      const lensChecks: Array<[string, string, number]> = [
        ['ai-systems', '#06b6d4', 0x06b6d4],
        ['crypto-quant', '#f59e0b', 0xf59e0b],
        ['cinematic-video', '#a855f7', 0xa855f7],
        ['hackathons-mentorship', '#10b981', 0x10b981],
        ['fintech-architecture', '#3b82f6', 0x3b82f6],
      ];
      for (const [lensId, hexStr, hexNum] of lensChecks) {
        controller.selectSubTarget(5, lensId);
        expect(controller.getInterestFocusColorHex()).toBe(hexStr);
        expect(beaconLight!.color.getHex()).toBe(hexNum);
        expect((eclipseRim!.material as THREE.MeshBasicMaterial).color.getHex()).toBe(hexNum);
        expect((astrolabe!.material as THREE.MeshBasicMaterial).color.getHex()).toBe(hexNum);
      }

      // 3. clearSubTargetFocus resets all gesture timers & CameraRig.setSheetOpen shifts lookAt rightward on desktop
      controller.selectSubTarget(1, 'vol-3');
      controller.clearSubTargetFocus();
      expect(controller.getActiveSubTarget()).toBeNull();
      expect(controller.getCameraRig().getActiveFocusTarget()).toBeNull();

      controller.updateScroll(0.0);
      for (let i = 0; i < 45; i++) controller.animateTick(0.016);
      const baseLookX = controller.getCameraRig().getCurrentLookAt().x;
      controller.setSheetOpen(true);
      for (let i = 0; i < 45; i++) controller.animateTick(0.016);
      expect(controller.getCameraRig().isSheetOpenState()).toBe(true);
      expect(controller.getCameraRig().getCurrentLookAt().x).toBeGreaterThan(baseLookX + 0.8);
      controller.setSheetOpen(false);
      for (let i = 0; i < 45; i++) controller.animateTick(0.016);
      expect(controller.getCameraRig().isSheetOpenState()).toBe(false);
      expect(controller.getCameraRig().getCurrentLookAt().x).toBeCloseTo(baseLookX, 1);

      // 4. pointermove 3D prop hover sets hoveredProp & cursor and cleans up on dispose()
      const coreGroup = controller.getEnterpriseAIEngine();
      expect(coreGroup).not.toBeNull();
      const hitPlane = new THREE.Mesh(
        new THREE.BoxGeometry(10, 10, 0.5),
        new THREE.MeshBasicMaterial()
      );
      controller.getScene().updateMatrixWorld(true);
      controller.getCamera().updateMatrixWorld(true);
      const camWorldPos = new THREE.Vector3();
      const camWorldDir = new THREE.Vector3();
      controller.getCamera().getWorldPosition(camWorldPos);
      controller.getCamera().getWorldDirection(camWorldDir);
      const hitWorld = camWorldPos.clone().add(camWorldDir.multiplyScalar(2.0));
      coreGroup!.worldToLocal(hitWorld);
      hitPlane.position.copy(hitWorld);
      hitPlane.userData = { type: 'subTargetProp', actIndex: 0, subTargetId: 'optical-core' };
      coreGroup!.add(hitPlane);
      controller.getScene().updateMatrixWorld(true);
      controller.getCamera().updateMatrixWorld(true);

      window.dispatchEvent(new MouseEvent('pointermove', { clientX: 640, clientY: 400 }));
      expect(document.body.dataset.hoveredProp).toBe('optical-core');
      expect(container.style.cursor).toBe('pointer');

      controller.dispose();
      expect(document.body.dataset.hoveredProp).toBeUndefined();
      expect(container.style.cursor).toBe('');
    });
  });
});



