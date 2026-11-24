import * as THREE from 'three';
import { CinemaSetsBuilder } from '../sets/CinemaSetsBuilder';
import { createCinemaSkyDome, type CinemaSkyController } from '../shaders/CinemaSkyShader';
import { isBackdropGroupVisible } from './stationProgress';

export interface ParticleLatticeOptions {
  scene: THREE.Scene;
}

/**
 * Deterministic pseudo-random number generator (Mulberry32)
 * Ensures reproducible spatial distribution across render cycles and testing baselines.
 */
function createPRNG(seed: number = 0x1337): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * ParticleLattice
 * Manages GPU-instanced persistent particle systems:
 * 1. Persistent 30,000-particle kinetic lattice with dynamic attractor fields
 *    morphing across the 6 acts.
 * 2. Act 1 Canonical 1,200-particle Kinetic Wave Field orbiting the presentation plinth.
 * All particle systems adhere to zero-allocation per frame (Invariant 11).
 */
export class ParticleLattice {
  private scene: THREE.Scene;

  // 1. Act 1 Canonical 1,200-particle Kinetic Wave Field
  private kineticWaveField!: THREE.InstancedMesh;
  private waveBasePositions: Float32Array = new Float32Array(1200 * 3);
  private wavePhases: Float32Array = new Float32Array(1200);
  private waveRadii: Float32Array = new Float32Array(1200);
  private waveTime: number = 0;

  // 2. Persistent 30,000-particle GPU-Accelerated Perimeter Stardust Lattice
  private persistentLattice!: THREE.InstancedMesh;
  private persistentCount: number = 30000;
  private persistentInitialPositions: Float32Array;
  private persistentVelocities: Float32Array;
  private persistentPhases: Float32Array;
  private latticeTime: number = 0;

  // 3. Luminous Spatial Light-Bridge connecting the 6 Diorama Islands (Z = +5.10 to -94.20)
  private spatialLightBridge!: THREE.Group;
  private bridgeSlatsMesh!: THREE.InstancedMesh;
  private bridgeSlatCount: number = 75;
  private bridgeSlatRest: Float32Array = new Float32Array(75 * 4);
  private bridgeRailMat: THREE.MeshStandardMaterial | null = null;
  private bridgeSlatMat: THREE.MeshStandardMaterial | null = null;
  private warpSmoothed: number = 0;

  // 4. Full-Viewport 6-Chapter Cinema Movie Sets & Continuous Atmospheric Sky Dome
  private chapterBackdropsGroup!: THREE.Group;
  private chapterGroups: THREE.Group[] = [];
  private cinemaSets!: CinemaSetsBuilder;
  private cinemaSky!: CinemaSkyController;
  private skyTime: number = 0;
  private fallbackCameraPos: THREE.Vector3 = new THREE.Vector3(-0.32, 0.22, 8.5);

  // 6-Act Morphing Dynamic Attractor Centers along the Z Trajectory:
  public static readonly ATTRACTOR_CENTERS: readonly THREE.Vector3[] = [
    new THREE.Vector3(0.0, 0.0, 5.0),     // Act 1: Executive Strategy Studio
    new THREE.Vector3(1.1, 0.0, -18.0),   // Act 2: The Academy
    new THREE.Vector3(0.15, 0.0, -36.0),  // Act 3: The Crucible
    new THREE.Vector3(0.35, 0.25, -56.0), // Act 4: Mount Pilatus Summit
    new THREE.Vector3(1.1, 0.10, -75.0),  // Act 5: The Frontier Exploded Core
    new THREE.Vector3(0.0, 0.0, -95.0),   // Act 6: Horizon Portal Gateway
  ];

  // Zero-allocation reusable animation scratch buffers
  private dummyObj: THREE.Object3D = new THREE.Object3D();

  constructor(options: ParticleLatticeOptions) {
    this.scene = options.scene;

    // 1. Initialize 1,200-particle Kinetic Wave Field (Act 1 plinth ocean)
    this.initKineticWaveField();

    // 2. Initialize 30,000-particle Outer-Perimeter Stardust Lattice
    this.persistentInitialPositions = new Float32Array(this.persistentCount * 3);
    this.persistentVelocities = new Float32Array(this.persistentCount * 3);
    this.persistentPhases = new Float32Array(this.persistentCount);
    this.initPersistentLattice();

    // 3. Initialize Luminous Spatial Light-Bridge connecting Acts 1-6
    this.initSpatialLightBridge();

    // 4. Initialize Full-Viewport Chapter Architectural Backdrops, Supergraphics & God-Rays
    this.initChapterArchitecturalBackdrops();
  }

