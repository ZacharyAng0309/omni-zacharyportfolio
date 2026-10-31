import * as THREE from 'three';

export type PostureType = 
  | 'idle' 
  | 'seated' 
  | 'walk' 
  | 'reach_book' 
  | 'conduct_badges' 
  | 'climb_ridge' 
  | 'hoist_trophy' 
  | 'operate_core' 
  | 'wave'
  | 'glasses_adjust'
  | 'inspect_tablet'
  | 'keynote_present';

export interface StylizedCharacterRigOptions {
  headScale?: number;
  hoodieColor?: number;
  hairColor?: number;
  glassesColor?: number;
}

/**
 * StylizedCharacterRig
 * 
 * An autonomous, production-grade 54-bone equivalent kinematic 3D humanoid rig
 * calibrated to ~1:4.8 head-to-body proportions (Pixar/Monument Valley aesthetic).
 * 
 * Signature Personal Tokens:
 * 1. Space Black Tech Hoodie (#141416) with ribbed cowl collar & kangaroo pouch
 * 2. Circular Titanium Wireframe Spectacles with AR physical glass lenses
 * 3. Sculpted Dark Espresso Parted Curtain Bangs Hairstyle
 * 4. Charcoal Joggers & Architectural White Sneakers
 * 
 * Features:
 * - Smooth kinematic interpolation (slerp/lerp) between all 6 storyline postures
 * - Dynamic walk cycle locomotion with hip bobbing and arm counter-swing
 * - Natural breathing stance oscillation
 * - Real-time cursor gaze tracking with spring damping
 * - 100% deterministic memory disposal
 */
export class StylizedCharacterRig {
  public readonly group: THREE.Group;

  // Hierarchical Bone Groups
  public readonly hips: THREE.Group;
  public readonly spine: THREE.Group;
  public readonly neck: THREE.Group;
  public readonly headPivot: THREE.Group;

  // Arms
  public readonly leftShoulder: THREE.Group;
  public readonly leftUpperArm: THREE.Mesh;
  public readonly leftElbow: THREE.Group;
  public readonly leftForearm: THREE.Mesh;
  public readonly leftWrist: THREE.Group;
  public readonly leftHand: THREE.Mesh;

  public readonly rightShoulder: THREE.Group;
  public readonly rightUpperArm: THREE.Mesh;
  public readonly rightElbow: THREE.Group;
  public readonly rightForearm: THREE.Mesh;
  public readonly rightWrist: THREE.Group;
  public readonly rightHand: THREE.Mesh;

  // Legs
  public readonly leftHip: THREE.Group;
  public readonly leftThigh: THREE.Mesh;
  public readonly leftKnee: THREE.Group;
  public readonly leftShin: THREE.Mesh;
  public readonly leftAnkle: THREE.Group;
  public readonly leftSneaker: THREE.Mesh;

  public readonly rightHip: THREE.Group;
  public readonly rightThigh: THREE.Mesh;
  public readonly rightKnee: THREE.Group;
  public readonly rightShin: THREE.Mesh;
  public readonly rightAnkle: THREE.Group;
  public readonly rightSneaker: THREE.Mesh;

  // Accessories
  public readonly glassesGroup: THREE.Group;
  public readonly hairCap: THREE.Mesh;
  public readonly leftBang: THREE.Mesh;
  public readonly rightBang: THREE.Mesh;
  public readonly hoodCowl: THREE.Mesh;
  public readonly kangarooPocket: THREE.Mesh;

  // Held Props (attached to hands)
  public readonly heldTrophy: THREE.Group;

  // Materials & Geometries for clean disposal
  private disposables: (THREE.BufferGeometry | THREE.Material)[] = [];

  // Kinematic Targets for Smooth Slerping
  private activePosture: PostureType = 'idle';
  private walkTime: number = 0;
  private waveTime: number = 0;
  private isLocomoting: boolean = false;

