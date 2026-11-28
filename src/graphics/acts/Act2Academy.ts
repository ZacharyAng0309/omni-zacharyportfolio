import * as THREE from 'three';
import {
  applyStudioEnvMapToRoot,
  createGltfLoader,
  resolveAssetUrl,
} from '../core/gltfLoader';
import { assetUrl } from '../../utils/assetUrl';

export interface Act2AcademyOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
  onModelLoaded?: () => void;
}

export interface AcademyVolumeMetadata {
  id: string;
  header: string;
  subtitle: string;
  detail: string;
  colorHex: number;
}

export const ACADEMY_VOLUMES: readonly AcademyVolumeMetadata[] = [
  {
    id: 'vol-1',
    header: 'VOL I • APU DIPLOMA IN ICT',
    subtitle: 'Distinction • 3.89 CGPA (2020–2022)',
    detail: 'Software Engineering & VC Honors List',
    colorHex: 0x1e3a8a,
  },
  {
    id: 'vol-2',
    header: 'VOL II • FULL-STACK & PRODUCT',
    subtitle: 'JustSimple & MoneyMatch (2022–2023)',
    detail: 'E-Commerce Engineering & Fintech Scrum',
    colorHex: 0x14532d,
  },
  {
    id: 'vol-3',
    header: 'VOL III • UK DUAL FIRST-CLASS',
    subtitle: 'APU & Staffordshire BSc • 3.75 CGPA',
    detail: 'Business Information Systems Honours',
    colorHex: 0x831843,
  },
  {
    id: 'vol-4',
    header: 'VOL IV • SOFT SPACE FINTECH',
    subtitle: 'Enterprise Business Analyst (2024–Now)',
    detail: 'Digital Wallet Super-App & C-Suite AI',
    colorHex: 0x312e81,
  },
];

/**
 * Act2Academy
 * Constructs and manages the Act 2 Academic Staging (APU & Staffordshire First-Class Honours):
 * - Grounded Mahogany & Brass Library Island (SM_Island_Act2)
 * - Wooden lectern pedestal extending flush to floor (Y = -1.45, DEF-08)
 * - Illuminated Tome with dynamic dirty-flagged CanvasTexture
 * - 4 Interactive Pull-Out Milestone Volumes (Prop_Book_Vol1..4)
 * - Warm banker lamp & tome point light
 */
export class Act2Academy {
  private academyGroup: THREE.Group;
  private bookshelfGroup: THREE.Group;
  private tomeMesh: THREE.Mesh;
  private tomeLight: THREE.PointLight;
  private tomeCanvas: HTMLCanvasElement | null = null;
  private tomeCanvasTexture: THREE.CanvasTexture | null = null;
  private interactiveVolumes: Map<string, THREE.Object3D> = new Map();
  private volumeMaterials: Map<string, THREE.MeshStandardMaterial> = new Map();
  private selectedVolumeId: string = 'vol-3';
  private fallbackMeshes: THREE.Mesh[] = [];
  private lecternCitationHolo: THREE.Group;
  private citationRingOuter: THREE.Mesh;
  private citationRingInner: THREE.Mesh;
  private disposableGeos: THREE.BufferGeometry[] = [];
  private studioEnvMap: THREE.Texture | null = null;
  private hasRequestedLoad: boolean = false;
  private isGlbLoaded: boolean = false;
  private onModelLoaded?: () => void;