  /**
   * Constructs the 1,200-particle kinetic wave field via InstancedMesh for zero draw-call overhead.
   */
  private initKineticWaveField(): void {
    const waveCount = 1200;
    const waveGeo = new THREE.SphereGeometry(0.008, 6, 6);
    const waveMat = new THREE.MeshBasicMaterial({
      color: 0xdcc296,
      transparent: true,
      opacity: 0.24,
    });

    this.kineticWaveField = new THREE.InstancedMesh(waveGeo, waveMat, waveCount);
    this.kineticWaveField.name = 'KineticWaveField';
    this.kineticWaveField.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    const dummy = this.dummyObj;
    const prng = createPRNG(0x42);
    for (let i = 0; i < waveCount; i++) {
      const radius = 3.8 + Math.pow(prng(), 1.6) * 3.8;
      const angle = prng() * Math.PI * 2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = -1.65 + (prng() - 0.5) * 0.10;

      this.waveBasePositions[i * 3 + 0] = x;
      this.waveBasePositions[i * 3 + 1] = y;
      this.waveBasePositions[i * 3 + 2] = z;

      this.wavePhases[i] = prng() * Math.PI * 2;
      this.waveRadii[i] = radius;

      dummy.position.set(x, y, z);
      const scale = 0.55 + prng() * 0.95;
      dummy.scale.set(scale, scale, scale);
      dummy.updateMatrix();
      this.kineticWaveField.setMatrixAt(i, dummy.matrix);
    }

    this.kineticWaveField.instanceMatrix.needsUpdate = true;
    this.kineticWaveField.position.set(1.35, 0.0, 5.10); // Anchored at Act 1 Plinth
    this.scene.add(this.kineticWaveField);
  }

  /**
   * Constructs the 30,000-particle outer-perimeter stardust lattice via InstancedMesh.
   * Confined strictly to the outer perimeter (radius > 5.5m) so the central 3D diorama
   * corridor and avatar frustum remain 100% unobstructed and free of foreground confetti.
   */
  private initPersistentLattice(): void {
    const geo = new THREE.PlaneGeometry(0.007, 0.007);
    const mat = new THREE.MeshBasicMaterial({
      color: 0xe5d3b3,
      transparent: true,
      opacity: 0.24,
      side: THREE.DoubleSide,
      depthWrite: false,
    });

    this.persistentLattice = new THREE.InstancedMesh(geo, mat, this.persistentCount);
    this.persistentLattice.name = 'PersistentParticleLattice';
    this.persistentLattice.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    const dummy = this.dummyObj;
    const prng = createPRNG(0x1337);
    for (let i = 0; i < this.persistentCount; i++) {
      // Distribute along the 6-act corridor outer horizon: Z from +6.0 down to -102.0
      const actProgress = i / this.persistentCount;
      const z = 6.0 - actProgress * 108.0 + (prng() - 0.5) * 8.0;
      const angle = prng() * Math.PI * 2;
      // Strictly outer cylindrical perimeter (R >= 5.8m in X-Y around corridor) so zero floating
      // dust squares ever enter the central avatar portrait frustum or land on Zachary's face/lips
      const radius = 5.8 + prng() * 7.5;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * (radius * 0.45) + 0.6;

      this.persistentInitialPositions[i * 3 + 0] = x;
      this.persistentInitialPositions[i * 3 + 1] = y;
      this.persistentInitialPositions[i * 3 + 2] = z;

      this.persistentVelocities[i * 3 + 0] = (prng() - 0.5) * 0.08;
      this.persistentVelocities[i * 3 + 1] = (prng() - 0.5) * 0.08;
      this.persistentVelocities[i * 3 + 2] = (prng() - 0.5) * 0.08;

      this.persistentPhases[i] = prng() * Math.PI * 2;

      dummy.position.set(x, y, z);
      dummy.scale.set(1, 1, 1);
      dummy.rotation.set(0, 0, 0);
      dummy.updateMatrix();
      this.persistentLattice.setMatrixAt(i, dummy.matrix);
    }

    this.persistentLattice.instanceMatrix.needsUpdate = true;
    this.scene.add(this.persistentLattice);
  }

