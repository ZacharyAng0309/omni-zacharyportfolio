import * as THREE from 'three';

export interface Act1StrategicCoreOptions {
  avatarRig: THREE.Group;
  materialsList: THREE.Material[];
}

/**
 * Act1StrategicCore
 * Constructs and manages the Act 1 Executive Strategy Studio & Interactive Enterprise AI Engine:
 * - Circular presentation plinth (Y = -1.55) & cyan illuminated perimeter ring (Y = -1.48)
 * - PersonaBody anchor (Y = -1.45 flush on plinth)
 * - 3-tier strata architecture (Containment Shield, Clearing Ring, Generative Neural Core)
 * - 6 Strata Connection Vectors with spring-damped expansion
 * - 96 Instanced glowing data nodes (ISO-20022 Financial Network)
 * - Drag rotation inertia and explode_strata dynamics
 */
export class Act1StrategicCore {
  private avatarRig: THREE.Group;
  private personaBodyGroup: THREE.Group;
  private enterpriseEngineGroup: THREE.Group;
  private engineTier1: THREE.Group;
  private engineTier2: THREE.Group;
  private engineTier3: THREE.Group;
  private engineVectorsGroup: THREE.Group;
  private engineVectors: THREE.Mesh[] = [];

  private clearingInstancedNodes: THREE.InstancedMesh;
  private clearingNodeAngles: Float32Array = new Float32Array(96);
  private clearingNodeRadii: Float32Array = new Float32Array(96);
  private clearingNodeSpeeds: Float32Array = new Float32Array(96);
  private clearingNodeHeights: Float32Array = new Float32Array(96);
  private clearingRingA: THREE.Mesh;
  private clearingRingB: THREE.Mesh;

  private neuralCoreLattice: THREE.Mesh;
  private neuralCoreInner: THREE.Mesh;
  private coreOriginalPositions: Float32Array | null = null;

  private studioGroup: THREE.Group;
  private curvedDisplaysGroup: THREE.Group;
  private executiveDesk: THREE.Group;
  private executiveTablet: THREE.Group;
  private executiveChair: THREE.Group;

  private isEngineExploded: boolean = false;
  private currentExplodeFactor: number = 0;
  private dummyObj: THREE.Object3D = new THREE.Object3D();

  private dragAngleX: number = 0;
  private dragAngleY: number = 0;
  private rotVelX: number = 0;
  private rotVelY: number = 0;
  private isDragging: boolean = false;
  private prevMouseX: number = 0;
  private prevMouseY: number = 0;

  private plinthMesh: THREE.Mesh;
  private plinthGlowRing: THREE.Mesh;
  private plinthMat: THREE.MeshStandardMaterial;
  private plinthGlowMat: THREE.MeshBasicMaterial;

