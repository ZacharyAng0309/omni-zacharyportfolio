import * as THREE from 'three';

export interface Act5FrontierOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
  onSelectCaseStudyNode?: (slug: string) => void;
}

/**
 * Act5Frontier
 * Constructs and manages Act 5 The Frontier (Multi-Modal Agentic Systems & Fintech Value Engine):
 * - Flagship interactive system orb (raycastable node)
 * - 96-node Instanced Constellation Swarm
 * - Titanium Gyroscope Group (outer rings & central core)
 */
export class Act5Frontier {
  private frontierGroup: THREE.Group;
  private flagshipOrb: THREE.Mesh;
  private instancedNodes: THREE.InstancedMesh;
  private instancedNodeCount: number = 96;
  private instancedAngles: Float32Array = new Float32Array(96);
  private instancedRadii: Float32Array = new Float32Array(96);
  private instancedHeights: Float32Array = new Float32Array(96);
  private instancedSpeeds: Float32Array = new Float32Array(96);

  private gyroscopeGroup: THREE.Group;
  private constellationSet!: THREE.Group;
  private gyroRings: THREE.Mesh[] = [];
  private gyroCore: THREE.Mesh;

  private dummyObj: THREE.Object3D = new THREE.Object3D();
  private onSelectCaseStudyNode?: (slug: string) => void;

