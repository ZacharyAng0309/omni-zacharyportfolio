import * as THREE from 'three';
import {
  applyStudioEnvMapToRoot,
  createGltfLoader,
  resolveAssetUrl,
} from '../core/gltfLoader';

export interface Act4SummitOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
  onSelectSummitBeacon?: () => void;
  onModelLoaded?: () => void;
}

/**
 * Act4Summit
 * Constructs and manages the Act 4 Swiss Alps Summit (Global Grand Champions Hilti ITC 2024):
 * - Mount Pilatus low-poly alpine terrain relief
 * - 24K Golden Trophy
 * - The Star Press Museum Parchment in right corridor (X > 0, DEF-03)
 * - Summit halo & raycast beacon
 */
export class Act4Summit {
  private summitGroup: THREE.Group;
  private goldenTrophyGroup: THREE.Group;
  private graniteRidgeGroup: THREE.Group;
  private starPressParchment: THREE.Group;
  private starPressPaperMesh: THREE.Mesh;
  private starPressBackingFrame: THREE.Mesh;
  private schaanBeaconGroup: THREE.Group;
  private contourRingsGroup: THREE.Group;
  private auroraBeamMesh: THREE.Mesh;
  private summitHalo: THREE.Mesh;
  private terrainConeMesh: THREE.Mesh;
  private summitBeaconLight: THREE.PointLight;
  private starCanvasTexture: THREE.CanvasTexture | null = null;
  private schaanHoloGroup: THREE.Group;
  private schaanPrismMesh: THREE.Mesh;
  private schaanCanvasTexture: THREE.CanvasTexture | null = null;
  private trophyCrownGroup: THREE.Group;
  private trophyRingOuter: THREE.Mesh;
  private trophyRingInner: THREE.Mesh;
  private disposableGeos: THREE.BufferGeometry[] = [];
  private selectedWaypointId: string = 'hilti-trophy';
  private onSelectSummitBeacon?: () => void;
  private studioEnvMap: THREE.Texture | null = null;
  private hasRequestedLoad: boolean = false;
  private isGlbLoaded: boolean = false;
  private onModelLoaded?: () => void;

