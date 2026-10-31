import * as THREE from 'three';

export interface Act6HorizonGatewayOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
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
  private horizonBeaconCore: THREE.Mesh;
  private horizonBeaconLight: THREE.PointLight;
  private radarRings: THREE.Mesh[] = [];

  constructor(options: Act6HorizonGatewayOptions) {
    this.horizonGroup = new THREE.Group();
    this.horizonGroup.name = 'HorizonGroup';
    this.horizonGroup.position.set(0, 0, -95.0); // Act 6 Station at Z = -95.0

    // 1. Portal Light Arch
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

    // 2. Horizon Beacon Core & Light
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.horizonBeaconCore = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), beaconMat);
    this.horizonBeaconCore.name = 'HorizonBeaconCore';
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

    options.scene.add(this.horizonGroup);

    options.materialsList.push(archMat, beaconMat, ringMat);
  }

  public getHorizonGroup(): THREE.Group { return this.horizonGroup; }
  public getBeaconLight(): THREE.PointLight { return this.horizonBeaconLight; }

  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    if (!isReducedMotion) {
      this.radarRings.forEach((r, idx) => {
        r.rotation.z += clampedDelta * (0.2 + idx * 0.1);
      });
    }
  }

  public dispose(): void {}
}