  constructor(options: Act2AcademyOptions) {
    this.onModelLoaded = options.onModelLoaded;
    this.academyGroup = new THREE.Group();
    this.academyGroup.name = 'AcademySet';
    this.academyGroup.position.set(0, -0.20, -18.0); // Act 2 Station at Z = -18.0, Y = -0.20

    // 0. Grounded Mahogany & Brass Library Island Base (Top surface flush at world Y = -1.45)
    const islandMat = new THREE.MeshStandardMaterial({
      color: 0x1a120b,
      roughness: 0.45,
      metalness: 0.35,
    });
    const islandMesh = new THREE.Mesh(new THREE.CylinderGeometry(2.35, 2.50, 0.20, 48), islandMat);
    islandMesh.name = 'SM_Island_Act2';
    islandMesh.position.set(0.35, -1.35, 0.0); // World Y = -0.20 + (-1.35) = -1.55 (top at -1.45)
    islandMesh.receiveShadow = true;
    this.academyGroup.add(islandMesh);

    const brassRimMat = new THREE.MeshBasicMaterial({ color: 0xfbbf24, transparent: true, opacity: 0.72 });
    const islandRim = new THREE.Mesh(new THREE.TorusGeometry(2.32, 0.018, 12, 64), brassRimMat);
    islandRim.name = 'SM_Island_Act2_Rim';
    islandRim.rotation.x = Math.PI / 2;
    islandRim.position.set(0.35, -1.26, 0.0);
    this.academyGroup.add(islandRim);
    options.materialsList.push(islandMat, brassRimMat);

    // 1. Lectern Base & Pedestal (Extends to Floor Y = -1.45, DEF-08)
    const woodMat = new THREE.MeshStandardMaterial({
      color: 0x3d2817,
      roughness: 0.72,
      metalness: 0.12,
    });

    const lecternBase = new THREE.Mesh(new THREE.BoxGeometry(0.70, 0.06, 0.70), woodMat);
    lecternBase.name = 'TomeLecternBase';
    lecternBase.position.set(1.1, -1.225, 0);
    this.academyGroup.add(lecternBase);

    // Pedestal: centered spanning between base and collar
    const lecternPedestal = new THREE.Mesh(new THREE.BoxGeometry(0.24, 1.05, 0.24), woodMat);
    lecternPedestal.name = 'TomeLecternPedestal';
    lecternPedestal.position.set(1.1, -0.68, 0);
    this.academyGroup.add(lecternPedestal);

    // Collar transition ring at top of pedestal
    const lecternCollar = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.08, 0.32), woodMat);
    lecternCollar.name = 'TomeLecternCollar';
    lecternCollar.position.set(1.1, -0.15, 0);
    this.academyGroup.add(lecternCollar);

    // Slanted bookrest desk at top of pedestal tilted toward overview camera for legible manuscript calligraphy
    const deskRest = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.04, 0.55), woodMat);
    deskRest.position.set(1.1, -0.10, 0);
    deskRest.rotation.x = Math.PI * 0.185;
    this.academyGroup.add(deskRest);

    // 2. Illuminated Tome
    const tomeCanvas = document.createElement('canvas');
    tomeCanvas.width = 512;
    tomeCanvas.height = 512;
    this.tomeCanvas = tomeCanvas;
    this.tomeCanvasTexture = new THREE.CanvasTexture(tomeCanvas);
    this.tomeCanvasTexture.colorSpace = THREE.SRGBColorSpace;
    this.redrawTomeCanvas(ACADEMY_VOLUMES[2]!);

    const tomeMat = new THREE.MeshStandardMaterial({
      color: 0x8a7960,
      map: this.tomeCanvasTexture,
      emissive: 0xffe8ba,
      emissiveMap: this.tomeCanvasTexture,
      emissiveIntensity: 0.42,
      roughness: 0.92,
      metalness: 0.02,
    });
    const pageEdgeMat = new THREE.MeshStandardMaterial({
      color: 0xd4c29a,
      roughness: 0.85,
      metalness: 0.04,
    });
    const coverMat = new THREE.MeshStandardMaterial({
      color: 0x3e2414,
      roughness: 0.58,
      metalness: 0.18,
    });
    // Render the illuminated manuscript spread strictly on the open top page face (+Y)
    const tomeMesh = new THREE.Mesh(
      new THREE.BoxGeometry(0.48, 0.06, 0.38),
      [pageEdgeMat, pageEdgeMat, tomeMat, coverMat, pageEdgeMat, pageEdgeMat]
    );
    tomeMesh.name = 'IlluminatedTome';
    tomeMesh.userData = { type: 'subTargetProp', actIndex: 1, subTargetId: 'vol-3' };
    tomeMesh.position.set(1.1, -0.06, 0);
    tomeMesh.rotation.set(Math.PI * 0.185, -0.16, 0);
    this.tomeMesh = tomeMesh;
    this.academyGroup.add(tomeMesh);
    options.materialsList.push(pageEdgeMat, coverMat);

    this.fallbackMeshes.push(islandMesh, islandRim, lecternBase, lecternPedestal, lecternCollar, deskRest);

    // 3. Banker Lamp & Tome Light
    const brassMat = new THREE.MeshStandardMaterial({ color: 0xb8860b, metalness: 0.85, roughness: 0.25 });
    const lampStem = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.35, 16), brassMat);
    lampStem.position.set(1.45, 0.05, -0.15);
    this.academyGroup.add(lampStem);

    const lampShadeMat = new THREE.MeshStandardMaterial({ color: 0x005522, roughness: 0.3, metalness: 0.2 });
    const lampShade = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.09, 0.18, 16, 1, false, 0, Math.PI), lampShadeMat);
    lampShade.rotation.z = Math.PI / 2;
    lampShade.position.set(1.45, 0.22, -0.15);
    this.academyGroup.add(lampShade);

    this.tomeLight = new THREE.PointLight(0xfffaed, 1.15, 4.5);
    this.tomeLight.name = 'TomeLight';
    this.tomeLight.position.set(1.1, 0.40, 0.0);
    this.academyGroup.add(this.tomeLight);

    // 4. Neoclassical Mahogany Bookshelf & Interactive Tomes
    this.bookshelfGroup = new THREE.Group();
    this.bookshelfGroup.name = 'AcademyBookshelf';
    this.bookshelfGroup.position.set(-0.6, -1.25, 0.4);

    const shelfFrame = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.8, 0.35), woodMat);
    shelfFrame.position.set(0, 0.9, 0);
    this.bookshelfGroup.add(shelfFrame);

    const bookColors = [0x1e3a8a, 0x831843, 0x14532d, 0x713f12, 0x312e81];
    let milestoneIdx = 0;
    for (let r = 0; r < 3; r++) {
      const shelfY = 0.45 + r * 0.48;
      const shelfPlank = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.03, 0.30), woodMat);
      shelfPlank.position.set(0, shelfY - 0.22, 0);
      this.bookshelfGroup.add(shelfPlank);

      for (let b = 0; b < 6; b++) {
        const isMilestoneBook = (r === 1 && (b === 1 || b === 4)) || (r === 2 && (b === 1 || b === 4));
        const volMeta = isMilestoneBook ? ACADEMY_VOLUMES[milestoneIdx] : undefined;
        const bMat = new THREE.MeshStandardMaterial({
          color: volMeta ? volMeta.colorHex : bookColors[(r * 6 + b) % bookColors.length],
          emissive: volMeta ? 0xb45309 : 0x000000,
          emissiveIntensity: volMeta ? 0.35 : 0.0,
          roughness: volMeta ? 0.32 : 0.5,
          metalness: volMeta ? 0.45 : 0.1,
        });
        options.materialsList.push(bMat);
        const bookWidth = volMeta ? 0.105 : 0.08 + (b % 2) * 0.02;
        const bookHeight = volMeta ? 0.34 : 0.32 - (b % 3) * 0.03;
        const baseY = shelfY - 0.22 + bookHeight / 2;
        const baseZ = 0.02;
        const book = new THREE.Mesh(new THREE.BoxGeometry(bookWidth, bookHeight, 0.22), bMat);
        book.position.set(-0.30 + b * 0.11, baseY, baseZ);
        if (volMeta) {
          milestoneIdx++;
          book.name = `Prop_Book_Vol${milestoneIdx}`;
          book.userData = {
            type: 'subTargetProp',
            actIndex: 1,
            subTargetId: volMeta.id,
            baseY,
            baseZ,
          };
          this.interactiveVolumes.set(volMeta.id, book);
        }
        this.bookshelfGroup.add(book);
      }
    }
    this.fallbackMeshes.push(lampStem, lampShade);
    this.academyGroup.add(this.bookshelfGroup);

    // 5. Lectern Citation Hologram (Vol III illumination beam + dual antique-brass astrolabe rings)
    this.lecternCitationHolo = new THREE.Group();
    this.lecternCitationHolo.name = 'LecternCitationHolo';
    this.lecternCitationHolo.position.set(1.55, 0.06, 0.15);

    const coneGeo = new THREE.ConeGeometry(0.30, 0.36, 24, 1, true);
    const coneMat = new THREE.MeshBasicMaterial({
      color: 0xffe4a0,
      transparent: true,
      opacity: 0.14,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    const readingCone = new THREE.Mesh(coneGeo, coneMat);
    readingCone.name = 'LecternReadingCone';
    readingCone.position.set(0.0, 0.02, 0.0);

    const ringOuterGeo = new THREE.TorusGeometry(0.24, 0.004, 12, 48);
    const ringInnerGeo = new THREE.TorusGeometry(0.18, 0.003, 12, 48);
    const citationRingMat = new THREE.MeshBasicMaterial({
      color: 0xfbbf24,
      transparent: true,
      opacity: 0.62,
    });
    this.disposableGeos.push(coneGeo, ringOuterGeo, ringInnerGeo);

    this.citationRingOuter = new THREE.Mesh(ringOuterGeo, citationRingMat);
    this.citationRingOuter.name = 'CitationAstrolabeOuter';
    this.citationRingOuter.rotation.set(Math.PI / 2 - 0.18, 0.14, 0.0);
    this.citationRingOuter.position.set(0.0, -0.02, 0.0);

    this.citationRingInner = new THREE.Mesh(ringInnerGeo, citationRingMat);
    this.citationRingInner.name = 'CitationAstrolabeInner';
    this.citationRingInner.rotation.set(Math.PI / 2 + 0.22, -0.18, 0.0);
    this.citationRingInner.position.set(0.0, -0.02, 0.0);

    this.lecternCitationHolo.add(readingCone, this.citationRingOuter, this.citationRingInner);
    const citationTag = { type: 'subTargetProp', actIndex: 1, subTargetId: 'vol-3' };
    this.lecternCitationHolo.traverse((obj) => {
      obj.userData = { ...citationTag };
    });
    this.academyGroup.add(this.lecternCitationHolo);

    options.scene.add(this.academyGroup);

    options.materialsList.push(woodMat, tomeMat, brassMat, lampShadeMat, coneMat, citationRingMat);
  }

  public setStudioEnvMap(envMap: THREE.Texture | null): void {
    this.studioEnvMap = envMap;
    applyStudioEnvMapToRoot(this.academyGroup, envMap);
  }

  public ensureLoaded(): void {
    if (this.hasRequestedLoad || typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    this.loadAcademyGLB(assetUrl('models/props/act2_academy.glb')).catch(() => {});
  }

  public async loadAcademyGLB(url: string = assetUrl('models/props/act2_academy.glb')): Promise<void> {
    if (typeof window === 'undefined') return;
    this.hasRequestedLoad = true;
    try {
      const resolvedUrl = resolveAssetUrl(url);
      const loader = await createGltfLoader();
      loader.load(
        resolvedUrl,
        (gltf) => {
          const root = gltf.scene;
          root.name = 'Act2AcademyGLB';
          root.position.set(0, -1.25, 0);
          this.isGlbLoaded = true;

          for (const m of this.fallbackMeshes) {
            m.geometry.scale(0.001, 0.001, 0.001);
          }
          this.bookshelfGroup.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });

          // Align live CanvasTexture IlluminatedTome onto the Blender SM_Pedestal_Lectern at X = 1.55, Z = +0.15
          this.tomeMesh.position.set(1.55, -0.14, 0.15);
          this.tomeMesh.rotation.set(Math.PI * 0.185, -0.18, 0);
          this.tomeLight.position.set(1.55, 0.35, 0.15);

          root.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
            }
            if (child.name === 'SM_Pedestal_Lectern' || child.name === 'SM_Banker_Lamp') {
              const tag = { type: 'subTargetProp', actIndex: 1, subTargetId: 'vol-3' };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            }
          });

          for (let i = 1; i <= 4; i++) {
            const bookObj = root.getObjectByName(`Prop_Book_Vol${i}`);
            const volId = `vol-${i}`;
            if (bookObj) {
              const baseY = bookObj.position.y;
              const baseZ = bookObj.position.z;
              bookObj.userData = {
                type: 'subTargetProp',
                actIndex: 1,
                subTargetId: volId,
                baseY,
                baseZ,
              };
              let coverMat: THREE.MeshStandardMaterial | null = null;
              bookObj.traverse((c) => {
                c.userData = bookObj.userData;
                if ((c as THREE.Mesh).isMesh) {
                  const rawMeshMat = (c as THREE.Mesh).material;
                  const mList: THREE.Material[] = Array.isArray(rawMeshMat) ? rawMeshMat : [rawMeshMat];
                  for (const m of mList) {
                    if (
                      m &&
                      (m as THREE.MeshStandardMaterial).isMeshStandardMaterial &&
                      (/M_Prop_Book_Vol/i.test(m.name || '') || !coverMat)
                    ) {
                      coverMat = m as THREE.MeshStandardMaterial;
                      if (/M_Prop_Book_Vol/i.test(m.name || '')) break;
                    }
                  }
                }
              });
              if (coverMat) {
                const stdMat = coverMat as THREE.MeshStandardMaterial;
                stdMat.emissive.setHex(0x4a3520);
                this.volumeMaterials.set(volId, stdMat);
              }
              this.interactiveVolumes.set(volId, bookObj);
            }
          }

          if (this.studioEnvMap) {
            applyStudioEnvMapToRoot(root, this.studioEnvMap);
          }
          this.academyGroup.add(root);
          this.onModelLoaded?.();
        },
        undefined,
        () => {}
      );
    } catch {
      // Ignore in headless/JSDOM environments
    }
  }

  private redrawTomeCanvas(vol: AcademyVolumeMetadata): void {
    if (!this.tomeCanvas) return;
    const ctx = this.tomeCanvas.getContext('2d');
    if (ctx) {
      // Rich mahogany folio binding rim around open parchment dual-page spread
      ctx.fillStyle = '#3c2214';
      ctx.fillRect(0, 0, 512, 512);

      // Aged vellum gradient base (warmer sepia stops so +Y face keeps high ink contrast under overview key light)
      const vellum = ctx.createLinearGradient(0, 0, 512, 0);
      vellum.addColorStop(0.0, '#cbb78d');
      vellum.addColorStop(0.18, '#dfd0ae');
      vellum.addColorStop(0.47, '#d6c49d');
      vellum.addColorStop(0.50, '#967b56'); // Spine gutter crease
      vellum.addColorStop(0.53, '#d7c59e');
      vellum.addColorStop(0.84, '#e2d3b2');
      vellum.addColorStop(1.0, '#c8b489');
      ctx.fillStyle = vellum;
      ctx.fillRect(22, 22, 468, 468);

      // Center spine rule & gold illumination borders
      ctx.fillStyle = 'rgba(58, 30, 12, 0.48)';
      ctx.fillRect(253, 22, 6, 468);

      ctx.strokeStyle = '#825517';
      ctx.lineWidth = 5;
      ctx.strokeRect(32, 32, 212, 448);
      ctx.strokeRect(268, 32, 212, 448);

      // Left folio seal & illuminated crest
      ctx.fillStyle = '#6b210b';
      ctx.beginPath();
      ctx.arc(138, 138, 44, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#d4a359';
      ctx.lineWidth = 4;
      ctx.stroke();
      ctx.fillStyle = '#fef3c7';
      ctx.font = 'bold 21px serif';
      ctx.textAlign = 'center';
      ctx.fillText('APU', 138, 145);
      ctx.fillStyle = '#2d190b';
      ctx.font = 'bold 16px serif';
      ctx.fillText('ASIA PACIFIC', 138, 216);
      ctx.fillText('UNIVERSITY', 138, 238);
      ctx.fillStyle = '#5c260a';
      ctx.font = 'bold 13px serif';
      ctx.fillText('ARCHIVE FOLIO', 138, 272);
      ctx.fillStyle = '#6e522d';
      for (let i = 0; i < 6; i++) {
        ctx.fillRect(62, 304 + i * 24, 152 - (i % 2) * 28, 5);
      }

      // Right folio chapter metadata
      ctx.textAlign = 'left';
      ctx.fillStyle = '#6b210b';
      ctx.font = 'bold 18px serif';
      ctx.fillText(vol.header, 282, 82);
      ctx.fillStyle = '#825517';
      ctx.fillRect(282, 96, 180, 3);
      ctx.fillStyle = '#111827';
      ctx.font = 'bold 16px serif';
      ctx.fillText(vol.subtitle, 282, 134);
      ctx.fillStyle = '#2c1e12';
      ctx.font = 'bold 14px serif';
      ctx.fillText(vol.detail, 282, 168);
      ctx.fillStyle = 'rgba(44, 30, 18, 0.58)';
      for (let i = 0; i < 9; i++) {
        ctx.fillRect(282, 206 + i * 24, 180 - (i % 3) * 22, 6);
      }
    }
    if (this.tomeCanvasTexture) {
      this.tomeCanvasTexture.needsUpdate = true;
    }
  }

  public selectVolume(volId: string): void {
    const found = ACADEMY_VOLUMES.find((v) => v.id === volId);
    if (!found) return;
    if (this.selectedVolumeId !== found.id) {
      this.selectedVolumeId = found.id;
      this.redrawTomeCanvas(found);
    }
  }

  public getSelectedVolumeId(): string {
    return this.selectedVolumeId;
  }

  public getInteractiveVolumes(): Map<string, THREE.Object3D> {
    return this.interactiveVolumes;
  }

  public getAcademyGroup(): THREE.Group { return this.academyGroup; }
  public getBookshelfGroup(): THREE.Group { return this.bookshelfGroup; }
  public getTomeLight(): THREE.PointLight { return this.tomeLight; }

  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);

    // Animate pull-out milestone volumes on the bookshelf
    this.interactiveVolumes.forEach((bookMesh, id) => {
      const isSelected = id === this.selectedVolumeId;
      const baseY = (bookMesh.userData.baseY as number) ?? bookMesh.position.y;
      const baseZ = (bookMesh.userData.baseZ as number) ?? 0.02;
      const targetZ = isSelected ? baseZ + 0.18 : baseZ;
      const targetY = isSelected ? baseY + 0.04 : baseY;
      const rawMat = (bookMesh as THREE.Mesh).material;
      const mat =
        this.volumeMaterials.get(id) ??
        ((Array.isArray(rawMat) ? rawMat[0] : rawMat) as THREE.MeshStandardMaterial | undefined);
      const targetEmissive = isSelected ? 0.65 : 0.12;

      if (isReducedMotion) {
        bookMesh.position.z = targetZ;
        bookMesh.position.y = targetY;
        if (mat && typeof mat.emissiveIntensity === 'number') mat.emissiveIntensity = targetEmissive;
      } else {
        bookMesh.position.z = THREE.MathUtils.damp(bookMesh.position.z, targetZ, 10.0, clampedDelta);
        bookMesh.position.y = THREE.MathUtils.damp(bookMesh.position.y, targetY, 10.0, clampedDelta);
        if (mat && typeof mat.emissiveIntensity === 'number') {
          mat.emissiveIntensity = THREE.MathUtils.damp(mat.emissiveIntensity, targetEmissive, 10.0, clampedDelta);
        }
      }
    });

    if (isReducedMotion) {
      this.tomeLight.intensity = 1.15;
      this.citationRingOuter.rotation.z = 0.22;
      this.citationRingInner.rotation.z = -0.22;
      return;
    }
    if (!this.isGlbLoaded) {
      this.citationRingOuter.rotation.z += clampedDelta * 0.42;
      this.citationRingInner.rotation.z -= clampedDelta * 0.58;
    }
    // Subtle breathing flicker on academic study lamp with clamped delta
    const targetIntensity = 1.15 + Math.sin(Date.now() * 0.003) * 0.08;
    this.tomeLight.intensity += (targetIntensity - this.tomeLight.intensity) * clampedDelta * 5.0;
  }

  public dispose(): void {
    this.studioEnvMap = null;
    this.tomeMesh?.geometry.dispose();
    for (const geo of this.disposableGeos) {
      geo.dispose();
    }
    this.disposableGeos = [];
    if (this.tomeCanvasTexture) {
      this.tomeCanvasTexture.dispose();
    }
  }
}