  /**
   * Constructs the Luminous Spatial Light-Bridge connecting the 6 Architectural Diorama Islands
   * directly underneath the persona transit trajectory at foot sole elevation (pos.y - 1.455).
   */
  private initSpatialLightBridge(): void {
    this.spatialLightBridge = new THREE.Group();
    this.spatialLightBridge.name = 'SpatialLightBridge';

    const stationFeet = [
      new THREE.Vector3(1.35, -1.455, 5.10),
      new THREE.Vector3(0.85, -1.455, -17.60),
      new THREE.Vector3(0.76, -1.455, -35.60),
      new THREE.Vector3(1.25, -1.305, -55.80),
      new THREE.Vector3(0.92, -1.455, -74.60),
      new THREE.Vector3(0.85, -1.455, -94.20),
    ];

    // 1. Dual Brushed Champagne-Bronze Guide Rails aligned per inter-act span
    const railMat = new THREE.MeshStandardMaterial({
      color: 0x282420,
      emissive: 0xc8a97e,
      emissiveIntensity: 0.24,
      metalness: 0.88,
      roughness: 0.24,
      transparent: true,
      opacity: 0.72,
    });
    this.bridgeRailMat = railMat;

    const zAxis = new THREE.Vector3(0, 0, 1);
    const upAxis = new THREE.Vector3(0, 1, 0);
    const spanDir = new THREE.Vector3();
    const lateralVec = new THREE.Vector3();
    const midPt = new THREE.Vector3();
    const startTrim = new THREE.Vector3();
    const endTrim = new THREE.Vector3();

    const slatsPerSpan = 15;
    const slatGeo = new THREE.BoxGeometry(0.56, 0.018, 1.08);
    const slatMat = new THREE.MeshStandardMaterial({
      color: 0x24201c,
      emissive: 0xc8a97e,
      emissiveIntensity: 0.28,
      metalness: 0.78,
      roughness: 0.26,
      transparent: true,
      opacity: 0.78,
    });
    this.bridgeSlatMat = slatMat;
    this.bridgeSlatsMesh = new THREE.InstancedMesh(slatGeo, slatMat, this.bridgeSlatCount);
    this.bridgeSlatsMesh.name = 'SpatialBridgeSlats';

    const dummy = this.dummyObj;
    let slatIdx = 0;

    for (let s = 0; s < stationFeet.length - 1; s++) {
      const a = stationFeet[s]!;
      const b = stationFeet[s + 1]!;
      startTrim.lerpVectors(a, b, 0.11);
      endTrim.lerpVectors(a, b, 0.89);
      midPt.lerpVectors(startTrim, endTrim, 0.5);

      spanDir.subVectors(endTrim, startTrim);
      const visibleLen = spanDir.length();
      spanDir.normalize();
      lateralVec.crossVectors(upAxis, spanDir).normalize();

      const railGeo = new THREE.BoxGeometry(0.032, 0.022, visibleLen);
      const leftRail = new THREE.Mesh(railGeo, railMat);
      leftRail.name = s === 0 ? 'LightBridgeLeftRail' : `LightBridgeLeftRail_${s}`;
      leftRail.position.copy(midPt).addScaledVector(lateralVec, -0.86);
      leftRail.position.y += 0.008;
      leftRail.quaternion.setFromUnitVectors(zAxis, spanDir);
      this.spatialLightBridge.add(leftRail);

      const rightRail = new THREE.Mesh(railGeo, railMat);
      rightRail.name = s === 0 ? 'LightBridgeRightRail' : `LightBridgeRightRail_${s}`;
      rightRail.position.copy(midPt).addScaledVector(lateralVec, 0.86);
      rightRail.position.y += 0.008;
      rightRail.quaternion.setFromUnitVectors(zAxis, spanDir);
      this.spatialLightBridge.add(rightRail);

      // 2. Instanced Warm Basalt & Travertine Walkway Slats along the span centerline
      for (let k = 0; k < slatsPerSpan; k++) {
        const u = 0.11 + (k / Math.max(slatsPerSpan - 1, 1)) * 0.78;
        dummy.position.lerpVectors(a, b, u);
        dummy.scale.set(1, 1, 1);
        const yaw = Math.atan2(b.x - a.x, b.z - a.z);
        dummy.rotation.set(0, yaw, 0);
        dummy.updateMatrix();
        this.bridgeSlatRest[slatIdx * 4 + 0] = dummy.position.x;
        this.bridgeSlatRest[slatIdx * 4 + 1] = dummy.position.y;
        this.bridgeSlatRest[slatIdx * 4 + 2] = dummy.position.z;
        this.bridgeSlatRest[slatIdx * 4 + 3] = yaw;
        this.bridgeSlatsMesh.setMatrixAt(slatIdx++, dummy.matrix);
      }
    }

    this.bridgeSlatsMesh.instanceMatrix.needsUpdate = true;
    this.spatialLightBridge.add(this.bridgeSlatsMesh);

    this.scene.add(this.spatialLightBridge);
  }