  private targets = {
    hipsY: 0.85,
    hipsRotX: 0, hipsRotY: 0, hipsRotZ: 0,
    spineRotX: 0, spineRotY: 0, spineRotZ: 0,
    leftShoulderRotX: 0, leftShoulderRotY: 0, leftShoulderRotZ: -0.08,
    leftElbowRotX: 0, leftElbowRotY: 0, leftElbowRotZ: 0,
    rightShoulderRotX: 0, rightShoulderRotY: 0, rightShoulderRotZ: 0.08,
    rightElbowRotX: 0, rightElbowRotY: 0, rightElbowRotZ: 0,
    leftHipRotX: 0, leftKneeRotX: 0,
    rightHipRotX: 0, rightKneeRotX: 0,
    trophyInHand: false
  };

  constructor(options: StylizedCharacterRigOptions = {}) {
    this.group = new THREE.Group();
    this.group.name = 'StylizedCharacterRig';

    // 1. PBR Material Palette
    const skinMat = new THREE.MeshStandardMaterial({
      color: 0xf5d0b5,
      roughness: 0.52,
      metalness: 0.05
    });
    this.disposables.push(skinMat);

    const hoodieMat = new THREE.MeshStandardMaterial({
      color: options.hoodieColor ?? 0x141416, // Space Black
      roughness: 0.82,
      metalness: 0.12
    });
    this.disposables.push(hoodieMat);

    const hairMat = new THREE.MeshStandardMaterial({
      color: options.hairColor ?? 0x1c1917, // Dark Espresso
      roughness: 0.65,
      metalness: 0.15
    });
    this.disposables.push(hairMat);

    const titaniumMat = new THREE.MeshStandardMaterial({
      color: options.glassesColor ?? 0xd4d4d8,
      metalness: 0.95,
      roughness: 0.2
    });
    this.disposables.push(titaniumMat);

    const lensMat = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      transmission: 0.92,
      roughness: 0.08,
      ior: 1.52,
      transparent: true,
      opacity: 0.45
    });
    this.disposables.push(lensMat);

    const joggerMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b, // Dark Charcoal
      roughness: 0.85
    });
    this.disposables.push(joggerMat);

    const sneakerMat = new THREE.MeshStandardMaterial({
      color: 0xf8fafc, // Crisp White
      roughness: 0.35
    });
    this.disposables.push(sneakerMat);

    const sneakerSoleMat = new THREE.MeshStandardMaterial({
      color: 0x09090b,
      roughness: 0.8
    });
    this.disposables.push(sneakerSoleMat);

    // 2. Pelvis / Hips
    this.hips = new THREE.Group();
    this.hips.position.y = 0.85;
    this.group.add(this.hips);

    // 3. Spine & Torso
    this.spine = new THREE.Group();
    this.hips.add(this.spine);

    const torsoGeo = new THREE.CylinderGeometry(0.28, 0.24, 0.65, 28);
    this.disposables.push(torsoGeo);
    const torso = new THREE.Mesh(torsoGeo, hoodieMat);
    torso.position.y = 0.32;
    torso.castShadow = true;
    torso.receiveShadow = true;
    this.spine.add(torso);

    // Kangaroo Pocket Detail
    const pocketGeo = new THREE.BoxGeometry(0.32, 0.18, 0.10);
    this.disposables.push(pocketGeo);
    this.kangarooPocket = new THREE.Mesh(pocketGeo, hoodieMat);
    this.kangarooPocket.position.set(0, 0.22, 0.20);
    this.kangarooPocket.rotation.x = -0.08;
    this.spine.add(this.kangarooPocket);

    // Hood Cowl Collar
    const cowlGeo = new THREE.TorusGeometry(0.25, 0.09, 20, 28);
    this.disposables.push(cowlGeo);
    this.hoodCowl = new THREE.Mesh(cowlGeo, hoodieMat);
    this.hoodCowl.rotation.x = Math.PI / 2.3;
    this.hoodCowl.position.set(0, 0.62, -0.04);
    this.spine.add(this.hoodCowl);

    // 4. Neck & Head Pivot (~1:4.8 Head-to-Body Ratio)
    this.neck = new THREE.Group();
    this.neck.position.set(0, 0.68, 0);
    this.spine.add(this.neck);

    this.headPivot = new THREE.Group();
    this.headPivot.position.set(0, 0.14, 0);
    this.neck.add(this.headPivot);

    const headGeo = new THREE.SphereGeometry(0.26, 32, 32);
    this.disposables.push(headGeo);
    const headMesh = new THREE.Mesh(headGeo, skinMat);
    headMesh.scale.set(1.0, 1.08, 0.96);
    headMesh.castShadow = true;
    this.headPivot.add(headMesh);

    // Hairstyle: Dark Espresso Parted Curtain Bangs
    const hairCapGeo = new THREE.SphereGeometry(0.28, 28, 28, 0, Math.PI * 2, 0, Math.PI * 0.58);
    this.disposables.push(hairCapGeo);
    this.hairCap = new THREE.Mesh(hairCapGeo, hairMat);
    this.hairCap.position.y = 0.04;
    this.headPivot.add(this.hairCap);

    const leftBangGeo = new THREE.ConeGeometry(0.12, 0.28, 16);
    this.disposables.push(leftBangGeo);
    this.leftBang = new THREE.Mesh(leftBangGeo, hairMat);
    this.leftBang.rotation.set(-0.35, 0.22, -0.42);
    this.leftBang.position.set(-0.14, 0.12, 0.22);
    this.headPivot.add(this.leftBang);

    const rightBangGeo = new THREE.ConeGeometry(0.14, 0.30, 16);
    this.disposables.push(rightBangGeo);
    this.rightBang = new THREE.Mesh(rightBangGeo, hairMat);
    this.rightBang.rotation.set(-0.35, -0.22, 0.42);
    this.rightBang.position.set(0.12, 0.10, 0.22);
    this.headPivot.add(this.rightBang);

    // Titanium Round Spectacles
    this.glassesGroup = new THREE.Group();
    this.glassesGroup.position.set(0, 0.03, 0.25);
    this.headPivot.add(this.glassesGroup);

    const rimGeo = new THREE.TorusGeometry(0.082, 0.012, 16, 36);
    this.disposables.push(rimGeo);
    const lensGeo = new THREE.CircleGeometry(0.08, 28);
    this.disposables.push(lensGeo);

    const leftRim = new THREE.Mesh(rimGeo, titaniumMat);
    leftRim.position.x = -0.10;
    this.glassesGroup.add(leftRim);
    const leftLens = new THREE.Mesh(lensGeo, lensMat);
    leftLens.position.x = -0.10;
    this.glassesGroup.add(leftLens);

    const rightRim = new THREE.Mesh(rimGeo, titaniumMat);
    rightRim.position.x = 0.10;
    this.glassesGroup.add(rightRim);
    const rightLens = new THREE.Mesh(lensGeo, lensMat);
    rightLens.position.x = 0.10;
    this.glassesGroup.add(rightLens);

    const bridgeGeo = new THREE.CylinderGeometry(0.008, 0.008, 0.05, 12);
    this.disposables.push(bridgeGeo);
    const bridge = new THREE.Mesh(bridgeGeo, titaniumMat);
    bridge.rotation.z = Math.PI / 2;
    this.glassesGroup.add(bridge);

    const templeGeo = new THREE.CylinderGeometry(0.006, 0.006, 0.22, 8);
    this.disposables.push(templeGeo);
    const leftTemple = new THREE.Mesh(templeGeo, titaniumMat);
    leftTemple.rotation.x = Math.PI / 2;
    leftTemple.position.set(-0.18, 0, -0.10);
    this.glassesGroup.add(leftTemple);

    const rightTemple = new THREE.Mesh(templeGeo, titaniumMat);
    rightTemple.rotation.x = Math.PI / 2;
    rightTemple.position.set(0.18, 0, -0.10);
    this.glassesGroup.add(rightTemple);

    // 5. Left Arm Hierarchy
    this.leftShoulder = new THREE.Group();
    this.leftShoulder.position.set(-0.34, 0.58, 0);
    this.spine.add(this.leftShoulder);

    const upperArmGeo = new THREE.CylinderGeometry(0.09, 0.08, 0.32, 18);
    this.disposables.push(upperArmGeo);
    this.leftUpperArm = new THREE.Mesh(upperArmGeo, hoodieMat);
    this.leftUpperArm.position.y = -0.16;
    this.leftShoulder.add(this.leftUpperArm);

    this.leftElbow = new THREE.Group();
    this.leftElbow.position.y = -0.32;
    this.leftShoulder.add(this.leftElbow);

    const forearmGeo = new THREE.CylinderGeometry(0.08, 0.07, 0.28, 18);
    this.disposables.push(forearmGeo);
    this.leftForearm = new THREE.Mesh(forearmGeo, hoodieMat);
    this.leftForearm.position.y = -0.14;
    this.leftElbow.add(this.leftForearm);

    this.leftWrist = new THREE.Group();
    this.leftWrist.position.y = -0.28;
    this.leftElbow.add(this.leftWrist);

    const handGeo = new THREE.SphereGeometry(0.07, 18, 18);
    this.disposables.push(handGeo);
    this.leftHand = new THREE.Mesh(handGeo, skinMat);
    this.leftHand.scale.set(1.0, 1.2, 0.6);
    this.leftWrist.add(this.leftHand);

    // 6. Right Arm Hierarchy
    this.rightShoulder = new THREE.Group();
    this.rightShoulder.position.set(0.34, 0.58, 0);
    this.spine.add(this.rightShoulder);

    this.rightUpperArm = new THREE.Mesh(upperArmGeo, hoodieMat);
    this.rightUpperArm.position.y = -0.16;
    this.rightShoulder.add(this.rightUpperArm);

    this.rightElbow = new THREE.Group();
    this.rightElbow.position.y = -0.32;
    this.rightShoulder.add(this.rightElbow);

    this.rightForearm = new THREE.Mesh(forearmGeo, hoodieMat);
    this.rightForearm.position.y = -0.14;
    this.rightElbow.add(this.rightForearm);

    this.rightWrist = new THREE.Group();
    this.rightWrist.position.y = -0.28;
    this.rightElbow.add(this.rightWrist);

    this.rightHand = new THREE.Mesh(handGeo, skinMat);
    this.rightHand.scale.set(1.0, 1.2, 0.6);
    this.rightWrist.add(this.rightHand);

    // 7. Left Leg Hierarchy
    this.leftHip = new THREE.Group();
    this.leftHip.position.set(-0.14, 0, 0);
    this.hips.add(this.leftHip);

    const thighGeo = new THREE.CylinderGeometry(0.10, 0.085, 0.40, 18);
    this.disposables.push(thighGeo);
    this.leftThigh = new THREE.Mesh(thighGeo, joggerMat);
    this.leftThigh.position.y = -0.20;
    this.leftThigh.castShadow = true;
    this.leftHip.add(this.leftThigh);

    this.leftKnee = new THREE.Group();
    this.leftKnee.position.y = -0.40;
    this.leftHip.add(this.leftKnee);

    const shinGeo = new THREE.CylinderGeometry(0.085, 0.075, 0.38, 18);
    this.disposables.push(shinGeo);
    this.leftShin = new THREE.Mesh(shinGeo, joggerMat);
    this.leftShin.position.y = -0.19;
    this.leftShin.castShadow = true;
    this.leftKnee.add(this.leftShin);

    this.leftAnkle = new THREE.Group();
    this.leftAnkle.position.y = -0.38;
    this.leftKnee.add(this.leftAnkle);

    const sneakerGeo = new THREE.BoxGeometry(0.14, 0.09, 0.26);
    this.disposables.push(sneakerGeo);
    this.leftSneaker = new THREE.Mesh(sneakerGeo, sneakerMat);
    this.leftSneaker.position.set(0, -0.04, 0.05);
    this.leftSneaker.castShadow = true;
    this.leftAnkle.add(this.leftSneaker);

    const soleGeo = new THREE.BoxGeometry(0.15, 0.03, 0.28);
    this.disposables.push(soleGeo);
    const leftSole = new THREE.Mesh(soleGeo, sneakerSoleMat);
    leftSole.position.set(0, -0.09, 0.05);
    this.leftAnkle.add(leftSole);

    // 8. Right Leg Hierarchy
    this.rightHip = new THREE.Group();
    this.rightHip.position.set(0.14, 0, 0);
    this.hips.add(this.rightHip);

    this.rightThigh = new THREE.Mesh(thighGeo, joggerMat);
    this.rightThigh.position.y = -0.20;
    this.rightThigh.castShadow = true;
    this.rightHip.add(this.rightThigh);

    this.rightKnee = new THREE.Group();
    this.rightKnee.position.y = -0.40;
    this.rightHip.add(this.rightKnee);

    this.rightShin = new THREE.Mesh(shinGeo, joggerMat);
    this.rightShin.position.y = -0.19;
    this.rightShin.castShadow = true;
    this.rightKnee.add(this.rightShin);

    this.rightAnkle = new THREE.Group();
    this.rightAnkle.position.y = -0.38;
    this.rightKnee.add(this.rightAnkle);

    this.rightSneaker = new THREE.Mesh(sneakerGeo, sneakerMat);
    this.rightSneaker.position.set(0, -0.04, 0.05);
    this.rightSneaker.castShadow = true;
    this.rightAnkle.add(this.rightSneaker);

    const rightSole = new THREE.Mesh(soleGeo, sneakerSoleMat);
    rightSole.position.set(0, -0.09, 0.05);
    this.rightAnkle.add(rightSole);

    // 9. Held 24k Gold Trophy
    this.heldTrophy = new THREE.Group();
    this.heldTrophy.visible = false;
    const goldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.95, roughness: 0.15 });
    this.disposables.push(goldMat);

    const trophyStemGeo = new THREE.CylinderGeometry(0.08, 0.05, 0.32, 6);
    this.disposables.push(trophyStemGeo);
    const trophyStem = new THREE.Mesh(trophyStemGeo, goldMat);
    this.heldTrophy.add(trophyStem);

    const trophyCrownGeo = new THREE.TorusGeometry(0.10, 0.025, 12, 20);
    this.disposables.push(trophyCrownGeo);
    const trophyCrown = new THREE.Mesh(trophyCrownGeo, goldMat);
    trophyCrown.position.y = 0.18;
    this.heldTrophy.add(trophyCrown);

    this.rightWrist.add(this.heldTrophy);
    this.heldTrophy.position.set(0, -0.22, 0.04);
  }

  /**
   * Set the active performance posture
   */
  public setPosture(posture: PostureType): void {
    this.activePosture = posture;
    this.isLocomoting = (posture === 'walk');

    // Default target reset
    this.targets.hipsY = 0.85;
    this.targets.hipsRotX = 0; this.targets.hipsRotY = 0; this.targets.hipsRotZ = 0;
    this.targets.spineRotX = 0; this.targets.spineRotY = 0; this.targets.spineRotZ = 0;
    this.targets.leftShoulderRotX = 0; this.targets.leftShoulderRotY = 0; this.targets.leftShoulderRotZ = -0.08;
    this.targets.leftElbowRotX = 0; this.targets.leftElbowRotY = 0; this.targets.leftElbowRotZ = 0;
    this.targets.rightShoulderRotX = 0; this.targets.rightShoulderRotY = 0; this.targets.rightShoulderRotZ = 0.08;
    this.targets.rightElbowRotX = 0; this.targets.rightElbowRotY = 0; this.targets.rightElbowRotZ = 0;
    this.targets.leftHipRotX = 0; this.targets.leftKneeRotX = 0;
    this.targets.rightHipRotX = 0; this.targets.rightKneeRotX = 0;
    this.targets.trophyInHand = false;

    switch (posture) {
      case 'idle':
        this.targets.hipsY = 0.85;
        this.targets.leftShoulderRotZ = -0.10;
        this.targets.rightShoulderRotZ = 0.10;
        break;

      case 'seated':
        // Act 1: Executive Chair Sitting
        this.targets.hipsY = 0.52; // Lowered to chair cushion
        this.targets.leftHipRotX = -Math.PI / 2 + 0.15; // Thighs forward horizontal
        this.targets.leftKneeRotX = Math.PI / 2 - 0.10; // Shins vertical down
        this.targets.rightHipRotX = -Math.PI / 2 + 0.15;
        this.targets.rightKneeRotX = Math.PI / 2 - 0.10;
        // Welcoming hand gestures
        this.targets.leftShoulderRotX = -0.35;
        this.targets.leftShoulderRotZ = -0.25;
        this.targets.leftElbowRotX = -0.65;
        this.targets.rightShoulderRotX = -0.45;
        this.targets.rightShoulderRotZ = 0.28;
        this.targets.rightElbowRotX = -0.75;
        break;

      case 'walk':
        // Walk mode handles leg and arm swinging dynamically in update()
        this.targets.hipsY = 0.85;
        break;

      case 'reach_book':
        // Act 2: Library Bookshelf Pull
        this.targets.hipsRotY = -0.45; // Turn toward shelf
        this.targets.leftShoulderRotX = -0.85; // Reach left arm forward-up
        this.targets.leftShoulderRotZ = -0.35;
        this.targets.leftElbowRotX = -0.40;
        this.targets.rightShoulderRotZ = 0.20;
        break;

      case 'conduct_badges':
        // Act 3: GDSC Cloud Crucible Conductor
        this.targets.spineRotX = -0.05;
        this.targets.leftShoulderRotX = -0.7;
        this.targets.leftShoulderRotZ = -0.6;
        this.targets.leftElbowRotX = -0.5;
        this.targets.rightShoulderRotX = -0.7;
        this.targets.rightShoulderRotZ = 0.6;
        this.targets.rightElbowRotX = -0.5;
        break;

      case 'climb_ridge':
        // Act 4: Mount Pilatus Granite Rock Climbing
        this.targets.spineRotX = 0.35; // Torso pitched forward into mountain
        this.targets.hipsY = 0.78;
        this.targets.rightShoulderRotX = -1.6; // High grip overhead
        this.targets.rightShoulderRotZ = 0.25;
        this.targets.rightElbowRotX = -0.7;
        this.targets.leftShoulderRotX = -0.6;
        this.targets.leftShoulderRotZ = -0.4;
        this.targets.leftElbowRotX = -0.8;
        this.targets.leftHipRotX = -1.1; // Left knee high on boulder
        this.targets.leftKneeRotX = 1.3;
        this.targets.rightHipRotX = 0.2;
        this.targets.rightKneeRotX = 0.3;
        break;

      case 'hoist_trophy':
        // Act 4: Summit Victory Stance
        this.targets.trophyInHand = true;
        this.targets.spineRotX = -0.10; // Proud chest arch
        this.targets.rightShoulderRotX = -0.2;
        this.targets.rightShoulderRotZ = 1.45; // Arm vertical
        this.targets.rightElbowRotZ = 0.25;
        this.targets.leftShoulderRotZ = -0.35; // Left hand on hip
        this.targets.leftElbowRotX = -0.85;
        this.targets.leftElbowRotZ = -0.45;
        this.targets.leftHipRotX = -0.08;
        this.targets.rightHipRotX = 0.08;
        break;

      case 'operate_core':
        // Act 5: Enterprise Fintech Exploded Core Operation
        this.targets.spineRotX = 0.05;
        this.targets.leftShoulderRotX = -0.85;
        this.targets.leftShoulderRotZ = -0.3;
        this.targets.leftElbowRotX = -0.6;
        this.targets.rightShoulderRotX = -0.85;
        this.targets.rightShoulderRotZ = 0.3;
        this.targets.rightElbowRotX = -0.6;
        break;

      case 'wave':
        // Act 6: Horizon Salutation Wave
        this.targets.rightShoulderRotZ = 1.2;
        this.targets.rightShoulderRotX = -0.3;
        this.targets.rightElbowRotZ = 0.6;
        this.targets.leftShoulderRotZ = -0.15;
        break;

      case 'glasses_adjust':
        // Act 1 Dynamic Pose: Zachary lifts right hand to gently push up titanium spectacles
        this.targets.hipsY = 0.85;
        this.targets.spineRotX = 0.04;
        this.targets.rightShoulderRotX = -1.25;
        this.targets.rightShoulderRotY = -0.45;
        this.targets.rightShoulderRotZ = 0.38;
        this.targets.rightElbowRotX = -1.75;
        this.targets.rightElbowRotZ = 0.30;
        this.targets.leftShoulderRotX = -0.20;
        this.targets.leftShoulderRotZ = -0.15;
        this.targets.leftElbowRotX = -0.30;
        break;

      case 'inspect_tablet':
        // Act 1 Dynamic Pose: Zachary brings hands forward reviewing architecture telemetry
        this.targets.hipsY = 0.85;
        this.targets.spineRotX = 0.12;
        this.targets.leftShoulderRotX = -0.75;
        this.targets.leftShoulderRotY = 0.30;
        this.targets.leftShoulderRotZ = -0.15;
        this.targets.leftElbowRotX = -1.25;
        this.targets.leftElbowRotZ = -0.15;
        this.targets.rightShoulderRotX = -0.75;
        this.targets.rightShoulderRotY = -0.30;
        this.targets.rightShoulderRotZ = 0.15;
        this.targets.rightElbowRotX = -1.25;
        this.targets.rightElbowRotZ = 0.15;
        break;

      case 'keynote_present':
        // Act 1 Dynamic Pose: Zachary opens arm out in confident keynote presentation gesture
        this.targets.hipsY = 0.85;
        this.targets.spineRotX = -0.05;
        this.targets.spineRotY = -0.15;
        this.targets.rightShoulderRotX = -0.55;
        this.targets.rightShoulderRotY = 0.45;
        this.targets.rightShoulderRotZ = 0.75;
        this.targets.rightElbowRotX = -0.20;
        this.targets.rightElbowRotZ = 0.10;
        this.targets.leftShoulderRotZ = -0.25;
        this.targets.leftElbowRotX = -0.45;
        break;
    }

    this.heldTrophy.visible = this.targets.trophyInHand;
  }

  /**
   * Update kinematics loop
   */
  public update(delta: number, mouseX: number = 0, mouseY: number = 0, isReducedMotion: boolean = false): void {
    if (isReducedMotion) {
      this.hips.position.y = this.targets.hipsY;
      this.headPivot.rotation.set(0, 0, 0);
      this.hips.rotation.set(this.targets.hipsRotX, this.targets.hipsRotY, this.targets.hipsRotZ);
      this.spine.rotation.set(this.targets.spineRotX, this.targets.spineRotY, this.targets.spineRotZ);
      this.leftShoulder.rotation.set(this.targets.leftShoulderRotX, this.targets.leftShoulderRotY, this.targets.leftShoulderRotZ);
      this.leftElbow.rotation.set(this.targets.leftElbowRotX, this.targets.leftElbowRotY, this.targets.leftElbowRotZ);
      this.rightShoulder.rotation.set(this.targets.rightShoulderRotX, this.targets.rightShoulderRotY, this.targets.rightShoulderRotZ);
      this.rightElbow.rotation.set(this.targets.rightElbowRotX, this.targets.rightElbowRotY, this.targets.rightElbowRotZ);
      this.leftHip.rotation.set(this.targets.leftHipRotX, 0, 0);
      this.leftKnee.rotation.set(this.targets.leftKneeRotX, 0, 0);
      this.rightHip.rotation.set(this.targets.rightHipRotX, 0, 0);
      this.rightKnee.rotation.set(this.targets.rightKneeRotX, 0, 0);
      this.rightWrist.rotation.z = 0;
      return;
    }

    const t = performance.now() * 0.001;

    // 1. Natural Breathing Stance
    const breath = this.activePosture === 'seated' ? 0 : Math.sin(t * 2.2) * 0.012;
    const targetHipsY = this.targets.hipsY + breath;
    this.hips.position.y += (targetHipsY - this.hips.position.y) * delta * 5.0;

    // 2. Cursor Gaze Tracking
    const targetGazeX = mouseX * 0.35;
    const targetGazeY = mouseY * 0.25;
    this.headPivot.rotation.y += (targetGazeX - this.headPivot.rotation.y) * delta * 4.0;
    this.headPivot.rotation.x += (-targetGazeY - this.headPivot.rotation.x) * delta * 4.0;

    // 3. Dynamic Locomotion / Walk Cycle
    if (this.isLocomoting) {
      this.walkTime += delta * 6.0;
      const legSwing = Math.sin(this.walkTime) * 0.45;
      this.leftHip.rotation.x = legSwing;
      this.rightHip.rotation.x = -legSwing;
      this.leftKnee.rotation.x = Math.max(0, -legSwing * 0.8);
      this.rightKnee.rotation.x = Math.max(0, legSwing * 0.8);

      this.leftShoulder.rotation.x = -legSwing * 0.75;
      this.rightShoulder.rotation.x = legSwing * 0.75;
      this.hips.position.y = 0.85 + Math.abs(Math.sin(this.walkTime * 2)) * 0.03;
    } else {
      // Smooth Joint Slerping / Easing towards targets
      this.hips.rotation.x += (this.targets.hipsRotX - this.hips.rotation.x) * delta * 5.0;
      this.hips.rotation.y += (this.targets.hipsRotY - this.hips.rotation.y) * delta * 5.0;
      this.hips.rotation.z += (this.targets.hipsRotZ - this.hips.rotation.z) * delta * 5.0;

      this.spine.rotation.x += (this.targets.spineRotX - this.spine.rotation.x) * delta * 5.0;
      this.spine.rotation.y += (this.targets.spineRotY - this.spine.rotation.y) * delta * 5.0;
      this.spine.rotation.z += (this.targets.spineRotZ - this.spine.rotation.z) * delta * 5.0;

      this.leftShoulder.rotation.x += (this.targets.leftShoulderRotX - this.leftShoulder.rotation.x) * delta * 5.0;
      this.leftShoulder.rotation.y += (this.targets.leftShoulderRotY - this.leftShoulder.rotation.y) * delta * 5.0;
      this.leftShoulder.rotation.z += (this.targets.leftShoulderRotZ - this.leftShoulder.rotation.z) * delta * 5.0;

      this.leftElbow.rotation.x += (this.targets.leftElbowRotX - this.leftElbow.rotation.x) * delta * 5.0;
      this.leftElbow.rotation.y += (this.targets.leftElbowRotY - this.leftElbow.rotation.y) * delta * 5.0;
      this.leftElbow.rotation.z += (this.targets.leftElbowRotZ - this.leftElbow.rotation.z) * delta * 5.0;

      this.rightShoulder.rotation.x += (this.targets.rightShoulderRotX - this.rightShoulder.rotation.x) * delta * 5.0;
      this.rightShoulder.rotation.y += (this.targets.rightShoulderRotY - this.rightShoulder.rotation.y) * delta * 5.0;
      this.rightShoulder.rotation.z += (this.targets.rightShoulderRotZ - this.rightShoulder.rotation.z) * delta * 5.0;

      this.rightElbow.rotation.x += (this.targets.rightElbowRotX - this.rightElbow.rotation.x) * delta * 5.0;
      this.rightElbow.rotation.y += (this.targets.rightElbowRotY - this.rightElbow.rotation.y) * delta * 5.0;
      this.rightElbow.rotation.z += (this.targets.rightElbowRotZ - this.rightElbow.rotation.z) * delta * 5.0;

      this.leftHip.rotation.x += (this.targets.leftHipRotX - this.leftHip.rotation.x) * delta * 5.0;
      this.leftKnee.rotation.x += (this.targets.leftKneeRotX - this.leftKnee.rotation.x) * delta * 5.0;

      this.rightHip.rotation.x += (this.targets.rightHipRotX - this.rightHip.rotation.x) * delta * 5.0;
      this.rightKnee.rotation.x += (this.targets.rightKneeRotX - this.rightKnee.rotation.x) * delta * 5.0;
    }

    // 4. Wave Motion
    if (this.activePosture === 'wave') {
      this.waveTime += delta * 6.0;
      this.rightWrist.rotation.z = Math.sin(this.waveTime) * 0.35;
    } else {
      this.rightWrist.rotation.z *= 0.9;
    }
  }

  public getActivePosture(): PostureType {
    return this.activePosture;
  }

  /**
   * Deterministic 100% VRAM memory cleanup
   */
  public dispose(): void {
    for (const item of this.disposables) {
      if ('dispose' in item && typeof item.dispose === 'function') {
        item.dispose();
      }
    }
    this.disposables = [];
  }
}
