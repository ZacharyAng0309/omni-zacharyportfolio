import * as THREE from 'three';

export interface CameraRigOptions {
  width: number;
  height: number;
  baseFov?: number;
}

/**
 * CameraRig
 * Orchestrates 6-act monotonic Catmull-Rom spline camera trajectory,
 * decoupled lookAt damping, mouse parallax, and scroll velocity FOV warping
 * ("The Boost Effect").
 */
export class CameraRig {
  private camera: THREE.PerspectiveCamera;
  private cameraCurve: THREE.CatmullRomCurve3;
  private lookAtCurve: THREE.CatmullRomCurve3;
  private avatarPathCurve: THREE.CatmullRomCurve3;

  private currentLookAt: THREE.Vector3 = new THREE.Vector3(0.3, -0.05, 4.8);
  private targetCamPos: THREE.Vector3 = new THREE.Vector3();
  private targetLookAtPos: THREE.Vector3 = new THREE.Vector3();

  private mouseParallax: THREE.Vector2 = new THREE.Vector2(0, 0);
  private targetParallax: THREE.Vector2 = new THREE.Vector2(0, 0);

  private scrollProgress: number = 0;
  private lastScrollProgress: number = 0;
  private scrollVelocity: number = 0;
  private baseFov: number = 46;

  constructor(options: CameraRigOptions) {
    this.baseFov = options.baseFov ?? 46;
    const aspect = options.width / Math.max(options.height, 1);

    this.camera = new THREE.PerspectiveCamera(this.baseFov, aspect, 0.1, 120);
    this.camera.position.set(0.0, 0.35, 8.5);

    // 100% Monotonic Forward -Z 3D Catmull-Rom Splines (6-Act Growth Journey)
    this.cameraCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0.0, 0.35, 8.5),     // Act 1 (#hero, sp = 0.00): Executive Strategy Studio
      new THREE.Vector3(0.4, 0.45, -12.2),   // Act 2 (#timeline, sp = 0.20): The Academy (Z = -18.0)
      new THREE.Vector3(-0.35, 0.45, -30.2), // Act 3 (#vault, sp = 0.40): The Crucible (Z = -36.0)
      new THREE.Vector3(0.0, 0.65, -50.2),   // Act 4 (#summit, sp = 0.60): Mount Pilatus Summit (Z = -56.0)
      new THREE.Vector3(0.4, 0.50, -69.2),   // Act 5 (#ai-solutions, sp = 0.80): The Frontier Exploded Core (Z = -75.0)
      new THREE.Vector3(0.0, 0.35, -89.2),   // Act 6 (#contact, sp = 1.00): Horizon Portal (Z = -95.0)
    ]);
    this.cameraCurve.curveType = 'centripetal';

    this.lookAtCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0.3, -0.05, 4.8),    // Act 1: Strategy Studio chest/eye level
      new THREE.Vector3(1.1, 0.05, -18.0),   // Act 2: Academy & Illuminated Tome
      new THREE.Vector3(0.15, 0.05, -36.0),  // Act 3: Crucible GDSC Podium & Orbiting Badges
      new THREE.Vector3(0.35, 0.25, -56.0),  // Act 4: Mount Pilatus Summit & Golden Trophy
      new THREE.Vector3(1.1, 0.10, -75.0),   // Act 5: Frontier Exploded Core & Console
      new THREE.Vector3(0.0, 0.05, -95.0),   // Act 6: Horizon Portal Gateway
    ]);
    this.lookAtCurve.curveType = 'centripetal';

    this.avatarPathCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(1.35, 0.0, 5.10),    // Act 1 (#hero, sp = 0.00): Executive Strategy Studio
      new THREE.Vector3(0.85, 0.0, -17.6),   // Act 2 (#timeline, sp = 0.20): The Academy (Z = -18.0)
      new THREE.Vector3(0.76, 0.0, -35.6),   // Act 3 (#vault, sp = 0.40): The Crucible (Z = -36.0)
      new THREE.Vector3(1.25, 0.15, -55.8),  // Act 4 (#summit, sp = 0.60): Mount Pilatus Summit (Z = -56.0)
      new THREE.Vector3(0.92, 0.0, -74.6),   // Act 5 (#ai-solutions, sp = 0.80): The Frontier Exploded Core (Z = -75.0)
      new THREE.Vector3(0.85, 0.0, -94.2),   // Act 6 (#contact, sp = 1.00): Horizon Portal (Z = -95.0)
    ]);
    this.avatarPathCurve.curveType = 'centripetal';

    this.currentLookAt.set(0.3, -0.05, 4.8);
    this.camera.lookAt(this.currentLookAt);
    this.camera.updateMatrixWorld(true);
  }

  public getCamera(): THREE.PerspectiveCamera {
    return this.camera;
  }

  public getCameraCurve(): THREE.CatmullRomCurve3 {
    return this.cameraCurve;
  }

  public getLookAtCurve(): THREE.CatmullRomCurve3 {
    return this.lookAtCurve;
  }

  public getAvatarPathCurve(): THREE.CatmullRomCurve3 {
    return this.avatarPathCurve;
  }

  public getCurrentLookAt(): THREE.Vector3 {
    return this.currentLookAt;
  }

  public updateParallax(x: number, y: number): void {
    this.targetParallax.set(
      THREE.MathUtils.clamp(x, -1, 1),
      THREE.MathUtils.clamp(y, -1, 1)
    );
  }

  public updateScroll(progress: number): void {
    this.scrollProgress = THREE.MathUtils.clamp(progress, 0, 1);
  }

  public resize(width: number, height: number): void {
    this.camera.aspect = width / Math.max(height, 1);
    this.camera.updateProjectionMatrix();
  }

  public getCurrentFov(): number {
    return this.camera.fov;
  }

  public getBaseFov(): number {
    return this.baseFov;
  }

  /**
   * Evaluates camera position and lookAt on the 6-act splines,
   * dampens mouse parallax, and computes scroll velocity FOV warping ("The Boost Effect").
   */
  public update(delta: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);

    // 1. Calculate scroll velocity and FOV warping ("The Boost Effect")
    const dScroll = Math.abs(this.scrollProgress - this.lastScrollProgress);
    const instantaneousVelocity = dScroll / Math.max(clampedDelta, 0.001);
    this.scrollVelocity = THREE.MathUtils.damp(this.scrollVelocity, instantaneousVelocity, 25.0, clampedDelta);
    if (this.scrollVelocity < 0.1) this.scrollVelocity = 0;
    this.lastScrollProgress = this.scrollProgress;

    // FOV expands with velocity up to +10 degrees in standard motion
    if (isReducedMotion) {
      this.camera.fov = this.baseFov;
    } else {
      const boostFov = Math.min(this.scrollVelocity * 2.8, 10.0);
      const targetFov = this.baseFov + boostFov;
      this.camera.fov = THREE.MathUtils.damp(this.camera.fov, targetFov, 20.0, clampedDelta);
      if (this.scrollVelocity === 0 && Math.abs(this.camera.fov - this.baseFov) < 0.3) {
        this.camera.fov = this.baseFov;
      }
    }
    this.camera.updateProjectionMatrix();

    // 2. Sample Spline Positions at scrollProgress
    this.cameraCurve.getPointAt(this.scrollProgress, this.targetCamPos);
    this.lookAtCurve.getPointAt(this.scrollProgress, this.targetLookAtPos);

    // 3. Smooth Mouse Parallax Dampening & LookAt
    if (isReducedMotion) {
      this.mouseParallax.set(0, 0);
      this.currentLookAt.copy(this.targetLookAtPos);
    } else {
      const parallaxDamp = 4.0;
      this.mouseParallax.x = THREE.MathUtils.damp(this.mouseParallax.x, this.targetParallax.x, parallaxDamp, clampedDelta);
      this.mouseParallax.y = THREE.MathUtils.damp(this.mouseParallax.y, this.targetParallax.y, parallaxDamp, clampedDelta);

      // 4. Smooth LookAt Damping
      const lookAtDamp = 24.0;
      this.currentLookAt.x = THREE.MathUtils.damp(this.currentLookAt.x, this.targetLookAtPos.x + this.mouseParallax.x * 0.15, lookAtDamp, clampedDelta);
      this.currentLookAt.y = THREE.MathUtils.damp(this.currentLookAt.y, this.targetLookAtPos.y + this.mouseParallax.y * 0.10, lookAtDamp, clampedDelta);
      this.currentLookAt.z = THREE.MathUtils.damp(this.currentLookAt.z, this.targetLookAtPos.z, lookAtDamp, clampedDelta);
    }

    const parallaxFactorX = 0.45;
    const parallaxFactorY = 0.28;

    this.camera.position.x = this.targetCamPos.x + this.mouseParallax.x * parallaxFactorX;
    this.camera.position.y = this.targetCamPos.y + this.mouseParallax.y * parallaxFactorY;
    this.camera.position.z = this.targetCamPos.z;

    this.camera.lookAt(this.currentLookAt);
  }
}
