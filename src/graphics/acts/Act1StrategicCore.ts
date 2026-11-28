import * as THREE from 'three';
import { createGltfLoader, resolveAssetUrl } from '../core/gltfLoader';
import { assetUrl } from '../../utils/assetUrl';

export interface Act1StrategicCoreOptions {
  avatarRig: THREE.Group;
  materialsList: THREE.Material[];
  onModelLoaded?: () => void;
}

/**
 * Act1StrategicCore
 * Constructs and manages the Act 1 Executive Strategy Studio & Interactive Enterprise AI Engine:
 * - Circular presentation plinth (Y = -1.55) & cyan illuminated perimeter ring (Y = -1.48)
 * - PersonaBody anchor (Y = -1.45 flush on plinth)
 * - 3-tier strata architecture (Containment Shield, Clearing Ring, Generative Neural Core)
 * - 6 Strata Connection Vectors with spring-damped expansion
 * - 96 Instanced glowing data nodes (ISO-20022 Financial Network)
 * - Drag rotation inertia and explode_strata dynamics
 */
export class Act1StrategicCore {
  private avatarRig: THREE.Group;
  private personaBodyGroup: THREE.Group;
  private enterpriseEngineGroup: THREE.Group;
  private engineTier1: THREE.Group;
  private engineTier2: THREE.Group;
  private engineTier3: THREE.Group;
  private engineVectorsGroup: THREE.Group;
  private engineVectors: THREE.Mesh[] = [];

  private clearingInstancedNodes: THREE.InstancedMesh;
  private clearingNodeAngles: Float32Array = new Float32Array(96);
  private clearingNodeRadii: Float32Array = new Float32Array(96);
  private clearingNodeSpeeds: Float32Array = new Float32Array(96);
  private clearingNodeHeights: Float32Array = new Float32Array(96);
  private clearingRingA: THREE.Mesh;
  private clearingRingB: THREE.Mesh;

  private neuralCoreLattice: THREE.Mesh;
  private neuralCoreInner: THREE.Mesh;
  private coreOriginalPositions: Float32Array | null = null;

  private studioGroup: THREE.Group;
  private curvedDisplaysGroup: THREE.Group;
  private executiveDesk: THREE.Group;
  private executiveTablet: THREE.Group;
  private executiveChair: THREE.Group;
  private blueprintGuidesGroup: THREE.Group | null = null;
  private blueprintGuideMat: THREE.MeshBasicMaterial | null = null;
  private blueprintTierRingMat: THREE.MeshBasicMaterial | null = null;
  private blueprintTierRings: THREE.Mesh[] = [];
  private glbBlueprintTiers: {
    tier1: THREE.Object3D | null;
    tier2: THREE.Object3D | null;
    tier3: THREE.Object3D | null;
    coreNucleus: THREE.Object3D | null;
    coreFilament: THREE.Object3D | null;
    gimbalOuter: THREE.Object3D | null;
    gimbalInner: THREE.Object3D | null;
    sculpturePivot: THREE.Group | null;
    baseY1: number;
    baseY2: number;
    baseY3: number;
    baseYNucleus: number;
    baseYFilament: number;
  } = {
    tier1: null,
    tier2: null,
    tier3: null,
    coreNucleus: null,
    coreFilament: null,
    gimbalOuter: null,
    gimbalInner: null,
    sculpturePivot: null,
    baseY1: 1.60,
    baseY2: 1.24,
    baseY3: 0.88,
    baseYNucleus: 1.24,
    baseYFilament: 1.24,
  };
  private atelierAnimTime: number = 0;
  private coreFocusBoost: boolean = false;
  private studioEnvMap: THREE.Texture | null = null;
  private filamentGlowMats: THREE.MeshStandardMaterial[] = [];
  private dossierMetallicMats: THREE.MeshStandardMaterial[] = [];
  private executiveDossierGroup: THREE.Group | null = null;
  private executiveDossierHalo: THREE.Mesh | null = null;
  private executiveDossierTex: THREE.CanvasTexture | null = null;
  private disposableGeos: THREE.BufferGeometry[] = [];

  private isEngineExploded: boolean = false;
  private currentExplodeFactor: number = 0;
  private dummyObj: THREE.Object3D = new THREE.Object3D();

  private dragAngleX: number = 0;
  private dragAngleY: number = 0;
  private rotVelX: number = 0;
  private rotVelY: number = 0;
  private isDragging: boolean = false;
  private prevMouseX: number = 0;
  private prevMouseY: number = 0;

  private plinthMesh: THREE.Mesh;
  private plinthGlowRing: THREE.Mesh;
  private plinthMat: THREE.MeshStandardMaterial;
  private plinthGlowMat: THREE.MeshBasicMaterial;
  private studioGlbRoot: THREE.Object3D | null = null;
  private onModelLoaded?: () => void;

