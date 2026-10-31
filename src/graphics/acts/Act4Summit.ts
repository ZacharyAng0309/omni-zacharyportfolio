import * as THREE from 'three';

export interface Act4SummitOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
  onSelectSummitBeacon?: () => void;
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
  private summitHalo: THREE.Mesh;
  private summitBeaconLight: THREE.PointLight;
  private starCanvasTexture: THREE.CanvasTexture | null = null;
  private onSelectSummitBeacon?: () => void;

  constructor(options: Act4SummitOptions) {
    this.onSelectSummitBeacon = options.onSelectSummitBeacon;
    this.summitGroup = new THREE.Group();
    this.summitGroup.name = 'SummitGroup';
    this.summitGroup.position.set(0, 0, -56.0); // Act 4 Station at Z = -56.0

    // 1. Swiss Alps Terrain Relief
    const terrainGeo = new THREE.ConeGeometry(8.5, 4.2, 7, 1);
    const terrainMat = new THREE.MeshStandardMaterial({
      color: 0x1f293d,
      roughness: 0.85,
      metalness: 0.15,
      flatShading: true,
    });
    const mountain = new THREE.Mesh(terrainGeo, terrainMat);
    mountain.position.set(0, -3.2, -5.0);
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
    this.starPressParchment.position.set(2.45, 0.20, 0.25); // X = 2.45 in right corridor per DEF-03

    const starCanvas = document.createElement('canvas');
    starCanvas.width = 512;
    starCanvas.height = 340;
    const ctx = starCanvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#fefdfa';
      ctx.fillRect(0, 0, 512, 340);
      ctx.fillStyle = '#dc2626';
      ctx.font = 'bold 36px serif';
      ctx.fillText('THE STAR', 40, 55);
      ctx.fillStyle = '#111827';
      ctx.font = 'bold 20px sans-serif';
      ctx.fillText('Malaysians Win Hilti Global IT Competition', 40, 95);
      ctx.font = '14px sans-serif';
      ctx.fillText('APU students crowned World Champions in Liechtenstein', 40, 125);
    }
    this.starCanvasTexture = new THREE.CanvasTexture(starCanvas);

    const paperMat = new THREE.MeshStandardMaterial({
      map: this.starCanvasTexture,
      roughness: 0.8,
      metalness: 0.05,
      side: THREE.DoubleSide,
    });
    const parchmentMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.72, 0.48), paperMat);
    parchmentMesh.rotation.y = -Math.PI * 0.15;
    this.starPressParchment.add(parchmentMesh);
    this.summitGroup.add(this.starPressParchment);

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

    options.materialsList.push(terrainMat, goldMat, paperMat, haloMat);
  }

  public getSummitGroup(): THREE.Group { return this.summitGroup; }
  public getGoldenTrophy(): THREE.Group { return this.goldenTrophyGroup; }
  public getGraniteRidgeGroup(): THREE.Group { return this.graniteRidgeGroup; }
  public getStarPressParchment(): THREE.Group { return this.starPressParchment; }
  public getSummitBeaconLight(): THREE.PointLight { return this.summitBeaconLight; }

  public triggerBeaconCallback(): void {
    this.onSelectSummitBeacon?.();
  }

  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    if (!isReducedMotion) {
      this.goldenTrophyGroup.rotation.y += clampedDelta * 0.4;
      this.summitHalo.rotation.z += clampedDelta * 0.6;
    }
  }

  public dispose(): void {
    if (this.starCanvasTexture) {
      this.starCanvasTexture.dispose();
    }
  }
}
