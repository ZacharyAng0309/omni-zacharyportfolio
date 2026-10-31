import * as THREE from 'three';

export interface Act2AcademyOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
}

/**
 * Act2Academy
 * Constructs and manages the Act 2 Academic Staging (APU & Staffordshire First-Class Honours):
 * - Wooden lectern pedestal extending flush to floor (Y = -1.45, DEF-08)
 * - TomeLecternBase
 * - Illuminated Tome with procedural university manuscript texture
 * - Warm banker lamp & tome point light
 */
export class Act2Academy {
  private academyGroup: THREE.Group;
  private bookshelfGroup: THREE.Group;
  private tomeLight: THREE.PointLight;
  private tomeCanvasTexture: THREE.CanvasTexture | null = null;

  constructor(options: Act2AcademyOptions) {
    this.academyGroup = new THREE.Group();
    this.academyGroup.name = 'AcademySet';
    this.academyGroup.position.set(0, -0.20, -18.0); // Act 2 Station at Z = -18.0, Y = -0.20

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

    // Slanted bookrest desk at top of pedestal
    const deskRest = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.04, 0.55), woodMat);
    deskRest.position.set(1.1, -0.10, 0);
    deskRest.rotation.x = Math.PI * 0.12;
    this.academyGroup.add(deskRest);

    // 2. Illuminated Tome
    const tomeCanvas = document.createElement('canvas');
    tomeCanvas.width = 512;
    tomeCanvas.height = 512;
    const ctx = tomeCanvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#f8f4e6';
      ctx.fillRect(0, 0, 512, 512);
      ctx.fillStyle = '#1e293b';
      ctx.font = 'bold 28px serif';
      ctx.fillText('ASIA PACIFIC UNIVERSITY', 40, 70);
      ctx.font = '20px serif';
      ctx.fillText('First Class Honours • 3.89 CGPA', 40, 110);
      ctx.fillText('Valedictorian Commendation', 40, 140);
    }
    this.tomeCanvasTexture = new THREE.CanvasTexture(tomeCanvas);

    const tomeMat = new THREE.MeshStandardMaterial({
      map: this.tomeCanvasTexture,
      roughness: 0.65,
      metalness: 0.1,
    });
    const tomeMesh = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.06, 0.38), tomeMat);
    tomeMesh.name = 'IlluminatedTome';
    tomeMesh.position.set(1.1, -0.06, 0);
    tomeMesh.rotation.x = Math.PI * 0.12;
    this.academyGroup.add(tomeMesh);

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

    this.tomeLight = new THREE.PointLight(0xfffaed, 2.8, 4.5);
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
    for (let r = 0; r < 3; r++) {
      const shelfY = 0.45 + r * 0.48;
      const shelfPlank = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.03, 0.30), woodMat);
      shelfPlank.position.set(0, shelfY - 0.22, 0);
      this.bookshelfGroup.add(shelfPlank);

      for (let b = 0; b < 6; b++) {
        const bMat = new THREE.MeshStandardMaterial({
          color: bookColors[(r * 6 + b) % bookColors.length],
          roughness: 0.5,
          metalness: 0.1
        });
        options.materialsList.push(bMat);
        const bookWidth = 0.08 + (b % 2) * 0.02;
        const bookHeight = 0.32 - (b % 3) * 0.03;
        const book = new THREE.Mesh(new THREE.BoxGeometry(bookWidth, bookHeight, 0.22), bMat);
        book.position.set(-0.30 + b * 0.11, shelfY - 0.22 + bookHeight / 2, 0.02);
        this.bookshelfGroup.add(book);
      }
    }
    this.academyGroup.add(this.bookshelfGroup);

    options.scene.add(this.academyGroup);

    options.materialsList.push(woodMat, tomeMat, brassMat, lampShadeMat);
  }

  public getAcademyGroup(): THREE.Group { return this.academyGroup; }
  public getBookshelfGroup(): THREE.Group { return this.bookshelfGroup; }
  public getTomeLight(): THREE.PointLight { return this.tomeLight; }

  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    if (isReducedMotion) {
      this.tomeLight.intensity = 2.8;
      return;
    }
    // Subtle breathing flicker on academic study lamp with clamped delta
    const targetIntensity = 2.8 + Math.sin(Date.now() * 0.003) * 0.15;
    this.tomeLight.intensity += (targetIntensity - this.tomeLight.intensity) * clampedDelta * 5.0;
  }

  public dispose(): void {
    if (this.tomeCanvasTexture) {
      this.tomeCanvasTexture.dispose();
    }
  }
}