  public getSpatialLightBridge(): THREE.Group {
    return this.spatialLightBridge;
  }

  public getChapterBackdropsGroup(): THREE.Group {
    return this.chapterBackdropsGroup;
  }

  /**
   * Builds 6 distinct full-viewport cinema movie-set scenarios behind each act stage
   * paired with a seamless 360-degree GLSL atmospheric sky dome.
   */
  private initChapterArchitecturalBackdrops(): void {
    this.cinemaSets = new CinemaSetsBuilder();
    const { root, chapterGroups } = this.cinemaSets.buildChapterBackdrops();
    this.chapterBackdropsGroup = root;
    this.chapterGroups = chapterGroups;
    this.scene.add(this.chapterBackdropsGroup);

    this.cinemaSky = createCinemaSkyDome();
    this.scene.add(this.cinemaSky.mesh);
  }

  public setAct1StudioEnvMap(envMap: THREE.Texture | null): void {
    this.cinemaSets.applyAct1StudioEnvMap(envMap);
  }

  public setAct6EclipseTheme(hex: number): void {
    this.cinemaSets.setAct6EclipseTheme(hex);
  }

  public getCinemaSkyMesh(): THREE.Mesh {
    return this.cinemaSky.mesh;
  }

  public getKineticWaveField(): THREE.InstancedMesh {
    return this.kineticWaveField;
  }

  public getPersistentLattice(): THREE.InstancedMesh {
    return this.persistentLattice;
  }

  public getWarpFactor(): number {
    return this.warpSmoothed;
  }

  public setBridgeTransitionWeight(bellWeight: number): void {
    const fade = THREE.MathUtils.clamp(bellWeight * 4.5, 0, 1);
    if (this.bridgeRailMat) {
      this.bridgeRailMat.opacity = 0.72 * fade;
    }
    if (this.bridgeSlatMat) {
      this.bridgeSlatMat.opacity = 0.78 * fade;
    }
  }

