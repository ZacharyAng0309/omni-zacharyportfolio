import * as THREE from 'three';
import { getCorridorTransitState } from '../core/stationProgress';

export interface ChapterBackdropAnchor {
  zCenter: number;
  floorY: number;
  accentHex: string;
  shaftColor: number;
}

export const CHAPTER_BACKDROP_ANCHORS: readonly ChapterBackdropAnchor[] = [
  { zCenter: 5.0, floorY: -1.45, accentHex: 'rgba(212, 180, 131,', shaftColor: 0xd4b483 },
  { zCenter: -18.0, floorY: -1.45, accentHex: 'rgba(216, 159, 84,', shaftColor: 0xdba052 },
  { zCenter: -36.0, floorY: -1.45, accentHex: 'rgba(56, 189, 248,', shaftColor: 0x38bdf8 },
  { zCenter: -56.0, floorY: -1.30, accentHex: 'rgba(255, 207, 109,', shaftColor: 0xffcf6d },
  { zCenter: -75.0, floorY: -1.45, accentHex: 'rgba(249, 115, 22,', shaftColor: 0xf97316 },
  { zCenter: -95.0, floorY: -1.45, accentHex: 'rgba(94, 234, 212,', shaftColor: 0x5eead4 },
] as const;

/**
 * Builds 6 distinct, full-viewport 3D movie-set environments behind each act diorama
 * with deterministic geometry/material/texture disposal (WebGL Governance Invariant 1).
 */
export class CinemaSetsBuilder {
  private geometries: THREE.BufferGeometry[] = [];
  private materials: THREE.Material[] = [];
  private textures: THREE.CanvasTexture[] = [];
  private cloudSeaMeshes: Array<{ mesh: THREE.Mesh; baseX: number; speed: number; phase: number }> = [];
  private animatedRings: THREE.Mesh[] = [];
  private chapterGroups: THREE.Group[] = [];
  private portalGates: Array<{
    group: THREE.Group;
    glowMats: THREE.MeshBasicMaterial[];
    midSp: number;
  }> = [];
  private corridorShards: Array<{
    mesh: THREE.Mesh;
    baseY: number;
    baseRotY: number;
    phase: number;
    gateIdx: number;
  }> = [];
  private lightShaftMeshes: Array<{
    mesh: THREE.Mesh;
    baseRotZ: number;
    baseOpacity: number;
    phase: number;
  }> = [];
  private spotlightPodsInst: THREE.InstancedMesh | null = null;
  private spotlightPodDummy: THREE.Object3D = new THREE.Object3D();
  private act1StudioMaterials: THREE.MeshStandardMaterial[] = [];
  private act6EclipseMats: THREE.MeshBasicMaterial[] = [];
  private act6CoronaMat: THREE.MeshBasicMaterial | null = null;
  private sunHaloMesh: THREE.Mesh | null = null;
  private featheredBeamTex: THREE.CanvasTexture | null = null;
  private softCloudTex: THREE.CanvasTexture | null = null;
  private eclipseCoronaTex: THREE.CanvasTexture | null = null;

  constructor() {
    this.initProceduralTextures();
  }

  private trackGeo<T extends THREE.BufferGeometry>(geo: T): T {
    this.geometries.push(geo);
    return geo;
  }

  private trackMat<T extends THREE.Material>(mat: T): T {
    this.materials.push(mat);
    return mat;
  }

  private initProceduralTextures(): void {
    if (typeof document === 'undefined') return;

    // 1. Soft Gaussian volumetric spotlight beam texture
    try {
      const c = document.createElement('canvas');
      c.width = 256;
      c.height = 256;
      const ctx = c.getContext('2d');
      if (ctx) {
        const img = ctx.createImageData(256, 256);
        const data = img.data;
        for (let py = 0; py < 256; py++) {
          const v = py / 255;
          const verticalEnv = Math.pow(Math.sin(v * Math.PI), 1.3) * (0.35 + 0.65 * (1.0 - v));
          for (let px = 0; px < 256; px++) {
            const u = px / 255;
            const distFromCenter = Math.abs(u - 0.5) * 2.0;
            const beamHalfWidth = 0.25 + v * 0.62;
            const normX = Math.min(1.0, distFromCenter / beamHalfWidth);
            const radialEnv = Math.pow(Math.cos(normX * Math.PI * 0.5), 2.3);
            const alpha = Math.max(0, Math.min(255, Math.round(verticalEnv * radialEnv * 255)));
            const offset = (py * 256 + px) * 4;
            data[offset] = 255;
            data[offset + 1] = 255;
            data[offset + 2] = 255;
            data[offset + 3] = alpha;
          }
        }
        ctx.putImageData(img, 0, 0);
        const tex = new THREE.CanvasTexture(c);
        tex.colorSpace = THREE.SRGBColorSpace;
        this.featheredBeamTex = tex;
        this.textures.push(tex);
      }
    } catch {
      // JSDOM headless fallback
    }

    // 2. Soft billowing cloud-sea texture (zero hard quad edges)
    try {
      const c = document.createElement('canvas');
      c.width = 256;
      c.height = 128;
      const ctx = c.getContext('2d');
      if (ctx) {
        const blobs = [
          { x: 128, y: 66, r: 62, a: 0.55 },
          { x: 84, y: 74, r: 48, a: 0.42 },
          { x: 172, y: 72, r: 48, a: 0.42 },
          { x: 52, y: 80, r: 36, a: 0.28 },
          { x: 204, y: 80, r: 36, a: 0.28 },
        ];
        for (const b of blobs) {
          const g = ctx.createRadialGradient(b.x, b.y, 4, b.x, b.y, b.r);
          g.addColorStop(0.0, `rgba(255, 250, 240, ${Math.min(1, b.a * 1.45)})`);
          g.addColorStop(0.45, `rgba(244, 212, 178, ${b.a * 0.72})`);
          g.addColorStop(1.0, 'rgba(140, 118, 132, 0)');
          ctx.fillStyle = g;
          ctx.fillRect(0, 0, 256, 128);
        }
        const tex = new THREE.CanvasTexture(c);
        tex.colorSpace = THREE.SRGBColorSpace;
        this.softCloudTex = tex;
        this.textures.push(tex);
      }
    } catch {
      // JSDOM headless fallback
    }

    // 3. Total Solar Eclipse smooth multi-harmonic astronomical corona texture (Act 6 — zero blocky spoke bars)
    try {
      const c = document.createElement('canvas');
      c.width = 512;
      c.height = 512;
      const ctx = c.getContext('2d');
      if (ctx) {
        const img = ctx.createImageData(512, 512);
        const data = img.data;
        const limbR = 0.285;
        for (let py = 0; py < 512; py++) {
          const dy = (py - 255.5) / 256.0;
          for (let px = 0; px < 512; px++) {
            const dx = (px - 255.5) / 256.0;
            const normR = Math.hypot(dx, dy);
            const idx = (py * 512 + px) * 4;
            if (normR < limbR * 0.94 || normR >= 0.995) {
              data[idx] = 0;
              data[idx + 1] = 0;
              data[idx + 2] = 0;
              data[idx + 3] = 0;
              continue;
            }
            const theta = Math.atan2(dy, dx);
            const dr = Math.max(0, normR - limbR);
            const innerRise = Math.min(1.0, Math.max(0.0, (normR - limbR * 0.94) / (limbR * 0.09)));
            const streamerHarm =
              0.56 +
              0.17 * Math.cos(theta * 2.0 + 0.35) +
              0.13 * Math.cos(theta * 5.0 - 0.85) +
              0.08 * Math.sin(theta * 9.0 + 1.1) +
              0.06 * Math.cos(theta * 14.0 - 0.4);
            const coreGlow = Math.exp(-dr * 18.0) * 0.96;
            const midCorona = Math.exp(-dr * (5.6 - 1.9 * streamerHarm)) * (0.48 + 0.42 * streamerHarm);
            const outerFade = Math.pow(Math.max(0, 1.0 - Math.max(0, (normR - 0.52) / 0.46)), 1.6);

            // Delicate celestial degree tick markings orbiting the corona rim
            let tickBoost = 0;
            if (Math.abs(normR - 0.415) < 0.0055) {
              const degMod = ((theta + Math.PI) * (180 / Math.PI)) % 10;
              if (degMod < 1.2 || degMod > 8.8) tickBoost = 0.22;
            } else if (Math.abs(normR - 0.465) < 0.003) {
              const degMod30 = ((theta + Math.PI) * (180 / Math.PI)) % 30;
              if (degMod30 < 1.4 || degMod30 > 28.6) tickBoost = 0.26;
            }

            const alphaF = Math.min(
              1.0,
              Math.max(0.0, innerRise * (coreGlow + midCorona * outerFade) + tickBoost)
            );
            const tHue = Math.min(1.0, dr / 0.36);
            const rCol = Math.round(254 * (1 - tHue) + 72 * tHue);
            const gCol = Math.round(244 * (1 - tHue) + 228 * tHue);
            const bCol = Math.round(212 * (1 - tHue) + 216 * tHue);

            data[idx] = rCol;
            data[idx + 1] = gCol;
            data[idx + 2] = bCol;
            data[idx + 3] = Math.round(alphaF * 255);
          }
        }
        ctx.putImageData(img, 0, 0);

        const tex = new THREE.CanvasTexture(c);
        tex.colorSpace = THREE.SRGBColorSpace;
        this.eclipseCoronaTex = tex;
        this.textures.push(tex);
      }
    } catch {
      // JSDOM headless fallback
    }
  }

  private createFloorAura(ch: ChapterBackdropAnchor, idx: number, targetGroup: THREE.Group): void {
    const floorGeo = this.trackGeo(new THREE.PlaneGeometry(30, 30));
    let floorTex: THREE.CanvasTexture | null = null;

    if (typeof document !== 'undefined') {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const fCtx = canvas.getContext('2d');
        if (fCtx) {
          const rad = fCtx.createRadialGradient(256, 256, 20, 256, 256, 252);
          rad.addColorStop(0.0, `${ch.accentHex} 0.20)`);
          rad.addColorStop(0.42, `${ch.accentHex} 0.09)`);
          rad.addColorStop(0.76, `${ch.accentHex} 0.025)`);
          rad.addColorStop(1.0, `${ch.accentHex} 0)`);
          fCtx.fillStyle = rad;
          fCtx.fillRect(0, 0, 512, 512);

          fCtx.lineWidth = 1.25;
          for (const ratio of [0.34, 0.50, 0.72]) {
            fCtx.strokeStyle = `${ch.accentHex} 0.14)`;
            fCtx.beginPath();
            fCtx.arc(256, 256, 252 * ratio, 0, Math.PI * 2);
            fCtx.stroke();
          }

          floorTex = new THREE.CanvasTexture(canvas);
          floorTex.colorSpace = THREE.SRGBColorSpace;
          this.textures.push(floorTex);
        }
      } catch {
        // JSDOM headless fallback
      }
    }

