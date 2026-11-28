import * as THREE from 'three';
import {
  applyStudioEnvMapToRoot,
  createGltfLoader,
  resolveAssetUrl,
} from '../core/gltfLoader';
import { assetUrl } from '../../utils/assetUrl';

export interface Act6HorizonGatewayOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
  onModelLoaded?: () => void;
}

/**
 * Act6HorizonGateway
 * Constructs and manages Act 6 Horizon Gateway (Strategic Executive Horizon & Contact):
 * - Monumental portal light arch
 * - Horizon beacon core & beacon point light
 * - Concentric radar rings
 */
export class Act6HorizonGateway {
  private horizonGroup: THREE.Group;
  private horizonPortalLightArch: THREE.Mesh;
  private portalInnerRing: THREE.Mesh;
  private horizonBeaconCore: THREE.Mesh;
  private horizonBeaconLight: THREE.PointLight;
  private radarRings: THREE.Mesh[] = [];
  private lensCrystals: THREE.Mesh[] = [];
  private lensGimbalsOuter: THREE.Mesh[] = [];
  private lensGimbalsInner: THREE.Mesh[] = [];
  private lensEquatorMats: THREE.MeshStandardMaterial[] = [];
  private selectedLensId: string = 'ai-systems';
  private glbInnerRingMats: THREE.MeshStandardMaterial[] = [];
  private clonedArchMats: THREE.Material[] = [];
  private disposableGeos: THREE.BufferGeometry[] = [];
  private studioEnvMap: THREE.Texture | null = null;
  private hasRequestedLoad: boolean = false;
  private isGlbLoaded: boolean = false;
  private onModelLoaded?: () => void;
  private dispatchReticleGroup!: THREE.Group;
  private dispatchReticleCore!: THREE.Mesh;
  private dispatchRadarDomeMat!: THREE.MeshBasicMaterial;
  private dispatchRadarSweep!: THREE.Mesh;
  private dispatchRadarSweepMat!: THREE.MeshBasicMaterial;
  private dispatchRangeRingMat!: THREE.MeshBasicMaterial;

