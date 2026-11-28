import * as THREE from 'three';
import {
  applyStudioEnvMapToRoot,
  createGltfLoader,
  resolveAssetUrl,
} from '../core/gltfLoader';
import { assetUrl } from '../../utils/assetUrl';

export interface Act5FrontierOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
  onSelectCaseStudyNode?: (slug: string) => void;
  onModelLoaded?: () => void;
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
  private strataTier1: THREE.Mesh;
  private strataTier3: THREE.Mesh;
  private isStrataExploded: boolean = false;
  private explodeFactor: number = 0;
  private selectedCoreSlug: string = 'hireti-sweetzerland';
  private frontierScreenMat: THREE.MeshStandardMaterial;
  private enterpriseWorkstationGroup: THREE.Group;
  private glbCoreAccentMats: THREE.MeshStandardMaterial[] = [];
  private frontierConduitsGroup: THREE.Group;
  private frontierWaferRings: THREE.Mesh[] = [];
  private frontierTensorCore!: THREE.Mesh;
  private frontierPacketRings: THREE.Mesh[] = [];
  private commandHoloDeck: THREE.Group;
  private frontierHoloTextures: THREE.CanvasTexture[] = [];
  private disposableGeos: THREE.BufferGeometry[] = [];
  private studioEnvMap: THREE.Texture | null = null;
  private hasRequestedLoad: boolean = false;
  private isGlbLoaded: boolean = false;
  private onModelLoaded?: () => void;
  private glbCoreTiers: {
    t1: THREE.Object3D | null;
    t2: THREE.Object3D | null;
    t3: THREE.Object3D | null;
    baseY1: number;
    baseY2: number;
    baseY3: number;
  } = { t1: null, t2: null, t3: null, baseY1: 1.56, baseY2: 1.24, baseY3: 0.92 };

  private dummyObj: THREE.Object3D = new THREE.Object3D();
  private onSelectCaseStudyNode?: (slug: string) => void;

  private createMonitorTelemetryTexture(spec: {
    title: string;
    subtitle: string;
    metric: string;
    accent: string;
    bars: readonly number[];
  }): THREE.CanvasTexture | null {
    if (typeof document === 'undefined') return null;
    try {
      const hCanvas = document.createElement('canvas');
      hCanvas.width = 256;
      hCanvas.height = 144;
      const hCtx = hCanvas.getContext('2d');
      if (!hCtx) return null;

      const grad = hCtx.createLinearGradient(0, 0, 256, 144);
      grad.addColorStop(0.0, '#090e17');
      grad.addColorStop(1.0, '#161114');
      hCtx.fillStyle = grad;
      hCtx.fillRect(0, 0, 256, 144);

      hCtx.strokeStyle = spec.accent;
      hCtx.lineWidth = 3;
      hCtx.strokeRect(5, 5, 246, 134);
      hCtx.strokeStyle = 'rgba(255, 255, 255, 0.16)';
      hCtx.lineWidth = 1;
      hCtx.strokeRect(10, 10, 236, 124);

      hCtx.fillStyle = spec.accent;
      hCtx.font = 'bold 12px sans-serif';
      hCtx.fillText(spec.title, 18, 30);

      hCtx.fillStyle = '#cbd5e1';
      hCtx.font = '10px monospace';
      hCtx.fillText(spec.subtitle, 18, 46);

      hCtx.fillStyle = '#f8fafc';
      hCtx.font = 'bold 16px monospace';
      hCtx.fillText(spec.metric, 18, 70);

      spec.bars.forEach((ratio, idx) => {
        const y = 84 + idx * 12;
        hCtx.fillStyle = 'rgba(255,255,255,0.10)';
        hCtx.fillRect(18, y, 220, 7);
        hCtx.fillStyle = spec.accent;
        hCtx.fillRect(18, y, Math.round(220 * ratio), 7);
      });

      const tex = new THREE.CanvasTexture(hCanvas);
      tex.colorSpace = THREE.SRGBColorSpace;
      this.frontierHoloTextures.push(tex);
      return tex;
    } catch {
      return null;
    }
  }

  constructor(options: Act5FrontierOptions) {
    this.onSelectCaseStudyNode = options.onSelectCaseStudyNode;
    this.onModelLoaded = options.onModelLoaded;
    this.frontierGroup = new THREE.Group();
    this.frontierGroup.name = 'FrontierGroup';
    this.frontierGroup.position.set(0, 0, -75.0); // Act 5 Station at Z = -75.0

    // 0. Grounded Orbital AI Lab Island (SM_Island_Act5)
    const islandMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.3,
      metalness: 0.88,
    });
    const islandMesh = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.55, 0.20, 48), islandMat);
    islandMesh.name = 'SM_Island_Act5';
    islandMesh.position.set(1.35, -1.55, 0.0);
    islandMesh.receiveShadow = true;
    this.frontierGroup.add(islandMesh);
    options.materialsList.push(islandMat);

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
    this.flagshipOrb.userData = { type: 'flagshipOrb', caseStudySlug: 'hireti', actIndex: 4, subTargetId: 'hireti-sweetzerland' };
    this.flagshipOrb.position.set(2.2, 0.15, 0);
    this.frontierGroup.add(this.flagshipOrb);

    // 2. Gyroscope Group (Titanium Rings, Core & 3-Strata Explodable Wafers)
    this.gyroscopeGroup = new THREE.Group();
    this.gyroscopeGroup.name = 'GyroscopeSet';
    this.gyroscopeGroup.position.set(2.2, 0.15, 0);

    const strataMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.55,
      side: THREE.DoubleSide,
    });
    this.strataTier1 = new THREE.Mesh(new THREE.RingGeometry(0.35, 0.58, 32), strataMat);
    this.strataTier1.name = 'FrontierStrataTier1';
    this.strataTier1.rotation.x = Math.PI / 2;
    this.strataTier1.position.y = 0.22;
    this.gyroscopeGroup.add(this.strataTier1);

    this.strataTier3 = new THREE.Mesh(new THREE.RingGeometry(0.35, 0.58, 32), strataMat);
    this.strataTier3.name = 'FrontierStrataTier3';
    this.strataTier3.rotation.x = Math.PI / 2;
    this.strataTier3.position.y = -0.22;
    this.gyroscopeGroup.add(this.strataTier3);
    options.materialsList.push(strataMat);

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
    this.enterpriseWorkstationGroup = enterpriseWorkstation;

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
    this.frontierScreenMat = fMat;
    const fMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.55, 0.35), fMat);
    fMesh.name = 'FrontierScreenMesh';
    fMesh.rotation.x = -Math.PI * 0.15;
    enterpriseWorkstation.add(fMesh);
    this.frontierGroup.add(enterpriseWorkstation);

    // Default visibility at sp = 0.0 is hidden
    this.constellationSet.visible = false;
    this.gyroscopeGroup.visible = false;

    // 5. Optical Fiber Conduits & Wafer Perimeter Rings (linking pedestal T3..T1 to orbital halo)
    this.frontierConduitsGroup = new THREE.Group();
    this.frontierConduitsGroup.name = 'FrontierOpticalConduits';
    this.frontierConduitsGroup.position.set(2.20, -1.45, 0);

    const conduitGeo = new THREE.CylinderGeometry(0.0045, 0.0045, 1.32, 8);
    const conduitMat = new THREE.MeshBasicMaterial({
      color: 0x22d3ee,
      transparent: true,
      opacity: 0.68,
    });
    this.disposableGeos.push(conduitGeo);
    options.materialsList.push(conduitMat);

    for (const cx of [-0.24, 0.24] as const) {
      for (const cz of [-0.16, 0.16] as const) {
        const rod = new THREE.Mesh(conduitGeo, conduitMat);
        rod.name = `FrontierConduit_${cx > 0 ? 'R' : 'L'}_${cz > 0 ? 'F' : 'B'}`;
        rod.position.set(cx, 1.46, cz);
        this.frontierConduitsGroup.add(rod);
      }
    }

    const waferRingGeo = new THREE.TorusGeometry(0.36, 0.005, 8, 48);
    this.disposableGeos.push(waferRingGeo);
    const waferRingSpecs = [
      { y: 0.93, color: 0x22d3ee },
      { y: 1.25, color: 0xf97316 },
      { y: 1.57, color: 0x22d3ee },
    ];
    waferRingSpecs.forEach((spec, wIdx) => {
      const wMat = new THREE.MeshBasicMaterial({
        color: spec.color,
        transparent: true,
        opacity: 0.72,
      });
      const wRing = new THREE.Mesh(waferRingGeo, wMat);
      wRing.name = `FrontierWaferRing_${wIdx}`;
      wRing.rotation.x = Math.PI / 2;
      wRing.position.y = spec.y;
      options.materialsList.push(wMat);
      this.frontierWaferRings.push(wRing);
      this.frontierConduitsGroup.add(wRing);
    });

    const tensorCoreGeo = new THREE.CylinderGeometry(0.16, 0.16, 0.68, 8);
    const tensorCoreMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.18,
      wireframe: true,
    });
    this.disposableGeos.push(tensorCoreGeo);
    options.materialsList.push(tensorCoreMat);
    this.frontierTensorCore = new THREE.Mesh(tensorCoreGeo, tensorCoreMat);
    this.frontierTensorCore.name = 'FrontierTensorCore';
    this.frontierTensorCore.position.set(0, 1.25, 0);
    this.frontierConduitsGroup.add(this.frontierTensorCore);

    // Inter-strata glowing optical packet rings pulsing along the tensor core conduits
    const packetRingGeo = new THREE.TorusGeometry(0.145, 0.008, 8, 28);
    const packetRingMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.78,
    });
    this.disposableGeos.push(packetRingGeo);
    options.materialsList.push(packetRingMat);
    for (let p = 0; p < 3; p++) {
      const pRing = new THREE.Mesh(packetRingGeo, packetRingMat);
      pRing.name = `FrontierPacketRing_${p}`;
      pRing.rotation.x = Math.PI / 2;
      pRing.position.y = 0.96 + p * 0.28;
      this.frontierPacketRings.push(pRing);
      this.frontierConduitsGroup.add(pRing);
    }

    this.frontierGroup.add(this.frontierConduitsGroup);

    // 6. FrontierCommandHoloDeck: 3 Curved Holographic AI/Fintech Monitors Seated on Left Console Arc
    this.commandHoloDeck = new THREE.Group();
    this.commandHoloDeck.name = 'FrontierCommandHoloDeck';
    // Console arc in act5_frontier.glb has r=2.65m around (1.15, 0) with tabletop at local Y = -0.775
    this.commandHoloDeck.position.set(0.05, -0.56, -2.28);

    const screenGeo = new THREE.PlaneGeometry(0.44, 0.26);
    const bezelGeo = new THREE.BoxGeometry(0.47, 0.29, 0.014);
    const standGeo = new THREE.CylinderGeometry(0.014, 0.020, 0.16, 8);
    this.disposableGeos.push(screenGeo, bezelGeo, standGeo);

    const bezelMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.90,
      roughness: 0.24,
    });
    const standMat = new THREE.MeshStandardMaterial({
      color: 0xf97316,
      emissive: 0x9a3412,
      emissiveIntensity: 0.35,
      metalness: 0.72,
      roughness: 0.28,
    });
    options.materialsList.push(bezelMat, standMat);

    const monitorSpecs = [
      {
        x: -0.44,
        z: 0.16,
        yaw: 0.42,
        subTargetId: 'hireti-sweetzerland',
        title: 'HIRETI WORKFORCE DAG',
        subtitle: 'MULTI-AGENT ORCHESTRATION',
        metric: '94% AUTOMATED',
        accent: '#f43f5e',
        bars: [0.84, 0.94, 0.76, 0.90],
      },
      {
        x: 0.05,
        z: -0.02,
        yaw: 0.22,
        subTargetId: 'privacy-first-ai-work-tracker',
        title: 'CHRONOAI EDGE ONNX',
        subtitle: 'LOCAL NPU • ZERO EGRESS',
        metric: '4.2ms LATENCY',
        accent: '#22d3ee',
        bars: [0.92, 0.86, 0.95, 0.81],
      },
      {
        x: 0.54,
        z: -0.14,
        yaw: 0.04,
        subTargetId: 'soft-space-super-app',
        title: 'SOFT SPACE SUPER-APP',
        subtitle: 'ISO-20022 LEDGER ENGINE',
        metric: '100% ENTERPRISE SLA',
        accent: '#10b981',
        bars: [0.89, 0.96, 0.84, 0.91],
      },
    ] as const;

    monitorSpecs.forEach((ms, mIdx) => {
      const mTex = this.createMonitorTelemetryTexture(ms);
      const mScreenMat = new THREE.MeshStandardMaterial({
        color: mTex ? 0xffffff : 0x0f172a,
        map: mTex,
        emissive: mTex ? 0xffffff : 0x38bdf8,
        emissiveMap: mTex,
        emissiveIntensity: mTex ? 0.58 : 0.40,
        roughness: 0.20,
        metalness: 0.30,
        side: THREE.DoubleSide,
      });
      options.materialsList.push(mScreenMat);

      const mPivot = new THREE.Group();
      mPivot.name = `FrontierHoloMonitor_${mIdx}`;
      mPivot.position.set(ms.x, 0.0, ms.z);
      mPivot.rotation.set(-0.22, ms.yaw, 0.0, 'YXZ');

      const mBezel = new THREE.Mesh(bezelGeo, bezelMat);
      mBezel.position.z = -0.010;
      const mScreen = new THREE.Mesh(screenGeo, mScreenMat);
      const mStand = new THREE.Mesh(standGeo, standMat);
      mStand.position.set(0.0, -0.15, -0.015);
      mPivot.add(mBezel, mScreen, mStand);

      const mTag = { type: 'subTargetProp', actIndex: 4, subTargetId: ms.subTargetId };
      mPivot.traverse((o) => {
        o.userData = { ...mTag };
      });
      this.commandHoloDeck.add(mPivot);
    });
    this.frontierGroup.add(this.commandHoloDeck);

    options.scene.add(this.frontierGroup);

    options.materialsList.push(orbMat, titaniumMat, nodeMat, fMat);
  }

  public setStudioEnvMap(envMap: THREE.Texture | null): void {
    this.studioEnvMap = envMap;
    applyStudioEnvMapToRoot(this.frontierGroup, envMap);
  }

  public ensureLoaded(): void {
    if (this.hasRequestedLoad || typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    this.loadFrontierGLB(assetUrl('models/props/act5_frontier.glb')).catch(() => {});
  }

  public async loadFrontierGLB(url: string = assetUrl('models/props/act5_frontier.glb')): Promise<void> {
    if (typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    try {
      const resolvedUrl = resolveAssetUrl(url);
      const loader = await createGltfLoader();
      loader.load(
        resolvedUrl,
        (gltf) => {
          const root = gltf.scene;
          root.name = 'Act5FrontierGLB';
          root.position.set(0, -1.45, 0);
          this.isGlbLoaded = true;

          // Shrink procedural FlagshipOrb mesh (retaining its X=2.20 world position for DEF-10) so the Blender hardware strata shine unobstructed
          this.flagshipOrb.geometry.scale(0.001, 0.001, 0.001);

          this.gyroscopeGroup.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.instancedNodes.geometry.scale(0.001, 0.001, 0.001);
          this.enterpriseWorkstationGroup.scale.set(0.001, 0.001, 0.001);
          this.frontierGroup.traverse((c) => {
            if (c.name === 'SM_Island_Act5' && c.parent === this.frontierGroup && (c as THREE.Mesh).isMesh) {
              (c as THREE.Mesh).geometry.scale(0.001, 0.001, 0.001);
            }
          });

          root.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
              const mesh = child as THREE.Mesh;
              const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
              for (const m of mats) {
                if (
                  m &&
                  /International_Orange/i.test(m.name || '') &&
                  (m as THREE.MeshStandardMaterial).isMeshStandardMaterial &&
                  !this.glbCoreAccentMats.includes(m as THREE.MeshStandardMaterial)
                ) {
                  this.glbCoreAccentMats.push(m as THREE.MeshStandardMaterial);
                }
              }
            }
            if (child.name === 'Prop_Core_Hireti_T1' || child.name === 'SM_Orbital_Lab_Rings') {
              const tag = { type: 'subTargetProp', actIndex: 4, subTargetId: 'hireti-sweetzerland' };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            } else if (child.name === 'Prop_Core_Hireti_T2') {
              const tag = {
                type: 'subTargetProp',
                actIndex: 4,
                subTargetId: 'privacy-first-ai-work-tracker',
              };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            } else if (child.name === 'Prop_Core_Hireti_T3') {
              const tag = {
                type: 'subTargetProp',
                actIndex: 4,
                subTargetId: 'soft-space-super-app',
              };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            }
          });

          const t1 = root.getObjectByName('Prop_Core_Hireti_T1') ?? null;
          const t2 = root.getObjectByName('Prop_Core_Hireti_T2') ?? null;
          const t3 = root.getObjectByName('Prop_Core_Hireti_T3') ?? null;
          this.glbCoreTiers = {
            t1,
            t2,
            t3,
            baseY1: t1 ? t1.position.y : 1.56,
            baseY2: t2 ? t2.position.y : 1.24,
            baseY3: t3 ? t3.position.y : 0.92,
          };

          if (this.studioEnvMap) {
            applyStudioEnvMapToRoot(root, this.studioEnvMap);
          }
          this.frontierGroup.add(root);
          this.onModelLoaded?.();
        },
        undefined,
        () => {}
      );
    } catch {
      // Ignore in headless/JSDOM environments
    }
  }

  public getFrontierGroup(): THREE.Group { return this.frontierGroup; }
  public getFlagshipOrb(): THREE.Mesh { return this.flagshipOrb; }
  public getGyroscopeGroup(): THREE.Group { return this.gyroscopeGroup; }
  public getInstancedNodes(): THREE.InstancedMesh { return this.instancedNodes; }
  public getSelectedCoreSlug(): string { return this.selectedCoreSlug; }
  public isStrataExplodedState(): boolean { return this.isStrataExploded; }

  public selectCore(slug: string, explode?: boolean): void {
    this.selectedCoreSlug = slug;
    if (typeof explode === 'boolean') {
      this.isStrataExploded = explode;
    } else {
      this.isStrataExploded = true;
    }
    const colorMap: Record<string, number> = {
      'hireti-sweetzerland': 0xf43f5e,
      hireti: 0xf43f5e,
      'privacy-first-ai-work-tracker': 0x00f2fe,
      chronoai: 0x00f2fe,
      'soft-space-super-app': 0x10b981,
      softspace: 0x10b981,
      'petronas-pies-energy-ai': 0xfbbf24,
      'omni-workstation': 0x8b5cf6,
    };
    const hex = colorMap[slug] ?? 0x00f2fe;
    (this.flagshipOrb.material as THREE.MeshStandardMaterial).color.setHex(hex);
    (this.flagshipOrb.material as THREE.MeshStandardMaterial).emissive.setHex(hex);
    (this.strataTier1.material as THREE.MeshBasicMaterial).color.setHex(hex);
    this.frontierScreenMat.emissive.setHex(hex);
    for (const mat of this.glbCoreAccentMats) {
      mat.emissive.setHex(hex);
      mat.emissiveIntensity = 0.65;
    }
  }

  public toggleStrataExplode(): boolean {
    this.isStrataExploded = !this.isStrataExploded;
    return this.isStrataExploded;
  }

  public setStrataExploded(exploded: boolean): void {
    this.isStrataExploded = exploded;
  }

  public triggerCaseStudyCallback(slug: string): void {
    this.onSelectCaseStudyNode?.(slug);
  }

  public update(delta: number, isReducedMotion: boolean = false, scrollProgress?: number): void {
    const isVisible =
      scrollProgress !== undefined
        ? this.frontierGroup.visible && scrollProgress >= 0.68 && scrollProgress <= 0.96
        : this.frontierGroup.visible;
    this.constellationSet.visible = isVisible;
    this.gyroscopeGroup.visible = isVisible;
    const clampedDelta = Math.min(delta, 0.1);
    const targetExplode = this.isStrataExploded ? 1.0 : 0.0;
    this.explodeFactor = isReducedMotion
      ? targetExplode
      : THREE.MathUtils.damp(this.explodeFactor, targetExplode, 8.0, clampedDelta);
    this.strataTier1.position.y = 0.22 + this.explodeFactor * 0.45;
    this.strataTier3.position.y = -0.22 - this.explodeFactor * 0.45;
    if (this.glbCoreTiers.t1) {
      this.glbCoreTiers.t1.position.y = this.glbCoreTiers.baseY1 + this.explodeFactor * 0.36;
    }
    if (this.glbCoreTiers.t2) {
      this.glbCoreTiers.t2.position.y = this.glbCoreTiers.baseY2 + this.explodeFactor * 0.14;
    }
    if (this.glbCoreTiers.t3) {
      this.glbCoreTiers.t3.position.y = this.glbCoreTiers.baseY3;
    }
    const waferHeights = [
      0.93,
      1.25 + this.explodeFactor * 0.14,
      1.57 + this.explodeFactor * 0.36,
    ];
    this.frontierWaferRings.forEach((ring, idx) => {
      ring.position.y = waferHeights[idx] ?? 0.93;
      if (!isReducedMotion) {
        ring.rotation.z += clampedDelta * (0.35 + idx * 0.12);
      }
    });
    this.frontierTensorCore.scale.y = 1.0 + this.explodeFactor * 0.52;
    this.frontierTensorCore.position.y = 1.25 + this.explodeFactor * 0.18;
    const tNow = isReducedMotion ? 0.0 : Date.now() * 0.0022;
    this.frontierPacketRings.forEach((pRing, pIdx) => {
      const baseH = 0.96 + pIdx * 0.28 + this.explodeFactor * (0.12 + pIdx * 0.10);
      const wave = isReducedMotion ? 0 : Math.sin(tNow + pIdx * 2.1) * 0.045;
      pRing.position.y = baseH + wave;
      if (!isReducedMotion) {
        pRing.rotation.z -= clampedDelta * (0.48 + pIdx * 0.16);
      }
    });
    if (!isReducedMotion) {
      this.frontierTensorCore.rotation.y -= clampedDelta * 0.65;
    }
    if (!isReducedMotion && !this.isGlbLoaded) {
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

  public dispose(): void {
    this.studioEnvMap = null;
    for (const geo of this.disposableGeos) {
      geo.dispose();
    }
    this.disposableGeos = [];
    for (const tex of this.frontierHoloTextures) {
      tex.dispose();
    }
    this.frontierHoloTextures = [];
  }
}