    const auraMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: floorTex ? 0xffffff : ch.shaftColor,
        map: floorTex,
        transparent: true,
        opacity: floorTex ? 0.92 : 0.08,
        side: THREE.DoubleSide,
        depthWrite: false,
      })
    );
    const auraMesh = new THREE.Mesh(floorGeo, auraMat);
    auraMesh.name = `ChapterFloorAura_${idx}`;
    auraMesh.rotation.x = -Math.PI / 2;
    auraMesh.position.set(0, ch.floorY - 0.06, -1.5);
    targetGroup.add(auraMesh);
  }

  private addLightShafts(
    group: THREE.Group,
    idx: number,
    colorHex: number,
    configs: ReadonlyArray<{ x: number; y: number; z: number; rotZ: number; w: number; h: number; opacity: number }>
  ): void {
    configs.forEach((cfg, sIdx) => {
      const geo = this.trackGeo(new THREE.PlaneGeometry(cfg.w, cfg.h));
      const baseOpacity = this.featheredBeamTex ? cfg.opacity : cfg.opacity * 0.35;
      const mat = this.trackMat(
        new THREE.MeshBasicMaterial({
          color: colorHex,
          map: this.featheredBeamTex,
          transparent: true,
          opacity: baseOpacity,
          side: THREE.DoubleSide,
          depthWrite: false,
          fog: false,
          blending: THREE.AdditiveBlending,
        })
      );
      const mesh = new THREE.Mesh(geo, mat);
      mesh.name = `ChapterLightShaft_${idx}_${sIdx}`;
      mesh.position.set(cfg.x, cfg.y, cfg.z);
      mesh.rotation.z = cfg.rotZ;
      group.add(mesh);
      this.lightShaftMeshes.push({
        mesh,
        baseRotZ: cfg.rotZ,
        baseOpacity,
        phase: idx * 1.15 + sIdx * 0.85,
      });
    });
  }

  /**
   * Scenario 01: Sovereign Titanium Atelier Gallery
   * Dark brushed-basalt rotunda floor, concentric champagne-brass datum rings,
   * 15 slender matte-obsidian apse monoliths with hairline metallic reveals,
   * and an overhead dark-anodized studio canopy cove.
   */
  private populateAct1TitaniumAtelier(group: THREE.Group, floorY: number): void {
    const centerX = 0.42;
    const centerZ = -0.10;

    const basaltFloorMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x090b10,
        roughness: 0.38,
        metalness: 0.45,
        envMapIntensity: 0.9,
      })
    );
    const obsidianMonolithMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x101218,
        roughness: 0.34,
        metalness: 0.68,
        envMapIntensity: 0.9,
      })
    );
    const champagneHairlineMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0xd4b483,
        emissive: 0x6b532f,
        emissiveIntensity: 0.24,
        roughness: 0.20,
        metalness: 0.94,
        envMapIntensity: 0.9,
      })
    );
    this.act1StudioMaterials.push(basaltFloorMat, obsidianMonolithMat, champagneHairlineMat);

    // 1. Wide seamless brushed-basalt gallery studio floor
    const studioFloorGeo = this.trackGeo(new THREE.CircleGeometry(14.0, 96));
    const studioFloor = new THREE.Mesh(studioFloorGeo, basaltFloorMat);
    studioFloor.name = 'AtelierBasaltFloor';
    studioFloor.rotation.x = -Math.PI / 2;
    studioFloor.position.set(centerX, floorY - 0.015, centerZ);
    studioFloor.receiveShadow = true;
    group.add(studioFloor);

    // 2. Three razor-thin concentric champagne-brass architectural floor datum rings
    for (const [rIdx, rad] of ([2.85, 4.45, 6.20] as const).entries()) {
      const ringGeo = this.trackGeo(new THREE.RingGeometry(rad, rad + 0.014, 96));
      const ringMesh = new THREE.Mesh(ringGeo, champagneHairlineMat);
      ringMesh.name = `AtelierFloorDatumRing_${rIdx}`;
      ringMesh.rotation.x = -Math.PI / 2;
      ringMesh.position.set(centerX, floorY - 0.010, centerZ);
      group.add(ringMesh);
    }

    // 3. Semi-circular architectural apse (R = 7.4m, -72 deg .. +72 deg) of 15 slender monolith blades
    const apseCount = 15;
    const apseRadius = 7.4;
    const monolithGeo = this.trackGeo(new THREE.BoxGeometry(0.42, 6.2, 0.28));
    const trimGeo = this.trackGeo(new THREE.BoxGeometry(0.014, 6.0, 0.022));
    const floorWashGeo = this.trackGeo(new THREE.BoxGeometry(0.46, 0.016, 0.16));

    const monolithInst = new THREE.InstancedMesh(monolithGeo, obsidianMonolithMat, apseCount);
    monolithInst.name = 'AtelierApseMonoliths';
    const trimInst = new THREE.InstancedMesh(trimGeo, champagneHairlineMat, apseCount);
    trimInst.name = 'AtelierApseHairlineTrims';

    const coveMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xd4b483,
        transparent: true,
        opacity: 0.28,
      })
    );
    const washInst = new THREE.InstancedMesh(floorWashGeo, coveMat, apseCount);
    washInst.name = 'AtelierApseFloorWashes';

    const dummy = new THREE.Object3D();
    for (let i = 0; i < apseCount; i++) {
      const frac = i / (apseCount - 1);
      const angle = (frac - 0.5) * THREE.MathUtils.degToRad(144);
      const x = centerX + Math.sin(angle) * apseRadius;
      const z = centerZ - Math.cos(angle) * apseRadius;
      const yaw = -angle;

      dummy.position.set(x, floorY + 3.08, z);
      dummy.rotation.set(0, yaw, 0);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      monolithInst.setMatrixAt(i, dummy.matrix);

      // Hairline champagne-titanium inner vertical edge trim
      dummy.position.set(
        centerX + Math.sin(angle) * (apseRadius - 0.155),
        floorY + 3.05,
        centerZ - Math.cos(angle) * (apseRadius - 0.155)
      );
      dummy.rotation.set(0, yaw, 0);
      dummy.updateMatrix();
      trimInst.setMatrixAt(i, dummy.matrix);

      // Subtle warm wall-grazing floor wash line at blade base
      dummy.position.set(
        centerX + Math.sin(angle) * (apseRadius - 0.24),
        floorY - 0.005,
        centerZ - Math.cos(angle) * (apseRadius - 0.24)
      );
      dummy.rotation.set(0, yaw, 0);
      dummy.updateMatrix();
      washInst.setMatrixAt(i, dummy.matrix);
    }
    monolithInst.instanceMatrix.needsUpdate = true;
    trimInst.instanceMatrix.needsUpdate = true;
    washInst.instanceMatrix.needsUpdate = true;
    group.add(monolithInst, trimInst, washInst);

    // 4. Minimalist overhead dark-anodized studio canopy ring (Y = 3.55m) with subtle warm cove rim
    const canopyGeo = this.trackGeo(new THREE.TorusGeometry(2.65, 0.055, 16, 96));
    const canopyMesh = new THREE.Mesh(canopyGeo, obsidianMonolithMat);
    canopyMesh.name = 'AtelierOverheadCanopyRing';
    canopyMesh.rotation.x = Math.PI / 2;
    canopyMesh.position.set(centerX, 3.55, centerZ);
    group.add(canopyMesh);

    const canopyCoveGeo = this.trackGeo(new THREE.TorusGeometry(2.58, 0.012, 12, 96));
    const canopyCoveMesh = new THREE.Mesh(canopyCoveGeo, champagneHairlineMat);
    canopyCoveMesh.name = 'AtelierOverheadCanopyCove';
    canopyCoveMesh.rotation.x = Math.PI / 2;
    canopyCoveMesh.position.set(centerX, 3.50, centerZ);
    group.add(canopyCoveMesh);

    this.addLightShafts(group, 0, 0xd4b483, [
      { x: centerX - 0.35, y: 2.05, z: centerZ - 0.65, rotZ: -0.06, w: 3.4, h: 6.4, opacity: 0.09 },
      { x: centerX + 0.55, y: 2.15, z: centerZ - 0.85, rotZ: 0.05, w: 3.2, h: 6.4, opacity: 0.08 },
    ]);
  }

  public applyAct1StudioEnvMap(envMap: THREE.Texture | null): void {
    for (const mat of this.act1StudioMaterials) {
      mat.envMap = envMap;
      mat.envMapIntensity = 0.9;
      mat.needsUpdate = true;
    }
  }

  /**
   * Scenario 02: Grand Cathedral Interstellar Archive
   * Soaring vaulted library arches & towering warm-lit book gallery stacks.
   */
  private populateAct2CathedralLibrary(group: THREE.Group, floorY: number): void {
    const walnutMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x2b1b12,
        roughness: 0.55,
        metalness: 0.25,
      })
    );
    const brassMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0xd4a359,
        emissive: 0x6b4715,
        emissiveIntensity: 0.45,
        roughness: 0.25,
        metalness: 0.88,
      })
    );
    const alcoveGlowMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0xffe4b5,
        emissive: 0xd99b43,
        emissiveIntensity: 0.85,
        roughness: 0.4,
      })
    );

    // 4 Giant Vaulted Cathedral Arches receding in depth (sized cleanly inside 46-deg camera frustum)
    const archGeo = this.trackGeo(new THREE.TorusGeometry(3.82, 0.13, 10, 44, Math.PI));
    const ribHaloGeo = this.trackGeo(new THREE.TorusGeometry(3.66, 0.024, 8, 44, Math.PI));
    const ribHaloMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xfbbf24,
        transparent: true,
        opacity: 0.78,
      })
    );
    const pierGeo = this.trackGeo(new THREE.BoxGeometry(0.42, 4.1, 0.44));
    [-1.4, -4.3, -7.2, -10.2].forEach((az, i) => {
      const arch = new THREE.Mesh(archGeo, i % 2 === 0 ? bronzeOrBrass(brassMat, walnutMat, true) : walnutMat);
      arch.name = `CathedralRibArch_${i}`;
      arch.position.set(0, -0.18, az);
      group.add(arch);

      const halo = new THREE.Mesh(ribHaloGeo, ribHaloMat);
      halo.name = `CathedralRibHalo_${i}`;
      halo.position.set(0, -0.18, az + 0.06);
      group.add(halo);
      this.animatedRings.push(halo);

      const leftPier = new THREE.Mesh(pierGeo, walnutMat);
      leftPier.position.set(-3.82, floorY + 2.05, az);
      const rightPier = new THREE.Mesh(pierGeo, walnutMat);
      rightPier.position.set(3.82, floorY + 2.05, az);
      group.add(leftPier, rightPier);
    });

    const pendantGeo = this.trackGeo(new THREE.SphereGeometry(0.11, 12, 12));
    const pendantInst = new THREE.InstancedMesh(pendantGeo, alcoveGlowMat, 6);
    pendantInst.name = 'CathedralPendantLuminaires';
    const pendantRodGeo = this.trackGeo(new THREE.CylinderGeometry(0.014, 0.014, 2.4, 8));
    const pendantRodInst = new THREE.InstancedMesh(pendantRodGeo, brassMat, 6);
    pendantRodInst.name = 'CathedralPendantRods';
    const pendantDummy = new THREE.Object3D();
    [-2.4, -5.2, -8.0].forEach((pz, pIdx) => {
      [-2.35, 2.35].forEach((px, sideIdx) => {
        const idx = pIdx * 2 + sideIdx;
        pendantDummy.position.set(px, 1.65, pz);
        pendantDummy.scale.set(1, 1, 1);
        pendantDummy.rotation.set(0, 0, 0);
        pendantDummy.updateMatrix();
        pendantInst.setMatrixAt(idx, pendantDummy.matrix);

        pendantDummy.position.set(px, 2.85, pz);
        pendantDummy.updateMatrix();
        pendantRodInst.setMatrixAt(idx, pendantDummy.matrix);
      });
    });
    pendantInst.instanceMatrix.needsUpdate = true;
    pendantRodInst.instanceMatrix.needsUpdate = true;
    group.add(pendantInst, pendantRodInst);

    // Instanced Semicircular Cathedral Rotunda Library Bays wrapping rear apse cleanly (-130 to +130 deg)
    const stackBayCount = 24;
    const bayGeo = this.trackGeo(new THREE.BoxGeometry(1.55, 5.4, 0.48));
    const bayInst = new THREE.InstancedMesh(bayGeo, walnutMat, stackBayCount);
    bayInst.name = 'LibraryStackBays';

    // Sleek fine brass gallery shelf cornice ledges (replaces thick zebra blocks with classical Long Room molding)
    const sconceRailMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0xe6b86a,
        emissive: 0xc27c28,
        emissiveIntensity: 0.48,
        roughness: 0.35,
        metalness: 0.65,
      })
    );
    const warmPanelGeo = this.trackGeo(new THREE.BoxGeometry(1.18, 0.045, 0.10));
    const warmInst = new THREE.InstancedMesh(warmPanelGeo, sconceRailMat, stackBayCount * 4);
    warmInst.name = 'LibrarySconceRows';

    // Vertical brass pilasters framing each library alcove bay + instanced archival folio spine blocks
    const pilasterGeo = this.trackGeo(new THREE.BoxGeometry(0.065, 5.2, 0.14));
    const pilasterInst = new THREE.InstancedMesh(pilasterGeo, brassMat, stackBayCount);
    pilasterInst.name = 'LibraryBayPilasters';

    const spineBlockCount = stackBayCount * 3 * 3;
    const spineBlockGeo = this.trackGeo(new THREE.BoxGeometry(0.18, 0.42, 0.16));
    const spineBlockMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0xffffff,
        emissive: 0x24140a,
        emissiveIntensity: 0.22,
        roughness: 0.48,
        metalness: 0.22,
      })
    );
    const spinePalette = [
      new THREE.Color(0x7c2d12), // Warm oxblood leather
      new THREE.Color(0x1e4d3b), // Deep forest calfskin
      new THREE.Color(0x1e3a5f), // Midnight archive navy
      new THREE.Color(0x8b4513), // Aged cognac folio
      new THREE.Color(0x6b2137), // Royal burgundy cloth
      new THREE.Color(0x926227), // Ochre vellum
    ];
    const spineInst = new THREE.InstancedMesh(spineBlockGeo, spineBlockMat, spineBlockCount);
    spineInst.name = 'LibraryBookBlocks';

    const dummy = new THREE.Object3D();
    let warmIdx = 0;
    let spineIdx = 0;

    for (let i = 0; i < stackBayCount; i++) {
      const frac = i / Math.max(stackBayCount - 1, 1);
      const angle = (frac - 0.5) * Math.PI * 1.44; // sweeps seamlessly across left flank, apse center, right flank behind stage
      const radius = 6.2 + (i % 2) * 0.18;
      const x = Math.sin(angle) * radius;
      const z = -2.2 - Math.cos(angle) * radius;
      const rotY = -angle;
      const tangentX = Math.cos(angle);
      const tangentZ = Math.sin(angle);

      dummy.position.set(x, floorY + 2.7, z);
      dummy.rotation.set(0, rotY, 0);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      bayInst.setMatrixAt(i, dummy.matrix);

      // Vertical brass divider pilaster centered cleanly between adjacent gallery bays
      const halfStep = (Math.PI * 1.44) / Math.max(stackBayCount - 1, 1) * 0.5;
      dummy.position.set(
        Math.sin(angle + halfStep) * (radius - 0.24),
        floorY + 2.65,
        -2.2 - Math.cos(angle + halfStep) * (radius - 0.24)
      );
      dummy.rotation.set(0, -(angle + halfStep), 0);
      dummy.updateMatrix();
      pilasterInst.setMatrixAt(i, dummy.matrix);

      for (let tier = 0; tier < 4; tier++) {
        dummy.position.set(
          Math.sin(angle) * (radius - 0.26),
          floorY + 0.85 + tier * 1.25,
          -2.2 - Math.cos(angle) * (radius - 0.26)
        );
        dummy.rotation.set(0, rotY, 0);
        dummy.updateMatrix();
        warmInst.setMatrixAt(warmIdx++, dummy.matrix);

        if (tier < 3) {
          for (let bSlot = 0; bSlot < 3; bSlot++) {
            const slotOff = (bSlot - 1) * 0.34;
            dummy.position.set(
              Math.sin(angle) * (radius - 0.24) + tangentX * slotOff,
              floorY + 1.08 + tier * 1.25,
              -2.2 - Math.cos(angle) * (radius - 0.24) + tangentZ * slotOff
            );
            dummy.rotation.set(0, rotY, 0);
            dummy.scale.set(1.0, 0.85 + ((i + tier + bSlot) % 3) * 0.14, 1.0);
            dummy.updateMatrix();
            spineInst.setColorAt(spineIdx, spinePalette[(i * 7 + tier * 3 + bSlot) % spinePalette.length]!);
            spineInst.setMatrixAt(spineIdx++, dummy.matrix);
          }
          dummy.scale.set(1, 1, 1);
        }
      }
    }
    bayInst.instanceMatrix.needsUpdate = true;
    warmInst.instanceMatrix.needsUpdate = true;
    pilasterInst.instanceMatrix.needsUpdate = true;
    spineInst.instanceMatrix.needsUpdate = true;
    if (spineInst.instanceColor) {
      spineInst.instanceColor.needsUpdate = true;
    }
    group.add(bayInst, warmInst, pilasterInst, spineInst);

    // Flush inlaid brass floor compass ring circling the scholar island
    const floorInlayRing = new THREE.Mesh(
      this.trackGeo(new THREE.RingGeometry(2.68, 2.74, 64)),
      this.trackMat(
        new THREE.MeshBasicMaterial({
          color: 0xd4a359,
          transparent: true,
          opacity: 0.42,
          side: THREE.DoubleSide,
        })
      )
    );
    floorInlayRing.name = 'CathedralFloorInlayRing';
    floorInlayRing.rotation.x = -Math.PI / 2;
    floorInlayRing.position.set(0.35, floorY + 0.018, -0.3);
    group.add(floorInlayRing);

    this.addLightShafts(group, 1, 0xdba052, [
      { x: -1.6, y: 2.3, z: -2.0, rotZ: -0.15, w: 3.2, h: 7.5, opacity: 0.20 },
      { x: 0.1, y: 2.5, z: -1.8, rotZ: 0.02, w: 3.6, h: 7.8, opacity: 0.24 },
      { x: 1.8, y: 2.3, z: -2.1, rotZ: 0.15, w: 3.2, h: 7.5, opacity: 0.20 },
    ]);
  }

  /**
   * Scenario 03: IMAX Keynote Stadium Arena
   * Overhead steel lighting truss rig, Fresnel stage pods & sweeping amphitheater seating tiers.
   */
  private populateAct3KeynoteArena(group: THREE.Group, floorY: number): void {
    const trussSteelMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x334155,
        roughness: 0.38,
        metalness: 0.85,
      })
    );
    const tierConcreteMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x0e172a,
        roughness: 0.65,
        metalness: 0.35,
        side: THREE.DoubleSide,
      })
    );
    const cyanRibbonMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.58,
        side: THREE.DoubleSide,
      })
    );

    // Overhead Arena Lighting Truss Canopy (widened span framed cleanly below top timeline HUD bar)
    const mainTrussGeo = this.trackGeo(new THREE.BoxGeometry(17.6, 0.24, 0.38));
    const upperTruss = new THREE.Mesh(mainTrussGeo, trussSteelMat);
    upperTruss.name = 'ArenaTrussBeam';
    upperTruss.position.set(0.3, 2.22, -3.6);
    group.add(upperTruss);

    const upperChordGeo = this.trackGeo(new THREE.BoxGeometry(17.6, 0.14, 0.28));
    const upperChord = new THREE.Mesh(upperChordGeo, trussSteelMat);
    upperChord.name = 'ArenaUpperChordBeam';
    upperChord.position.set(0.3, 2.52, -3.6);
    group.add(upperChord);

    const fasciaStripGeo = this.trackGeo(new THREE.BoxGeometry(17.2, 0.035, 0.05));
    const fasciaStrip = new THREE.Mesh(fasciaStripGeo, cyanRibbonMat);
    fasciaStrip.name = 'ArenaTrussFasciaStrip';
    fasciaStrip.position.set(0.3, 2.22, -3.40);
    group.add(fasciaStrip);

    const towerGeo = this.trackGeo(new THREE.BoxGeometry(0.28, 4.2, 0.28));
    const leftTrussCol = new THREE.Mesh(towerGeo, trussSteelMat);
    leftTrussCol.position.set(-8.3, floorY + 2.1, -3.6);
    const rightTrussCol = new THREE.Mesh(towerGeo, trussSteelMat);
    rightTrussCol.position.set(8.9, floorY + 2.1, -3.6);
    group.add(leftTrussCol, rightTrussCol);

    // Diagonal Warren-truss webbing struts tying upper & lower arena chords together
    const webCount = 18;
    const webGeo = this.trackGeo(new THREE.BoxGeometry(0.045, 0.56, 0.06));
    const webInst = new THREE.InstancedMesh(webGeo, trussSteelMat, webCount);
    webInst.name = 'ArenaTrussWebbing';
    const webDummy = new THREE.Object3D();
    for (let w = 0; w < webCount; w++) {
      const wx = -7.7 + (w / (webCount - 1)) * 16.0;
      webDummy.position.set(wx, 2.37, -3.6);
      webDummy.rotation.set(0, 0, w % 2 === 0 ? 0.65 : -0.65);
      webDummy.scale.set(1, 1, 1);
      webDummy.updateMatrix();
      webInst.setMatrixAt(w, webDummy.matrix);
    }
    webInst.instanceMatrix.needsUpdate = true;
    group.add(webInst);

    // 7 Compact Downward-Aimed Stage Spotlight Pods
    const podGeo = this.trackGeo(new THREE.CylinderGeometry(0.08, 0.11, 0.22, 12));
    const podMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        emissive: 0x38bdf8,
        emissiveIntensity: 0.65,
      })
    );
    const podInst = new THREE.InstancedMesh(podGeo, podMat, 7);
    podInst.name = 'ArenaSpotlightPods';
    const coneGeo = this.trackGeo(new THREE.ConeGeometry(0.62, 3.4, 16, 1, true));
    const coneMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.09,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      })
    );
    const coneInst = new THREE.InstancedMesh(coneGeo, coneMat, 7);
    coneInst.name = 'ArenaSpotlightCones';
    const dummy = new THREE.Object3D();
    for (let i = 0; i < 7; i++) {
      const px = 0.3 + (i - 3) * 1.9;
      dummy.position.set(px, 2.18, -3.6);
      dummy.rotation.set(0.08, 0, (px / 6.0) * -0.18);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      podInst.setMatrixAt(i, dummy.matrix);

      dummy.position.set(px, 0.48, -3.5);
      dummy.rotation.set(0, 0, (px / 6.0) * -0.18);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      coneInst.setMatrixAt(i, dummy.matrix);
    }
    podInst.instanceMatrix.needsUpdate = true;
    coneInst.instanceMatrix.needsUpdate = true;
    this.spotlightPodsInst = podInst;
    group.add(podInst, coneInst);

    // Sweeping Rear-Only Amphitheater Stadium Tiers (Cylinder arc around -Z = PI, never entering +Z foreground)
    for (let tier = 0; tier < 5; tier++) {
      const radius = 5.8 + tier * 1.45;
      const tierGeo = this.trackGeo(
        new THREE.CylinderGeometry(radius, radius + 0.45, 0.55, 48, 1, true, Math.PI * 0.42, Math.PI * 1.16)
      );
      const tierMesh = new THREE.Mesh(tierGeo, tierConcreteMat);
      tierMesh.name = `StadiumTier_${tier}`;
      tierMesh.position.set(0, floorY + 0.38 + tier * 0.64, -2.0);
      group.add(tierMesh);

      const ledGeo = this.trackGeo(
        new THREE.CylinderGeometry(radius - 0.04, radius - 0.04, 0.042, 48, 1, true, Math.PI * 0.42, Math.PI * 1.16)
      );
      const ledMesh = new THREE.Mesh(ledGeo, cyanRibbonMat);
      ledMesh.position.set(0, floorY + 0.65 + tier * 0.64, -2.0);
      group.add(ledMesh);
    }

    // Panoramic amphitheater seat micro-LED embers & sleek stage horizon frame behind lectern
    const emberCount = 120;
    const emberGeo = this.trackGeo(new THREE.BoxGeometry(0.055, 0.04, 0.04));
    const emberMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xbae6fd,
        transparent: true,
        opacity: 0.72,
      })
    );
    const emberInst = new THREE.InstancedMesh(emberGeo, emberMat, emberCount);
    emberInst.name = 'ArenaAudienceEmbers';
    let aSeed = 3307;
    const aRand = () => {
      aSeed = (aSeed * 1664525 + 1013904223) >>> 0;
      return aSeed / 4294967296;
    };
    for (let e = 0; e < emberCount; e++) {
      const tier = e % 5;
      const radius = 5.86 + tier * 1.45;
      const frac = ((Math.floor(e / 5) + 0.5) / 24);
      const ang = Math.PI * 0.44 + frac * Math.PI * 1.12;
      const ex = Math.sin(ang) * radius;
      const ez = -2.0 + Math.cos(ang) * radius;
      dummy.position.set(ex, floorY + 0.50 + tier * 0.64 + aRand() * 0.10, ez);
      dummy.rotation.set(0, ang, 0);
      dummy.scale.set(0.7 + aRand() * 1.1, 1, 1);
      dummy.updateMatrix();
      emberInst.setMatrixAt(e, dummy.matrix);
    }
    emberInst.instanceMatrix.needsUpdate = true;
    group.add(emberInst);

    const keynoteBackdrop = new THREE.Mesh(
      this.trackGeo(new THREE.CylinderGeometry(5.15, 5.15, 2.2, 40, 1, true, Math.PI * 0.72, Math.PI * 0.56)),
      this.trackMat(
        new THREE.MeshBasicMaterial({
          color: 0x0ea5e9,
          map: this.featheredBeamTex,
          transparent: true,
          opacity: this.featheredBeamTex ? 0.14 : 0.05,
          side: THREE.DoubleSide,
          depthWrite: false,
          blending: THREE.AdditiveBlending,
        })
      )
    );
    keynoteBackdrop.name = 'ArenaKeynoteBackdropFrame';
    keynoteBackdrop.position.set(0, floorY + 1.45, -1.8);
    group.add(keynoteBackdrop);

    this.addLightShafts(group, 2, 0x38bdf8, [
      { x: -3.2, y: 1.0, z: -3.4, rotZ: -0.24, w: 2.8, h: 5.4, opacity: 0.16 },
      { x: 0.0, y: 1.0, z: -3.4, rotZ: 0.0, w: 3.2, h: 5.5, opacity: 0.20 },
      { x: 2.8, y: 1.0, z: -3.4, rotZ: 0.20, w: 2.8, h: 5.4, opacity: 0.16 },
    ]);
  }

  /**
   * Scenario 04: Swiss Alps Sunrise Over the Cloud Sea
   * Layered far Alpine silhouettes + huge golden sunrise solar bloom + drifting 3D cloud sea.
   */
  private populateAct4AlpineSunrise(group: THREE.Group, floorY: number): void {
    // 1. Far Deep Alpine Silhouette Mountain Band (behind foreground Pilatus GLB, spanning right horizon cleanly)
    const ridge1Shape = new THREE.Shape();
    ridge1Shape.moveTo(-24, -4);
    const pts1 = [
      [-24, 1.4], [-20, 3.2], [-16, 1.9], [-12.5, 4.1], [-9.0, 2.3],
      [-5.2, 4.6], [-2.0, 2.5], [1.6, 3.9], [5.4, 3.5], [9.2, 4.85],
      [13.5, 3.4], [17.8, 4.4], [22.0, 2.8], [24.0, 2.9],
    ];
    for (const p of pts1) {
      ridge1Shape.lineTo(p[0]!, p[1]!);
    }
    ridge1Shape.lineTo(24, -4);
    ridge1Shape.closePath();

    const ridge1Geo = this.trackGeo(new THREE.ShapeGeometry(ridge1Shape));
    const ridge1Mat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x1d2638,
        emissive: 0x261d24,
        emissiveIntensity: 0.16,
        roughness: 0.94,
        metalness: 0.03,
        side: THREE.DoubleSide,
      })
    );
    const ridge1Mesh = new THREE.Mesh(ridge1Geo, ridge1Mat);
    ridge1Mesh.name = 'FarAlpineRidge_Near';
    ridge1Mesh.position.set(0, -1.0, -9.2);
    group.add(ridge1Mesh);

    const ridge2Mat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x28354d,
        emissive: 0x3a2824,
        emissiveIntensity: 0.20,
        roughness: 0.96,
        metalness: 0.02,
        side: THREE.DoubleSide,
      })
    );
    const ridge2Mesh = new THREE.Mesh(ridge1Geo, ridge2Mat);
    ridge2Mesh.name = 'FarAlpineRidge_Distant';
    ridge2Mesh.position.set(1.8, -0.35, -13.6);
    ridge2Mesh.scale.set(1.25, 1.15, 1);
    group.add(ridge2Mesh);

    // Layered aerial-perspective mist bands between near & distant ridges so peaks separate without a hard top seam
    const interRidgeMistMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xffd199,
        map: this.softCloudTex ?? this.featheredBeamTex,
        transparent: true,
        opacity: this.softCloudTex ? 0.30 : (this.featheredBeamTex ? 0.14 : 0.06),
        depthWrite: false,
        fog: false,
      })
    );
    const interRidgeMist = new THREE.Mesh(this.trackGeo(new THREE.PlaneGeometry(34, 4.4)), interRidgeMistMat);
    interRidgeMist.name = 'AlpineInterRidgeMist';
    interRidgeMist.position.set(0.4, 0.05, -11.4);
    group.add(interRidgeMist);

    // Subtle brushed-gold Swiss Summit observation deck arc at floorY
    const summitDeckRing = new THREE.Mesh(
      this.trackGeo(new THREE.RingGeometry(2.55, 2.61, 64)),
      this.trackMat(
        new THREE.MeshBasicMaterial({
          color: 0xf59e0b,
          transparent: true,
          opacity: 0.45,
          side: THREE.DoubleSide,
        })
      )
    );
    summitDeckRing.name = 'SummitTerraceTrim';
    summitDeckRing.rotation.x = -Math.PI / 2;
    summitDeckRing.position.set(0.35, floorY + 0.02, -0.2);
    group.add(summitDeckRing);

    // 2. Radiant Golden Sunrise Disc & Atmospheric Dawn Halo (framed inside central Alpine saddle at X = -0.35, Y = 3.65)
    const sunCoreGeo = this.trackGeo(new THREE.CircleGeometry(1.38, 32));
    const sunCoreMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xffe4a0,
        transparent: true,
        opacity: 0.94,
        fog: false,
      })
    );
    const sunCore = new THREE.Mesh(sunCoreGeo, sunCoreMat);
    sunCore.name = 'AlpineSunriseSunDisc';
    sunCore.position.set(-0.35, 3.65, -14.6);
    group.add(sunCore);

    const haloGeo = this.trackGeo(new THREE.PlaneGeometry(11.5, 11.5));
    const haloMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xffb85c,
        map: this.softCloudTex,
        transparent: true,
        opacity: this.softCloudTex ? 0.42 : 0.14,
        depthWrite: false,
        fog: false,
        blending: THREE.AdditiveBlending,
      })
    );
    const sunHalo = new THREE.Mesh(haloGeo, haloMat);
    sunHalo.name = 'AlpineSunriseHalo';
    sunHalo.position.set(-0.35, 3.65, -14.4);
    this.sunHaloMesh = sunHalo;
    group.add(sunHalo);

    const innerHaloRingGeo = this.trackGeo(new THREE.TorusGeometry(1.62, 0.018, 10, 48));
    const innerHaloRingMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xfff1c2,
        transparent: true,
        opacity: 0.42,
        fog: false,
      })
    );
    const innerHaloRing = new THREE.Mesh(innerHaloRingGeo, innerHaloRingMat);
    innerHaloRing.name = 'AlpineSunriseInnerHaloRing';
    innerHaloRing.position.set(-0.35, 3.65, -14.52);
    group.add(innerHaloRing);
    this.animatedRings.push(innerHaloRing);

    const coronaRingGeo = this.trackGeo(new THREE.TorusGeometry(1.94, 0.026, 10, 48));
    const coronaRingMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xffdf8e,
        transparent: true,
        opacity: 0.36,
        fog: false,
      })
    );
    const coronaRing = new THREE.Mesh(coronaRingGeo, coronaRingMat);
    coronaRing.name = 'AlpineSunriseCoronaRing';
    coronaRing.position.set(-0.35, 3.65, -14.5);
    group.add(coronaRing);
    this.animatedRings.push(coronaRing);

    const alpineVeilGeo = this.trackGeo(new THREE.PlaneGeometry(26.0, 7.5));
    const alpineVeilMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xffb347,
        map: this.featheredBeamTex,
        transparent: true,
        opacity: this.featheredBeamTex ? 0.28 : 0.08,
        depthWrite: false,
        fog: false,
        blending: THREE.AdditiveBlending,
      })
    );
    const alpineVeil = new THREE.Mesh(alpineVeilGeo, alpineVeilMat);
    alpineVeil.name = 'AlpineHorizonGlowVeil';
    alpineVeil.position.set(0, 1.85, -14.2);
    group.add(alpineVeil);

    // 3. Drifting 3D Volumetric Alpine Cloud Sea nestled across valleys below & behind Pilatus
    const cloudGeo = this.trackGeo(new THREE.PlaneGeometry(10.5, 4.2));
    let seed = 8821;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    const valleyCloudBanks = [
      { cx: -4.6, cy: floorY + 0.56, cz: -3.8, op: 0.68 },
      { cx: -3.2, cy: floorY + 0.78, cz: -4.9, op: 0.62 },
      { cx: -5.4, cy: floorY + 0.42, cz: -5.2, op: 0.58 },
      { cx: 4.5, cy: floorY + 0.52, cz: -4.0, op: 0.68 },
      { cx: 3.1, cy: floorY + 0.76, cz: -5.0, op: 0.62 },
      { cx: 5.5, cy: floorY + 0.38, cz: -5.4, op: 0.58 },
    ];
    for (let i = 0; i < 20 + valleyCloudBanks.length; i++) {
      const bank = i >= 20 ? valleyCloudBanks[i - 20] : undefined;
      const cx = bank ? bank.cx : (i / 19 - 0.5) * 26.0 + (rand() - 0.5) * 1.4;
      const cz = bank ? bank.cz : -3.1 - (i % 4) * 1.9 - rand() * 1.2;
      const cy = bank ? bank.cy : floorY + 0.05 + (i % 3) * 0.28;
      const cloudMat = this.trackMat(
        new THREE.MeshBasicMaterial({
          color: i % 2 === 0 ? 0xfff3e0 : 0xf4cfb2,
          map: this.softCloudTex,
          transparent: true,
          opacity: this.softCloudTex ? (bank ? bank.op : 0.56 + rand() * 0.20) : 0.14,
          side: THREE.DoubleSide,
          depthWrite: false,
        })
      );
      const cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
      cloudMesh.name = `AlpineCloudSea_${i}`;
      cloudMesh.position.set(cx, cy, cz);
      if (bank) {
        cloudMesh.scale.set(0.68, 0.72, 1);
      }
      cloudMesh.rotation.x = -0.14;
      group.add(cloudMesh);
      this.cloudSeaMeshes.push({
        mesh: cloudMesh,
        baseX: cx,
        speed: 0.14 + rand() * 0.14,
        phase: rand() * Math.PI * 2,
      });
    }

    this.addLightShafts(group, 3, 0xffcf6d, [
      { x: -2.2, y: 1.9, z: -2.8, rotZ: -0.22, w: 4.5, h: 7.5, opacity: 0.18 },
      { x: 0.6, y: 2.0, z: -3.2, rotZ: -0.06, w: 4.0, h: 7.2, opacity: 0.15 },
    ]);
  }

  /**
   * Scenario 05: Cyber-Amber AI Reactor Vault
   * Colossal receding octagonal reactor bulkhead ribs & towering compute blade monoliths.
   */
  private populateAct5ReactorChamber(group: THREE.Group, floorY: number): void {
    const gantrySteelMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x161316,
        roughness: 0.35,
        metalness: 0.88,
      })
    );
    const emberStripMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xf97316,
        transparent: true,
        opacity: 0.85,
      })
    );
    const cyanStripMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0x22d3ee,
        transparent: true,
        opacity: 0.72,
      })
    );

    // 5 Receding Monumental Octagonal Reactor Tunnel Bulkhead Ribs
    const ribGeo = this.trackGeo(new THREE.TorusGeometry(3.42, 0.16, 6, 8));
    const innerGlowGeo = this.trackGeo(new THREE.TorusGeometry(3.22, 0.032, 6, 8));
    [-1.6, -4.2, -6.9, -9.8, -12.8].forEach((rz, idx) => {
      const rib = new THREE.Mesh(ribGeo, gantrySteelMat);
      rib.name = `ReactorBulkheadRib_${idx}`;
      rib.rotation.z = Math.PI / 8;
      rib.position.set(0.55, 0.16, rz);
      group.add(rib);

      const strip = new THREE.Mesh(innerGlowGeo, idx % 2 === 0 ? emberStripMat : cyanStripMat);
      strip.rotation.z = Math.PI / 8;
      strip.position.set(0.55, 0.16, rz + 0.14);
      group.add(strip);
      this.animatedRings.push(strip);
    });

    // Flanking Floor-to-Ceiling Compute Server Blade Monoliths (Instanced)
    const bladeCount = 22;
    const bladeGeo = this.trackGeo(new THREE.BoxGeometry(0.65, 7.2, 0.95));
    const bladeInst = new THREE.InstancedMesh(bladeGeo, gantrySteelMat, bladeCount);
    bladeInst.name = 'ReactorComputeBlades';

    const traceGeo = this.trackGeo(new THREE.BoxGeometry(0.06, 6.4, 0.08));
    const traceInst = new THREE.InstancedMesh(traceGeo, emberStripMat, bladeCount);
    traceInst.name = 'ReactorBladeTraces';

    const dummy = new THREE.Object3D();
    const reactorAxisX = 0.55;
    for (let i = 0; i < bladeCount; i++) {
      const side = i < 11 ? -1 : 1;
      const k = i < 11 ? i : i - 11;
      const bx = k >= 9
        ? reactorAxisX + side * (5.65 + (k % 2) * 0.65)
        : reactorAxisX + side * (4.55 + (k % 2) * 0.55);
      const bz = k >= 9
        ? -0.65 - (k - 9) * 0.75
        : -1.8 - k * 1.25;
      dummy.position.set(bx, floorY + 3.55, bz);
      dummy.rotation.set(0, side * -0.18, 0);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      bladeInst.setMatrixAt(i, dummy.matrix);

      dummy.position.set(bx - side * 0.34, floorY + 3.55, bz);
      dummy.updateMatrix();
      traceInst.setMatrixAt(i, dummy.matrix);
    }
    bladeInst.instanceMatrix.needsUpdate = true;
    traceInst.instanceMatrix.needsUpdate = true;
    group.add(bladeInst, traceInst);

    // High-density dual-tone telemetry LED matrix bars embedded along reactor compute blades
    const ledMatrixCount = bladeCount * 10;
    const ledCellGeo = this.trackGeo(new THREE.BoxGeometry(0.032, 0.14, 0.24));
    const ledMatrixInst = new THREE.InstancedMesh(ledCellGeo, cyanStripMat, ledMatrixCount);
    ledMatrixInst.name = 'ReactorTelemetryMatrix';
    let ledIdx = 0;
    for (let i = 0; i < bladeCount; i++) {
      const side = i < 11 ? -1 : 1;
      const k = i < 11 ? i : i - 11;
      const bx = (k >= 9
        ? reactorAxisX + side * (5.65 + (k % 2) * 0.65)
        : reactorAxisX + side * (4.55 + (k % 2) * 0.55)) - side * 0.34;
      const bz = k >= 9
        ? -0.65 - (k - 9) * 0.75
        : -1.8 - k * 1.25;
      for (let row = 0; row < 10; row++) {
        dummy.position.set(bx, floorY + 0.8 + row * 0.54, bz + ((row % 2) - 0.5) * 0.22);
        dummy.rotation.set(0, side * -0.18, 0);
        dummy.scale.set(1, 0.5 + ((i + row) % 3) * 0.35, 1);
        dummy.updateMatrix();
        ledMatrixInst.setMatrixAt(ledIdx++, dummy.matrix);
      }
    }
    ledMatrixInst.instanceMatrix.needsUpdate = true;
    group.add(ledMatrixInst);

    // Diagonal industrial gantry braces locking bulkhead ribs into side compute bays concentrically around x=0.55
    const strutGeo = this.trackGeo(new THREE.BoxGeometry(0.11, 2.8, 0.11));
    const strutInst = new THREE.InstancedMesh(strutGeo, gantrySteelMat, 8);
    strutInst.name = 'ReactorGantryStruts';
    for (let s = 0; s < 8; s++) {
      const side = s % 2 === 0 ? -1 : 1;
      const bay = Math.floor(s / 2);
      dummy.position.set(reactorAxisX + side * 3.85, floorY + 3.2, -2.2 - bay * 2.6);
      dummy.rotation.set(0, 0, side * 0.52);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      strutInst.setMatrixAt(s, dummy.matrix);
    }
    strutInst.instanceMatrix.needsUpdate = true;
    group.add(strutInst);

    // Deep-Tunnel Central AI Reactor Core Spire, Base/Upper Manifolds & Containment Rings
    const baseManifold = new THREE.Mesh(
      this.trackGeo(new THREE.CylinderGeometry(0.95, 1.15, 0.65, 8)),
      gantrySteelMat
    );
    baseManifold.name = 'ReactorBaseManifold';
    baseManifold.position.set(0.55, floorY + 0.325, -11.6);
    group.add(baseManifold);

    const upperCollector = new THREE.Mesh(
      this.trackGeo(new THREE.CylinderGeometry(1.08, 0.86, 0.55, 8)),
      gantrySteelMat
    );
    upperCollector.name = 'ReactorUpperCollector';
    upperCollector.position.set(0.55, floorY + 5.92, -11.6);
    group.add(upperCollector);

    const coreSpire = new THREE.Mesh(
      this.trackGeo(new THREE.CylinderGeometry(0.45, 0.72, 6.2, 12)),
      gantrySteelMat
    );
    coreSpire.name = 'ReactorDeepCoreSpire';
    coreSpire.position.set(0.55, floorY + 3.1, -11.6);
    group.add(coreSpire);

    const coreRingGeo = this.trackGeo(new THREE.TorusGeometry(1.15, 0.045, 8, 24));
    [-0.65, 0.0, 0.65, 1.30, 1.95].forEach((ry, idx) => {
      const ring = new THREE.Mesh(coreRingGeo, idx % 2 === 0 ? cyanStripMat : emberStripMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.set(0.55, ry, -11.6);
      group.add(ring);
      this.animatedRings.push(ring);
    });

    // Dual counter-tilted containment gimbals encircling the deep reactor spire
    const coreGimbal = new THREE.Mesh(
      this.trackGeo(new THREE.TorusGeometry(1.75, 0.032, 8, 36)),
      emberStripMat
    );
    coreGimbal.name = 'ReactorCoreGimbal';
    coreGimbal.position.set(0.55, 0.82, -11.6);
    coreGimbal.rotation.set(0.48, 0.25, -0.35);
    group.add(coreGimbal);
    this.animatedRings.push(coreGimbal);

    const coreInnerGimbal = new THREE.Mesh(
      this.trackGeo(new THREE.TorusGeometry(1.45, 0.026, 8, 36)),
      cyanStripMat
    );
    coreInnerGimbal.name = 'ReactorCoreInnerGimbal';
    coreInnerGimbal.position.set(0.55, 0.82, -11.6);
    coreInnerGimbal.rotation.set(-0.52, -0.30, 0.40);
    group.add(coreInnerGimbal);
    this.animatedRings.push(coreInnerGimbal);

    const floorBusbarGroup = new THREE.Group();
    floorBusbarGroup.name = 'ReactorFloorBusbars';
    const busbarGeo = this.trackGeo(new THREE.BoxGeometry(0.07, 0.025, 3.8));
    const leftBusbar = new THREE.Mesh(busbarGeo, emberStripMat);
    leftBusbar.position.set(0.0, floorY + 0.02, -12.2);
    const rightBusbar = new THREE.Mesh(busbarGeo, cyanStripMat);
    rightBusbar.position.set(1.10, floorY + 0.02, -12.2);
    floorBusbarGroup.add(leftBusbar, rightBusbar);
    group.add(floorBusbarGroup);

    const plasmaColGeo = this.trackGeo(new THREE.CylinderGeometry(0.18, 0.18, 5.8, 16));
    const plasmaColMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0x22d3ee,
        transparent: true,
        opacity: 0.42,
        fog: false,
        blending: THREE.AdditiveBlending,
      })
    );
    const plasmaCol = new THREE.Mesh(plasmaColGeo, plasmaColMat);
    plasmaCol.name = 'ReactorPlasmaCoreColumn';
    plasmaCol.position.set(0.55, floorY + 3.1, -11.6);
    group.add(plasmaCol);

    this.addLightShafts(group, 4, 0xf97316, [
      { x: -1.4, y: 1.9, z: -2.2, rotZ: -0.12, w: 3.4, h: 7.4, opacity: 0.18 },
      { x: 1.6, y: 1.9, z: -2.2, rotZ: 0.12, w: 3.4, h: 7.4, opacity: 0.20 },
    ]);
  }

  /**
   * Scenario 06: Cosmic Total-Solar-Eclipse Observatory Horizon
   * Giant backlit eclipse totality corona + ceremonial obsidian horizon colonnade.
   */
  private populateAct6CosmicEclipse(group: THREE.Group, floorY: number): void {
    // 1. Monumental Lunar Occultation Sphere + Corona Halo
    const coronaGeo = this.trackGeo(new THREE.PlaneGeometry(11.4, 11.4));
    const coronaMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        map: this.eclipseCoronaTex,
        transparent: true,
        opacity: this.eclipseCoronaTex ? 0.96 : 0.25,
        depthWrite: false,
        fog: false,
        blending: THREE.AdditiveBlending,
      })
    );
    this.act6CoronaMat = coronaMat;
    const coronaPlane = new THREE.Mesh(coronaGeo, coronaMat);
    coronaPlane.name = 'CosmicEclipseCorona';
    coronaPlane.position.set(-0.08, 2.18, -13.6);
    group.add(coronaPlane);

    const moonGeo = this.trackGeo(new THREE.CircleGeometry(1.75, 48));
    const moonMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0x020408,
        fog: false,
      })
    );
    const moonDisc = new THREE.Mesh(moonGeo, moonMat);
    moonDisc.name = 'CosmicEclipseMoonDisc';
    moonDisc.position.set(-0.08, 2.18, -13.3);
    group.add(moonDisc);

    // Fine glowing teal diamond-ring rim circling totality
    const rimGeo = this.trackGeo(new THREE.TorusGeometry(1.79, 0.032, 12, 64));
    const rimMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0x99f6e4,
        transparent: true,
        opacity: 0.92,
        fog: false,
      })
    );
    this.act6EclipseMats.push(rimMat);
    const eclipseRim = new THREE.Mesh(rimGeo, rimMat);
    eclipseRim.name = 'CosmicEclipseRim';
    eclipseRim.position.set(-0.08, 2.18, -13.25);
    group.add(eclipseRim);
    this.animatedRings.push(eclipseRim);

    const astrolabeGeo = this.trackGeo(new THREE.TorusGeometry(2.42, 0.022, 10, 64));
    const astrolabeMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0x5eead4,
        transparent: true,
        opacity: 0.72,
        fog: false,
      })
    );
    this.act6EclipseMats.push(astrolabeMat);
    const astrolabeRing = new THREE.Mesh(astrolabeGeo, astrolabeMat);
    astrolabeRing.name = 'CosmicEclipseAstrolabeRing';
    astrolabeRing.position.set(-0.08, 2.18, -13.22);
    astrolabeRing.rotation.set(0.42, 0.18, -0.26);
    group.add(astrolabeRing);
    this.animatedRings.push(astrolabeRing);

    const meridianRing = new THREE.Mesh(
      this.trackGeo(new THREE.TorusGeometry(2.88, 0.018, 8, 64)),
      this.trackMat(
        new THREE.MeshBasicMaterial({
          color: 0xfde68a,
          transparent: true,
          opacity: 0.48,
          fog: false,
        })
      )
    );
    meridianRing.name = 'CosmicEclipseMeridianArc';
    meridianRing.position.set(-0.08, 2.18, -13.18);
    meridianRing.rotation.set(-0.36, -0.24, 0.34);
    group.add(meridianRing);
    this.animatedRings.push(meridianRing);

    const diamondFlareGeo = this.trackGeo(new THREE.CircleGeometry(0.11, 24));
    const diamondFlareMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.85,
        fog: false,
      })
    );
    const diamondFlare = new THREE.Mesh(diamondFlareGeo, diamondFlareMat);
    diamondFlare.name = 'CosmicEclipseDiamondFlare';
    diamondFlare.position.set(1.18, 3.40, -13.20);
    group.add(diamondFlare);

    // 2. Ceremonial Horizon Colonnade Pylons + Illuminated Vertical Edge Trim
    const pylonGeo = this.trackGeo(new THREE.BoxGeometry(0.42, 4.8, 0.42));
    const pylonMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x0d1724,
        roughness: 0.35,
        metalness: 0.86,
      })
    );
    const pylonTrimGeo = this.trackGeo(new THREE.BoxGeometry(0.05, 4.3, 0.06));
    const pylonTrimMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0x2dd4bf,
        transparent: true,
        opacity: 0.72,
      })
    );
    this.act6EclipseMats.push(pylonTrimMat);
    const pylonCount = 10;
    const pylonInst = new THREE.InstancedMesh(pylonGeo, pylonMat, pylonCount);
    pylonInst.name = 'CosmicObservatoryColonnade';
    const pylonTrimInst = new THREE.InstancedMesh(pylonTrimGeo, pylonTrimMat, pylonCount);
    pylonTrimInst.name = 'CosmicObservatoryColonnadeTrim';

    const dummy = new THREE.Object3D();
    for (let i = 0; i < pylonCount; i++) {
      const side = i % 2 === 0 ? -1 : 1;
      const depthIdx = Math.floor(i / 2);
      const px = side * (3.6 + depthIdx * 0.42);
      const pz = -3.0 - depthIdx * 2.1;
      dummy.position.set(px, floorY + 2.35, pz);
      dummy.rotation.set(0, 0, 0);
      dummy.scale.set(1, 1 + depthIdx * 0.06, 1);
      dummy.updateMatrix();
      pylonInst.setMatrixAt(i, dummy.matrix);

      dummy.position.set(px - side * 0.22, floorY + 2.35, pz + 0.18);
      dummy.updateMatrix();
      pylonTrimInst.setMatrixAt(i, dummy.matrix);
    }
    pylonInst.instanceMatrix.needsUpdate = true;
    pylonTrimInst.instanceMatrix.needsUpdate = true;
    group.add(pylonInst, pylonTrimInst);

    // Stepped obsidian plinth bases & teal observatory caps so colonnade pillars read architecturally
    const capGeo = this.trackGeo(new THREE.BoxGeometry(0.62, 0.16, 0.62));
    const capInst = new THREE.InstancedMesh(capGeo, pylonMat, pylonCount * 2);
    capInst.name = 'CosmicColonnadeCapitals';
    let capIdx = 0;
    for (let i = 0; i < pylonCount; i++) {
      const side = i % 2 === 0 ? -1 : 1;
      const depthIdx = Math.floor(i / 2);
      const px = side * (3.6 + depthIdx * 0.42);
      const pz = -3.0 - depthIdx * 2.1;
      const hScale = 1 + depthIdx * 0.06;
      dummy.position.set(px, floorY + 0.08, pz);
      dummy.rotation.set(0, 0, 0);
      dummy.scale.set(1.15, 1.4, 1.15);
      dummy.updateMatrix();
      capInst.setMatrixAt(capIdx++, dummy.matrix);

      dummy.position.set(px, floorY + 2.35 + 2.4 * hScale, pz);
      dummy.scale.set(1.0, 1.0, 1.0);
      dummy.updateMatrix();
      capInst.setMatrixAt(capIdx++, dummy.matrix);
    }
    capInst.instanceMatrix.needsUpdate = true;
    group.add(capInst);

    // Ceremonial astrolabe horizon ring inlaid concentrically around world (0, -1.43, -95) Stargate terrace
    const deckCompass = new THREE.Mesh(
      this.trackGeo(new THREE.RingGeometry(2.72, 2.78, 64)),
      pylonTrimMat
    );
    deckCompass.name = 'CosmicDeckCompassRing';
    deckCompass.rotation.x = -Math.PI / 2;
    deckCompass.position.set(-0.35, floorY + 0.02, 0.0);
    group.add(deckCompass);

    this.addLightShafts(group, 5, 0x5eead4, [
      { x: -1.6, y: 2.0, z: -2.4, rotZ: -0.1, w: 3.6, h: 7.4, opacity: 0.16 },
      { x: 1.6, y: 2.0, z: -2.4, rotZ: 0.1, w: 3.6, h: 7.4, opacity: 0.16 },
    ]);
  }

  public buildChapterBackdrops(): {
    root: THREE.Group;
    chapterGroups: THREE.Group[];
  } {
    const root = new THREE.Group();
    root.name = 'ChapterArchitecturalBackdrops';
    const chapterGroups: THREE.Group[] = [];

    CHAPTER_BACKDROP_ANCHORS.forEach((ch, idx) => {
      const group = new THREE.Group();
      group.name = `ChapterBackdrop_${idx}`;
      group.position.set(0.35, 0, ch.zCenter);
      group.visible = idx === 0;

      this.createFloorAura(ch, idx, group);

      switch (idx) {
        case 0:
          this.populateAct1TitaniumAtelier(group, ch.floorY);
          break;
        case 1:
          this.populateAct2CathedralLibrary(group, ch.floorY);
          break;
        case 2:
          this.populateAct3KeynoteArena(group, ch.floorY);
          break;
        case 3:
          this.populateAct4AlpineSunrise(group, ch.floorY);
          break;
        case 4:
          this.populateAct5ReactorChamber(group, ch.floorY);
          break;
        case 5:
          this.populateAct6CosmicEclipse(group, ch.floorY);
          break;
      }

      chapterGroups.push(group);
      root.add(group);
    });

    const obsidianMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x0f121a,
        roughness: 0.28,
        metalness: 0.86,
      })
    );
    const mirrorDeckMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x090b12,
        roughness: 0.18,
        metalness: 0.88,
        transparent: true,
        opacity: 0.92,
      })
    );
    const duskTowerMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0x10131c,
        emissive: 0x3b2a18,
        emissiveIntensity: 0.18,
        roughness: 0.32,
        metalness: 0.84,
      })
    );
    const duskTowerTrimGeo = this.trackGeo(new THREE.BoxGeometry(0.055, 6.2, 0.055));
    const duskTowerTrimMat = this.trackMat(
      new THREE.MeshBasicMaterial({
        color: 0xd4b483,
        transparent: true,
        opacity: 0.72,
      })
    );
    const brassStanchionMat = this.trackMat(
      new THREE.MeshStandardMaterial({
        color: 0xd9a85e,
        emissive: 0x6b4718,
        emissiveIntensity: 0.25,
        roughness: 0.28,
        metalness: 0.88,
      })
    );
    const archVaultGeo = this.trackGeo(new THREE.TorusGeometry(2.12, 0.078, 8, 44, Math.PI));
    const archOuterAstrolabeGeo = this.trackGeo(new THREE.TorusGeometry(2.24, 0.022, 8, 44, Math.PI));
    const archVernierStrutGeo = this.trackGeo(new THREE.BoxGeometry(0.14, 0.024, 0.026));
    const archHaloGeo = this.trackGeo(new THREE.TorusGeometry(2.00, 0.017, 8, 44, Math.PI));
    const dockingRingGeo = this.trackGeo(new THREE.TorusGeometry(2.15, 0.022, 8, 48));
    const dockingPlazaGeo = this.trackGeo(new THREE.CylinderGeometry(2.15, 2.25, 0.03, 48));
    const pierBaseGeo = this.trackGeo(new THREE.BoxGeometry(0.24, 0.84, 0.40));
    const finGeo = this.trackGeo(new THREE.BoxGeometry(0.036, 1.55, 0.26));
    const finVeilGeo = this.trackGeo(new THREE.PlaneGeometry(1.05, 3.2));
    const shardGeo = this.trackGeo(new THREE.OctahedronGeometry(0.065, 0));
    const duskTowerGeo = this.trackGeo(new THREE.CylinderGeometry(0.42, 0.54, 7.4, 8));

    const portalDefs = [
      { ax: 1.35, ay: 0, az: 5.10, bx: 0.85, by: 0, bz: -17.60, accent: 0xdba052, midSp: 0.12 },
      { ax: 0.85, ay: 0, az: -17.60, bx: 0.76, by: 0, bz: -35.60, accent: 0x38bdf8, midSp: 0.32 },
      { ax: 0.76, ay: 0, az: -35.60, bx: 1.25, by: 0.15, bz: -55.80, accent: 0xffcf6d, midSp: 0.52 },
      { ax: 1.25, ay: 0.15, az: -55.80, bx: 0.92, by: 0, bz: -74.60, accent: 0xf97316, midSp: 0.72 },
      { ax: 0.92, ay: 0, az: -74.60, bx: 0.85, by: 0, bz: -94.20, accent: 0x5eead4, midSp: 0.92 },
    ] as const;

    portalDefs.forEach((def, idx) => {
      const gate = new THREE.Group();
      gate.name = `InterActPortalGate_${idx}`;
      gate.position.set(0, -1.45, 0);
      gate.visible = false;

      const glowMat = this.trackMat(
        new THREE.MeshBasicMaterial({
          color: def.accent,
          transparent: true,
          opacity: 0.78,
        })
      );
      const veilMat = this.trackMat(
        new THREE.MeshBasicMaterial({
          color: def.accent,
          map: this.featheredBeamTex,
          transparent: true,
          opacity: this.featheredBeamTex ? 0.17 : 0.06,
          side: THREE.DoubleSide,
          depthWrite: false,
          fog: false,
          blending: THREE.AdditiveBlending,
        })
      );
      const shardMat = this.trackMat(
        new THREE.MeshStandardMaterial({
          color: 0xffe6ba,
          emissive: def.accent,
          emissiveIntensity: 0.82,
          roughness: 0.22,
          metalness: 0.65,
          transparent: true,
          opacity: 0.85,
        })
      );

      // 1. Cantilevered Dark-Mirror Obsidian Skybridge Promenade Deck & Outer Edge Strips
      const spanDx = def.bx - def.ax;
      const spanDy = def.by - def.ay;
      const spanDz = def.bz - def.az;
      const horizLen = Math.hypot(spanDx, spanDz);
      const spanLen = Math.hypot(horizLen, spanDy);
      const spanYaw = Math.atan2(spanDx, spanDz);
      const spanPitch = -Math.atan2(spanDy, horizLen);
      const midX = (def.ax + def.bx) * 0.5;
      const midY = (def.ay + def.by) * 0.5;
      const midZ = (def.az + def.bz) * 0.5;

      const deckGroup = new THREE.Group();
      deckGroup.name = `SkybridgeDeckGroup_${idx}`;
      deckGroup.position.set(midX, midY - 0.055, midZ);
      deckGroup.rotation.order = 'YXZ';
      deckGroup.rotation.set(spanPitch, spanYaw, 0);

      const deckMesh = new THREE.Mesh(
        this.trackGeo(new THREE.BoxGeometry(4.7, 0.04, spanLen * 0.96)),
        mirrorDeckMat
      );
      deckMesh.name = `SkybridgePromenadeDeck_${idx}`;
      deckGroup.add(deckMesh);

      const borderRailGeo = this.trackGeo(new THREE.BoxGeometry(0.03, 0.02, spanLen * 0.95));
      const handrailGeo = this.trackGeo(new THREE.BoxGeometry(0.035, 0.035, spanLen * 0.92));
      const stanchionGeo = this.trackGeo(new THREE.BoxGeometry(0.028, 0.58, 0.028));
      const stanchionFracs = [-0.38, -0.22, -0.06, 0.06, 0.22, 0.38] as const;
      for (const side of [-1, 1] as const) {
        const outerStrip = new THREE.Mesh(borderRailGeo, glowMat);
        outerStrip.position.set(side * 2.04, 0.025, 0);
        deckGroup.add(outerStrip);

        const handrail = new THREE.Mesh(handrailGeo, glowMat);
        handrail.name = `SkybridgeHandrail_${idx}_${side > 0 ? 'R' : 'L'}`;
        handrail.position.set(side * 2.06, 0.62, 0);
        deckGroup.add(handrail);

        for (const u of stanchionFracs) {
          const post = new THREE.Mesh(stanchionGeo, brassStanchionMat);
          post.position.set(side * 2.06, 0.33, u * spanLen);
          deckGroup.add(post);
        }
      }

      const dockingRing = new THREE.Mesh(dockingRingGeo, glowMat);
      dockingRing.name = `SkybridgeThresholdRing_${idx}`;
      dockingRing.rotation.x = Math.PI / 2;
      dockingRing.position.set(0, 0.02, -spanLen * 0.44);
      deckGroup.add(dockingRing);

      const arrivalPlaza = new THREE.Mesh(dockingPlazaGeo, obsidianMat);
      arrivalPlaza.name = `SkybridgeArrivalPlaza_${idx}`;
      arrivalPlaza.position.set(0, 0.005, -spanLen * 0.44);
      deckGroup.add(arrivalPlaza);

      const departureRing = new THREE.Mesh(dockingRingGeo, glowMat);
      departureRing.name = `SkybridgeDepartureRing_${idx}`;
      departureRing.rotation.x = Math.PI / 2;
      departureRing.position.set(0, 0.02, spanLen * 0.44);
      deckGroup.add(departureRing);

      const departurePlaza = new THREE.Mesh(dockingPlazaGeo, obsidianMat);
      departurePlaza.name = `SkybridgeDeparturePlaza_${idx}`;
      departurePlaza.position.set(0, 0.005, spanLen * 0.44);
      deckGroup.add(departurePlaza);

      // Continuous razor-thin inlaid champagne-brass promenade strips along deck flanks
      const promenadeStripGeo = this.trackGeo(new THREE.BoxGeometry(0.022, 0.014, spanLen * 0.88));
      for (const side of [-1, 1] as const) {
        const inlayStrip = new THREE.Mesh(promenadeStripGeo, glowMat);
        inlayStrip.name = `SkybridgeInlayStrip_${idx}_${side > 0 ? 'R' : 'L'}`;
        inlayStrip.position.set(side * 1.24, 0.024, 0);
        deckGroup.add(inlayStrip);
      }
      gate.add(deckGroup);

      // 2. Sculpted Curved Parabolic Vaulted Bronze-Obsidian Arches (morphing seamlessly into Act 2 Cathedral ribs)
      const subFractions = [0.42, 0.61, 0.80] as const;
      subFractions.forEach((u, subIdx) => {
        const subArch = new THREE.Group();
        const cx = THREE.MathUtils.lerp(def.ax, def.bx, u);
        const cy = THREE.MathUtils.lerp(def.ay, def.by, u);
        const cz = THREE.MathUtils.lerp(def.az, def.bz, u);
        subArch.position.set(cx, cy, cz);
        subArch.rotation.y = spanYaw;
        const ribScale = 1.0 - subIdx * 0.045;
        subArch.scale.set(ribScale, ribScale, 1);

        const vaultRib = new THREE.Mesh(archVaultGeo, obsidianMat);
        vaultRib.position.set(0, 0.80, 0);
        subArch.add(vaultRib);

        const outerAstrolabeArch = new THREE.Mesh(archOuterAstrolabeGeo, brassStanchionMat);
        outerAstrolabeArch.position.set(0, 0.80, 0);
        subArch.add(outerAstrolabeArch);

        for (const strutDeg of [30, 60, 90, 120, 150]) {
          const sRad = THREE.MathUtils.degToRad(strutDeg);
          const strut = new THREE.Mesh(archVernierStrutGeo, brassStanchionMat);
          strut.position.set(Math.cos(sRad) * 2.18, 0.80 + Math.sin(sRad) * 2.18, 0);
          strut.rotation.z = sRad;
          subArch.add(strut);
        }

        const haloArc = new THREE.Mesh(archHaloGeo, glowMat);
        haloArc.position.set(0, 0.80, 0.04);
        subArch.add(haloArc);

        for (const side of [-1, 1] as const) {
          const pierBase = new THREE.Mesh(pierBaseGeo, obsidianMat);
          pierBase.position.set(side * 2.12, 0.42, 0);
          subArch.add(pierBase);

          const fin = new THREE.Mesh(finGeo, obsidianMat);
          fin.position.set(side * 2.02, 0.78, 0.45);
          subArch.add(fin);

          const finAccent = new THREE.Mesh(
            this.trackGeo(new THREE.BoxGeometry(0.018, 1.42, 0.03)),
            glowMat
          );
          finAccent.position.set(side * 1.99, 0.78, 0.56);
          subArch.add(finAccent);

          const veil = new THREE.Mesh(finVeilGeo, veilMat);
          veil.position.set(side * 2.06, 1.45, 0.15);
          veil.rotation.y = side * -0.18;
          subArch.add(veil);
        }

        gate.add(subArch);
      });

      // 3. Swirling Luminous Knowledge Shards flanking the skybridge promenade
      const shardFracs = [0.40, 0.48, 0.56, 0.65, 0.74, 0.83] as const;
      shardFracs.forEach((u, sIdx) => {
        for (const side of [-1, 1] as const) {
          const cx = THREE.MathUtils.lerp(def.ax, def.bx, u);
          const cy = THREE.MathUtils.lerp(def.ay, def.by, u);
          const cz = THREE.MathUtils.lerp(def.az, def.bz, u);
          const by = cy + 0.72 + ((sIdx + (side > 0 ? 2 : 0)) % 4) * 0.34;
          const bx = cx + side * (1.72 + (sIdx % 3) * 0.32);
          const shard = new THREE.Mesh(shardGeo, shardMat);
          shard.position.set(bx, by, cz + (sIdx % 2 === 0 ? 0.35 : -0.35));
          shard.scale.set(0.75, 1.65, 0.75);
          const rotY = side * -0.35 + (sIdx % 3) * 0.12;
          shard.rotation.set(0.18, rotY, side * -0.12);
          gate.add(shard);
          this.corridorShards.push({
            mesh: shard,
            baseY: by,
            baseRotY: rotY,
            phase: sIdx * 0.9 + (side > 0 ? 1.4 : 0),
            gateIdx: idx,
          });
        }
      });

      // 4. All-Corridor Peripheral Flank Monolith Silhouettes, Stepped Buttresses & Diagonal Volumetric God-Rays
      const towerPlacements = [
        { lx: -5.2, lz: -2.0, sY: 1.05 },
        { lx: -6.4, lz: -6.2, sY: 1.28 },
        { lx: -5.4, lz: -10.4, sY: 0.92 },
        { lx: -6.8, lz: -14.0, sY: 1.15 },
        { lx: 5.3, lz: -2.4, sY: 1.12 },
        { lx: 6.5, lz: -6.6, sY: 1.32 },
        { lx: 5.5, lz: -10.8, sY: 0.96 },
        { lx: 6.9, lz: -14.4, sY: 1.18 },
      ] as const;
      towerPlacements.forEach((tp) => {
        const tower = new THREE.Mesh(duskTowerGeo, duskTowerMat);
        tower.position.set(midX + tp.lx, midY + tp.sY * 3.2 - 1.2, def.az + tp.lz);
        tower.scale.set(1.0 + (Math.abs(tp.lx) - 5.2) * 0.15, tp.sY, 1.0);
        gate.add(tower);

        const trim = new THREE.Mesh(duskTowerTrimGeo, duskTowerTrimMat);
        trim.position.set(
          midX + tp.lx - Math.sign(tp.lx) * 0.46,
          midY + tp.sY * 3.2 - 1.2,
          def.az + tp.lz + 0.16
        );
        trim.scale.set(1, tp.sY, 1);
        gate.add(trim);
      });

      const buttressGeo = this.trackGeo(new THREE.BoxGeometry(0.44, 3.6, 0.52));
      const buttressTrimGeo = this.trackGeo(new THREE.BoxGeometry(0.04, 3.2, 0.05));
      const buttressBandGeo = this.trackGeo(new THREE.BoxGeometry(0.48, 0.06, 0.56));
      const buttressCapGeo = this.trackGeo(new THREE.BoxGeometry(0.52, 0.08, 0.60));
      for (const u of [0.34, 0.50, 0.68] as const) {
        const bxBase = THREE.MathUtils.lerp(def.ax, def.bx, u);
        const byBase = THREE.MathUtils.lerp(def.ay, def.by, u);
        const bzBase = THREE.MathUtils.lerp(def.az, def.bz, u);
        for (const side of [-1, 1] as const) {
          const buttress = new THREE.Mesh(buttressGeo, obsidianMat);
          buttress.name = `SkybridgeFlankPier_${idx}_${Math.round(u * 100)}_${side > 0 ? 'R' : 'L'}`;
          buttress.position.set(bxBase + side * 4.15, byBase + 1.65, bzBase);
          buttress.rotation.y = spanYaw + side * -0.14;
          gate.add(buttress);

          const trim = new THREE.Mesh(buttressTrimGeo, glowMat);
          trim.position.set(bxBase + side * 3.92, byBase + 1.65, bzBase + 0.18);
          trim.rotation.y = spanYaw + side * -0.14;
          gate.add(trim);

          for (const bandY of [1.05, 2.65]) {
            const band = new THREE.Mesh(buttressBandGeo, glowMat);
            band.position.set(bxBase + side * 4.15, byBase + bandY, bzBase);
            band.rotation.y = spanYaw + side * -0.14;
            gate.add(band);
          }

          const pierCap = new THREE.Mesh(buttressCapGeo, glowMat);
          pierCap.name = `SkybridgeFlankPierCap_${idx}_${Math.round(u * 100)}_${side > 0 ? 'R' : 'L'}`;
          pierCap.position.set(bxBase + side * 4.15, byBase + 3.48, bzBase);
          pierCap.rotation.y = spanYaw + side * -0.14;
          gate.add(pierCap);
        }
      }

      const godRayGeo = this.trackGeo(new THREE.PlaneGeometry(5.2, 8.6));
      const rayLeft = new THREE.Mesh(godRayGeo, veilMat);
      rayLeft.position.set(midX - 1.4, midY + 2.3, midZ + 1.2);
      rayLeft.rotation.z = -0.36;
      const rayRight = new THREE.Mesh(godRayGeo, veilMat);
      rayRight.position.set(midX + 1.6, midY + 2.5, midZ - 2.4);
      rayRight.rotation.z = -0.28;
      gate.add(rayLeft, rayRight);

      this.portalGates.push({ group: gate, glowMats: [glowMat, veilMat], midSp: def.midSp });
      root.add(gate);
    });

    this.chapterGroups = chapterGroups;
    return { root, chapterGroups };
  }

  public update(elapsedTime: number, isReducedMotion: boolean, scrollProgress: number = 0): void {
    // Gate Inter-Act Architectural Portals strictly inside mid-flight corridors (never clutters act stations)
    const transit = getCorridorTransitState(scrollProgress);
    for (let i = 0; i < this.portalGates.length; i++) {
      const portal = this.portalGates[i]!;
      const inCorridor = transit.isInCorridor && transit.corridorIndex === i;
      portal.group.visible = inCorridor;
      if (inCorridor) {
        const bell = transit.corridorBell;
        const glowMat = portal.glowMats[0];
        const veilMat = portal.glowMats[1];
        if (glowMat) glowMat.opacity = 0.25 + bell * 0.62;
        if (veilMat) veilMat.opacity = (this.featheredBeamTex ? 0.17 : 0.06) * (0.35 + bell * 0.65);
        portal.group.position.y = isReducedMotion ? -1.45 : -1.45 - (1.0 - bell) * 0.18;
      }
    }

    if (!isReducedMotion) {
      for (const shard of this.corridorShards) {
        const parentPortal = this.portalGates[shard.gateIdx];
        if (parentPortal && parentPortal.group.visible) {
          shard.mesh.position.y = shard.baseY + Math.sin(elapsedTime * 1.6 + shard.phase) * 0.11;
          shard.mesh.rotation.y = shard.baseRotY + Math.sin(elapsedTime * 0.9 + shard.phase) * 0.22;
        }
      }
    }

    // Subtle architectural rise/unfurl per chapter when entering a stage (instant 1.0 under reduced motion)
    for (let idx = 0; idx < this.chapterGroups.length; idx++) {
      const grp = this.chapterGroups[idx]!;
      if (isReducedMotion) {
        grp.position.y = 0;
      } else {
        const dist = Math.abs(scrollProgress - idx * 0.2);
        const entrance = THREE.MathUtils.smoothstep(0.16 - dist, 0.0, 0.08);
        grp.position.y = (1.0 - entrance) * -0.32;
      }
    }

    if (isReducedMotion) return;

    for (const cloud of this.cloudSeaMeshes) {
      cloud.mesh.position.x = cloud.baseX + Math.sin(elapsedTime * cloud.speed + cloud.phase) * 1.15;
    }

    for (let i = 0; i < this.animatedRings.length; i++) {
      const ring = this.animatedRings[i]!;
      const mat = ring.material as THREE.MeshBasicMaterial;
      if (mat && typeof mat.opacity === 'number') {
        mat.opacity = 0.72 + Math.sin(elapsedTime * 1.8 + i * 0.9) * 0.18;
      }
    }

    for (const shaft of this.lightShaftMeshes) {
      const mat = shaft.mesh.material as THREE.MeshBasicMaterial;
      const wave = Math.sin(elapsedTime * 0.95 + shaft.phase);
      shaft.mesh.rotation.z = shaft.baseRotZ + wave * 0.025;
      if (mat && typeof mat.opacity === 'number') {
        mat.opacity = shaft.baseOpacity * (0.86 + wave * 0.14);
      }
    }

    if (this.sunHaloMesh) {
      const haloScale = 1.0 + Math.sin(elapsedTime * 0.7) * 0.045;
      this.sunHaloMesh.scale.set(haloScale, haloScale, 1);
    }

    if (this.spotlightPodsInst) {
      const sweepPhase = Math.sin(elapsedTime * 1.1) * 0.08;
      const d = this.spotlightPodDummy;
      for (let i = 0; i < 7; i++) {
        const px = 0.3 + (i - 3) * 1.9;
        d.position.set(px, 2.18, -3.6);
        d.rotation.set(0.08 + Math.sin(elapsedTime * 1.3 + i * 0.7) * 0.06, 0, (px / 6.0) * -0.18 + sweepPhase);
        d.scale.set(1, 1, 1);
        d.updateMatrix();
        this.spotlightPodsInst.setMatrixAt(i, d.matrix);
      }
      this.spotlightPodsInst.instanceMatrix.needsUpdate = true;
    }
  }

  public setAct6EclipseTheme(hex: number): void {
    const target = new THREE.Color(hex);
    for (const mat of this.act6EclipseMats) {
      mat.color.copy(target);
    }
    if (this.act6CoronaMat) {
      this.act6CoronaMat.color.setHex(0xffffff).lerp(target, 0.48);
    }
  }

  public dispose(): void {
    for (const geo of this.geometries) {
      geo.dispose();
    }
    for (const mat of this.materials) {
      mat.dispose();
    }
    for (const tex of this.textures) {
      tex.dispose();
    }
    this.geometries = [];
    this.materials = [];
    this.textures = [];
    this.cloudSeaMeshes = [];
    this.animatedRings = [];
    this.chapterGroups = [];
    this.portalGates = [];
    this.corridorShards = [];
    this.lightShaftMeshes = [];
    this.spotlightPodsInst = null;
    this.act1StudioMaterials = [];
    this.act6EclipseMats = [];
    this.act6CoronaMat = null;
    this.sunHaloMesh = null;
  }
}

function bronzeOrBrass(
  brassMat: THREE.MeshStandardMaterial,
  walnutMat: THREE.MeshStandardMaterial,
  useBrass: boolean
): THREE.MeshStandardMaterial {
  return useBrass ? brassMat : walnutMat;
}