  /**
   * Updates wave fields, attractor fields, cinema sets, and atmospheric sky with zero memory allocation.
   */
  public update(
    delta: number,
    scrollProgress: number,
    isReducedMotion: boolean = false,
    cameraPos?: THREE.Vector3,
    scrollVelocity: number = 0
  ): void {
    const clampedDelta = Math.min(delta, 0.1);
    const dummy = this.dummyObj;
    if (!isReducedMotion) {
      this.skyTime += clampedDelta;
    }

    // 0. Depth-Gate Chapter Movie-Set Backdrops synchronously with canonical corridor schedule
    for (let idx = 0; idx < this.chapterGroups.length; idx++) {
      const grp = this.chapterGroups[idx]!;
      grp.visible = isBackdropGroupVisible(idx, scrollProgress);
    }
    this.cinemaSets.update(this.skyTime, isReducedMotion, scrollProgress);
    this.cinemaSky.update(
      scrollProgress,
      cameraPos ?? this.fallbackCameraPos,
      this.skyTime,
      isReducedMotion
    );

    if (isReducedMotion) {
      this.warpSmoothed = 0;
    }

    // 0b. Sequential Photon Ripple along SpatialLightBridge Slats during Active Transit
    if (!isReducedMotion && this.spatialLightBridge?.visible && this.bridgeSlatsMesh) {
      for (let i = 0; i < this.bridgeSlatCount; i++) {
        const bx = this.bridgeSlatRest[i * 4 + 0]!;
        const by = this.bridgeSlatRest[i * 4 + 1]!;
        const bz = this.bridgeSlatRest[i * 4 + 2]!;
        const yaw = this.bridgeSlatRest[i * 4 + 3]!;
        const pulse = Math.max(0, Math.sin(this.skyTime * 5.2 - i * 0.42));
        dummy.position.set(bx, by + pulse * 0.012, bz);
        dummy.rotation.set(0, yaw, 0);
        dummy.scale.set(1 + pulse * 0.055, 1 + pulse * 0.20, 1 + pulse * 0.08);
        dummy.updateMatrix();
        this.bridgeSlatsMesh.setMatrixAt(i, dummy.matrix);
      }
      this.bridgeSlatsMesh.instanceMatrix.needsUpdate = true;
      if (this.bridgeRailMat) {
        this.bridgeRailMat.emissiveIntensity =
          0.24 + Math.min(0.45, scrollVelocity * 0.35) + Math.sin(this.skyTime * 2.4) * 0.06;
      }
    }

    // 1. Update 1,200 Kinetic Wave Field
    if (this.kineticWaveField && !isReducedMotion) {
      this.waveTime += clampedDelta * 1.4;
      const waveFreq = 2.4;
      const waveSpeed = 1.8;

      // In Act 1 hero (sp < 0.15), wave field is fully active; smoothly cross-fades out across acts
      const waveFade = THREE.MathUtils.clamp(1.0 - scrollProgress * 5.0, 0.05, 1.0);
      (this.kineticWaveField.material as THREE.MeshBasicMaterial).opacity = 0.24 * waveFade;

      for (let i = 0; i < 1200; i++) {
        const bx = this.waveBasePositions[i * 3 + 0]!;
        const by = this.waveBasePositions[i * 3 + 1]!;
        const bz = this.waveBasePositions[i * 3 + 2]!;
        const r = this.waveRadii[i]!;
        const phase = this.wavePhases[i]!;

        const ripple = Math.sin(r * waveFreq - this.waveTime * waveSpeed + phase) * 0.09 * waveFade;
        dummy.position.set(bx, by + ripple, bz);

        const scale = (0.55 + Math.sin(this.waveTime + phase) * 0.25) * waveFade;
        dummy.scale.set(scale, scale, scale);
        dummy.updateMatrix();
        this.kineticWaveField.setMatrixAt(i, dummy.matrix);
      }
      this.kineticWaveField.instanceMatrix.needsUpdate = true;
    }

    // 2. Update 30,000 Persistent Lattice with Morphing Dynamic Attractor Fields & Speed-Warp Filaments
    if (this.persistentLattice && !isReducedMotion) {
      this.latticeTime += clampedDelta * 0.75;
      const t = this.latticeTime;

      const targetWarp = THREE.MathUtils.clamp(scrollVelocity * 1.4, 0, 1);
      this.warpSmoothed = THREE.MathUtils.damp(this.warpSmoothed, targetWarp, 12.0, clampedDelta);

      // Smooth persistent lattice rotation and breathing
      this.persistentLattice.rotation.y = t * 0.03;
      this.persistentLattice.rotation.z = Math.sin(t * 0.02) * 0.05;

      // 6-Act Dynamic Attractor Center Interpolation
      const actProgress = scrollProgress * 5.0; // [0.0, 5.0] spanning Acts 1 through 6
      const actIdx = Math.min(Math.floor(actProgress), 4);
      const actAlpha = actProgress - actIdx;

      const c1 = ParticleLattice.ATTRACTOR_CENTERS[actIdx]!;
      const c2 = ParticleLattice.ATTRACTOR_CENTERS[actIdx + 1]!;
      const currentAttractorX = THREE.MathUtils.lerp(c1.x, c2.x, actAlpha);
      const currentAttractorY = THREE.MathUtils.lerp(c1.y, c2.y, actAlpha);
      const currentAttractorZ = THREE.MathUtils.lerp(c1.z, c2.z, actAlpha);

      // Morph dynamic attractor field & stretch filaments along -Z when flying quickly between acts
      const sliceSize = 900;
      const startIdx = Math.floor(actIdx * 5000 + (t * 140) % 4000);
      const warpStretchZ = 1.0 + this.warpSmoothed * 20.0;
      const warpThinXY = 1.0 - this.warpSmoothed * 0.25;
      for (let k = 0; k < sliceSize; k++) {
        const i = (startIdx + k) % this.persistentCount;
        const bx = this.persistentInitialPositions[i * 3 + 0]!;
        const by = this.persistentInitialPositions[i * 3 + 1]!;
        const bz = this.persistentInitialPositions[i * 3 + 2]!;
        const phase = this.persistentPhases[i]!;

        const dx = bx - currentAttractorX;
        const dy = by - currentAttractorY;
        const dz = bz - currentAttractorZ;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        const swirlStrength = Math.max(0, 1.0 - dist / 8.0) * 0.35;

        const swirlAngle = t * 1.5 + phase;
        const ox = Math.cos(swirlAngle) * swirlStrength;
        const oy = Math.sin(t * 1.2 + phase) * 0.12 * swirlStrength;
        const oz = Math.sin(swirlAngle) * swirlStrength;

        const baseScale = 1.0 + Math.sin(t * 2.0 + phase) * 0.25 * swirlStrength;
        dummy.position.set(bx + ox, by + oy, bz + oz);
        dummy.rotation.set(0, 0, 0);
        dummy.scale.set(
          baseScale * warpThinXY,
          baseScale * warpThinXY,
          baseScale * warpStretchZ
        );
        dummy.updateMatrix();
        this.persistentLattice.setMatrixAt(i, dummy.matrix);
      }
      this.persistentLattice.instanceMatrix.needsUpdate = true;
    }
  }

