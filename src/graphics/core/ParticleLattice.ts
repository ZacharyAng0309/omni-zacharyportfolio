import * as THREE from 'three';

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

  // 2. Persistent 30,000-particle GPU-Accelerated Lattice
  private persistentLattice!: THREE.InstancedMesh;
  private persistentCount: number = 30000;
  private persistentInitialPositions: Float32Array;
  private persistentVelocities: Float32Array;
  private persistentPhases: Float32Array;
  private latticeTime: number = 0;

  // 6-Act Morphing Dynamic Attractor Centers along the Z Spline:
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

    // 2. Initialize 30,000-particle Persistent Lattice along the 6-Act Spline
    this.persistentInitialPositions = new Float32Array(this.persistentCount * 3);
    this.persistentVelocities = new Float32Array(this.persistentCount * 3);
    this.persistentPhases = new Float32Array(this.persistentCount);
    this.initPersistentLattice();
  }

  /**
   * Constructs the 1,200-particle kinetic wave field via InstancedMesh for zero draw-call overhead.
   */
  private initKineticWaveField(): void {
    const waveCount = 1200;
    const waveGeo = new THREE.SphereGeometry(0.016, 6, 6);
    const waveMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.72,
    });

    this.kineticWaveField = new THREE.InstancedMesh(waveGeo, waveMat, waveCount);
    this.kineticWaveField.name = 'KineticWaveField';
    this.kineticWaveField.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    const dummy = this.dummyObj;
    const prng = createPRNG(0x42);
    for (let i = 0; i < waveCount; i++) {
      const radius = 1.6 + Math.pow(prng(), 1.6) * 3.4;
      const angle = prng() * Math.PI * 2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = -1.48 + (prng() - 0.5) * 0.12;

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
   * Constructs the 30,000-particle persistent kinetic lattice via InstancedMesh
   * with dynamic attractor fields morphing across the 6 acts.
   */
  private initPersistentLattice(): void {
    const geo = new THREE.PlaneGeometry(0.02, 0.02);
    const mat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.38,
      side: THREE.DoubleSide,
      depthWrite: false,
    });

    this.persistentLattice = new THREE.InstancedMesh(geo, mat, this.persistentCount);
    this.persistentLattice.name = 'PersistentParticleLattice';
    this.persistentLattice.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    const dummy = this.dummyObj;
    const prng = createPRNG(0x1337);
    for (let i = 0; i < this.persistentCount; i++) {
      // Distribute along the 6-act corridor: Z from +10.0 down to -100.0
      const actProgress = i / this.persistentCount;
      const z = 8.5 - actProgress * 105.0 + (prng() - 0.5) * 8.0;
      const angle = prng() * Math.PI * 2;
      const radius = 0.5 + prng() * 4.5;
      const x = Math.cos(angle) * radius + (prng() - 0.5) * 1.5;
      const y = (prng() - 0.5) * 3.5;

      this.persistentInitialPositions[i * 3 + 0] = x;
      this.persistentInitialPositions[i * 3 + 1] = y;
      this.persistentInitialPositions[i * 3 + 2] = z;

      this.persistentVelocities[i * 3 + 0] = (prng() - 0.5) * 0.15;
      this.persistentVelocities[i * 3 + 1] = (prng() - 0.5) * 0.15;
      this.persistentVelocities[i * 3 + 2] = (prng() - 0.5) * 0.15;

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

  public getKineticWaveField(): THREE.InstancedMesh {
    return this.kineticWaveField;
  }

  public getPersistentLattice(): THREE.InstancedMesh {
    return this.persistentLattice;
  }

  /**
   * Updates wave fields and attractor fields with zero memory allocation.
   */
  public update(delta: number, scrollProgress: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    const dummy = this.dummyObj;

    // 1. Update 1,200 Kinetic Wave Field
    if (this.kineticWaveField && !isReducedMotion) {
      this.waveTime += clampedDelta * 1.4;
      const waveFreq = 2.4;
      const waveSpeed = 1.8;

      // In Act 1 hero (sp < 0.15), wave field is fully active; smoothly cross-fades out across acts
      const waveFade = THREE.MathUtils.clamp(1.0 - scrollProgress * 5.0, 0.05, 1.0);
      (this.kineticWaveField.material as THREE.MeshBasicMaterial).opacity = 0.72 * waveFade;

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

    // 2. Update 30,000 Persistent Lattice with Morphing Dynamic Attractor Fields
    if (this.persistentLattice && !isReducedMotion) {
      this.latticeTime += clampedDelta * 0.75;
      const t = this.latticeTime;

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

      // Morph dynamic attractor field by updating the active slice around the camera
      const sliceSize = 600;
      const startIdx = Math.floor(actIdx * 5000 + (t * 120) % 4000);
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

        dummy.position.set(bx + ox, by + oy, bz + oz);
        dummy.scale.setScalar(1.0 + Math.sin(t * 2.0 + phase) * 0.25 * swirlStrength);
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
  }
}
