import * as THREE from 'three';
import {
  applyStudioEnvMapToRoot,
  createGltfLoader,
  resolveAssetUrl,
} from '../core/gltfLoader';

export interface Act3CrucibleOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
  onModelLoaded?: () => void;
}

/**
 * Act3Crucible
 * Constructs and manages the Act 3 Crucible (GDSC Core & Cloud Quests):
 * - GDSC Hexagonal Center Stage Podium
 * - CrucibleOrbitBadges with DEF-01 safe clearance radius (0.72m)
 * - Badge Surge action dynamics
 */
export class Act3Crucible {
  private crucibleGroup: THREE.Group;
  private orbitBadgesGroup: THREE.Group;
  private badges: THREE.Mesh[] = [];
  private badgeAngles: Float32Array = new Float32Array(5);
  private badgeSurgeUntil: number = 0;
  private surgeWaveGroup: THREE.Group | null = null;
  private surgeColumnMat: THREE.MeshBasicMaterial | null = null;
  private surgeRingMats: THREE.MeshBasicMaterial[] = [];
  private surgeRingMeshes: THREE.Mesh[] = [];
  private disposableGeos: THREE.BufferGeometry[] = [];
  private selectedCategoryId: string = 'cloud-ai';
  private projectorBeamMesh: THREE.Mesh;
  private projectorRingMesh: THREE.Mesh;
  private outerIslandMesh: THREE.Mesh;
  private podiumMesh: THREE.Mesh;
  private keynoteDisplayGroup: THREE.Group;
  private lecternHoloGroup: THREE.Group;
  private badgeHalos: THREE.Mesh[] = [];
  private badgeOrbMats: THREE.MeshStandardMaterial[] = [];
  private tensorCoreGroup: THREE.Group;
  private tensorCage: THREE.Mesh;
  private tensorRings: THREE.Mesh[] = [];
  private tensorCoreMat: THREE.MeshStandardMaterial;
  private tensorCageMat: THREE.MeshStandardMaterial;
  private screenCanvas: HTMLCanvasElement | null = null;
  private screenTexture: THREE.CanvasTexture | null = null;
  private glbRingMats: THREE.MeshStandardMaterial[] = [];
  private studioEnvMap: THREE.Texture | null = null;
  private hasRequestedLoad: boolean = false;
  private isGlbLoaded: boolean = false;
  private onModelLoaded?: () => void;

  private drawTelemetryCanvas(accentHex: string): void {
    const canvas = this.screenCanvas;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#070b14';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Header band
    ctx.fillStyle = accentHex;
    ctx.fillRect(10, 10, canvas.width - 20, 6);

    // Architectural grid & telemetry bars
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.18)';
    ctx.lineWidth = 1;
    for (let x = 16; x < canvas.width - 12; x += 28) {
      ctx.beginPath();
      ctx.moveTo(x, 24);
      ctx.lineTo(x, canvas.height - 14);
      ctx.stroke();
    }
    const barWidths = [0.76, 0.58, 0.88, 0.64];
    barWidths.forEach((bw, idx) => {
      const y = 30 + idx * 24;
      ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.fillRect(16, y, canvas.width - 32, 12);
      ctx.fillStyle = idx % 2 === 0 ? accentHex : '#fbbf24';
      ctx.fillRect(16, y, Math.round((canvas.width - 32) * bw), 12);
    });