  constructor(options: Act6HorizonGatewayOptions) {
    this.onModelLoaded = options.onModelLoaded;
    this.horizonGroup = new THREE.Group();
    this.horizonGroup.name = 'HorizonGroup';
    this.horizonGroup.position.set(0, 0, -95.0); // Act 6 Station at Z = -95.0

    // 0. Grounded Cosmic Obsidian Platform (SM_Island_Act6)
    const islandMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.28,
      metalness: 0.9,
    });
    const islandMesh = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.7, 0.20, 48), islandMat);
    islandMesh.name = 'SM_Island_Act6';
    islandMesh.position.set(0.35, -1.56, 0.0);
    islandMesh.receiveShadow = true;
    this.horizonGroup.add(islandMesh);
    options.materialsList.push(islandMat);

    // 1. Portal Light Arch & Counter-Rotating Inner Glyph Ring
    const archMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      emissive: 0x0088aa,
      emissiveIntensity: 2.0,
      roughness: 0.2,
      metalness: 0.9,
    });
    this.horizonPortalLightArch = new THREE.Mesh(
      new THREE.TorusGeometry(1.6, 0.045, 16, 64, Math.PI),
      archMat
    );
    this.horizonPortalLightArch.name = 'HorizonPortalLightArch';
    this.horizonPortalLightArch.position.set(0, -0.2, 0);
    this.horizonGroup.add(this.horizonPortalLightArch);

    const innerRingMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, transparent: true, opacity: 0.72 });
    this.portalInnerRing = new THREE.Mesh(
      new THREE.TorusGeometry(1.38, 0.018, 12, 48, Math.PI),
      innerRingMat
    );
    this.portalInnerRing.name = 'SM_Portal_InnerRing';
    this.portalInnerRing.position.set(0, -0.2, 0.04);
    this.horizonGroup.add(this.portalInnerRing);
    options.materialsList.push(innerRingMat);

    // 1B. 5 Multi-Gimbal Optical Orrery Lenses framing SM_Stargate_PortalArch (Prop_Lens_Crystal_01..05)
    const lensConfigs = [
      { id: 'ai-systems', color: 0x06b6d4, angle: Math.PI * 0.15, rx: 2.40, ry: 2.25, z: -0.18 },
      { id: 'crypto-quant', color: 0xf59e0b, angle: Math.PI * 0.67, rx: 1.96, ry: 1.88, z: -0.35 },
      { id: 'cinematic-video', color: 0xa855f7, angle: Math.PI * 0.50, rx: 1.96, ry: 1.88, z: -0.35 },
      { id: 'hackathons-mentorship', color: 0x10b981, angle: Math.PI * 0.28, rx: 2.34, ry: 2.22, z: -0.22 },
      { id: 'fintech-architecture', color: 0x3b82f6, angle: Math.PI * 0.84, rx: 1.96, ry: 1.88, z: -0.35 },
    ];
    const lensOrbGeo = new THREE.IcosahedronGeometry(0.092, 2);
    const innerCoreGeo = new THREE.OctahedronGeometry(0.058, 0);
    const gimbalOuterGeo = new THREE.TorusGeometry(0.145, 0.008, 12, 36);
    const gimbalInnerGeo = new THREE.TorusGeometry(0.175, 0.006, 12, 36);
    const equatorGeo = new THREE.TorusGeometry(0.205, 0.005, 8, 36);
    this.disposableGeos.push(lensOrbGeo, innerCoreGeo, gimbalOuterGeo, gimbalInnerGeo, equatorGeo);
    const gimbalMat = new THREE.MeshStandardMaterial({
      color: 0xe5d3b3,
      emissive: 0xc8a97e,
      emissiveIntensity: 0.28,
      roughness: 0.20,
      metalness: 0.90,
    });
    options.materialsList.push(gimbalMat);

    lensConfigs.forEach((cfg, idx) => {
      const cMat = new THREE.MeshPhysicalMaterial({
        color: cfg.color,
        emissive: cfg.color,
        emissiveIntensity: 1.15,
        roughness: 0.14,
        metalness: 0.25,
        clearcoat: 1.0,
        clearcoatRoughness: 0.06,
      });
      const crystal = new THREE.Mesh(lensOrbGeo, cMat);
      crystal.name = `Prop_Lens_Crystal_0${idx + 1}`;
      crystal.userData = { type: 'subTargetProp', actIndex: 5, subTargetId: cfg.id, baseColor: cfg.color };
      crystal.position.set(
        Math.cos(cfg.angle) * cfg.rx,
        -0.95 + Math.sin(cfg.angle) * cfg.ry,
        cfg.z
      );
      crystal.rotation.set(0.22, idx * 0.5, 0.14);

      const gimbalOuter = new THREE.Mesh(gimbalOuterGeo, gimbalMat);
      gimbalOuter.name = `Prop_Lens_Gimbal_0${idx + 1}`;
      gimbalOuter.rotation.set(Math.PI / 3, 0.35 + idx * 0.25, 0.18);
      gimbalOuter.userData = { ...crystal.userData };
      crystal.add(gimbalOuter);
      this.lensGimbalsOuter.push(gimbalOuter);

      const gimbalInner = new THREE.Mesh(gimbalInnerGeo, gimbalMat);
      gimbalInner.name = `Prop_Lens_GimbalInner_0${idx + 1}`;
      gimbalInner.rotation.set(-Math.PI / 4, -0.4 + idx * 0.3, Math.PI / 5);
      gimbalInner.userData = { ...crystal.userData };
      crystal.add(gimbalInner);
      this.lensGimbalsInner.push(gimbalInner);

      const eqMat = new THREE.MeshStandardMaterial({
        color: cfg.color,
        emissive: cfg.color,
        emissiveIntensity: 0.68,
        roughness: 0.22,
        metalness: 0.85,
      });
      const equatorRing = new THREE.Mesh(equatorGeo, eqMat);
      equatorRing.name = `Prop_Lens_Equator_0${idx + 1}`;
      equatorRing.rotation.set(Math.PI / 2 - 0.18, idx * 0.4, 0);
      equatorRing.userData = { ...crystal.userData };
      crystal.add(equatorRing);
      this.lensEquatorMats.push(eqMat);

      const innerCoreMat = new THREE.MeshStandardMaterial({
        color: cfg.color,
        emissive: cfg.color,
        emissiveIntensity: 0.9,
        roughness: 0.24,
        metalness: 0.55,
      });
      const innerCore = new THREE.Mesh(innerCoreGeo, innerCoreMat);
      innerCore.name = `Prop_Lens_InnerCore_0${idx + 1}`;
      innerCore.rotation.set(Math.PI / 4, Math.PI / 4, 0.12);
      innerCore.userData = { ...crystal.userData };
      crystal.add(innerCore);

      this.lensCrystals.push(crystal);
      this.horizonGroup.add(crystal);
      options.materialsList.push(cMat, eqMat, innerCoreMat);
    });

    // 2. Horizon Beacon Core & Light
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.horizonBeaconCore = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), beaconMat);
    this.horizonBeaconCore.name = 'HorizonBeaconCore';
    this.horizonBeaconCore.userData = { type: 'subTargetProp', actIndex: 5, subTargetId: 'direct-dispatch' };
    this.horizonBeaconCore.position.set(0, 0.25, 0);
    this.horizonGroup.add(this.horizonBeaconCore);

    this.horizonBeaconLight = new THREE.PointLight(0x00f2fe, 0.0, 8.0);
    this.horizonBeaconLight.name = 'HorizonBeaconLight';
    this.horizonBeaconLight.position.set(0, 0.25, 0);
    this.horizonGroup.add(this.horizonBeaconLight);

    // 3. Concentric Radar Rings
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.35 });
    const ringRadii = [0.8, 1.4, 2.0];
    ringRadii.forEach((r, idx) => {
      const ring = new THREE.Mesh(new THREE.RingGeometry(r, r + 0.015, 64), ringMat);
      ring.name = `RadarRing_${idx}`;
      ring.rotation.x = Math.PI / 2;
      ring.position.y = -1.45;
      this.radarRings.push(ring);
      this.horizonGroup.add(ring);
    });

    // 4. 3D Holographic Radar Dome & Azimuth Sweep hovering cleanly above Prop_Beacon_Dispatch
    const dispatchTag = { type: 'subTargetProp', actIndex: 5, subTargetId: 'direct-dispatch' };
    this.dispatchReticleGroup = new THREE.Group();
    this.dispatchReticleGroup.name = 'HorizonDispatchReticle';
    this.dispatchReticleGroup.position.set(-0.25, -0.44, 0.25);
    this.dispatchReticleGroup.rotation.set(-0.28, 0.26, 0.0);

    const radarDomeGeo = new THREE.SphereGeometry(0.20, 20, 10, 0, Math.PI * 2, 0, Math.PI * 0.52);
    this.dispatchRadarDomeMat = new THREE.MeshBasicMaterial({
      color: 0x22d3ee,
      wireframe: true,
      transparent: true,
      opacity: 0.30,
      depthWrite: false,
    });
    const radarDomeMesh = new THREE.Mesh(radarDomeGeo, this.dispatchRadarDomeMat);
    radarDomeMesh.name = 'HorizonDispatchRadarDome';
    radarDomeMesh.userData = { ...dispatchTag };
    this.dispatchReticleGroup.add(radarDomeMesh);

    this.dispatchRangeRingMat = new THREE.MeshBasicMaterial({
      color: 0x5eead4,
      transparent: true,
      opacity: 0.78,
    });
    const rangeRingGeos = [
      new THREE.TorusGeometry(0.20, 0.005, 8, 40),
      new THREE.TorusGeometry(0.14, 0.004, 8, 36),
      new THREE.TorusGeometry(0.08, 0.004, 8, 28),
    ];
    rangeRingGeos.forEach((rGeo, rIdx) => {
      const rMesh = new THREE.Mesh(rGeo, this.dispatchRangeRingMat);
      rMesh.name = `HorizonDispatchRangeRing_${rIdx}`;
      rMesh.rotation.x = Math.PI / 2;
      rMesh.position.y = rIdx * 0.014;
      rMesh.userData = { ...dispatchTag };
      this.dispatchReticleGroup.add(rMesh);
    });

    const radarSweepGeo = new THREE.RingGeometry(0.03, 0.195, 16, 1, 0, Math.PI * 0.28);
    this.dispatchRadarSweepMat = new THREE.MeshBasicMaterial({
      color: 0x22d3ee,
      transparent: true,
      opacity: 0.44,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    this.dispatchRadarSweep = new THREE.Mesh(radarSweepGeo, this.dispatchRadarSweepMat);
    this.dispatchRadarSweep.name = 'HorizonDispatchRadarSweep';
    this.dispatchRadarSweep.rotation.x = -Math.PI / 2;
    this.dispatchRadarSweep.position.y = 0.008;
    this.dispatchRadarSweep.userData = { ...dispatchTag };
    this.dispatchReticleGroup.add(this.dispatchRadarSweep);

    const reticleCoreGeo = new THREE.OctahedronGeometry(0.042, 1);
    const reticleCoreMat = new THREE.MeshStandardMaterial({
      color: 0xfde68a,
      emissive: 0x00f2fe,
      emissiveIntensity: 0.95,
      roughness: 0.2,
      metalness: 0.75,
    });
    this.dispatchReticleCore = new THREE.Mesh(reticleCoreGeo, reticleCoreMat);
    this.dispatchReticleCore.name = 'HorizonDispatchReticleCore';
    this.dispatchReticleCore.position.y = 0.055;
    this.dispatchReticleCore.userData = { ...dispatchTag };
    this.dispatchReticleGroup.add(this.dispatchReticleCore);

    this.disposableGeos.push(radarDomeGeo, ...rangeRingGeos, radarSweepGeo, reticleCoreGeo);
    options.materialsList.push(
      this.dispatchRadarDomeMat,
      this.dispatchRangeRingMat,
      this.dispatchRadarSweepMat,
      reticleCoreMat
    );
    this.horizonGroup.add(this.dispatchReticleGroup);

    options.scene.add(this.horizonGroup);

    options.materialsList.push(archMat, beaconMat, ringMat);
  }

  public setStudioEnvMap(envMap: THREE.Texture | null): void {
    this.studioEnvMap = envMap;
    applyStudioEnvMapToRoot(this.horizonGroup, envMap);
  }

  public ensureLoaded(): void {
    if (this.hasRequestedLoad || typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    this.loadHorizonGLB(assetUrl('models/props/act6_horizon.glb')).catch(() => {});
  }

  public async loadHorizonGLB(url: string = assetUrl('models/props/act6_horizon.glb')): Promise<void> {
    if (typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    try {
      const resolvedUrl = resolveAssetUrl(url);
      const loader = await createGltfLoader();
      loader.load(
        resolvedUrl,
        (gltf) => {
          const root = gltf.scene;
          root.name = 'Act6HorizonGLB';
          root.position.set(0, -1.45, 0);
          this.isGlbLoaded = true;

          this.horizonPortalLightArch.geometry.scale(0.001, 0.001, 0.001);
          this.portalInnerRing.geometry.scale(0.001, 0.001, 0.001);
          this.horizonBeaconCore.geometry.scale(0.001, 0.001, 0.001);
          this.radarRings.forEach((r) => r.geometry.scale(0.001, 0.001, 0.001));
          this.updateLensCrystalColors(
            this.selectedLensId,
            this.resolveLensHex(this.selectedLensId)
          );
          this.horizonGroup.traverse((c) => {
            if (c.name === 'SM_Island_Act6' && c.parent === this.horizonGroup && (c as THREE.Mesh).isMesh) {
              (c as THREE.Mesh).geometry.scale(0.001, 0.001, 0.001);
            }
          });

          const crystalLensIds = [
            'ai-systems',
            'crypto-quant',
            'cinematic-video',
            'hackathons-mentorship',
            'fintech-architecture',
          ];
          root.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
            }
            if (child.name === 'Prop_Beacon_Dispatch') {
              const tag = { type: 'subTargetProp', actIndex: 5, subTargetId: 'direct-dispatch' };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            } else if (/^Prop_Lens_Crystal_0([1-5])$/.test(child.name)) {
              const match = /^Prop_Lens_Crystal_0([1-5])$/.exec(child.name);
              const idx = match ? parseInt(match[1]!, 10) - 1 : 0;
              const subTargetId = crystalLensIds[idx] ?? 'ai-systems';
              const tag = { type: 'subTargetProp', actIndex: 5, subTargetId };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            }
            const isInnerRing = child.name === 'SM_Portal_InnerRing';
            const isPortalArch = child.name === 'SM_Stargate_PortalArch';
            if (isInnerRing || isPortalArch) {
              child.traverse((sub) => {
                if (!(sub as THREE.Mesh).isMesh) return;
                const mesh = sub as THREE.Mesh;
                const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
                const updatedMats = mats.map((m) => {
                  if (!m || !(m as THREE.MeshStandardMaterial).isMeshStandardMaterial) {
                    return m;
                  }
                  const stdMat = m as THREE.MeshStandardMaterial;
                  const isAccent =
                    isInnerRing ||
                    /champagne|bronze|accent|glow|teal|cyan/i.test(stdMat.name);
                  if (!isAccent) return m;
                  if (isPortalArch) {
                    const archMat = stdMat.clone();
                    this.clonedArchMats.push(archMat);
                    if (!this.glbInnerRingMats.includes(archMat)) {
                      this.glbInnerRingMats.push(archMat);
                    }
                    return archMat;
                  }
                  if (!this.glbInnerRingMats.includes(stdMat)) {
                    this.glbInnerRingMats.push(stdMat);
                  }
                  return stdMat;
                });
                mesh.material = Array.isArray(mesh.material)
                  ? updatedMats
                  : (updatedMats[0] ?? mesh.material);
              });
            }
          });

          const activeHex = this.resolveLensHex(this.selectedLensId);
          for (const mat of this.glbInnerRingMats) {
            mat.emissive.setHex(activeHex);
            mat.emissiveIntensity = 0.55;
          }
          if (this.studioEnvMap) {
            applyStudioEnvMapToRoot(root, this.studioEnvMap);
          }

          this.horizonGroup.add(root);
          this.onModelLoaded?.();
        },
        undefined,
        () => {}
      );
    } catch {
      // Ignore in headless/JSDOM environments
    }
  }

  public getHorizonGroup(): THREE.Group { return this.horizonGroup; }
  public getBeaconLight(): THREE.PointLight { return this.horizonBeaconLight; }
  public getSelectedLensId(): string { return this.selectedLensId; }

  private resolveLensHex(lensId: string, colorHex?: string): number {
    const colorMap: Record<string, number> = {
      'ai-systems': 0x06b6d4,
      'crypto-quant': 0xf59e0b,
      'cinematic-video': 0xa855f7,
      'hackathons-mentorship': 0x10b981,
      'fintech-architecture': 0x3b82f6,
      'direct-dispatch': 0x00f2fe,
    };
    let hex = colorMap[lensId] ?? 0x00f2fe;
    if (colorHex && colorHex.startsWith('#')) {
      const parsed = parseInt(colorHex.slice(1), 16);
      if (!Number.isNaN(parsed)) hex = parsed;
    }
    return hex;
  }

  private updateLensCrystalColors(selectedId: string, activeHex: number): void {
    this.lensCrystals.forEach((c) => {
      const mat = c.material as THREE.MeshStandardMaterial;
      if (c.userData.subTargetId === selectedId) {
        mat.color.setHex(activeHex);
        mat.emissive.setHex(activeHex);
        mat.emissiveIntensity = 1.25;
      } else {
        mat.color.setHex(0xe5d3b3);
        mat.emissive.setHex(0xc8a97e);
        mat.emissiveIntensity = 0.35;
      }
    });
  }

  public selectLens(lensId: string, colorHex?: string): void {
    this.selectedLensId = lensId;
    const hex = this.resolveLensHex(lensId, colorHex);
    (this.horizonPortalLightArch.material as THREE.MeshStandardMaterial).color.setHex(hex);
    (this.horizonPortalLightArch.material as THREE.MeshStandardMaterial).emissive.setHex(hex);
    (this.portalInnerRing.material as THREE.MeshBasicMaterial).color.setHex(hex);
    this.horizonBeaconLight.color.setHex(hex);
    this.dispatchRadarDomeMat.color.setHex(hex);
    this.dispatchRadarSweepMat.color.setHex(hex);
    this.dispatchRangeRingMat.color.setHex(hex);
    for (const mat of this.glbInnerRingMats) {
      mat.emissive.setHex(hex);
      mat.emissiveIntensity = 0.55;
    }
    this.radarRings.forEach((r) => {
      (r.material as THREE.MeshBasicMaterial).color.setHex(hex);
    });
    this.updateLensCrystalColors(lensId, hex);
  }

  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    if (!isReducedMotion) {
      if (!this.isGlbLoaded) {
        this.radarRings.forEach((r, idx) => {
          r.rotation.z += clampedDelta * (0.2 + idx * 0.1);
        });
        this.portalInnerRing.rotation.z = Math.sin(Date.now() * 0.0015) * 0.08;
      }
      this.lensCrystals.forEach((crystal, idx) => {
        const isSel = crystal.userData.subTargetId === this.selectedLensId;
        const targetScale = isSel ? 1.36 : 1.0;
        crystal.scale.setScalar(THREE.MathUtils.damp(crystal.scale.x, targetScale, 10.0, clampedDelta));
        crystal.rotation.y += clampedDelta * (isSel ? 1.8 : 0.7);
        const eqMat = this.lensEquatorMats[idx];
        if (eqMat) {
          eqMat.emissiveIntensity = THREE.MathUtils.damp(eqMat.emissiveIntensity, isSel ? 1.35 : 0.62, 8.0, clampedDelta);
        }
      });
      this.lensGimbalsOuter.forEach((g, idx) => {
        g.rotation.z += clampedDelta * (0.85 + idx * 0.12);
      });
      this.lensGimbalsInner.forEach((g, idx) => {
        g.rotation.x -= clampedDelta * (1.05 + idx * 0.10);
      });
      this.dispatchReticleGroup.rotation.y += clampedDelta * 0.40;
      this.dispatchRadarSweep.rotation.z -= clampedDelta * 2.1;
      this.dispatchReticleCore.rotation.y -= clampedDelta * 1.1;
    }
  }

  public dispose(): void {
    this.studioEnvMap = null;
    for (const geo of this.disposableGeos) {
      geo.dispose();
    }
    for (const mat of this.clonedArchMats) {
      mat.dispose();
    }
    this.disposableGeos = [];
    this.clonedArchMats = [];
    this.glbInnerRingMats = [];
  }
}