  constructor(options: Act1StrategicCoreOptions) {
    this.avatarRig = options.avatarRig;

    // 1. Presentation Plinth & Glow Ring
    const plinthGeo = new THREE.CylinderGeometry(1.45, 1.55, 0.20, 64);
    this.plinthMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.32,
      metalness: 0.88,
      transparent: true,
      opacity: 1.0,
    });
    this.plinthMesh = new THREE.Mesh(plinthGeo, this.plinthMat);
    this.plinthMesh.name = 'Plinth';
    this.plinthMesh.position.y = -1.55;
    this.plinthMesh.receiveShadow = true;
    this.plinthMesh.visible = true;
    this.avatarRig.add(this.plinthMesh);

    this.plinthGlowMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.95 });
    this.plinthGlowRing = new THREE.Mesh(new THREE.TorusGeometry(1.42, 0.022, 16, 72), this.plinthGlowMat);
    this.plinthGlowRing.name = 'PlinthGlowRing';
    this.plinthGlowRing.rotation.x = Math.PI / 2;
    this.plinthGlowRing.position.y = -1.48;
    this.plinthGlowRing.visible = true;
    this.avatarRig.add(this.plinthGlowRing);

    // Option B procedural grounded legs
    const legGeo = new THREE.CylinderGeometry(0.08, 0.07, 0.70, 16);
    const legMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.8,
      metalness: 0.2,
    });
    const leftLeg = new THREE.Mesh(legGeo, legMat);
    leftLeg.name = 'LeftLegMesh';
    leftLeg.position.set(-0.16, -1.05, 0);
    leftLeg.visible = false;
    this.avatarRig.add(leftLeg);

    const rightLeg = new THREE.Mesh(legGeo, legMat);
    rightLeg.name = 'RightLegMesh';
    rightLeg.position.set(0.16, -1.05, 0);
    rightLeg.visible = false;
    this.avatarRig.add(rightLeg);

    options.materialsList.push(this.plinthMat, this.plinthGlowMat, legMat);

    // 2. Master Persona Body Group (Station Y = -1.45 on top surface of plinth)
    this.personaBodyGroup = new THREE.Group();
    this.personaBodyGroup.name = 'PersonaBody';
    this.personaBodyGroup.position.set(0, -1.45, 0);
    this.avatarRig.add(this.personaBodyGroup);

    // 3. Enterprise AI Engine Root Group
    this.enterpriseEngineGroup = new THREE.Group();
    this.enterpriseEngineGroup.name = 'EnterpriseAIEngine';
    this.enterpriseEngineGroup.position.set(0, 0, 0);
    this.avatarRig.add(this.enterpriseEngineGroup);

    const legacyMonolith = new THREE.Group();
    legacyMonolith.name = 'KeynoteCrystalMonolith';
    legacyMonolith.visible = false;
    this.enterpriseEngineGroup.add(legacyMonolith);

    // 4. Strata Connection Vectors
    this.engineVectorsGroup = new THREE.Group();
    this.engineVectorsGroup.name = 'EngineVectorsGroup';
    const vectorGeo = new THREE.CylinderGeometry(0.007, 0.007, 1.0, 8);
    const vectorMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.45,
    });
    const vectorCount = 6;
    for (let v = 0; v < vectorCount; v++) {
      const angle = (v / vectorCount) * Math.PI * 2;
      const vx = Math.cos(angle) * 0.45;
      const vz = Math.sin(angle) * 0.45;
      const vectorMesh = new THREE.Mesh(vectorGeo, vectorMat);
      vectorMesh.name = `EngineVector_${v}`;
      vectorMesh.position.set(vx, 0, vz);
      vectorMesh.scale.set(1.0, 0.15, 1.0);
      this.engineVectors.push(vectorMesh);
      this.engineVectorsGroup.add(vectorMesh);
    }
    this.enterpriseEngineGroup.add(this.engineVectorsGroup);

    // 5. Tier 1: Outer Containment Shield (Frosted Physical Transmission Glass)
    this.engineTier1 = new THREE.Group();
    this.engineTier1.name = 'EngineTier1';
    const shieldGlassMat = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(0x0a192f),
      transmission: 0.65,
      roughness: 0.15,
      metalness: 0.1,
      clearcoat: 1.0,
      clearcoatRoughness: 0.10,
      ior: 1.52,
      thickness: 0.12,
      transparent: true,
      opacity: 0.88,
    });
    const outerShieldRing = new THREE.Mesh(new THREE.TorusGeometry(1.18, 0.045, 32, 96), shieldGlassMat);
    outerShieldRing.name = 'ShieldOuterTorus';
    outerShieldRing.castShadow = true;
    outerShieldRing.receiveShadow = true;
    this.engineTier1.add(outerShieldRing);

    const innerShieldRing = new THREE.Mesh(new THREE.TorusGeometry(1.04, 0.035, 32, 96), shieldGlassMat);
    innerShieldRing.name = 'ShieldInclinedRing';
    innerShieldRing.rotation.x = Math.PI / 4.5;
    innerShieldRing.rotation.z = Math.PI / 12;
    this.engineTier1.add(innerShieldRing);

    const rimSpecularMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.75 });
    const specularRim = new THREE.Mesh(new THREE.TorusGeometry(1.22, 0.007, 16, 96), rimSpecularMat);
    specularRim.name = 'ShieldSpecularRim';
    this.engineTier1.add(specularRim);

    // 4 Titanium Bezel Brackets
    const titaniumMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.94,
      roughness: 0.18,
    });
    const bracketGeo = new THREE.BoxGeometry(0.06, 0.12, 0.08);
    for (let b = 0; b < 4; b++) {
      const bAngle = (b / 4) * Math.PI * 2;
      const bracket = new THREE.Mesh(bracketGeo, titaniumMat);
      bracket.position.set(Math.cos(bAngle) * 1.18, 0, Math.sin(bAngle) * 1.18);
      bracket.rotation.y = -bAngle;
      this.engineTier1.add(bracket);
    }
    this.enterpriseEngineGroup.add(this.engineTier1);

    // 6. Tier 2: Middle Clearing Ring (ISO-20022 Financial Network)
    this.engineTier2 = new THREE.Group();
    this.engineTier2.name = 'EngineTier2';
    const ringAMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.88, roughness: 0.22 });
    this.clearingRingA = new THREE.Mesh(new THREE.TorusGeometry(0.86, 0.024, 16, 80), ringAMat);
    this.clearingRingA.name = 'ClearingRingA';
    this.engineTier2.add(this.clearingRingA);

    const ringBMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.92, roughness: 0.16 });
    this.clearingRingB = new THREE.Mesh(new THREE.TorusGeometry(0.72, 0.018, 16, 80), ringBMat);
    this.clearingRingB.name = 'ClearingRingB';
    this.engineTier2.add(this.clearingRingB);

    const equatorDisc = new THREE.Mesh(
      new THREE.RingGeometry(0.70, 0.88, 64),
      new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.20, side: THREE.DoubleSide })
    );
    equatorDisc.rotation.x = Math.PI / 2;
    this.engineTier2.add(equatorDisc);

    // 8 Radial Gate Stators
    const statorGeo = new THREE.BoxGeometry(0.14, 0.012, 0.02);
    for (let s = 0; s < 8; s++) {
      const sAngle = (s / 8) * Math.PI * 2;
      const stator = new THREE.Mesh(statorGeo, titaniumMat);
      stator.position.set(Math.cos(sAngle) * 0.79, 0, Math.sin(sAngle) * 0.79);
      stator.rotation.y = -sAngle;
      this.engineTier2.add(stator);
    }

    // 96 Instanced Data Nodes
    const nodeCount = 96;
    const nodeGeo = new THREE.SphereGeometry(0.024, 8, 8);
    const nodeMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      emissive: 0x00f2fe,
      emissiveIntensity: 1.8,
      roughness: 0.15,
      metalness: 0.85,
    });
    this.clearingInstancedNodes = new THREE.InstancedMesh(nodeGeo, nodeMat, nodeCount);
    this.clearingInstancedNodes.name = 'ClearingDataNodes';
    this.clearingInstancedNodes.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    for (let i = 0; i < nodeCount; i++) {
      const angle = (i / nodeCount) * Math.PI * 2;
      const radius = 0.72 + (i % 3) * 0.07;
      const speed = 0.6 + (i % 5) * 0.25;
      const height = ((i % 7) - 3) * 0.012;

      this.clearingNodeAngles[i] = angle;
      this.clearingNodeRadii[i] = radius;
      this.clearingNodeSpeeds[i] = speed;
      this.clearingNodeHeights[i] = height;

      this.dummyObj.position.set(Math.cos(angle) * radius, height, Math.sin(angle) * radius);
      this.dummyObj.updateMatrix();
      this.clearingInstancedNodes.setMatrixAt(i, this.dummyObj.matrix);
    }
    this.clearingInstancedNodes.instanceMatrix.needsUpdate = true;
    this.engineTier2.add(this.clearingInstancedNodes);
    this.enterpriseEngineGroup.add(this.engineTier2);

    // 7. Tier 3: Inner Generative Neural Core
    this.engineTier3 = new THREE.Group();
    this.engineTier3.name = 'EngineTier3';
    const latticeGeo = new THREE.IcosahedronGeometry(0.40, 2);
    if (latticeGeo.attributes.position) {
      this.coreOriginalPositions = new Float32Array(latticeGeo.attributes.position.array);
    }
    const latticeMat = new THREE.MeshPhysicalMaterial({
      color: 0x00f2fe,
      emissive: 0x00334e,
      emissiveIntensity: 0.75,
      roughness: 0.18,
      metalness: 0.85,
      wireframe: true,
      transparent: true,
      opacity: 0.85,
    });
    this.neuralCoreLattice = new THREE.Mesh(latticeGeo, latticeMat);
    this.neuralCoreLattice.name = 'NeuralCoreLattice';
    this.engineTier3.add(this.neuralCoreLattice);

    const nucleusGeo = new THREE.IcosahedronGeometry(0.24, 1);
    const nucleusMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      emissive: 0x00f2fe,
      emissiveIntensity: 2.2,
      roughness: 0.15,
      metalness: 0.85,
    });
    this.neuralCoreInner = new THREE.Mesh(nucleusGeo, nucleusMat);
    this.neuralCoreInner.name = 'NeuralCoreNucleus';
    this.engineTier3.add(this.neuralCoreInner);
    this.enterpriseEngineGroup.add(this.engineTier3);

    // 8. Executive Strategy Studio Props
    this.studioGroup = new THREE.Group();
    this.studioGroup.name = 'StudioGroup';

    this.curvedDisplaysGroup = new THREE.Group();
    this.curvedDisplaysGroup.name = 'CurvedDisplays';
    const displayMat = new THREE.MeshStandardMaterial({ color: 0x111827, metalness: 0.8, roughness: 0.2 });
    const screenMesh = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, 0.7, 32, 1, true, 0, Math.PI * 0.4), displayMat);
    screenMesh.rotation.y = -Math.PI * 0.2;
    screenMesh.position.set(0, 0.35, 1.2);
    this.curvedDisplaysGroup.add(screenMesh);
    this.studioGroup.add(this.curvedDisplaysGroup);

    this.executiveDesk = new THREE.Group();
    this.executiveDesk.name = 'ExecutiveDesk';
    const deskTop = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.08, 0.9), displayMat);
    deskTop.position.set(0, -0.1, 0.9);
    this.executiveDesk.add(deskTop);
    this.studioGroup.add(this.executiveDesk);

    this.executiveTablet = new THREE.Group();
    this.executiveTablet.name = 'ExecutiveTablet';
    const tabletMesh = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.01, 0.20), new THREE.MeshBasicMaterial({ color: 0x00f2fe, wireframe: true }));
    tabletMesh.position.set(0.35, -0.05, 0.75);
    this.executiveTablet.add(tabletMesh);
    this.studioGroup.add(this.executiveTablet);

    // Executive Lounge Chair (Eames / Modern Architectural aesthetic)
    this.executiveChair = new THREE.Group();
    this.executiveChair.name = 'ExecutiveChair';
    this.executiveChair.position.set(0, -1.45, -0.05);

    const leatherMat = new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.65, metalness: 0.1 });
    const woodShellMat = new THREE.MeshStandardMaterial({ color: 0x271c19, roughness: 0.4, metalness: 0.2 });
    const steelMat = new THREE.MeshStandardMaterial({ color: 0x71717a, roughness: 0.2, metalness: 0.9 });

    const seatCushion = new THREE.Mesh(new THREE.BoxGeometry(0.70, 0.12, 0.65), leatherMat);
    seatCushion.position.set(0, 0.45, 0);
    this.executiveChair.add(seatCushion);

    const seatShell = new THREE.Mesh(new THREE.BoxGeometry(0.74, 0.06, 0.69), woodShellMat);
    seatShell.position.set(0, 0.38, 0);
    this.executiveChair.add(seatShell);

    const backCushion = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.65, 0.12), leatherMat);
    backCushion.position.set(0, 0.85, -0.30);
    backCushion.rotation.x = -0.15;
    this.executiveChair.add(backCushion);

    const backShell = new THREE.Mesh(new THREE.BoxGeometry(0.69, 0.69, 0.06), woodShellMat);
    backShell.position.set(0, 0.85, -0.36);
    backShell.rotation.x = -0.15;
    this.executiveChair.add(backShell);

    const chairStem = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.35, 16), steelMat);
    chairStem.position.set(0, 0.18, 0);
    this.executiveChair.add(chairStem);

    const chairBase = new THREE.Mesh(new THREE.CylinderGeometry(0.40, 0.40, 0.04, 32), steelMat);
    chairBase.position.set(0, 0.02, 0);
    this.executiveChair.add(chairBase);

    this.studioGroup.add(this.executiveChair);

    this.avatarRig.add(this.studioGroup);

    // Register Act 1 materials for cross-fading
    options.materialsList.push(
      this.plinthMat,
      this.plinthGlowMat,
      vectorMat,
      shieldGlassMat,
      rimSpecularMat,
      titaniumMat,
      ringAMat,
      ringBMat,
      nodeMat,
      latticeMat,
      nucleusMat,
      displayMat
    );
  }

  public getPlinth(): THREE.Mesh { return this.plinthMesh; }
  public getPlinthGlowRing(): THREE.Mesh { return this.plinthGlowRing; }
  public getEnterpriseAIEngine(): THREE.Group { return this.enterpriseEngineGroup; }
  public getEngineTier1(): THREE.Group { return this.engineTier1; }
  public getEngineTier2(): THREE.Group { return this.engineTier2; }
  public getEngineTier3(): THREE.Group { return this.engineTier3; }
  public getEngineVectorsGroup(): THREE.Group { return this.engineVectorsGroup; }
  public getStudioGroup(): THREE.Group { return this.studioGroup; }
  public getCurvedDisplays(): THREE.Group { return this.curvedDisplaysGroup; }
  public getExecutiveChair(): THREE.Group { return this.executiveChair; }
  public getExecutiveDesk(): THREE.Group { return this.executiveDesk; }
  public getExecutiveTablet(): THREE.Group { return this.executiveTablet; }

  public isEngineExplodedState(): boolean {
    return this.isEngineExploded;
  }

  public toggleExplode(): boolean {
    this.isEngineExploded = !this.isEngineExploded;
    return this.isEngineExploded;
  }

  public setExploded(exploded: boolean): void {
    this.isEngineExploded = exploded;
  }

  public onPointerDown(clientX: number, clientY: number): void {
    this.isDragging = true;
    this.prevMouseX = clientX;
    this.prevMouseY = clientY;
  }

  public onPointerMove(clientX: number, clientY: number): void {
    if (!this.isDragging) return;
    const dx = clientX - this.prevMouseX;
    const dy = clientY - this.prevMouseY;
    this.prevMouseX = clientX;
    this.prevMouseY = clientY;

    this.rotVelY = dx * 0.006;
    this.rotVelX = dy * 0.006;

    this.dragAngleY += this.rotVelY;
    this.dragAngleX += this.rotVelX;
  }

  public onPointerUp(): void {
    this.isDragging = false;
  }

  public update(delta: number, isReducedMotion: boolean = false, scrollProgress: number = 0): void {
    const sp = Number.isFinite(scrollProgress) ? Math.max(0, scrollProgress) : 0;
    this.studioGroup.visible = sp <= 0.16;
    this.enterpriseEngineGroup.visible = sp <= 0.16;

    // Plinth and Glow Ring Transition across Acts:
    // Scale down and fade out when leaving Act 1 (sp > 0.16), and restore when returning to Act 1
    const plinthTransitionEnd = 0.22;
    let plinthFactor = 1.0;
    if (sp > 0.16) {
      const exitProgress = Math.min(1.0, (sp - 0.16) / (plinthTransitionEnd - 0.16));
      plinthFactor = Math.max(0.0, 1.0 - exitProgress);
    }

    this.plinthMesh.scale.set(plinthFactor, plinthFactor, plinthFactor);
    this.plinthGlowRing.scale.set(plinthFactor, plinthFactor, plinthFactor);
    this.plinthMat.opacity = plinthFactor;
    this.plinthGlowMat.opacity = 0.95 * plinthFactor;
    this.plinthMesh.visible = plinthFactor > 0.001;
    this.plinthGlowRing.visible = plinthFactor > 0.001;

    const clampedDelta = Math.min(delta, 0.1);

    // 1. Spring-damped Strata Explosion Dynamics
    const targetFactor = this.isEngineExploded ? 1.0 : 0.0;
    this.currentExplodeFactor = isReducedMotion
      ? targetFactor
      : THREE.MathUtils.damp(this.currentExplodeFactor, targetFactor, 8.0, clampedDelta);

    // Vertical displacement
    const tier1Displacement = this.currentExplodeFactor * 0.95;
    const tier3Displacement = -this.currentExplodeFactor * 0.85;

    this.engineTier1.position.y = tier1Displacement;
    this.engineTier3.position.y = tier3Displacement;

    // Expand connection vectors
    const vectorScaleY = 0.15 + this.currentExplodeFactor * 1.65;
    for (const vector of this.engineVectors) {
      vector.scale.y = vectorScaleY;
      (vector.material as THREE.MeshBasicMaterial).opacity = 0.35 + this.currentExplodeFactor * 0.55;
    }

    // 2. Drag & Inertia Dynamics
    if (!this.isDragging) {
      this.rotVelX *= 0.96;
      this.rotVelY *= 0.96;
      this.dragAngleX += this.rotVelX;
      this.dragAngleY += this.rotVelY;
    }
    this.enterpriseEngineGroup.rotation.x = this.dragAngleX;
    this.enterpriseEngineGroup.rotation.y = this.dragAngleY;

    // 3. Counter-rotating rings & Gyro Motion (culled when engine is hidden)
    if (this.enterpriseEngineGroup.visible && !isReducedMotion) {
      this.clearingRingA.rotation.z += 0.45 * clampedDelta;
      this.clearingRingB.rotation.z -= 0.55 * clampedDelta;
      this.engineTier1.rotation.y += 0.22 * clampedDelta;

      // Pulse Nucleus heartbeat
      const heartBeat = 1.0 + Math.sin(Date.now() * 0.004) * 0.18;
      this.neuralCoreInner.scale.set(heartBeat, heartBeat, heartBeat);

      // Animate Outer Neural Core Lattice with Vertex Noise Morphing
      if (this.neuralCoreLattice && this.coreOriginalPositions) {
        const geo = this.neuralCoreLattice.geometry;
        const posAttr = geo.attributes.position;
        if (posAttr) {
          const orig = this.coreOriginalPositions;
          const timeFactor = Date.now() * 0.003;
          for (let i = 0; i < posAttr.count; i++) {
            const i3 = i * 3;
            const ox = orig[i3 + 0] ?? 0;
            const oy = orig[i3 + 1] ?? 0;
            const oz = orig[i3 + 2] ?? 0;
            const displacement = Math.sin(timeFactor + ox * 5.0 + oy * 5.0) * 0.035;
            posAttr.setXYZ(i, ox + ox * displacement, oy + oy * displacement, oz + oz * displacement);
          }
          posAttr.needsUpdate = true;
        }
      }

      // Animate 96 Instanced Nodes
      const dummy = this.dummyObj;
      for (let i = 0; i < 96; i++) {
        const speed = this.clearingNodeSpeeds[i] ?? 1.0;
        const curAngle = (this.clearingNodeAngles[i] ?? 0) + speed * clampedDelta;
        this.clearingNodeAngles[i] = curAngle;
        const r = this.clearingNodeRadii[i] ?? 0.8;
        const h = this.clearingNodeHeights[i] ?? 0;

        dummy.position.set(Math.cos(curAngle) * r, h, Math.sin(curAngle) * r);
        dummy.updateMatrix();
        this.clearingInstancedNodes.setMatrixAt(i, dummy.matrix);
      }
      this.clearingInstancedNodes.instanceMatrix.needsUpdate = true;
    }
  }

  public dispose(): void {
    // All geometries and materials registered with scene will be recursed
  }
}