  /**
   * Resets all particle matrices and simulation time back to their deterministic initial seed state.
   * Useful when switching to reduced motion or synchronizing visual testing baselines.
   */
  public resetToRest(): void {
    this.waveTime = 0;
    this.latticeTime = 0;
    this.warpSmoothed = 0;
    const dummy = this.dummyObj;

    if (this.kineticWaveField) {
      for (let i = 0; i < 1200; i++) {
        dummy.position.set(
          this.waveBasePositions[i * 3 + 0]!,
          this.waveBasePositions[i * 3 + 1]!,
          this.waveBasePositions[i * 3 + 2]!
        );
        dummy.scale.set(0.8, 0.8, 0.8);
        dummy.rotation.set(0, 0, 0);
        dummy.updateMatrix();
        this.kineticWaveField.setMatrixAt(i, dummy.matrix);
      }
      this.kineticWaveField.instanceMatrix.needsUpdate = true;
    }

    if (this.persistentLattice) {
      this.persistentLattice.rotation.set(0, 0, 0);
      for (let i = 0; i < this.persistentCount; i++) {
        dummy.position.set(
          this.persistentInitialPositions[i * 3 + 0]!,
          this.persistentInitialPositions[i * 3 + 1]!,
          this.persistentInitialPositions[i * 3 + 2]!
        );
        dummy.scale.set(1, 1, 1);
        dummy.rotation.set(0, 0, 0);
        dummy.updateMatrix();
        this.persistentLattice.setMatrixAt(i, dummy.matrix);
      }
      this.persistentLattice.instanceMatrix.needsUpdate = true;
    }
  }

  public dispose(): void {
    if (this.kineticWaveField) {
      this.kineticWaveField.geometry.dispose();
      (this.kineticWaveField.material as THREE.Material).dispose();
      this.scene.remove(this.kineticWaveField);
    }
    if (this.persistentLattice) {
      this.persistentLattice.geometry.dispose();
      (this.persistentLattice.material as THREE.Material).dispose();
      this.scene.remove(this.persistentLattice);
    }
    if (this.spatialLightBridge) {
      this.spatialLightBridge.traverse((obj) => {
        if ((obj as THREE.Mesh).isMesh) {
          const m = obj as THREE.Mesh;
          m.geometry?.dispose();
          if (Array.isArray(m.material)) {
            m.material.forEach((mat) => mat.dispose());
          } else {
            m.material?.dispose();
          }
        }
      });
      this.scene.remove(this.spatialLightBridge);
      this.bridgeRailMat = null;
      this.bridgeSlatMat = null;
    }
    if (this.cinemaSets) {
      this.cinemaSets.dispose();
    }
    if (this.cinemaSky) {
      this.scene.remove(this.cinemaSky.mesh);
      this.cinemaSky.dispose();
    }
    if (this.chapterBackdropsGroup) {
      this.chapterGroups = [];
      this.scene.remove(this.chapterBackdropsGroup);
    }
  }
}