  constructor(options: Act1StrategicCoreOptions) {
    this.onModelLoaded = options.onModelLoaded;
    this.avatarRig = options.avatarRig;

    // 1. Presentation Plinth & Glow Ring
    const plinthGeo = new THREE.CylinderGeometry(1.45, 1.55, 0.20, 64);
    this.plinthMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.32,
      metalness: 0.88,
      transparent: true,
      opacity: 1.0,
    });
    this.plinthMesh = new THREE.Mesh(plinthGeo, this.plinthMat);
    this.plinthMesh.name = 'Plinth';
    this.plinthMesh.position.y = -1.55;
    this.plinthMesh.receiveShadow = true;
    this.plinthMesh.visible = true;
    this.avatarRig.add(this.plinthMesh);

    this.plinthGlowMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.95 });
    this.plinthGlowRing = new THREE.Mesh(new THREE.TorusGeometry(1.42, 0.022, 16, 72), this.plinthGlowMat);
    this.plinthGlowRing.name = 'PlinthGlowRing';
    this.plinthGlowRing.rotation.x = Math.PI / 2;
    this.plinthGlowRing.position.y = -1.48;
    this.plinthGlowRing.visible = true;
    this.avatarRig.add(this.plinthGlowRing);

    // Option B procedural grounded legs
    const legGeo = new THREE.CylinderGeometry(0.08, 0.07, 0.70, 16);
    const legMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.8,
      metalness: 0.2,
    });
    const leftLeg = new THREE.Mesh(legGeo, legMat);
    leftLeg.name = 'LeftLegMesh';
    leftLeg.position.set(-0.16, -1.05, 0);
    leftLeg.visible = false;
    this.avatarRig.add(leftLeg);

    const rightLeg = new THREE.Mesh(legGeo, legMat);
    rightLeg.name = 'RightLegMesh';
    rightLeg.position.set(0.16, -1.05, 0);
    rightLeg.visible = false;
    this.avatarRig.add(rightLeg);

    options.materialsList.push(this.plinthMat, this.plinthGlowMat, legMat);

    // 2. Master Persona Body Group (Station Y = -1.45 on top surface of plinth)
    this.personaBodyGroup = new THREE.Group();
    this.personaBodyGroup.name = 'PersonaBody';
    this.personaBodyGroup.position.set(0, -1.45, 0);
    this.avatarRig.add(this.personaBodyGroup);

    // 3. Enterprise AI Engine Root Group
    this.enterpriseEngineGroup = new THREE.Group();
    this.enterpriseEngineGroup.name = 'EnterpriseAIEngine';
    this.enterpriseEngineGroup.position.set(0, 0, 0);
    this.avatarRig.add(this.enterpriseEngineGroup);

    const legacyMonolith = new THREE.Group();
    legacyMonolith.name = 'KeynoteCrystalMonolith';
    legacyMonolith.visible = false;
    this.enterpriseEngineGroup.add(legacyMonolith);

    // 4. Strata Connection Vectors
    this.engineVectorsGroup = new THREE.Group();
    this.engineVectorsGroup.name = 'EngineVectorsGroup';
    const vectorGeo = new THREE.CylinderGeometry(0.007, 0.007, 1.0, 8);
    const vectorMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.45,
    });
    const vectorCount = 6;
    for (let v = 0; v < vectorCount; v++) {
      const angle = (v / vectorCount) * Math.PI * 2;
      const vx = Math.cos(angle) * 0.45;
      const vz = Math.sin(angle) * 0.45;
      const vectorMesh = new THREE.Mesh(vectorGeo, vectorMat);
      vectorMesh.name = `EngineVector_${v}`;
      vectorMesh.position.set(vx, 0, vz);
      vectorMesh.scale.set(1.0, 0.15, 1.0);
      this.engineVectors.push(vectorMesh);
      this.engineVectorsGroup.add(vectorMesh);
    }
    this.enterpriseEngineGroup.add(this.engineVectorsGroup);

    // 5. Tier 1: Outer Containment Shield (Frosted Physical Transmission Glass)
    this.engineTier1 = new THREE.Group();
    this.engineTier1.name = 'EngineTier1';
    const shieldGlassMat = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(0x0a192f),
      transmission: 0.65,
      roughness: 0.15,
      metalness: 0.1,
      clearcoat: 1.0,
      clearcoatRoughness: 0.10,
      ior: 1.52,
      thickness: 0.12,
      transparent: true,
      opacity: 0.88,
    });
    const outerShieldRing = new THREE.Mesh(new THREE.TorusGeometry(1.18, 0.045, 32, 96), shieldGlassMat);
    outerShieldRing.name = 'ShieldOuterTorus';
    outerShieldRing.castShadow = true;
    outerShieldRing.receiveShadow = true;
    this.engineTier1.add(outerShieldRing);

    const innerShieldRing = new THREE.Mesh(new THREE.TorusGeometry(1.04, 0.035, 32, 96), shieldGlassMat);
    innerShieldRing.name = 'ShieldInclinedRing';
    innerShieldRing.rotation.x = Math.PI / 4.5;
    innerShieldRing.rotation.z = Math.PI / 12;
    this.engineTier1.add(innerShieldRing);

    const rimSpecularMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.75 });
    const specularRim = new THREE.Mesh(new THREE.TorusGeometry(1.22, 0.007, 16, 96), rimSpecularMat);
    specularRim.name = 'ShieldSpecularRim';
    this.engineTier1.add(specularRim);

    // 4 Titanium Bezel Brackets
    const titaniumMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.94,
      roughness: 0.18,
    });
    const bracketGeo = new THREE.BoxGeometry(0.06, 0.12, 0.08);
    for (let b = 0; b < 4; b++) {
      const bAngle = (b / 4) * Math.PI * 2;
      const bracket = new THREE.Mesh(bracketGeo, titaniumMat);
      bracket.position.set(Math.cos(bAngle) * 1.18, 0, Math.sin(bAngle) * 1.18);
      bracket.rotation.y = -bAngle;
      this.engineTier1.add(bracket);
    }
    this.enterpriseEngineGroup.add(this.engineTier1);

    // 6. Tier 2: Middle Clearing Ring (ISO-20022 Financial Network)
    this.engineTier2 = new THREE.Group();
    this.engineTier2.name = 'EngineTier2';
    const ringAMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.88, roughness: 0.22 });
    this.clearingRingA = new THREE.Mesh(new THREE.TorusGeometry(0.86, 0.024, 16, 80), ringAMat);
    this.clearingRingA.name = 'ClearingRingA';
    this.engineTier2.add(this.clearingRingA);

    const ringBMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.92, roughness: 0.16 });
    this.clearingRingB = new THREE.Mesh(new THREE.TorusGeometry(0.72, 0.018, 16, 80), ringBMat);
    this.clearingRingB.name = 'ClearingRingB';
    this.engineTier2.add(this.clearingRingB);

    const equatorDisc = new THREE.Mesh(
      new THREE.RingGeometry(0.70, 0.88, 64),
      new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.20, side: THREE.DoubleSide })
    );
    equatorDisc.rotation.x = Math.PI / 2;
    this.engineTier2.add(equatorDisc);

    // 8 Radial Gate Stators
    const statorGeo = new THREE.BoxGeometry(0.14, 0.012, 0.02);
    for (let s = 0; s < 8; s++) {
      const sAngle = (s / 8) * Math.PI * 2;
      const stator = new THREE.Mesh(statorGeo, titaniumMat);
      stator.position.set(Math.cos(sAngle) * 0.79, 0, Math.sin(sAngle) * 0.79);
      stator.rotation.y = -sAngle;
      this.engineTier2.add(stator);
    }

    // 96 Instanced Data Nodes
    const nodeCount = 96;
    const nodeGeo = new THREE.SphereGeometry(0.024, 8, 8);
    const nodeMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      emissive: 0x00f2fe,
      emissiveIntensity: 1.8,
      roughness: 0.15,
      metalness: 0.85,
    });
    this.clearingInstancedNodes = new THREE.InstancedMesh(nodeGeo, nodeMat, nodeCount);
    this.clearingInstancedNodes.name = 'ClearingDataNodes';
    this.clearingInstancedNodes.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    for (let i = 0; i < nodeCount; i++) {
      const angle = (i / nodeCount) * Math.PI * 2;
      const radius = 0.72 + (i % 3) * 0.07;
      const speed = 0.6 + (i % 5) * 0.25;
      const height = ((i % 7) - 3) * 0.012;

      this.clearingNodeAngles[i] = angle;
      this.clearingNodeRadii[i] = radius;
      this.clearingNodeSpeeds[i] = speed;
      this.clearingNodeHeights[i] = height;

      this.dummyObj.position.set(Math.cos(angle) * radius, height, Math.sin(angle) * radius);
      this.dummyObj.updateMatrix();
      this.clearingInstancedNodes.setMatrixAt(i, this.dummyObj.matrix);
    }
    this.clearingInstancedNodes.instanceMatrix.needsUpdate = true;
    this.engineTier2.add(this.clearingInstancedNodes);
    this.enterpriseEngineGroup.add(this.engineTier2);

    // 7. Tier 3: Inner Generative Neural Core
    this.engineTier3 = new THREE.Group();
    this.engineTier3.name = 'EngineTier3';
    const latticeGeo = new THREE.IcosahedronGeometry(0.40, 2);
    if (latticeGeo.attributes.position) {
      this.coreOriginalPositions = new Float32Array(latticeGeo.attributes.position.array);
    }
    const latticeMat = new THREE.MeshPhysicalMaterial({
      color: 0x00f2fe,
      emissive: 0x00334e,
      emissiveIntensity: 0.75,
      roughness: 0.18,
      metalness: 0.85,
      wireframe: true,
      transparent: true,
      opacity: 0.85,
    });
    this.neuralCoreLattice = new THREE.Mesh(latticeGeo, latticeMat);
    this.neuralCoreLattice.name = 'NeuralCoreLattice';
    this.engineTier3.add(this.neuralCoreLattice);

    const nucleusGeo = new THREE.IcosahedronGeometry(0.24, 1);
    const nucleusMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      emissive: 0x00f2fe,
      emissiveIntensity: 2.2,
      roughness: 0.15,
      metalness: 0.85,
    });
    this.neuralCoreInner = new THREE.Mesh(nucleusGeo, nucleusMat);
    this.neuralCoreInner.name = 'NeuralCoreNucleus';
    this.engineTier3.add(this.neuralCoreInner);
    this.enterpriseEngineGroup.add(this.engineTier3);

    // 8. Executive Strategy Studio Props
    this.studioGroup = new THREE.Group();
    this.studioGroup.name = 'StudioGroup';

    this.curvedDisplaysGroup = new THREE.Group();
    this.curvedDisplaysGroup.name = 'CurvedDisplays';
    const displayMat = new THREE.MeshStandardMaterial({ color: 0x111827, metalness: 0.8, roughness: 0.2 });
    const screenMesh = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, 0.7, 32, 1, true, 0, Math.PI * 0.4), displayMat);
    screenMesh.rotation.y = -Math.PI * 0.2;
    screenMesh.position.set(0, 0.35, 1.2);
    this.curvedDisplaysGroup.add(screenMesh);
    this.studioGroup.add(this.curvedDisplaysGroup);

    this.executiveDesk = new THREE.Group();
    this.executiveDesk.name = 'ExecutiveDesk';
    const deskTop = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.08, 0.9), displayMat);
    deskTop.position.set(0, -0.1, 0.9);
    this.executiveDesk.add(deskTop);
    this.studioGroup.add(this.executiveDesk);

    this.executiveTablet = new THREE.Group();
    this.executiveTablet.name = 'ExecutiveTablet';
    const tabletMesh = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.01, 0.20), new THREE.MeshBasicMaterial({ color: 0x00f2fe, wireframe: true }));
    tabletMesh.position.set(0.35, -0.05, 0.75);
    this.executiveTablet.add(tabletMesh);
    this.studioGroup.add(this.executiveTablet);

    // Executive Lounge Chair (Eames / Modern Architectural aesthetic)
    this.executiveChair = new THREE.Group();
    this.executiveChair.name = 'ExecutiveChair';
    this.executiveChair.position.set(0, -1.45, -0.05);

    const leatherMat = new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.65, metalness: 0.1 });
    const woodShellMat = new THREE.MeshStandardMaterial({ color: 0x271c19, roughness: 0.4, metalness: 0.2 });
    const steelMat = new THREE.MeshStandardMaterial({ color: 0x71717a, roughness: 0.2, metalness: 0.9 });

    const seatCushion = new THREE.Mesh(new THREE.BoxGeometry(0.70, 0.12, 0.65), leatherMat);
    seatCushion.position.set(0, 0.45, 0);
    this.executiveChair.add(seatCushion);

    const seatShell = new THREE.Mesh(new THREE.BoxGeometry(0.74, 0.06, 0.69), woodShellMat);
    seatShell.position.set(0, 0.38, 0);
    this.executiveChair.add(seatShell);

    const backCushion = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.65, 0.12), leatherMat);
    backCushion.position.set(0, 0.85, -0.30);
    backCushion.rotation.x = -0.15;
    this.executiveChair.add(backCushion);

    const backShell = new THREE.Mesh(new THREE.BoxGeometry(0.69, 0.69, 0.06), woodShellMat);
    backShell.position.set(0, 0.85, -0.36);
    backShell.rotation.x = -0.15;
    this.executiveChair.add(backShell);

    const chairStem = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.35, 16), steelMat);
    chairStem.position.set(0, 0.18, 0);
    this.executiveChair.add(chairStem);

    const chairBase = new THREE.Mesh(new THREE.CylinderGeometry(0.40, 0.40, 0.04, 32), steelMat);
    chairBase.position.set(0, 0.02, 0);
    this.executiveChair.add(chairBase);

    this.studioGroup.add(this.executiveChair);

    // Blueprint Explode Architectural CAD Guide Rods & Tier Locator Rings aligned to (-1.07, -0.21, -0.12)
    this.blueprintGuidesGroup = new THREE.Group();
    this.blueprintGuidesGroup.name = 'BlueprintExplodeGuides';
    this.blueprintGuidesGroup.position.set(-1.07, -0.21, -0.12);
    this.blueprintGuidesGroup.visible = false;

    this.blueprintGuideMat = new THREE.MeshBasicMaterial({
      color: 0xd4b483,
      transparent: true,
      opacity: 0.0,
    });
    const rodGeo = new THREE.CylinderGeometry(0.0032, 0.0032, 0.86, 8);
    for (let r = 0; r < 4; r++) {
      const ang = 0.3927 + (r * Math.PI) / 2;
      const rod = new THREE.Mesh(rodGeo, this.blueprintGuideMat);
      rod.name = `BlueprintGuideRod_${r}`;
      rod.position.set(Math.cos(ang) * 0.515, 0.06, Math.sin(ang) * 0.515);
      this.blueprintGuidesGroup.add(rod);
    }

    this.blueprintTierRingMat = new THREE.MeshBasicMaterial({
      color: 0xe2e8f0,
      transparent: true,
      opacity: 0.0,
    });
    const ringRadii = [0.50, 0.515, 0.525];
    for (let t = 0; t < 3; t++) {
      const ringGeo = new THREE.TorusGeometry(ringRadii[t] ?? 0.51, 0.0038, 8, 64);
      const ring = new THREE.Mesh(ringGeo, this.blueprintTierRingMat);
      ring.name = `BlueprintTierLocatorRing_${t}`;
      ring.rotation.x = Math.PI / 2;
      ring.position.y = -0.36 + t * 0.36;
      this.blueprintTierRings.push(ring);
      this.blueprintGuidesGroup.add(ring);
    }
    const corePrismGeo = new THREE.OctahedronGeometry(0.075, 0);
    const corePrismMat = new THREE.MeshBasicMaterial({
      color: 0xd4b483,
      transparent: true,
      opacity: 0.0,
      wireframe: true,
    });
    const corePrism = new THREE.Mesh(corePrismGeo, corePrismMat);
    corePrism.name = 'BlueprintExplodeCorePrism';
    corePrism.visible = false;
    corePrism.position.y = 0.0;
    this.blueprintGuidesGroup.add(corePrism);
    this.studioGroup.add(this.blueprintGuidesGroup);

    // 9. Right-Flank Titanium Executive Dossier Monolith & Holographic Brief Console (Pin 03: executive-dossier)
    const dossierGroup = new THREE.Group();
    dossierGroup.name = 'ExecutiveDossierMonolith';
    dossierGroup.position.set(0.60, -1.31, 0.02);

    const dossierDarkTiMat = new THREE.MeshStandardMaterial({
      color: 0x181c24,
      metalness: 0.90,
      roughness: 0.24,
      envMap: this.studioEnvMap,
      envMapIntensity: 1.25,
    });
    const dossierNaturalTiMat = new THREE.MeshStandardMaterial({
      color: 0x7c828d,
      metalness: 0.94,
      roughness: 0.18,
      envMap: this.studioEnvMap,
      envMapIntensity: 1.25,
    });
    const dossierBrassMat = new THREE.MeshStandardMaterial({
      color: 0xd4b483,
      metalness: 0.94,
      roughness: 0.18,
      emissive: 0x5c4726,
      emissiveIntensity: 0.25,
      envMap: this.studioEnvMap,
      envMapIntensity: 1.25,
    });
    this.dossierMetallicMats.push(dossierDarkTiMat, dossierNaturalTiMat, dossierBrassMat);

    const dPlinthGeo = new THREE.CylinderGeometry(0.24, 0.27, 0.06, 8);
    const dPlinthCollarGeo = new THREE.CylinderGeometry(0.19, 0.21, 0.025, 8);
    const dShaftGeo = new THREE.CylinderGeometry(0.11, 0.145, 0.78, 8);
    const dRibGeo = new THREE.BoxGeometry(0.018, 0.72, 0.022);
    const dNeckGeo = new THREE.CylinderGeometry(0.135, 0.135, 0.025, 8);
    const dCapGeo = new THREE.CylinderGeometry(0.16, 0.135, 0.05, 8);
    const dBezelGeo = new THREE.BoxGeometry(0.50, 0.34, 0.018);
    const dScreenGeo = new THREE.PlaneGeometry(0.46, 0.30);
    const dHaloGeo = new THREE.TorusGeometry(0.175, 0.0045, 12, 48);
    this.disposableGeos.push(
      dPlinthGeo,
      dPlinthCollarGeo,
      dShaftGeo,
      dRibGeo,
      dNeckGeo,
      dCapGeo,
      dBezelGeo,
      dScreenGeo,
      dHaloGeo
    );

    const dPlinth = new THREE.Mesh(dPlinthGeo, dossierDarkTiMat);
    dPlinth.position.y = 0.03;
    dPlinth.castShadow = true;
    dPlinth.receiveShadow = true;

    const dCollar = new THREE.Mesh(dPlinthCollarGeo, dossierBrassMat);
    dCollar.position.y = 0.072;

    const dShaft = new THREE.Mesh(dShaftGeo, dossierDarkTiMat);
    dShaft.position.y = 0.47;
    dShaft.castShadow = true;

    for (let r = 0; r < 8; r++) {
      const rAng = (r / 8) * Math.PI * 2;
      const rib = new THREE.Mesh(dRibGeo, dossierNaturalTiMat);
      rib.position.set(Math.sin(rAng) * 0.132, 0.47, Math.cos(rAng) * 0.132);
      rib.rotation.y = rAng;
      rib.castShadow = true;
      dossierGroup.add(rib);
    }

    const dNeck = new THREE.Mesh(dNeckGeo, dossierBrassMat);
    dNeck.position.y = 0.87;

    const dCap = new THREE.Mesh(dCapGeo, dossierDarkTiMat);
    dCap.position.y = 0.905;

    let dTex: THREE.CanvasTexture | null = null;
    if (typeof document !== 'undefined') {
      try {
        const dCanvas = document.createElement('canvas');
        dCanvas.width = 256;
        dCanvas.height = 160;
        const dCtx = dCanvas.getContext('2d');
        if (dCtx) {
          const grad = dCtx.createLinearGradient(0, 0, 256, 160);
          grad.addColorStop(0.0, '#0f1218');
          grad.addColorStop(1.0, '#1a1612');
          dCtx.fillStyle = grad;
          dCtx.fillRect(0, 0, 256, 160);

          dCtx.strokeStyle = '#d4b483';
          dCtx.lineWidth = 3;
          dCtx.strokeRect(6, 6, 244, 148);
          dCtx.strokeStyle = 'rgba(212, 180, 131, 0.35)';
          dCtx.lineWidth = 1;
          dCtx.strokeRect(12, 12, 232, 136);

          dCtx.fillStyle = '#e5c997';
          dCtx.font = 'bold 13px sans-serif';
          dCtx.fillText('FOUNDER & C-SUITE BRIEF', 20, 32);

          dCtx.fillStyle = 'rgba(212, 180, 131, 0.55)';
          dCtx.fillRect(20, 40, 216, 1.5);

          dCtx.fillStyle = '#f8fafc';
          dCtx.font = 'bold 11px sans-serif';
          dCtx.fillText('1ST PLACE HILTI GLOBAL', 20, 62);
          dCtx.fillStyle = '#d4b483';
          dCtx.font = 'bold 10px sans-serif';
          dCtx.fillText('FIRST-CLASS HONOURS 3.89', 20, 80);

          // Architectural metric telemetry bars
          const bars = [
            { y: 98, w: 184, color: '#d4b483' },
            { y: 114, w: 152, color: '#94a3b8' },
            { y: 130, w: 202, color: '#e2c799' },
          ];
          for (const b of bars) {
            dCtx.fillStyle = 'rgba(255, 255, 255, 0.10)';
            dCtx.fillRect(20, b.y, 216, 7);
            dCtx.fillStyle = b.color;
            dCtx.fillRect(20, b.y, b.w, 7);
          }
          dTex = new THREE.CanvasTexture(dCanvas);
          dTex.colorSpace = THREE.SRGBColorSpace;
          this.executiveDossierTex = dTex;
        }
      } catch {
        // JSDOM headless fallback
      }
    }

    const dScreenMat = new THREE.MeshStandardMaterial({
      color: dTex ? 0xffffff : 0x16181f,
      map: dTex,
      emissive: 0xd4b483,
      emissiveMap: dTex,
      emissiveIntensity: dTex ? 0.62 : 0.35,
      roughness: 0.18,
      metalness: 0.25,
    });

    const consolePivot = new THREE.Group();
    consolePivot.name = 'ExecutiveDossierConsole';
    consolePivot.position.set(0, 0.96, 0.02);
    consolePivot.rotation.set(-0.28, -0.24, 0, 'YXZ');

    const dBezel = new THREE.Mesh(dBezelGeo, dossierBrassMat);
    dBezel.position.z = -0.012;
    const dScreen = new THREE.Mesh(dScreenGeo, dScreenMat);
    dScreen.name = 'ExecutiveDossierScreen';
    consolePivot.add(dBezel, dScreen);

    const dHaloMat = new THREE.MeshBasicMaterial({
      color: 0xd4b483,
      transparent: true,
      opacity: 0.52,
    });
    const dHalo = new THREE.Mesh(dHaloGeo, dHaloMat);
    dHalo.name = 'ExecutiveDossierHalo';
    dHalo.rotation.x = Math.PI / 2;
    dHalo.position.set(0, 0.875, 0.0);
    this.executiveDossierHalo = dHalo;

    dossierGroup.add(dPlinth, dCollar, dShaft, dNeck, dCap, consolePivot, dHalo);
    const dossierTag = {
      type: 'subTargetProp',
      actIndex: 0,
      subTargetId: 'executive-dossier',
    };
    dossierGroup.traverse((obj) => {
      obj.userData = { ...dossierTag };
    });
    this.executiveDossierGroup = dossierGroup;
    this.studioGroup.add(dossierGroup);

    this.avatarRig.add(this.studioGroup);

    // Register Act 1 materials for cross-fading
    options.materialsList.push(
      this.blueprintGuideMat,
      this.blueprintTierRingMat,
      corePrismMat,
      this.plinthMat,
      this.plinthGlowMat,
      vectorMat,
      shieldGlassMat,
      rimSpecularMat,
      titaniumMat,
      ringAMat,
      ringBMat,
      nodeMat,
      latticeMat,
      nucleusMat,
      displayMat,
      dossierDarkTiMat,
      dossierNaturalTiMat,
      dossierBrassMat,
      dScreenMat,
      dHaloMat
    );

    if (typeof window !== 'undefined') {
      this.loadStudioGLB(assetUrl('models/props/act1_studio.glb')).catch(() => {});
    }
  }

  public setStudioEnvMap(envMap: THREE.Texture | null): void {
    this.studioEnvMap = envMap;
    for (const mat of this.dossierMetallicMats) {
      mat.envMap = envMap;
      mat.envMapIntensity = 1.25;
      mat.needsUpdate = true;
    }
    if (this.studioGlbRoot) {
      this.applyAtelierPbrToRoot(this.studioGlbRoot);
    }
  }

  public setCoreFocusHighlight(active: boolean): void {
    this.coreFocusBoost = active;
  }

  private applyAtelierPbrToRoot(root: THREE.Object3D): void {
    this.filamentGlowMats = [];
    root.traverse((child) => {
      if (!(child as THREE.Mesh).isMesh) return;
      const mesh = child as THREE.Mesh;
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      const nextMaterials = materials.map((mat) => {
        if (!mat) return mat;
        if (mat.name === 'Mat_Act1_OpticalGlass') {
          if (mat instanceof THREE.MeshPhysicalMaterial && mat.transmission > 0.5) {
            mat.envMap = this.studioEnvMap;
            mat.envMapIntensity = 1.65;
            mat.needsUpdate = true;
            return mat;
          }
          const physMat = new THREE.MeshPhysicalMaterial({
            name: 'Mat_Act1_OpticalGlass',
            color: new THREE.Color(0xdce8f8),
            transmission: 0.88,
            ior: 1.54,
            thickness: 0.55,
            roughness: 0.05,
            metalness: 0.04,
            clearcoat: 1.0,
            clearcoatRoughness: 0.04,
            transparent: true,
            opacity: 1.0,
            envMap: this.studioEnvMap,
            envMapIntensity: 1.65,
          });
          mat.dispose();
          mesh.castShadow = false;
          return physMat;
        }
        const stdMat = mat as THREE.MeshStandardMaterial;
        if (mat.name === 'Mat_Act1_WarmCove') {
          stdMat.emissiveIntensity = 1.65;
          this.filamentGlowMats.push(stdMat);
        } else if (mat.name === 'Mat_Act1_ObsidianBasalt') {
          stdMat.envMap = this.studioEnvMap;
          stdMat.envMapIntensity = 0.65;
        } else {
          stdMat.envMap = this.studioEnvMap;
          stdMat.envMapIntensity = 1.25;
        }
        stdMat.needsUpdate = true;
        return stdMat;
      });
      mesh.material = Array.isArray(mesh.material) ? nextMaterials : nextMaterials[0]!;
    });
  }

  public async loadStudioGLB(url: string = assetUrl('models/props/act1_studio.glb')): Promise<void> {
    if (typeof window === 'undefined') return;
    try {
      const resolvedUrl = resolveAssetUrl(url);
      const loader = await createGltfLoader();
      loader.load(
        resolvedUrl,
        (gltf) => {
          const root = gltf.scene;
          root.name = 'Act1StudioGLB';
          root.position.set(-0.52, -1.45, -0.02);
          this.studioGlbRoot = root;

          // Hide legacy placeholder primitives and procedural sci-fi gyro clutter once architectural Blender GLB kit is mounted
          this.curvedDisplaysGroup.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.executiveDesk.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.executiveTablet.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.executiveChair.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });
          this.enterpriseEngineGroup.traverse((c) => {
            if ((c as THREE.Mesh).isMesh) c.visible = false;
          });

          // Tuck legacy procedural plinth & cyan glow ring geometry inside the SM_Island_Act1 stone slab
          this.plinthMesh.geometry.scale(0.001, 0.001, 0.001);
          this.plinthGlowRing.geometry.scale(0.001, 0.001, 0.001);

          // Co-locate EnterpriseAIEngine above the side-staged SM_Strategy_Table so center stage stays clear
          this.enterpriseEngineGroup.position.set(-1.30, -0.18, 0.05);
          this.enterpriseEngineGroup.scale.set(0.42, 0.42, 0.42);

          root.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
            }
            if (child.name.startsWith('Prop_Blueprint_Tier')) {
              const tag = {
                type: 'subTargetProp',
                actIndex: 0,
                subTargetId: 'strategy-table',
              };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            } else if (
              child.name === 'SM_Core_Nucleus' ||
              child.name === 'SM_Core_Filament' ||
              child.name.startsWith('SM_Gyro_Gimbal')
            ) {
              const tag = {
                type: 'subTargetProp',
                actIndex: 0,
                subTargetId: 'optical-core',
              };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            } else if (
              child.name === 'SM_Island_Act1' ||
              child.name === 'SM_Atelier_Pedestal'
            ) {
              const tag = {
                type: 'subTargetProp',
                actIndex: 0,
                subTargetId: 'executive-dossier',
              };
              child.traverse((sub) => {
                sub.userData = { ...tag };
              });
            }
          });

          this.applyAtelierPbrToRoot(root);

          const t1 = root.getObjectByName('Prop_Blueprint_Tier1') ?? null;
          const t2 = root.getObjectByName('Prop_Blueprint_Tier2') ?? null;
          const t3 = root.getObjectByName('Prop_Blueprint_Tier3') ?? null;
          const coreNucleus = root.getObjectByName('SM_Core_Nucleus') ?? null;
          const coreFilament = root.getObjectByName('SM_Core_Filament') ?? null;
          const gimbalOuter = root.getObjectByName('SM_Gyro_Gimbal_Outer') ?? null;
          const gimbalInner = root.getObjectByName('SM_Gyro_Gimbal_Inner') ?? null;

          // Group all floating orbital/tier pieces around their true local axis (-0.55, 0, -0.10)
          // so interactive drag orbital rotation stays coaxial above SM_Atelier_Pedestal
          const sculpturePivot = new THREE.Group();
          sculpturePivot.name = 'AtelierSculpturePivot';
          sculpturePivot.position.set(-0.55, 0, -0.10);
          root.add(sculpturePivot);
          for (const part of [t1, t2, t3, coreNucleus, coreFilament, gimbalOuter, gimbalInner]) {
            if (!part) continue;
            part.position.x = 0;
            part.position.z = 0;
            sculpturePivot.add(part);
          }

          if (gimbalOuter) {
            gimbalOuter.rotation.set(0.44, 0.32, -0.24);
          }
          if (gimbalInner) {
            gimbalInner.rotation.set(-0.58, -0.42, 0.34);
          }

          this.glbBlueprintTiers = {
            tier1: t1,
            tier2: t2,
            tier3: t3,
            coreNucleus,
            coreFilament,
            gimbalOuter,
            gimbalInner,
            sculpturePivot,
            baseY1: t1 ? t1.position.y : 1.60,
            baseY2: t2 ? t2.position.y : 1.24,
            baseY3: t3 ? t3.position.y : 0.88,
            baseYNucleus: coreNucleus ? coreNucleus.position.y : 1.24,
            baseYFilament: coreFilament ? coreFilament.position.y : 1.24,
          };

          this.studioGroup.add(root);
          this.onModelLoaded?.();
        },
        undefined,
        () => {}
      );
    } catch {
      // Ignore in headless/JSDOM environments
    }
  }

  public getPlinth(): THREE.Mesh { return this.plinthMesh; }
  public getPlinthGlowRing(): THREE.Mesh { return this.plinthGlowRing; }
  public getEnterpriseAIEngine(): THREE.Group { return this.enterpriseEngineGroup; }
  public getEngineTier1(): THREE.Group { return this.engineTier1; }
  public getEngineTier2(): THREE.Group { return this.engineTier2; }
  public getEngineTier3(): THREE.Group { return this.engineTier3; }
  public getEngineVectorsGroup(): THREE.Group { return this.engineVectorsGroup; }
  public getStudioGroup(): THREE.Group { return this.studioGroup; }
  public getCurvedDisplays(): THREE.Group { return this.curvedDisplaysGroup; }
  public getExecutiveChair(): THREE.Group { return this.executiveChair; }
  public getExecutiveDesk(): THREE.Group { return this.executiveDesk; }
  public getExecutiveTablet(): THREE.Group { return this.executiveTablet; }
  public getExecutiveDossierMonolith(): THREE.Group | null { return this.executiveDossierGroup; }

  public isEngineExplodedState(): boolean {
    return this.isEngineExploded;
  }

  public toggleExplode(): boolean {
    this.isEngineExploded = !this.isEngineExploded;
    return this.isEngineExploded;
  }

  public setExploded(exploded: boolean): void {
    this.isEngineExploded = exploded;
  }

  public onPointerDown(clientX: number, clientY: number): void {
    this.isDragging = true;
    this.prevMouseX = clientX;
    this.prevMouseY = clientY;
  }

  public onPointerMove(clientX: number, clientY: number): void {
    if (!this.isDragging) return;
    const dx = clientX - this.prevMouseX;
    const dy = clientY - this.prevMouseY;
    this.prevMouseX = clientX;
    this.prevMouseY = clientY;

    this.rotVelY = dx * 0.006;
    this.rotVelX = dy * 0.006;

    this.dragAngleY += this.rotVelY;
    this.dragAngleX += this.rotVelX;
  }

  public onPointerUp(): void {
    this.isDragging = false;
  }

  public update(delta: number, isReducedMotion: boolean = false, scrollProgress: number = 0): void {
    const sp = Number.isFinite(scrollProgress) ? Math.max(0, scrollProgress) : 0;
    this.studioGroup.visible = sp <= 0.16;
    if (this.studioGlbRoot) {
      this.studioGlbRoot.visible = sp <= 0.16;
    }
    this.enterpriseEngineGroup.visible = sp <= 0.16;

    // Plinth and Glow Ring Transition across Acts:
    // Scale down and fade out when leaving Act 1 (sp > 0.16), and restore when returning to Act 1
    const plinthTransitionEnd = 0.22;
    let plinthFactor = 1.0;
    if (sp > 0.16) {
      const exitProgress = Math.min(1.0, (sp - 0.16) / (plinthTransitionEnd - 0.16));
      plinthFactor = Math.max(0.0, 1.0 - exitProgress);
    }

    this.plinthMesh.scale.set(plinthFactor, plinthFactor, plinthFactor);
    this.plinthGlowRing.scale.set(plinthFactor, plinthFactor, plinthFactor);
    this.plinthMat.opacity = plinthFactor;
    this.plinthGlowMat.opacity = 0.95 * plinthFactor;
    this.plinthMesh.visible = plinthFactor > 0.001;
    this.plinthGlowRing.visible = plinthFactor > 0.001;

    const clampedDelta = Math.min(delta, 0.1);
    if (!isReducedMotion) {
      this.atelierAnimTime += clampedDelta;
    }

    // 1. Spring-damped Strata Explosion Dynamics
    const targetFactor = this.isEngineExploded ? 1.0 : 0.0;
    this.currentExplodeFactor = isReducedMotion
      ? targetFactor
      : THREE.MathUtils.damp(this.currentExplodeFactor, targetFactor, 8.0, clampedDelta);

    // Vertical displacement
    const tier1Displacement = this.currentExplodeFactor * 0.95;
    const tier3Displacement = -this.currentExplodeFactor * 0.85;

    this.engineTier1.position.y = tier1Displacement;
    this.engineTier3.position.y = tier3Displacement;

    // Animate Sovereign Titanium Atelier GLB sculpture (strata separation, horological gimbals & core crystal)
    const ex = this.currentExplodeFactor;
    const tAnim = this.atelierAnimTime;
    const bobOffset = isReducedMotion ? 0 : Math.sin(tAnim * 1.35) * 0.016;
    if (this.glbBlueprintTiers.tier1) {
      this.glbBlueprintTiers.tier1.position.y =
        this.glbBlueprintTiers.baseY1 + ex * 0.32 + bobOffset * 0.5;
      this.glbBlueprintTiers.tier1.rotation.y = ex * 0.24;
    }
    if (this.glbBlueprintTiers.tier2) {
      this.glbBlueprintTiers.tier2.position.y =
        this.glbBlueprintTiers.baseY2 + ex * 0.01 + bobOffset * 0.35;
      this.glbBlueprintTiers.tier2.rotation.y = -ex * 0.18;
    }
    if (this.glbBlueprintTiers.tier3) {
      this.glbBlueprintTiers.tier3.position.y =
        this.glbBlueprintTiers.baseY3 - ex * 0.155 + bobOffset * 0.25;
      this.glbBlueprintTiers.tier3.rotation.y = ex * 0.12;
    }
    if (this.glbBlueprintTiers.coreNucleus) {
      const nucScale = 1.0 + ex * 0.14 + (this.coreFocusBoost ? 0.06 : 0.0);
      this.glbBlueprintTiers.coreNucleus.position.y = this.glbBlueprintTiers.baseYNucleus + bobOffset;
      this.glbBlueprintTiers.coreNucleus.scale.setScalar(nucScale);
      this.glbBlueprintTiers.coreNucleus.rotation.y = isReducedMotion ? 0.35 : tAnim * 0.22;
    }
    if (this.glbBlueprintTiers.coreFilament) {
      const filScale = 1.0 + ex * 0.14 + (this.coreFocusBoost ? 0.08 : 0.0);
      this.glbBlueprintTiers.coreFilament.position.y = this.glbBlueprintTiers.baseYFilament + bobOffset;
      this.glbBlueprintTiers.coreFilament.scale.setScalar(filScale);
      this.glbBlueprintTiers.coreFilament.rotation.y = isReducedMotion ? -0.35 : -tAnim * 0.45;
    }
    if (this.glbBlueprintTiers.gimbalOuter) {
      if (isReducedMotion) {
        this.glbBlueprintTiers.gimbalOuter.rotation.set(0.44, 0.32, -0.24);
      } else {
        this.glbBlueprintTiers.gimbalOuter.rotation.set(
          0.44 + Math.sin(tAnim * 0.35) * 0.06,
          0.32 + tAnim * 0.38,
          -0.24
        );
      }
    }
    if (this.glbBlueprintTiers.gimbalInner) {
      if (isReducedMotion) {
        this.glbBlueprintTiers.gimbalInner.rotation.set(-0.58, -0.42, 0.34);
      } else {
        this.glbBlueprintTiers.gimbalInner.rotation.set(
          -0.58 + Math.cos(tAnim * 0.42) * 0.06,
          -0.42 - tAnim * 0.52,
          0.34
        );
      }
    }
    if (this.executiveDossierHalo) {
      if (isReducedMotion) {
        this.executiveDossierHalo.rotation.z = 0.25;
      } else {
        this.executiveDossierHalo.rotation.z += clampedDelta * 0.48;
      }
    }
    for (const mat of this.filamentGlowMats) {
      const targetGlow = this.coreFocusBoost ? 2.45 : 1.65 + ex * 0.45;
      mat.emissiveIntensity = THREE.MathUtils.damp(mat.emissiveIntensity, targetGlow, 6.0, clampedDelta);
    }

    if (this.blueprintGuidesGroup && this.blueprintGuideMat && this.blueprintTierRingMat) {
      this.blueprintGuidesGroup.visible = ex > 0.015;
      this.blueprintGuideMat.opacity = Math.min(0.55, ex * 0.62);
      this.blueprintTierRingMat.opacity = Math.min(0.68, ex * 0.72);
      this.blueprintGuidesGroup.children.forEach((child) => {
        if (child.name.startsWith('BlueprintGuideRod_')) {
          const hScale = Math.max(0.20, 0.25 + ex * 0.85);
          child.scale.y = hScale;
          child.position.y = 0.06;
        }
      });
      const tierOffsets = [-0.36 - ex * 0.155, 0.0 + ex * 0.01, 0.36 + ex * 0.32];
      this.blueprintTierRings.forEach((ring, idx) => {
        ring.position.y = tierOffsets[idx] ?? 0;
        const rScale = 0.96 + ex * 0.08;
        ring.scale.set(rScale, rScale, 1);
      });
    }

    // Expand connection vectors
    const vectorScaleY = 0.15 + this.currentExplodeFactor * 1.65;
    for (const vector of this.engineVectors) {
      vector.scale.y = vectorScaleY;
      (vector.material as THREE.MeshBasicMaterial).opacity = 0.35 + this.currentExplodeFactor * 0.55;
    }

    // 2. Drag & Inertia Dynamics
    if (!this.isDragging) {
      this.rotVelX *= 0.96;
      this.rotVelY *= 0.96;
      this.dragAngleX += this.rotVelX;
      this.dragAngleY += this.rotVelY;
    }
    this.enterpriseEngineGroup.rotation.x = this.dragAngleX;
    this.enterpriseEngineGroup.rotation.y = this.dragAngleY;
    if (this.glbBlueprintTiers.sculpturePivot) {
      this.glbBlueprintTiers.sculpturePivot.rotation.y = this.dragAngleY;
      this.glbBlueprintTiers.sculpturePivot.rotation.x = THREE.MathUtils.clamp(this.dragAngleX * 0.25, -0.22, 0.22);
    }

    // 3. Counter-rotating rings & Gyro Motion (culled when hidden or replaced by Act1StudioGLB)
    if (this.enterpriseEngineGroup.visible && !this.studioGlbRoot && !isReducedMotion) {
      this.clearingRingA.rotation.z += 0.45 * clampedDelta;
      this.clearingRingB.rotation.z -= 0.55 * clampedDelta;
      this.engineTier1.rotation.y += 0.22 * clampedDelta;

      // Pulse Nucleus heartbeat
      const heartBeat = 1.0 + Math.sin(Date.now() * 0.004) * 0.18;
      this.neuralCoreInner.scale.set(heartBeat, heartBeat, heartBeat);

      // Animate Outer Neural Core Lattice with Vertex Noise Morphing
      if (this.neuralCoreLattice && this.coreOriginalPositions) {
        const geo = this.neuralCoreLattice.geometry;
        const posAttr = geo.attributes.position;
        if (posAttr) {
          const orig = this.coreOriginalPositions;
          const timeFactor = Date.now() * 0.003;
          for (let i = 0; i < posAttr.count; i++) {
            const i3 = i * 3;
            const ox = orig[i3 + 0] ?? 0;
            const oy = orig[i3 + 1] ?? 0;
            const oz = orig[i3 + 2] ?? 0;
            const displacement = Math.sin(timeFactor + ox * 5.0 + oy * 5.0) * 0.035;
            posAttr.setXYZ(i, ox + ox * displacement, oy + oy * displacement, oz + oz * displacement);
          }
          posAttr.needsUpdate = true;
        }
      }

      // Animate 96 Instanced Nodes
      const dummy = this.dummyObj;
      for (let i = 0; i < 96; i++) {
        const speed = this.clearingNodeSpeeds[i] ?? 1.0;
        const curAngle = (this.clearingNodeAngles[i] ?? 0) + speed * clampedDelta;
        this.clearingNodeAngles[i] = curAngle;
        const r = this.clearingNodeRadii[i] ?? 0.8;
        const h = this.clearingNodeHeights[i] ?? 0;

        dummy.position.set(Math.cos(curAngle) * r, h, Math.sin(curAngle) * r);
        dummy.updateMatrix();
        this.clearingInstancedNodes.setMatrixAt(i, dummy.matrix);
      }
      this.clearingInstancedNodes.instanceMatrix.needsUpdate = true;
    }
  }

  public dispose(): void {
    this.filamentGlowMats = [];
    this.dossierMetallicMats = [];
    this.studioEnvMap = null;
    for (const geo of this.disposableGeos) {
      geo.dispose();
    }
    this.disposableGeos = [];
    if (this.executiveDossierTex) {
      this.executiveDossierTex.dispose();
      this.executiveDossierTex = null;
    }
    this.executiveDossierGroup = null;
    this.executiveDossierHalo = null;
  }
}
