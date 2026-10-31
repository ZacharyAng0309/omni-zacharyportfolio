import * as THREE from 'three';

export interface Act3CrucibleOptions {
  scene: THREE.Scene;
  materialsList: THREE.Material[];
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

  constructor(options: Act3CrucibleOptions) {
    this.crucibleGroup = new THREE.Group();
    this.crucibleGroup.name = 'CrucibleGroup';
    this.crucibleGroup.position.set(0, 0, -36.0); // Act 3 Station at Z = -36.0

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
    this.crucibleGroup.add(podium);

    // 2. CrucibleOrbitBadges Group (DEF-01: Radius 0.72m safe clearance from avatar torso)
    this.orbitBadgesGroup = new THREE.Group();
    this.orbitBadgesGroup.name = 'CrucibleOrbitBadges';
    this.orbitBadgesGroup.position.set(0.15, 0.25, 0);

    const badgeMat = new THREE.MeshStandardMaterial({
      color: 0x4285f4,
      emissive: 0x1a73e8,
      emissiveIntensity: 1.4,
      metalness: 0.9,
      roughness: 0.2,
    });

    const badgeGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.02, 6);
    const badgeCount = 5;
    const orbitRadius = 0.72; // DEF-01: Exactly 0.72m safe clearance

    for (let b = 0; b < badgeCount; b++) {
      const angle = (b / badgeCount) * Math.PI * 2;
      this.badgeAngles[b] = angle;

      const badge = new THREE.Mesh(badgeGeo, badgeMat);
      badge.name = `OrbitBadge_${b}`;
      badge.rotation.x = Math.PI / 2;
      badge.position.set(Math.cos(angle) * orbitRadius, ((b % 2) - 0.5) * 0.12, Math.sin(angle) * orbitRadius);
      this.badges.push(badge);
      this.orbitBadgesGroup.add(badge);
    }

    this.crucibleGroup.add(this.orbitBadgesGroup);

    // 3. KeynoteMonitorDisplay & PodiumScreenMesh (Acts 1, 3, 5 High-Contrast Emissive Displays)
    const keynoteDisplay = new THREE.Group();
    keynoteDisplay.name = 'KeynoteMonitorDisplay';
    keynoteDisplay.position.set(0.15, -0.95, -0.65);

    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, 128, 128);
      ctx.fillStyle = '#4285f4';
      ctx.fillRect(10, 10, 108, 108);
    }
    const screenTex = new THREE.CanvasTexture(canvas);

    const screenMat = new THREE.MeshStandardMaterial({
      color: 0x111827,
      emissive: 0x4285f4,
      emissiveIntensity: 1.25,
      emissiveMap: screenTex,
      roughness: 0.2,
      metalness: 0.8,
    });
    const screenMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.55, 0.35), screenMat);
    screenMesh.name = 'PodiumScreenMesh';
    screenMesh.rotation.x = -Math.PI * 0.15;
    keynoteDisplay.add(screenMesh);
    this.crucibleGroup.add(keynoteDisplay);

    options.scene.add(this.crucibleGroup);

    options.materialsList.push(podiumMat, badgeMat, screenMat);
  }

  public getCrucibleGroup(): THREE.Group { return this.crucibleGroup; }
  public getOrbitBadgesGroup(): THREE.Group { return this.orbitBadgesGroup; }
  public getBadgeSurgeUntil(): number { return this.badgeSurgeUntil; }

  public triggerBadgeSurge(durationSec: number = 3.0): void {
    this.badgeSurgeUntil = Date.now() + durationSec * 1000;
  }

  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    const isSurging = Date.now() < this.badgeSurgeUntil;
    const speedMult = isSurging ? 3.5 : 1.0;
    const orbitRadius = 0.72; // DEF-01: Exactly 0.72m safe clearance

    if (!isReducedMotion) {
      for (let b = 0; b < this.badges.length; b++) {
        const curAngle = (this.badgeAngles[b] ?? 0) + clampedDelta * 0.75 * speedMult;
        this.badgeAngles[b] = curAngle;
        const badge = this.badges[b];
        if (!badge) continue;

        badge.position.x = Math.cos(curAngle) * orbitRadius;
        badge.position.z = Math.sin(curAngle) * orbitRadius;
        badge.position.y = Math.sin(curAngle * 2.0) * 0.08;
        badge.rotation.y += clampedDelta * 1.8 * speedMult;
      }
    }
  }

  public dispose(): void {}
}
