import * as THREE from 'three';

export interface CameraRigOptions {
  width: number;
  height: number;
  baseFov?: number;
}

export interface CameraFocusTarget {
  actIndex: number;
  subTargetId: string;
  camPos: THREE.Vector3;
  lookAt: THREE.Vector3;
  fov?: number;
}

/**
 * CameraRig
 * Orchestrates 6-act monotonic Catmull-Rom 3D Camera Trajectory,
 * interactive sub-target Camera Focus Dolly (left-60% framing for Slide-Over Sheet),
 * decoupled lookAt damping, mouse parallax, and scroll velocity FOV warping
 * ("The Boost Effect").
 */
export class CameraRig {
  private camera: THREE.PerspectiveCamera;
  private cameraCurve: THREE.CatmullRomCurve3;
  private lookAtCurve: THREE.CatmullRomCurve3;
  private avatarPathCurve: THREE.CatmullRomCurve3;

  private currentLookAt: THREE.Vector3 = new THREE.Vector3(0.36, -0.22, 4.8);
  private targetCamPos: THREE.Vector3 = new THREE.Vector3();
  private targetLookAtPos: THREE.Vector3 = new THREE.Vector3();
  private focusTarget: CameraFocusTarget | null = null;
  private focusBlendWeight: number = 0;
  private isSheetOpen: boolean = false;
  private sheetOpenBlend: number = 0;

  private mouseParallax: THREE.Vector2 = new THREE.Vector2(0, 0);
  private targetParallax: THREE.Vector2 = new THREE.Vector2(0, 0);

  private scrollProgress: number = 0;
  private lastScrollProgress: number = 0;
  private scrollVelocity: number = 0;
  private currentBankRoll: number = 0;
  private steadicamPhase: number = 0;
  private prevTargetCamX: number = -0.48;
  private baseFov: number = 46;