  constructor(options: Act4SummitOptions) {
    this.onSelectSummitBeacon = options.onSelectSummitBeacon;
    this.onModelLoaded = options.onModelLoaded;
    this.summitGroup = new THREE.Group();
    this.summitGroup.name = 'SummitGroup';
    this.summitGroup.position.set(0, 0, -56.0); // Act 4 Station at Z = -56.0

    // 0. Grounded Alpine Slate Diorama Island & 3 Topographic Elevation Contour Rings
    const islandMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.65,
      metalness: 0.45,
    });
    const islandMesh = new THREE.Mesh(new THREE.CylinderGeometry(2.65, 2.85, 0.22, 48), islandMat);
    islandMesh.name = 'SM_Island_Act4';
    islandMesh.position.set(0.85, -1.56, 0.0);
    islandMesh.receiveShadow = true;
    this.summitGroup.add(islandMesh);

    this.contourRingsGroup = new THREE.Group();
    this.contourRingsGroup.name = 'SM_Contour_Rings';
    const contourMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.42 });
    [1.1, 1.75, 2.45].forEach((r, idx) => {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(r, 0.012, 12, 64), contourMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.set(0.65, -1.44 + idx * 0.04, 0.0);
      this.contourRingsGroup.add(ring);
    });
    this.summitGroup.add(this.contourRingsGroup);

    // Waypoint 1: Schaan HQ Basecamp Beacon (47.166° N, 9.509° E)
    this.schaanBeaconGroup = new THREE.Group();
    this.schaanBeaconGroup.name = 'Prop_Beacon_Schaan';
    this.schaanBeaconGroup.position.set(-0.95, -0.85, 0.55);
    const schaanPillar = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.12, 0.65, 16),
      new THREE.MeshStandardMaterial({ color: 0xdc2626, emissive: 0x991b1b, emissiveIntensity: 0.85, metalness: 0.7, roughness: 0.25 })
    );
    schaanPillar.userData = { type: 'subTargetProp', actIndex: 3, subTargetId: 'schaan-hq' };
    this.schaanBeaconGroup.add(schaanPillar);
    this.summitGroup.add(this.schaanBeaconGroup);

    // Golden Aurora Sky Beam above the 24k Trophy
    const auroraMat = new THREE.MeshBasicMaterial({
      color: 0xffd700,
      transparent: true,
      opacity: 0.18,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.auroraBeamMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.52, 4.5, 24, 1, true), auroraMat);
    this.auroraBeamMesh.name = 'SummitAuroraBeam';
    this.auroraBeamMesh.position.set(0.35, 2.1, 0.0);
    this.summitGroup.add(this.auroraBeamMesh);
    options.materialsList.push(islandMat, contourMat, auroraMat);

    // 1. Swiss Alps Terrain Relief
    const terrainGeo = new THREE.ConeGeometry(8.5, 4.2, 7, 1);
    const terrainMat = new THREE.MeshStandardMaterial({
      color: 0x1f293d,
      roughness: 0.85,
      metalness: 0.15,
      flatShading: true,
    });
    const mountain = new THREE.Mesh(terrainGeo, terrainMat);
    mountain.name = 'LegacySummitTerrainCone';
    mountain.position.set(0, -3.2, -5.0);
    this.terrainConeMesh = mountain;
    this.summitGroup.add(mountain);

    // 1B. Alpine Granite Ridge Trail & Climbable Boulders
    this.graniteRidgeGroup = new THREE.Group();
    this.graniteRidgeGroup.name = 'GraniteRidgeGroup';
    const rockMat = new THREE.MeshStandardMaterial({
      color: 0x334155,
      roughness: 0.9,
      metalness: 0.1,
      flatShading: true,
    });
    options.materialsList.push(rockMat);

    const boulder1 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.75, 1), rockMat);
    boulder1.position.set(0.65, -0.65, 1.2);
    boulder1.scale.set(1.4, 0.8, 1.1);
    this.graniteRidgeGroup.add(boulder1);

    const boulder2 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.60, 1), rockMat);
    boulder2.position.set(-0.45, -0.85, 0.6);
    boulder2.scale.set(1.2, 0.9, 1.0);
    this.graniteRidgeGroup.add(boulder2);

    const summitPedestal = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.65, 0.35, 8), rockMat);
    summitPedestal.position.set(0.35, 0.05, 0.0);
    this.graniteRidgeGroup.add(summitPedestal);

    this.summitGroup.add(this.graniteRidgeGroup);

    // 2. 24K Golden Trophy Group
    this.goldenTrophyGroup = new THREE.Group();
    this.goldenTrophyGroup.name = 'GoldenTrophy';
    this.goldenTrophyGroup.userData = { type: 'subTargetProp', actIndex: 3, subTargetId: 'hilti-trophy' };
    this.goldenTrophyGroup.position.set(0.35, 0.25, 0.0);

    const goldMat = new THREE.MeshStandardMaterial({
      color: 0xffd700,
      emissive: 0x735100,
      emissiveIntensity: 0.45,
      metalness: 0.96,
      roughness: 0.12,
    });

    const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.08, 0.32, 24), goldMat);
    cup.position.y = 0.16;
    this.goldenTrophyGroup.add(cup);

    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.16, 16), goldMat);
    stem.position.y = -0.05;
    this.goldenTrophyGroup.add(stem);

    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.18, 0.08, 24), goldMat);
    base.position.y = -0.16;
    this.goldenTrophyGroup.add(base);

    this.summitGroup.add(this.goldenTrophyGroup);

    // 3. DEF-03: The Star Press Parchment in Right Spatial Corridor (X > 0)
    this.starPressParchment = new THREE.Group();
    this.starPressParchment.name = 'StarPressParchment';
    this.starPressParchment.userData = { type: 'subTargetProp', actIndex: 3, subTargetId: 'star-press' };
    this.starPressParchment.position.set(2.45, 0.20, 0.25); // X = 2.45 in right corridor per DEF-03

    const starCanvas = document.createElement('canvas');
    starCanvas.width = 512;
    starCanvas.height = 512;
    const ctx = starCanvas.getContext('2d');
    if (ctx) {
      // Warm archival broadsheet gradient so ACESFilmic dawn lighting reads crisply
      const newsBg = ctx.createLinearGradient(0, 0, 512, 512);
      newsBg.addColorStop(0.0, '#f0e9d7');
      newsBg.addColorStop(0.5, '#eae1cc');
      newsBg.addColorStop(1.0, '#dfd4bc');
      ctx.fillStyle = newsBg;
      ctx.fillRect(0, 0, 512, 512);

      // Double gold-leaf editorial frame & masthead dividers
      ctx.strokeStyle = '#9a6e29';
      ctx.lineWidth = 8;
      ctx.strokeRect(14, 14, 484, 484);
      ctx.strokeStyle = '#b98b3f';
      ctx.lineWidth = 2;
      ctx.strokeRect(24, 24, 464, 464);

      ctx.fillStyle = '#b91c1c';
      ctx.font = 'bold 42px serif';
      ctx.fillText('THE STAR', 38, 76);
      ctx.fillStyle = '#475569';
      ctx.font = 'bold 13px sans-serif';
      ctx.fillText('NATIONAL PRESS FEATURE  •  MALAYSIA  •  1ST WORLDWIDE', 38, 102);

      ctx.fillStyle = '#9a6e29';
      ctx.fillRect(38, 114, 436, 3);
      ctx.fillRect(38, 120, 436, 1);

      ctx.fillStyle = '#0f172a';
      ctx.font = 'bold 27px serif';
      ctx.fillText('Malaysians Win Hilti', 38, 162);
      ctx.fillText('Global IT Competition', 38, 196);

      // Two-column editorial hairline & copy
      ctx.fillStyle = '#94a3b8';
      ctx.fillRect(262, 224, 1, 180);

      ctx.fillStyle = '#1e293b';
      ctx.font = '16px sans-serif';
      ctx.fillText('Team Sweetzerland', 38, 244);
      ctx.fillText('crowned 1st Place', 38, 270);
      ctx.fillText('Worldwide across', 38, 296);
      ctx.fillText('53 global finalists.', 38, 322);

      ctx.fillStyle = '#334155';
      ctx.font = '15px sans-serif';
      ctx.fillText('Schaan HQ ->', 278, 244);
      ctx.fillText('Mount Pilatus', 278, 268);
      ctx.fillText('Alpine Summit', 278, 292);
      ctx.fillText('7,000 ft Finale', 278, 316);

      ctx.fillStyle = '#9a6e29';
      ctx.fillRect(38, 412, 436, 2);
      ctx.fillStyle = '#92400e';
      ctx.font = 'bold 15px sans-serif';
      ctx.fillText('LIECHTENSTEIN  •  SWITZERLAND  •  ARCHIVE 04', 38, 444);
    }
    this.starCanvasTexture = new THREE.CanvasTexture(starCanvas);
    this.starCanvasTexture.colorSpace = THREE.SRGBColorSpace;

    const paperMat = new THREE.MeshStandardMaterial({
      color: 0xd8d0be,
      map: this.starCanvasTexture,
      roughness: 0.9,
      metalness: 0.04,
      side: THREE.DoubleSide,
    });
    this.starPressPaperMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.72, 0.48), paperMat);
    this.starPressPaperMesh.name = 'StarPressPaperMesh';
    this.starPressPaperMesh.userData = { type: 'subTargetProp', actIndex: 3, subTargetId: 'star-press' };
    this.starPressPaperMesh.rotation.y = -Math.PI * 0.15;
    this.starPressParchment.add(this.starPressPaperMesh);

    // Antique bronze backing plaque behind the fallback broadsheet so it reads as an archival museum frame
    const backingMat = new THREE.MeshStandardMaterial({
      color: 0x4c3a22,
      roughness: 0.42,
      metalness: 0.78,
    });
    this.starPressBackingFrame = new THREE.Mesh(new THREE.BoxGeometry(0.76, 0.52, 0.025), backingMat);
    this.starPressBackingFrame.name = 'StarPressBackingFrame';
    this.starPressBackingFrame.userData = { type: 'subTargetProp', actIndex: 3, subTargetId: 'star-press' };
    this.starPressBackingFrame.rotation.y = -Math.PI * 0.15;
    this.starPressBackingFrame.position.set(0.007, 0, -0.015);
    this.starPressParchment.add(this.starPressBackingFrame);
    this.summitGroup.add(this.starPressParchment);
    options.materialsList.push(backingMat);

    // 4. Summit Halo & Interactive Beacon
    const haloMat = new THREE.MeshBasicMaterial({ color: 0xffd700, transparent: true, opacity: 0.65 });
    this.summitHalo = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.015, 16, 64), haloMat);
    this.summitHalo.name = 'SummitHalo';
    this.summitHalo.position.set(0.35, 0.65, 0.0);
    this.summitHalo.rotation.x = Math.PI / 2;
    this.summitGroup.add(this.summitHalo);

    const beaconCore = new THREE.Mesh(
      new THREE.SphereGeometry(0.08, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0xfff4cc })
    );
    beaconCore.name = 'SummitBeaconCore';
    beaconCore.userData = { type: 'summitBeacon' };
    beaconCore.position.set(0.35, 0.65, 0.0);
    this.summitGroup.add(beaconCore);

    this.summitBeaconLight = new THREE.PointLight(0xf59e0b, 0.0, 6.0);
    this.summitBeaconLight.name = 'SummitBeaconLight';
    this.summitBeaconLight.position.set(0.35, 0.65, 0.0);
    this.summitGroup.add(this.summitBeaconLight);

    options.scene.add(this.summitGroup);

    // 5. SchaanPitchHolo (Pin 01: Hilti Schaan HQ Executive Pitch Telemetry Screen & Enterprise Prism)
    this.schaanHoloGroup = new THREE.Group();
    this.schaanHoloGroup.name = 'SchaanPitchHolo';
    this.schaanHoloGroup.position.set(-0.95, -0.45, 0.35);

    let sTex: THREE.CanvasTexture | null = null;
    if (typeof document !== 'undefined') {
      try {
        const sCanvas = document.createElement('canvas');
        sCanvas.width = 256;
        sCanvas.height = 144;
        const sCtx = sCanvas.getContext('2d');
        if (sCtx) {
          const grad = sCtx.createLinearGradient(0, 0, 256, 144);
          grad.addColorStop(0.0, '#140c10');
          grad.addColorStop(1.0, '#1e1618');
          sCtx.fillStyle = grad;
          sCtx.fillRect(0, 0, 256, 144);

          sCtx.strokeStyle = '#dc2626';
          sCtx.lineWidth = 3;
          sCtx.strokeRect(5, 5, 246, 134);
          sCtx.strokeStyle = 'rgba(251, 191, 36, 0.55)';
          sCtx.lineWidth = 1;
          sCtx.strokeRect(10, 10, 236, 124);

          sCtx.fillStyle = '#fbbf24';
          sCtx.font = 'bold 10px sans-serif';
          sCtx.fillText('SCHAAN HQ EXECUTIVE PITCH', 18, 28);
          sCtx.fillStyle = '#fca5a5';
          sCtx.font = 'bold 10px sans-serif';
          sCtx.fillText('47.166° N  •  9.509° E', 18, 44);

          const bars = [
            { y: 64, w: 196, col: '#dc2626' },
            { y: 84, w: 168, col: '#fbbf24' },
            { y: 104, w: 210, col: '#f8fafc' },
          ];
          for (const b of bars) {
            sCtx.fillStyle = 'rgba(255,255,255,0.12)';
            sCtx.fillRect(18, b.y, 220, 8);
            sCtx.fillStyle = b.col;
            sCtx.fillRect(18, b.y, b.w, 8);
          }
          sTex = new THREE.CanvasTexture(sCanvas);
          sTex.colorSpace = THREE.SRGBColorSpace;
          this.schaanCanvasTexture = sTex;
        }
      } catch {
        // JSDOM headless fallback
      }
    }

    const schaanScreenGeo = new THREE.PlaneGeometry(0.42, 0.26);
    const schaanBezelGeo = new THREE.BoxGeometry(0.45, 0.29, 0.014);
    const schaanPrismGeo = new THREE.OctahedronGeometry(0.085, 0);
    const schaanScreenMat = new THREE.MeshStandardMaterial({
      color: sTex ? 0xffffff : 0x261216,
      map: sTex,
      emissive: 0xdc2626,
      emissiveMap: sTex,
      emissiveIntensity: sTex ? 0.65 : 0.45,
      roughness: 0.22,
      metalness: 0.25,
      side: THREE.DoubleSide,
    });
    const schaanBezelMat = new THREE.MeshStandardMaterial({
      color: 0xd4a338,
      metalness: 0.90,
      roughness: 0.22,
    });
    const schaanPrismMat = new THREE.MeshBasicMaterial({
      color: 0xfbbf24,
      transparent: true,
      opacity: 0.78,
      wireframe: true,
    });

    const schaanConsoleGroup = new THREE.Group();
    schaanConsoleGroup.rotation.set(-0.46, 0.28, 0, 'YXZ');
    const schaanBezel = new THREE.Mesh(schaanBezelGeo, schaanBezelMat);
    schaanBezel.position.z = -0.010;
    const schaanScreen = new THREE.Mesh(schaanScreenGeo, schaanScreenMat);
    schaanScreen.name = 'SchaanPitchScreen';
    schaanConsoleGroup.add(schaanBezel, schaanScreen);

    this.schaanPrismMesh = new THREE.Mesh(schaanPrismGeo, schaanPrismMat);
    this.schaanPrismMesh.name = 'SchaanEnterprisePrism';
    this.schaanPrismMesh.position.set(0.0, 0.22, 0.0);

    this.schaanHoloGroup.add(schaanConsoleGroup, this.schaanPrismMesh);
    const schaanTag = { type: 'subTargetProp', actIndex: 3, subTargetId: 'schaan-hq' };
    this.schaanHoloGroup.traverse((o) => {
      o.userData = { ...schaanTag };
    });
    this.summitGroup.add(this.schaanHoloGroup);

    // 6. TrophyVictoryCrown (Pin 02: Dual Counter-Rotating Golden Victory Rings circling the 24K Championship Cup)
    this.trophyCrownGroup = new THREE.Group();
    this.trophyCrownGroup.name = 'TrophyVictoryCrown';
    this.trophyCrownGroup.position.set(0.25, 0.16, 0.0);

    const vRingOuterGeo = new THREE.TorusGeometry(0.28, 0.005, 12, 48);
    const vRingInnerGeo = new THREE.TorusGeometry(0.34, 0.004, 12, 48);
    const vRingMat = new THREE.MeshBasicMaterial({
      color: 0xfbbf24,
      transparent: true,
      opacity: 0.70,
    });
    this.trophyRingOuter = new THREE.Mesh(vRingOuterGeo, vRingMat);
    this.trophyRingOuter.name = 'TrophyVictoryRingOuter';
    this.trophyRingOuter.rotation.set(Math.PI / 2 - 0.34, 0.24, 0.0);

    this.trophyRingInner = new THREE.Mesh(vRingInnerGeo, vRingMat);
    this.trophyRingInner.name = 'TrophyVictoryRingInner';
    this.trophyRingInner.rotation.set(Math.PI / 2 + 0.38, -0.28, 0.0);

    this.trophyCrownGroup.add(this.trophyRingOuter, this.trophyRingInner);
    const trophyTag = { type: 'subTargetProp', actIndex: 3, subTargetId: 'hilti-trophy' };
    this.trophyCrownGroup.traverse((o) => {
      o.userData = { ...trophyTag };
    });
    this.summitGroup.add(this.trophyCrownGroup);

    this.disposableGeos.push(schaanScreenGeo, schaanBezelGeo, schaanPrismGeo, vRingOuterGeo, vRingInnerGeo);

    options.materialsList.push(
      terrainMat,
      goldMat,
      paperMat,
      haloMat,
      schaanScreenMat,
      schaanBezelMat,
      schaanPrismMat,
      vRingMat
    );
  }

  public setStudioEnvMap(envMap: THREE.Texture | null): void {
    this.studioEnvMap = envMap;
    applyStudioEnvMapToRoot(this.summitGroup, envMap);
  }

  public ensureLoaded(): void {
    if (this.hasRequestedLoad || typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    this.loadSummitGLB('/models/props/act4_summit.glb').catch(() => {});
  }

  public async loadSummitGLB(url: string = '/models/props/act4_summit.glb'): Promise<void> {
    if (typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    try {
      const resolvedUrl = resolveAssetUrl(url);
      const loader = await createGltfLoader();
      loader.load(
        resolvedUrl,
        (gltf) => {
          const root = gltf.scene;
          root.name = 'Act4SummitGLB';
          root.position.set(0, -1.45, 0);
          this.isGlbLoaded = true;

          // Hide procedural fallback boulders, cone mountain, and aurora cylinder once Blender Alpine massif & plinths load
          this.graniteRidgeGroup.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.contourRingsGroup.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.schaanBeaconGroup.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.goldenTrophyGroup.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.auroraBeamMesh.visible = false;
          this.terrainConeMesh.visible = false;
          this.summitHalo.geometry.scale(0.001, 0.001, 0.001);
          this.alignStarPressToGLBFrame();
          this.summitGroup.traverse((c) => {
            if (
              (c.name === 'SM_Island_Act4' || c.name === 'SummitBeaconCore') &&
              c.parent === this.summitGroup &&
              (c as THREE.Mesh).isMesh
            ) {
              (c as THREE.Mesh).geometry.scale(0.001, 0.001, 0.001);
            }
          });

          root.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
              const isMassifMesh =
                child.name.startsWith('SM_Mount_Pilatus_Massif') ||
                child.parent?.name === 'SM_Mount_Pilatus_Massif';
              child.castShadow = !isMassifMesh;
              child.receiveShadow = !isMassifMesh;
            }
            if (child.name === 'Prop_Beacon_Schaan') {
              const tag = { type: 'subTargetProp', actIndex: 3, subTargetId: 'schaan-hq' };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            } else if (child.name === 'Prop_Trophy_Hilti24k') {
              const tag = { type: 'subTargetProp', actIndex: 3, subTargetId: 'hilti-trophy' };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            } else if (child.name === 'Prop_Star_PressFrame') {
              const tag = { type: 'subTargetProp', actIndex: 3, subTargetId: 'star-press' };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            }
          });

          if (this.studioEnvMap) {
            applyStudioEnvMapToRoot(root, this.studioEnvMap);
          }
          this.summitGroup.add(root);
          this.onModelLoaded?.();
        },
        undefined,
        () => {}
      );
    } catch {
      // Ignore in headless/JSDOM environments
    }
  }

  public alignStarPressToGLBFrame(): void {
    const yaw = -0.27925; // Matches Prop_Star_PressFrame -16 deg rotation in act4_summit.glb
    const frontOffset = 0.030;
    this.starPressParchment.position.set(
      2.35 + frontOffset * Math.sin(yaw),
      -0.21,
      0.25 + frontOffset * Math.cos(yaw)
    );
    this.starPressParchment.rotation.y = yaw;
    this.starPressPaperMesh.rotation.y = 0;
    this.starPressPaperMesh.geometry.dispose();
    this.starPressPaperMesh.geometry = new THREE.PlaneGeometry(0.54, 0.56);
    // Prop_Star_PressFrame in act4_summit.glb already renders the gneiss-and-gold museum frame
    this.starPressBackingFrame.visible = false;
  }

  public getSummitGroup(): THREE.Group { return this.summitGroup; }
  public getGoldenTrophy(): THREE.Group { return this.goldenTrophyGroup; }
  public getGraniteRidgeGroup(): THREE.Group { return this.graniteRidgeGroup; }
  public getStarPressParchment(): THREE.Group { return this.starPressParchment; }
  public getSummitBeaconLight(): THREE.PointLight { return this.summitBeaconLight; }
  public getSelectedWaypointId(): string { return this.selectedWaypointId; }

  public selectWaypoint(waypointId: string): void {
    this.selectedWaypointId = waypointId;
    const auroraMat = this.auroraBeamMesh.material as THREE.MeshBasicMaterial;
    auroraMat.opacity = waypointId === 'hilti-trophy' ? 0.35 : 0.14;
  }

  public triggerBeaconCallback(): void {
    this.onSelectSummitBeacon?.();
  }

  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    if (!isReducedMotion) {
      if (!this.isGlbLoaded) {
        this.goldenTrophyGroup.rotation.y += clampedDelta * 0.4;
        this.summitHalo.rotation.z += clampedDelta * 0.6;
      }
      this.schaanPrismMesh.rotation.y += clampedDelta * 0.55;
      this.schaanPrismMesh.rotation.x += clampedDelta * 0.25;
      this.trophyRingOuter.rotation.z += clampedDelta * 0.48;
      this.trophyRingInner.rotation.z -= clampedDelta * 0.62;
    } else {
      this.schaanPrismMesh.rotation.set(0.18, 0.45, 0.0);
    }
  }

  public dispose(): void {
    this.studioEnvMap = null;
    this.starPressPaperMesh.geometry.dispose();
    this.starPressBackingFrame.geometry.dispose();
    for (const geo of this.disposableGeos) {
      geo.dispose();
    }
    this.disposableGeos = [];
    if (this.starCanvasTexture) {
      this.starCanvasTexture.dispose();
    }
    if (this.schaanCanvasTexture) {
      this.schaanCanvasTexture.dispose();
      this.schaanCanvasTexture = null;
    }
  }
}