    if (this.screenTexture) {
      this.screenTexture.needsUpdate = true;
    }
  }

  constructor(options: Act3CrucibleOptions) {
    this.onModelLoaded = options.onModelLoaded;
    this.crucibleGroup = new THREE.Group();
    this.crucibleGroup.name = 'CrucibleGroup';
    this.crucibleGroup.position.set(0, 0, -36.0); // Act 3 Station at Z = -36.0

    // 0. Tiered Hexagonal Amphitheater Island & Google Quad-Color Neon Strips
    const islandMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.32,
      metalness: 0.88,
    });
    const outerIsland = new THREE.Mesh(new THREE.CylinderGeometry(2.35, 2.50, 0.18, 6), islandMat);
    outerIsland.name = 'SM_Island_Act3';
    outerIsland.position.set(0.15, -1.62, 0);
    outerIsland.receiveShadow = true;
    this.outerIslandMesh = outerIsland;
    this.crucibleGroup.add(outerIsland);
    options.materialsList.push(islandMat);

    // Hologram Projector Ring & Vertical Beam
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xeab308, transparent: true, opacity: 0.85 });
    this.projectorRingMesh = new THREE.Mesh(new THREE.TorusGeometry(0.85, 0.016, 12, 6), ringMat);
    this.projectorRingMesh.name = 'SM_Hologram_Projector_Ring';
    this.projectorRingMesh.rotation.x = Math.PI / 2;
    this.projectorRingMesh.position.set(0.15, -1.47, 0);
    this.crucibleGroup.add(this.projectorRingMesh);

    const beamMat = new THREE.MeshBasicMaterial({
      color: 0xeab308,
      transparent: true,
      opacity: 0.06,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.projectorBeamMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.68, 0.82, 2.1, 24, 1, true), beamMat);
    this.projectorBeamMesh.name = 'CrucibleProjectorBeam';
    this.projectorBeamMesh.position.set(0.15, -0.40, 0);
    this.crucibleGroup.add(this.projectorBeamMesh);
    options.materialsList.push(ringMat, beamMat);

    // 1. GDSC Hexagonal Podium
    const podiumMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.35,
      metalness: 0.85,
    });
    const podium = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.35, 0.25, 6), podiumMat);
    podium.name = 'CruciblePodium';
    // Elevation centered at Y = -1.605 so top surface sits at Y = -1.48, eliminating foot/ankle clipping with plinth (Y = -1.45)
    podium.position.set(0.15, -1.605, 0);
    this.podiumMesh = podium;
    this.crucibleGroup.add(podium);

    // 2. CrucibleOrbitBadges Group (DEF-01: Strictly 5 direct children at radius 0.72m safe clearance)
    this.orbitBadgesGroup = new THREE.Group();
    this.orbitBadgesGroup.name = 'CrucibleOrbitBadges';
    this.orbitBadgesGroup.position.set(0.15, 0.25, 0);

    const badgeMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      emissive: 0x1e293b,
      emissiveIntensity: 0.45,
      metalness: 0.90,
      roughness: 0.22,
    });

    const badgeGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.022, 6);
    const badgeCoreGeo = new THREE.CylinderGeometry(0.095, 0.095, 0.036, 6);
    const badgeCount = 5;
    const orbitRadius = 0.72; // DEF-01: Exactly 0.72m safe clearance
    const categorySubTargets = ['cloud-ai', 'product-ba', 'global-wins', 'cloud-ai', 'product-ba'];
    const categoryColors: Record<string, number> = {
      'cloud-ai': 0x00f2fe,
      'product-ba': 0xa855f7,
      'global-wins': 0xfbbf24,
    };
    const badgeHeights = [0.24, 0.38, 0.28, 0.12, 0.16];

    const bevelGeo = new THREE.TorusGeometry(0.132, 0.013, 12, 6);
    const haloGeo = new THREE.TorusGeometry(0.165, 0.006, 8, 32);
    const crestGeo = new THREE.OctahedronGeometry(0.050, 1);
    this.disposableGeos.push(badgeGeo, badgeCoreGeo, bevelGeo, haloGeo, crestGeo);
    const bevelMat = new THREE.MeshStandardMaterial({
      color: 0xe5d3b3,
      emissive: 0xc8a97e,
      emissiveIntensity: 0.45,
      roughness: 0.22,
      metalness: 0.90,
    });
    const crestMat = new THREE.MeshStandardMaterial({
      color: 0xfde68a,
      emissive: 0xfbbf24,
      emissiveIntensity: 0.9,
      roughness: 0.18,
      metalness: 0.85,
    });

    for (let b = 0; b < badgeCount; b++) {
      const angle = 0.32 + (b / badgeCount) * Math.PI * 2;
      this.badgeAngles[b] = angle;
      const subId = categorySubTargets[b] ?? 'cloud-ai';
      const catHex = categoryColors[subId] ?? 0x00f2fe;

      const badge = new THREE.Mesh(badgeGeo, badgeMat);
      badge.name = `OrbitBadge_${b}`;
      badge.userData = {
        type: 'subTargetProp',
        actIndex: 2,
        subTargetId: subId,
      };
      badge.rotation.x = Math.PI / 2;
      badge.position.set(
        Math.cos(angle) * orbitRadius,
        badgeHeights[b] ?? 0.24,
        Math.sin(angle) * orbitRadius
      );

      const coreMat = new THREE.MeshStandardMaterial({
        color: catHex,
        emissive: catHex,
        emissiveIntensity: 0.65,
        metalness: 0.72,
        roughness: 0.22,
      });
      this.badgeOrbMats.push(coreMat);
      options.materialsList.push(coreMat);

      const emblem = new THREE.Mesh(badgeCoreGeo, coreMat);
      emblem.name = `OrbitBadgeEmblem_${b}`;
      emblem.userData = { ...badge.userData };
      badge.add(emblem);

      const bevelRing = new THREE.Mesh(bevelGeo, bevelMat);
      bevelRing.name = `OrbitBadgeBevel_${b}`;
      bevelRing.userData = { ...badge.userData };
      badge.add(bevelRing);

      const haloRing = new THREE.Mesh(haloGeo, coreMat);
      haloRing.name = `OrbitBadgeHalo_${b}`;
      haloRing.rotation.set(Math.PI / 3, 0.3 + b * 0.4, 0);
      haloRing.userData = { ...badge.userData };
      badge.add(haloRing);
      this.badgeHalos.push(haloRing);

      const crest = new THREE.Mesh(crestGeo, crestMat);
      crest.name = `OrbitBadgeCrest_${b}`;
      crest.scale.set(1, 1, 1.35);
      crest.userData = { ...badge.userData };
      badge.add(crest);

      this.badges.push(badge);
      this.orbitBadgesGroup.add(badge);
    }

    this.crucibleGroup.add(this.orbitBadgesGroup);

    // 2B. Suspended CrucibleTensorNucleus anchoring Pin 03 (`global-wins`) at world (0.16, 0.52, -35.65)
    const nucleusTag = { type: 'subTargetProp', actIndex: 2, subTargetId: 'global-wins' };
    this.tensorCoreGroup = new THREE.Group();
    this.tensorCoreGroup.name = 'CrucibleTensorNucleus';
    this.tensorCoreGroup.position.set(0.16, 0.52, 0.35);

    const coreIcoGeo = new THREE.IcosahedronGeometry(0.125, 1);
    this.tensorCoreMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0284c7,
      emissiveIntensity: 0.78,
      metalness: 0.75,
      roughness: 0.16,
    });
    const coreMesh = new THREE.Mesh(coreIcoGeo, this.tensorCoreMat);
    coreMesh.name = 'CrucibleTensorCore';
    coreMesh.userData = { ...nucleusTag };
    this.tensorCoreGroup.add(coreMesh);

    const cageGeo = new THREE.IcosahedronGeometry(0.165, 1);
    this.tensorCageMat = new THREE.MeshStandardMaterial({
      color: 0xfde68a,
      emissive: 0xfbbf24,
      emissiveIntensity: 0.65,
      wireframe: true,
      roughness: 0.22,
      metalness: 0.90,
    });
    this.tensorCage = new THREE.Mesh(cageGeo, this.tensorCageMat);
    this.tensorCage.name = 'CrucibleTensorCage';
    this.tensorCage.userData = { ...nucleusTag };
    this.tensorCoreGroup.add(this.tensorCage);

    const tRing1Geo = new THREE.TorusGeometry(0.225, 0.008, 12, 48);
    const tRing2Geo = new THREE.TorusGeometry(0.275, 0.007, 12, 48);
    const tRing1 = new THREE.Mesh(tRing1Geo, bevelMat);
    tRing1.name = 'CrucibleTensorRing_0';
    tRing1.rotation.set(Math.PI / 3, 0.25, 0);
    tRing1.userData = { ...nucleusTag };
    const tRing2 = new THREE.Mesh(tRing2Geo, crestMat);
    tRing2.name = 'CrucibleTensorRing_1';
    tRing2.rotation.set(-Math.PI / 4, -0.35, Math.PI / 6);
    tRing2.userData = { ...nucleusTag };
    this.tensorRings.push(tRing1, tRing2);
    this.tensorCoreGroup.add(tRing1, tRing2);

    this.disposableGeos.push(coreIcoGeo, cageGeo, tRing1Geo, tRing2Geo);
    options.materialsList.push(this.tensorCoreMat, this.tensorCageMat);
    this.crucibleGroup.add(this.tensorCoreGroup);

    this.surgeWaveGroup = new THREE.Group();
    this.surgeWaveGroup.name = 'CrucibleSurgeWaveGroup';
    this.surgeWaveGroup.position.set(-0.40, -0.35, 0.20);

    const surgeColumnGeo = new THREE.CylinderGeometry(0.18, 0.38, 1.45, 24, 1, true);
    this.surgeColumnMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.02,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    const surgeColumnMesh = new THREE.Mesh(surgeColumnGeo, this.surgeColumnMat);
    surgeColumnMesh.name = 'CrucibleSurgeColumn';
    surgeColumnMesh.position.y = 0.68;
    this.surgeWaveGroup.add(surgeColumnMesh);
    this.disposableGeos.push(surgeColumnGeo);

    const surgeRingSpecs = [
      { radius: 0.46, tube: 0.009, color: 0x00f2fe, y: 0.12, rotX: Math.PI / 2 - 0.42, rotY: -0.26 },
      { radius: 0.68, tube: 0.008, color: 0xfbbf24, y: 0.36, rotX: Math.PI / 2 - 0.42, rotY: 0.26 },
    ];
    surgeRingSpecs.forEach((spec, sIdx) => {
      const sGeo = new THREE.TorusGeometry(spec.radius, spec.tube, 10, 48);
      const sMat = new THREE.MeshBasicMaterial({
        color: spec.color,
        transparent: true,
        opacity: 0.05,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });
      const sMesh = new THREE.Mesh(sGeo, sMat);
      sMesh.name = `CrucibleSurgeRing_${sIdx}`;
      sMesh.rotation.set(spec.rotX, spec.rotY, 0);
      sMesh.position.y = spec.y;
      this.disposableGeos.push(sGeo);
      this.surgeRingMats.push(sMat);
      this.surgeRingMeshes.push(sMesh);
      this.surgeWaveGroup!.add(sMesh);
    });

    this.crucibleGroup.add(this.surgeWaveGroup);
    options.materialsList.push(bevelMat, crestMat, this.surgeColumnMat, ...this.surgeRingMats);

    // 3. KeynoteMonitorDisplay (Procedural Fallback) & Floating LecternHoloConsole over SM_GDSC_Lectern (Pin 02)
    const keynoteDisplay = new THREE.Group();
    keynoteDisplay.name = 'KeynoteMonitorDisplay';
    keynoteDisplay.position.set(0.15, -0.95, -0.65);
    this.keynoteDisplayGroup = keynoteDisplay;

    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 144;
    this.screenCanvas = canvas;
    const screenTex = new THREE.CanvasTexture(canvas);
    this.screenTexture = screenTex;
    this.drawTelemetryCanvas('#38bdf8');

    const screenGeo = new THREE.PlaneGeometry(0.55, 0.35);
    const screenMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      emissive: 0xffffff,
      emissiveIntensity: 0.92,
      emissiveMap: screenTex,
      roughness: 0.2,
      metalness: 0.65,
      transparent: true,
      opacity: 0.92,
      side: THREE.DoubleSide,
    });
    const screenMesh = new THREE.Mesh(screenGeo, screenMat);
    screenMesh.name = 'PodiumScreenMesh';
    screenMesh.userData = { type: 'subTargetProp', actIndex: 2, subTargetId: 'cloud-ai' };
    screenMesh.rotation.x = -Math.PI * 0.15;
    keynoteDisplay.add(screenMesh);
    this.crucibleGroup.add(keynoteDisplay);

    // Persistent Holographic Telemetry Console hovering cleanly over SM_GDSC_Lectern (-0.65, -0.22, 0.25)
    const lecternTag = { type: 'subTargetProp', actIndex: 2, subTargetId: 'product-ba' };
    this.lecternHoloGroup = new THREE.Group();
    this.lecternHoloGroup.name = 'LecternHoloConsole';
    this.lecternHoloGroup.position.set(-0.65, -0.20, 0.25);
    this.lecternHoloGroup.rotation.set(-0.22, 0.21, 0.0);

    const holoPlaneGeo = new THREE.PlaneGeometry(0.46, 0.26);
    const holoScreen = new THREE.Mesh(holoPlaneGeo, screenMat);
    holoScreen.name = 'LecternHoloScreen';
    holoScreen.userData = { ...lecternTag };
    this.lecternHoloGroup.add(holoScreen);

    const frameTopGeo = new THREE.BoxGeometry(0.48, 0.012, 0.012);
    const frameSideGeo = new THREE.BoxGeometry(0.012, 0.28, 0.012);
    const holoTop = new THREE.Mesh(frameTopGeo, bevelMat);
    holoTop.position.y = 0.135;
    const holoBot = new THREE.Mesh(frameTopGeo, bevelMat);
    holoBot.position.y = -0.135;
    const holoL = new THREE.Mesh(frameSideGeo, bevelMat);
    holoL.position.x = -0.235;
    const holoR = new THREE.Mesh(frameSideGeo, bevelMat);
    holoR.position.x = 0.235;
    [holoTop, holoBot, holoL, holoR].forEach((fPart) => {
      fPart.userData = { ...lecternTag };
      this.lecternHoloGroup.add(fPart);
    });
    this.crucibleGroup.add(this.lecternHoloGroup);

    this.disposableGeos.push(screenGeo, holoPlaneGeo, frameTopGeo, frameSideGeo);

    options.scene.add(this.crucibleGroup);

    options.materialsList.push(podiumMat, badgeMat, screenMat);
  }

  public setStudioEnvMap(envMap: THREE.Texture | null): void {
    this.studioEnvMap = envMap;
    applyStudioEnvMapToRoot(this.crucibleGroup, envMap);
  }

  public ensureLoaded(): void {
    if (this.hasRequestedLoad || typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    this.loadCrucibleGLB('/models/props/act3_crucible.glb').catch(() => {});
  }

  public async loadCrucibleGLB(url: string = '/models/props/act3_crucible.glb'): Promise<void> {
    if (typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    try {
      const resolvedUrl = resolveAssetUrl(url);
      const loader = await createGltfLoader();
      loader.load(
        resolvedUrl,
        (gltf) => {
          const root = gltf.scene;
          root.name = 'Act3CrucibleGLB';
          root.position.set(0, -1.45, 0);
          this.isGlbLoaded = true;

          this.outerIslandMesh.geometry.scale(0.001, 0.001, 0.001);
          this.projectorRingMesh.geometry.scale(0.001, 0.001, 0.001);
          this.projectorBeamMesh.geometry.scale(0.001, 0.001, 0.001);
          this.podiumMesh.geometry.scale(0.001, 0.001, 0.001);
          this.keynoteDisplayGroup.scale.set(0.001, 0.001, 0.001);
          this.orbitBadgesGroup.position.set(-0.55, 0.24, 0.35);
          const restHeights = [0.24, 0.38, 0.28, 0.12, 0.16];
          for (let b = 0; b < this.badges.length; b++) {
            const badge = this.badges[b];
            if (!badge) continue;
            const ang = 0.32 + (b / 5) * Math.PI * 2;
            this.badgeAngles[b] = ang;
            badge.position.set(
              Math.cos(ang) * 0.72,
              restHeights[b] ?? 0.24,
              Math.sin(ang) * 0.72
            );
            badge.scale.set(0.62, 0.62, 0.62);
            badge.rotation.set(Math.PI / 2, 0, Math.sin(ang) * 0.15);
            const bMat = badge.material as THREE.MeshStandardMaterial;
            bMat.color.setHex(0xf5d061);
            bMat.emissive.setHex(0xd97706);
            bMat.emissiveIntensity = 0.42;
          }

          root.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
            }
            if (child.name === 'SM_GDSC_Lectern' || child.name === 'SM_Hologram_Projector_Ring') {
              const subTargetId = child.name === 'SM_GDSC_Lectern' ? 'product-ba' : 'cloud-ai';
              const tag = { type: 'subTargetProp', actIndex: 2, subTargetId };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            }
            if (child.name === 'SM_Hologram_Projector_Ring') {
              child.traverse((sub) => {
                if (!(sub as THREE.Mesh).isMesh) return;
                const mesh = sub as THREE.Mesh;
                const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
                for (const m of mats) {
                  if (
                    m &&
                    /Smoked_Bronze_Glass|Stage_Gold/i.test(m.name || '') &&
                    (m as THREE.MeshStandardMaterial).isMeshStandardMaterial &&
                    !this.glbRingMats.includes(m as THREE.MeshStandardMaterial)
                  ) {
                    this.glbRingMats.push(m as THREE.MeshStandardMaterial);
                  }
                }
              });
            }
          });

          if (this.studioEnvMap) {
            applyStudioEnvMapToRoot(root, this.studioEnvMap);
          }
          this.crucibleGroup.add(root);
          this.onModelLoaded?.();
        },
        undefined,
        () => {}
      );
    } catch {
      // Ignore in headless/JSDOM environments
    }
  }

  public getCrucibleGroup(): THREE.Group { return this.crucibleGroup; }
  public getOrbitBadgesGroup(): THREE.Group { return this.orbitBadgesGroup; }
  public getBadgeSurgeUntil(): number { return this.badgeSurgeUntil; }
  public getSelectedCategoryId(): string { return this.selectedCategoryId; }

  public selectCategory(categoryId: string): void {
    this.selectedCategoryId = categoryId;
    this.triggerBadgeSurge(3.0);
    const colorMap: Record<string, number> = {
      'cloud-ai': 0x00f2fe,
      'product-ba': 0xa855f7,
      'global-wins': 0xfbbf24,
      all: 0x4285f4,
    };
    const hex = colorMap[categoryId] ?? 0x00f2fe;
    (this.projectorBeamMesh.material as THREE.MeshBasicMaterial).color.setHex(hex);
    (this.projectorRingMesh.material as THREE.MeshBasicMaterial).color.setHex(hex);
    this.tensorCoreMat.emissive.setHex(hex);
    for (const mat of this.glbRingMats) {
      mat.emissive.setHex(hex);
      mat.emissiveIntensity = 0.45;
    }
    this.drawTelemetryCanvas(`#${hex.toString(16).padStart(6, '0')}`);
  }

  public triggerBadgeSurge(durationSec: number = 3.0): void {
    this.badgeSurgeUntil = Date.now() + durationSec * 1000;
    const orbitRadius = 0.72;
    this.orbitBadgesGroup.position.y = 0.44;
    (this.projectorBeamMesh.material as THREE.MeshBasicMaterial).opacity = 0.22;
    (this.projectorRingMesh.material as THREE.MeshBasicMaterial).opacity = 1.0;
    this.tensorCoreMat.emissiveIntensity = 1.65;
    this.tensorCageMat.emissiveIntensity = 1.35;
    for (const m of this.badgeOrbMats) {
      m.emissiveIntensity = 1.35;
    }
    for (const mat of this.glbRingMats) {
      mat.emissiveIntensity = 1.35;
    }
    if (this.surgeColumnMat) {
      this.surgeColumnMat.opacity = 0.11;
    }
    this.surgeRingMats.forEach((mat, idx) => {
      mat.opacity = idx === 0 ? 0.52 : 0.44;
    });
    this.surgeRingMeshes.forEach((mesh, idx) => {
      mesh.scale.setScalar(1.06 + idx * 0.12);
      mesh.position.y = 0.16 + idx * 0.28;
    });
    for (let b = 0; b < this.badges.length; b++) {
      const badge = this.badges[b];
      if (!badge) continue;
      const ang = (this.badgeAngles[b] ?? 0) - Math.PI / 5;
      this.badgeAngles[b] = ang;
      const surgeHeight = 0.34 + ((b + 1) % 3) * 0.12;
      badge.position.set(
        Math.cos(ang) * orbitRadius,
        surgeHeight,
        Math.sin(ang) * orbitRadius
      );
      badge.rotation.set(Math.PI / 2, 0, Math.sin(ang) * 0.15);
      badge.scale.set(0.84, 0.84, 0.84);
      const bMat = badge.material as THREE.MeshStandardMaterial;
      bMat.emissiveIntensity = 1.45;
    }
  }

  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    const isSurging = Date.now() < this.badgeSurgeUntil;
    const speedMult = isSurging ? 3.5 : 1.0;
    const orbitRadius = 0.72; // DEF-01: Exactly 0.72m safe clearance

    if (!isReducedMotion) {
      const targetScale = isSurging ? 0.84 : 0.62;
      const targetEmissive = isSurging ? 1.45 : 0.42;
      const targetGroupY = isSurging ? 0.44 : 0.24;
      const targetRingEmissive = isSurging ? 1.35 : 0.45;
      const targetBeamOpacity = isSurging ? 0.22 : 0.06;
      const targetRingOpacity = isSurging ? 1.0 : 0.85;
      const targetSurgeColOpacity = isSurging ? 0.11 : 0.02;

      this.tensorCoreGroup.rotation.y += clampedDelta * 0.65 * speedMult;
      this.tensorCoreGroup.position.y = 0.52 + Math.sin(Date.now() * 0.002) * 0.025;
      this.tensorCage.rotation.x += clampedDelta * 0.45 * speedMult;
      this.tensorRings.forEach((tr, tIdx) => {
        tr.rotation.z += clampedDelta * (tIdx === 0 ? 1.15 : -1.35) * speedMult;
      });
      this.tensorCoreMat.emissiveIntensity = THREE.MathUtils.damp(
        this.tensorCoreMat.emissiveIntensity,
        isSurging ? 1.55 : 0.78,
        6.0,
        clampedDelta
      );
      this.tensorCageMat.emissiveIntensity = THREE.MathUtils.damp(
        this.tensorCageMat.emissiveIntensity,
        isSurging ? 1.25 : 0.65,
        6.0,
        clampedDelta
      );
      this.badgeHalos.forEach((h, hIdx) => {
        h.rotation.z += clampedDelta * (1.2 + hIdx * 0.15) * (hIdx % 2 === 0 ? 1 : -1) * speedMult;
      });
      for (const m of this.badgeOrbMats) {
        m.emissiveIntensity = THREE.MathUtils.damp(
          m.emissiveIntensity,
          isSurging ? 1.35 : 0.65,
          6.0,
          clampedDelta
        );
      }
      this.lecternHoloGroup.position.y = -0.20 + Math.sin(Date.now() * 0.0022) * 0.014;

      if (this.surgeColumnMat) {
        this.surgeColumnMat.opacity = THREE.MathUtils.damp(
          this.surgeColumnMat.opacity,
          targetSurgeColOpacity,
          6.0,
          clampedDelta
        );
      }
      this.surgeRingMats.forEach((mat, idx) => {
        const targetSROpacity = isSurging ? (idx === 0 ? 0.52 : 0.44) : 0.05;
        mat.opacity = THREE.MathUtils.damp(mat.opacity, targetSROpacity, 6.0, clampedDelta);
      });
      this.surgeRingMeshes.forEach((mesh, idx) => {
        const phase = (Date.now() * 0.0022 + idx * 0.5) % 1;
        const targetRingScale = isSurging
          ? 1.0 + phase * 0.42
          : 0.94 + Math.sin(Date.now() * 0.0015 + idx) * 0.04;
        const nextRScale = THREE.MathUtils.damp(mesh.scale.x, targetRingScale, 6.0, clampedDelta);
        mesh.scale.setScalar(nextRScale);
        const targetRingY = isSurging ? 0.12 + phase * 0.78 : 0.12 + idx * 0.24;
        mesh.position.y = THREE.MathUtils.damp(mesh.position.y, targetRingY, 6.0, clampedDelta);
        mesh.rotation.z += clampedDelta * (isSurging ? 1.4 : 0.35) * (idx === 0 ? 1 : -1);
      });

      if (!this.isGlbLoaded) {
        const beamMat = this.projectorBeamMesh.material as THREE.MeshBasicMaterial;
        beamMat.opacity = THREE.MathUtils.damp(beamMat.opacity, targetBeamOpacity, 8.0, clampedDelta);
        const ringMat = this.projectorRingMesh.material as THREE.MeshBasicMaterial;
        ringMat.opacity = THREE.MathUtils.damp(ringMat.opacity, targetRingOpacity, 8.0, clampedDelta);
      }
      for (const gMat of this.glbRingMats) {
        gMat.emissiveIntensity = THREE.MathUtils.damp(
          gMat.emissiveIntensity,
          targetRingEmissive,
          8.0,
          clampedDelta
        );
      }

      this.orbitBadgesGroup.position.y = THREE.MathUtils.damp(
        this.orbitBadgesGroup.position.y,
        targetGroupY,
        8.0,
        clampedDelta
      );
      for (let b = 0; b < this.badges.length; b++) {
        const curAngle = (this.badgeAngles[b] ?? 0) + clampedDelta * 0.75 * speedMult;
        this.badgeAngles[b] = curAngle;
        const badge = this.badges[b];
        if (!badge) continue;

        badge.position.x = Math.cos(curAngle) * orbitRadius;
        badge.position.z = Math.sin(curAngle) * orbitRadius;
        badge.position.y = Math.sin(curAngle * 2.0) * 0.08;
        badge.rotation.set(Math.PI / 2, 0, Math.sin(curAngle) * 0.15);
        const nextScale = THREE.MathUtils.damp(badge.scale.x, targetScale, 8.0, clampedDelta);
        badge.scale.set(nextScale, nextScale, nextScale);
        const bMat = badge.material as THREE.MeshStandardMaterial;
        bMat.emissiveIntensity = THREE.MathUtils.damp(
          bMat.emissiveIntensity,
          targetEmissive,
          8.0,
          clampedDelta
        );
      }
    }
  }

  public dispose(): void {
    this.studioEnvMap = null;
    for (const geo of this.disposableGeos) {
      geo.dispose();
    }
    this.disposableGeos = [];
    if (this.screenTexture) {
      this.screenTexture.dispose();
      this.screenTexture = null;
    }
  }
}