  constructor(options: CameraRigOptions) {
    this.baseFov = options.baseFov ?? 46;
    const aspect = options.width / Math.max(options.height, 1);

    this.camera = new THREE.PerspectiveCamera(this.baseFov, aspect, 0.1, 145);
    if (aspect < 1.0) {
      this.camera.fov = this.getResponsiveBaseFov();
      this.camera.updateProjectionMatrix();
    }
    this.camera.position.set(-0.48, 0.44, 8.5);

    // 100% Monotonic Forward -Z 3D Catmull-Rom Splines with Distinct Cinema Camera Framing per Act
    this.cameraCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-0.48, 0.44, 8.5),   // Act 1 (#hero, sp = 0.00): 3/4 Architectural Titanium Atelier Shot
      new THREE.Vector3(1.35, 0.14, -12.3),  // Act 2 (#timeline, sp = 0.20): Right-Flank Cathedral Library Sweep
      new THREE.Vector3(-1.35, 0.08, -30.4), // Act 3 (#vault, sp = 0.40): Hero Left-Flank Keynote Arena Angle
      new THREE.Vector3(-0.48, 0.18, -49.5), // Act 4 (#summit, sp = 0.60): Wide-Scope Alpine Sunrise Overlook
      new THREE.Vector3(-0.78, 0.34, -69.5), // Act 5 (#ai-solutions, sp = 0.80): High Diagonal Reactor Chamber Shot
      new THREE.Vector3(-0.22, -0.10, -89.2),// Act 6 (#contact, sp = 1.00): Monumental Low-Angle Eclipse Finale
    ]);
    this.cameraCurve.curveType = 'centripetal';

    this.lookAtCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0.36, -0.22, 4.8),   // Act 1: Sovereign Titanium Atelier Dais & 3-Strata Core
      new THREE.Vector3(0.32, 0.06, -18.0),  // Act 2: Cathedral Vaults, Bookcase & Lectern
      new THREE.Vector3(0.28, 0.06, -36.0),  // Act 3: Keynote Arena, Truss Rig & Orbiting Badges
      new THREE.Vector3(0.58, 0.12, -56.0),  // Act 4: Mount Pilatus Sunrise & Star Press Corridor
      new THREE.Vector3(0.62, 0.02, -75.0),  // Act 5: Cyber-Amber Reactor Bay & Exploded Strata Core
      new THREE.Vector3(-0.16, 0.08, -95.0), // Act 6: Stargate Observatory & Solar Eclipse Corona
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

    this.currentLookAt.set(0.36, -0.22, 4.8);
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
   * Preserves wide diorama framing on portrait mobile viewports (aspect < 1.0)
   * while remaining bit-for-bit identical to baseFov on desktop landscape screens.
   */
  public getResponsiveBaseFov(): number {
    const aspect = this.camera.aspect;
    if (!Number.isFinite(aspect) || aspect >= 1.0) {
      return this.baseFov;
    }
    const halfBaseRad = THREE.MathUtils.degToRad(this.baseFov * 0.5);
    const compensatedRad = 2 * Math.atan(Math.tan(halfBaseRad) / Math.pow(Math.max(aspect, 0.42), 0.55));
    return THREE.MathUtils.clamp(THREE.MathUtils.radToDeg(compensatedRad), this.baseFov, 68);
  }

  public setFocusTarget(target: CameraFocusTarget | null): void {
    this.focusTarget = target;
  }

  public clearFocusTarget(): void {
    this.focusTarget = null;
  }

  public setSheetOpen(isOpen: boolean): void {
    this.isSheetOpen = isOpen;
  }

  public isSheetOpenState(): boolean {
    return this.isSheetOpen;
  }

  public getActiveFocusTarget(): CameraFocusTarget | null {
    return this.focusTarget;
  }

  public getFocusBlendWeight(): number {
    return this.focusBlendWeight;
  }

  public getScrollVelocity(): number {
    return this.scrollVelocity;
  }

  public getBankRoll(): number {
    return this.currentBankRoll;
  }

  /**
   * Evaluates camera position and lookAt on the 6-act 3D Camera Trajectory (or active Focus Dolly),
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

    const targetFocusWeight = this.focusTarget ? 1.0 : 0.0;
    this.focusBlendWeight = isReducedMotion
      ? targetFocusWeight
      : THREE.MathUtils.damp(this.focusBlendWeight, targetFocusWeight, 7.5, clampedDelta);

    const effectiveBaseFov = this.getResponsiveBaseFov();
    const isPortrait = this.camera.aspect < 1.0;

    const targetSheetWeight = this.isSheetOpen && !this.focusTarget && !isPortrait ? 1.0 : 0.0;
    this.sheetOpenBlend = isReducedMotion
      ? targetSheetWeight
      : THREE.MathUtils.damp(this.sheetOpenBlend, targetSheetWeight, 7.5, clampedDelta);

    // FOV expands with velocity up to +10 degrees in standard motion, or narrows to focus FOV in Focus Mode
    if (isReducedMotion) {
      const rawFocusFov = this.focusTarget ? (this.focusTarget.fov ?? 39) : effectiveBaseFov;
      this.camera.fov = this.focusTarget && isPortrait
        ? Math.min(62, rawFocusFov + (effectiveBaseFov - this.baseFov) * 0.75)
        : rawFocusFov;
    } else if (this.focusTarget) {
      const rawFocusFov = this.focusTarget.fov ?? 39;
      const focusFov = isPortrait
        ? Math.min(62, rawFocusFov + (effectiveBaseFov - this.baseFov) * 0.75)
        : rawFocusFov;
      this.camera.fov = THREE.MathUtils.damp(this.camera.fov, focusFov, 7.5, clampedDelta);
    } else {
      const boostFov = Math.min(this.scrollVelocity * 2.8, 10.0);
      const targetFov = effectiveBaseFov + boostFov;
      this.camera.fov = THREE.MathUtils.damp(this.camera.fov, targetFov, 20.0, clampedDelta);
      if (this.scrollVelocity === 0 && Math.abs(this.camera.fov - effectiveBaseFov) < 0.3) {
        this.camera.fov = effectiveBaseFov;
      }
    }
    this.camera.updateProjectionMatrix();

    // 2. Sample 3D Camera Trajectory Positions at scrollProgress
    this.cameraCurve.getPointAt(this.scrollProgress, this.targetCamPos);
    this.lookAtCurve.getPointAt(this.scrollProgress, this.targetLookAtPos);

    const portraitFactor = isPortrait
      ? THREE.MathUtils.clamp((1.0 - this.camera.aspect) / 0.54, 0.0, 1.0)
      : 0.0;

    if (isPortrait && !this.focusTarget) {
      this.targetCamPos.z += portraitFactor * 2.1;
      this.targetLookAtPos.x += portraitFactor * 0.30;
    }

    if (this.sheetOpenBlend > 0.0001) {
      this.targetCamPos.x += 0.52 * this.sheetOpenBlend;
      this.targetCamPos.z += 0.55 * this.sheetOpenBlend;
      this.targetLookAtPos.x += 1.18 * this.sheetOpenBlend;
    }

    // Blend with Focus Target if active
    if (this.focusTarget) {
      this.targetCamPos.lerp(this.focusTarget.camPos, this.focusBlendWeight);
      this.targetLookAtPos.lerp(this.focusTarget.lookAt, this.focusBlendWeight);
      if (isPortrait) {
        this.targetCamPos.z += portraitFactor * 1.15 * this.focusBlendWeight;
        this.targetLookAtPos.x -= portraitFactor * 0.28 * this.focusBlendWeight;
      }
    }

    // 3. Smooth Mouse Parallax Dampening, Steadicam Float & Banking Roll
    let floatX = 0;
    let floatY = 0;

    if (isReducedMotion) {
      this.mouseParallax.set(0, 0);
      this.currentBankRoll = 0;
      this.prevTargetCamX = this.targetCamPos.x;
      this.currentLookAt.copy(this.targetLookAtPos);
    } else {
      const parallaxDamp = 4.0;
      this.mouseParallax.x = THREE.MathUtils.damp(this.mouseParallax.x, this.targetParallax.x, parallaxDamp, clampedDelta);
      this.mouseParallax.y = THREE.MathUtils.damp(this.mouseParallax.y, this.targetParallax.y, parallaxDamp, clampedDelta);

      const lateralVel = (this.targetCamPos.x - this.prevTargetCamX) / Math.max(clampedDelta, 0.001);
      this.prevTargetCamX = this.targetCamPos.x;

      const focusSuppression = 1.0 - this.focusBlendWeight * 0.8;
      const targetRoll = THREE.MathUtils.clamp(
        (-lateralVel * 0.011 - this.mouseParallax.x * 0.012) * focusSuppression,
        -0.055,
        0.055
      );
      this.currentBankRoll = THREE.MathUtils.damp(this.currentBankRoll, targetRoll, 7.0, clampedDelta);

      this.steadicamPhase += clampedDelta * 1.15;
      const floatScale = 1.0 - this.focusBlendWeight * 0.7;
      floatX = Math.sin(this.steadicamPhase * 0.65) * 0.011 * floatScale;
      floatY = Math.cos(this.steadicamPhase) * 0.014 * floatScale;

      // 4. Smooth LookAt Damping
      const lookAtDamp = 24.0;
      this.currentLookAt.x = THREE.MathUtils.damp(this.currentLookAt.x, this.targetLookAtPos.x + this.mouseParallax.x * 0.15, lookAtDamp, clampedDelta);
      this.currentLookAt.y = THREE.MathUtils.damp(this.currentLookAt.y, this.targetLookAtPos.y + this.mouseParallax.y * 0.10, lookAtDamp, clampedDelta);
      this.currentLookAt.z = THREE.MathUtils.damp(this.currentLookAt.z, this.targetLookAtPos.z, lookAtDamp, clampedDelta);
    }

    const parallaxScale = 1.0 - this.focusBlendWeight * 0.65;
    const parallaxFactorX = 0.45 * parallaxScale;
    const parallaxFactorY = 0.28 * parallaxScale;

    this.camera.position.x = this.targetCamPos.x + this.mouseParallax.x * parallaxFactorX + floatX;
    this.camera.position.y = this.targetCamPos.y + this.mouseParallax.y * parallaxFactorY + floatY;
    this.camera.position.z = this.targetCamPos.z;

    this.camera.lookAt(this.currentLookAt);
    if (Math.abs(this.currentBankRoll) > 0.0001) {
      this.camera.rotateZ(this.currentBankRoll);
    }
  }
}