  constructor(options: Act5FrontierOptions) {
    this.onSelectCaseStudyNode = options.onSelectCaseStudyNode;
    this.frontierGroup = new THREE.Group();
    this.frontierGroup.name = 'FrontierGroup';
    this.frontierGroup.position.set(0, 0, -75.0); // Act 5 Station at Z = -75.0

    // 1. Flagship System Orb (Interactive Case Study Node)
    const orbMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      emissive: 0x005577,
      emissiveIntensity: 1.6,
      roughness: 0.2,
      metalness: 0.85,
    });
    this.flagshipOrb = new THREE.Mesh(new THREE.SphereGeometry(0.32, 32, 32), orbMat);
    this.flagshipOrb.name = 'FlagshipOrb';
    this.flagshipOrb.userData = { type: 'flagshipOrb', caseStudySlug: 'hireti' };
    this.flagshipOrb.position.set(2.2, 0.15, 0);
    this.frontierGroup.add(this.flagshipOrb);

    // 2. Gyroscope Group (Titanium Rings & Core)
    this.gyroscopeGroup = new THREE.Group();
    this.gyroscopeGroup.name = 'GyroscopeSet';
    this.gyroscopeGroup.position.set(2.2, 0.15, 0);

    const titaniumMat = new THREE.MeshStandardMaterial({
      color: 0x334155,
      metalness: 0.95,
      roughness: 0.15,
    });

    const ringRadii = [0.55, 0.68, 0.82];
    ringRadii.forEach((r, idx) => {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(r, 0.012, 16, 64), titaniumMat);
      ring.name = `GyroRing_${idx}`;
      ring.rotation.x = (idx * Math.PI) / 3;
      this.gyroRings.push(ring);
      this.gyroscopeGroup.add(ring);
    });

    this.gyroCore = new THREE.Mesh(
      new THREE.IcosahedronGeometry(0.18, 1),
      new THREE.MeshStandardMaterial({ color: 0x6366f1, emissive: 0x3730a3, roughness: 0.3 })
    );
    this.gyroCore.name = 'GyroCore';
    this.gyroscopeGroup.add(this.gyroCore);
    this.frontierGroup.add(this.gyroscopeGroup);

    // 3. 96-Node Instanced Constellation Swarm inside ConstellationSet Group
    this.constellationSet = new THREE.Group();
    this.constellationSet.name = 'ConstellationSet';

    const nodeGeo = new THREE.SphereGeometry(0.022, 8, 8);
    const nodeMat = new THREE.MeshBasicMaterial({ color: 0x6366f1 });
    this.instancedNodes = new THREE.InstancedMesh(nodeGeo, nodeMat, this.instancedNodeCount);
    this.instancedNodes.name = 'ConstellationSwarm';
    this.instancedNodes.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    for (let i = 0; i < this.instancedNodeCount; i++) {
      const angle = (i / this.instancedNodeCount) * Math.PI * 2;
      const radius = 1.2 + (i % 4) * 0.35;
      const height = ((i % 5) - 2) * 0.25;
      const speed = 0.4 + (i % 3) * 0.3;

      this.instancedAngles[i] = angle;
      this.instancedRadii[i] = radius;
      this.instancedHeights[i] = height;
      this.instancedSpeeds[i] = speed;

      this.dummyObj.position.set(2.2 + Math.cos(angle) * radius, 0.15 + height, Math.sin(angle) * radius);
      this.dummyObj.updateMatrix();
      this.instancedNodes.setMatrixAt(i, this.dummyObj.matrix);
    }
    this.instancedNodes.instanceMatrix.needsUpdate = true;
    this.constellationSet.add(this.instancedNodes);
    this.frontierGroup.add(this.constellationSet);

    // 4. EnterpriseTerminalWorkstation & FrontierScreenMesh (Acts 1, 3, 5 High-Contrast Emissive Displays)
    const enterpriseWorkstation = new THREE.Group();
    enterpriseWorkstation.name = 'EnterpriseTerminalWorkstation';
    enterpriseWorkstation.position.set(2.2, -0.85, -0.5);

    const fCanvas = document.createElement('canvas');
    fCanvas.width = 128;
    fCanvas.height = 128;
    const fCtx = fCanvas.getContext('2d');
    if (fCtx) {
      fCtx.fillStyle = '#0f172a';
      fCtx.fillRect(0, 0, 128, 128);
      fCtx.fillStyle = '#6366f1';
      fCtx.fillRect(10, 10, 108, 108);
    }
    const fTex = new THREE.CanvasTexture(fCanvas);
    const fMat = new THREE.MeshStandardMaterial({
      color: 0x111827,
      emissive: 0x6366f1,
      emissiveIntensity: 1.3,
      emissiveMap: fTex,
      roughness: 0.2,
      metalness: 0.8,
    });
    const fMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.55, 0.35), fMat);
    fMesh.name = 'FrontierScreenMesh';
    fMesh.rotation.x = -Math.PI * 0.15;
    enterpriseWorkstation.add(fMesh);
    this.frontierGroup.add(enterpriseWorkstation);

    // Default visibility at sp = 0.0 is hidden
    this.constellationSet.visible = false;
    this.gyroscopeGroup.visible = false;

    options.scene.add(this.frontierGroup);

    options.materialsList.push(orbMat, titaniumMat, nodeMat, fMat);
  }

  public getFrontierGroup(): THREE.Group { return this.frontierGroup; }
  public getFlagshipOrb(): THREE.Mesh { return this.flagshipOrb; }
  public getGyroscopeGroup(): THREE.Group { return this.gyroscopeGroup; }
  public getInstancedNodes(): THREE.InstancedMesh { return this.instancedNodes; }

  public triggerCaseStudyCallback(slug: string): void {
    this.onSelectCaseStudyNode?.(slug);
  }

  public update(delta: number, isReducedMotion: boolean = false, scrollProgress?: number): void {
    if (scrollProgress !== undefined) {
      const isVisible = scrollProgress >= 0.70 && scrollProgress <= 0.95;
      this.constellationSet.visible = isVisible;
      this.gyroscopeGroup.visible = isVisible;
    }
    const clampedDelta = Math.min(delta, 0.1);
    if (!isReducedMotion) {
      this.flagshipOrb.rotation.y += clampedDelta * 0.5;

      this.gyroRings.forEach((r, idx) => {
        r.rotation.x += clampedDelta * (0.3 + idx * 0.2);
        r.rotation.y += clampedDelta * (0.4 - idx * 0.15);
      });
      this.gyroCore.rotation.y -= clampedDelta * 0.8;

      const dummy = this.dummyObj;
      for (let i = 0; i < this.instancedNodeCount; i++) {
        const speed = this.instancedSpeeds[i] ?? 0.5;
        const curAngle = (this.instancedAngles[i] ?? 0) + speed * clampedDelta;
        this.instancedAngles[i] = curAngle;
        const radius = this.instancedRadii[i] ?? 1.2;
        const height = this.instancedHeights[i] ?? 0;

        dummy.position.set(2.2 + Math.cos(curAngle) * radius, 0.15 + height, Math.sin(curAngle) * radius);
        dummy.updateMatrix();
        this.instancedNodes.setMatrixAt(i, dummy.matrix);
      }
      this.instancedNodes.instanceMatrix.needsUpdate = true;
    }
  }

  public dispose(): void {}
}
