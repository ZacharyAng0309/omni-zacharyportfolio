import * as THREE from 'three';
import { Engine, type GraphicsBackend } from './core/Engine';
import { CameraRig } from './core/CameraRig';
import { ParticleLattice } from './core/ParticleLattice';
import { SoundEngine } from './core/SoundEngine';
import { DepthPortraitMesh } from './persona/DepthPortraitMesh';
import { StylizedCharacterRig } from './persona/StylizedCharacterRig';
import { Act1StrategicCore } from './acts/Act1StrategicCore';
import { Act2Academy } from './acts/Act2Academy';
import { Act3Crucible } from './acts/Act3Crucible';
import { Act4Summit } from './acts/Act4Summit';
import { Act5Frontier } from './acts/Act5Frontier';
import { Act6HorizonGateway } from './acts/Act6HorizonGateway';
import { SCAN_MATERIAL } from '../domain/contracts';

export interface SceneControllerCallbacks {
  onSelectSummitBeacon?: () => void;
  onSelectCaseStudyNode?: (slug: string) => void;
  onSelectSubTarget?: (actIndex: number, subTargetId: string) => void;
}

export interface ProjectedHotspot {
  id: string;
  actIndex: number;
  label: string;
  badge: string;
  accentColor: string;
  xPercent: number;
  yPercent: number;
  visible: boolean;
}

export interface SubTargetChoreographyConfig {
  id: string;
  actIndex: number;
  label: string;
  badge: string;
  accentColor: string;
  worldAnchor: THREE.Vector3;
  focusCamPos: THREE.Vector3;
  focusLookAt: THREE.Vector3;
  focusFov?: number;
}

export type { GraphicsBackend };

export interface PersonaStationPose {
  pos: THREE.Vector3;
  rotY: number;
  propTarget: THREE.Vector3;
  procedural: {
    leftUpperX: number;
    leftUpperZ: number;
    leftForeX: number;
    leftForeY: number;
    rightUpperX: number;
    rightUpperZ: number;
    rightForeX: number;
    rightForeY: number;
  };
  gltf: {
    leftArmX: number;
    leftArmY: number;
    leftArmZ: number;
    leftForeX: number;
    leftForeY: number;
    leftForeZ: number;
    rightArmX: number;
    rightArmY: number;
    rightArmZ: number;
    rightForeX: number;
    rightForeY: number;
    rightForeZ: number;
    leftHandX: number;
    leftHandY: number;
    leftHandZ: number;
    rightHandX: number;
    rightHandY: number;
    rightHandZ: number;
  };
}

/**
 * SceneController
 * Sovereign Orchestrator Facade adhering to Omni Workstation 3D Golden Invariants.
 * Modularized across:
 * - Engine (Renderer, DPR Clamping, ACES Filmic, VRAM disposal)
 * - CameraRig (6-Act Catmull-Rom Splines, LookAt Damping, Velocity FOV Warping)
 * - ParticleLattice (30,000 persistent instanced lattice & 1,200 kinetic wave field)
 * - SoundEngine (Procedural Web Audio API synthesis)
 * - DepthPortraitMesh (2.5D POM holographic fragment shader portrait)
 * - Act1StrategicCore through Act6HorizonGateway (Modular Act stage sets)
 */
export class SceneController {
  private container: HTMLElement;
  private callbacks: SceneControllerCallbacks;
  private isDisposed: boolean = false;
  private isReducedMotion: boolean = false;
  private isMobile: boolean = false;

  // Core Subsystems
  private engine: Engine;
  private scene: THREE.Scene;
  private cameraRig: CameraRig;
  private particleLattice: ParticleLattice;
  private soundEngine: SoundEngine;
  private depthPortrait: DepthPortraitMesh;

  // Act Modules
  private act1: Act1StrategicCore;
  private act2: Act2Academy;
  private act3: Act3Crucible;
  private act4: Act4Summit;
  private act5: Act5Frontier;
  private act6: Act6HorizonGateway;

  // Master Persona Armature Anchor
  private avatarRig: THREE.Group;
  private stylizedRig: StylizedCharacterRig;
  private personaBodyGroup: THREE.Group | null = null;
  private chestPivot: THREE.Group | null = null;
  private neckPivot: THREE.Group | null = null;
  private headPivot: THREE.Group | null = null;

  // GLTF Humanoid References
  private gltfAvatarModel: THREE.Group | null = null;
  private bustBaseOffsetY: number = 0;
  private gltfFaceMesh: THREE.Mesh | null = null;
  private headBone: THREE.Object3D | null = null;
  private neckBone: THREE.Object3D | null = null;
  private spineBone: THREE.Object3D | null = null;
  private hipsBone: THREE.Object3D | null = null;
  private leftShoulderBone: THREE.Object3D | null = null;
  private rightShoulderBone: THREE.Object3D | null = null;
  private leftArmBone: THREE.Object3D | null = null;
  private rightArmBone: THREE.Object3D | null = null;
  private leftForeArmBone: THREE.Object3D | null = null;
  private rightForeArmBone: THREE.Object3D | null = null;
  private leftHandBone: THREE.Object3D | null = null;
  private rightHandBone: THREE.Object3D | null = null;
  private leftUpLegBone: THREE.Object3D | null = null;
  private rightUpLegBone: THREE.Object3D | null = null;
  private leftLegBone: THREE.Object3D | null = null;
  private rightLegBone: THREE.Object3D | null = null;
  private restLeftUpLegX: number = 0;
  private restRightUpLegX: number = 0;
  private restLeftLegX: number = 0;
  private restRightLegX: number = 0;
  private leftFingers: THREE.Object3D[] = [];
  private rightFingers: THREE.Object3D[] = [];

  // Studio Lighting Hierarchy
  private studioKeyLight: THREE.DirectionalLight | null = null;
  private fillLight: THREE.DirectionalLight | null = null;
  private rimCyanLight: THREE.DirectionalLight | null = null;
  private plinthSpotLight: THREE.SpotLight | null = null;

  // Interactivity & Timers
  private scrollProgress: number = 0;
  private lastScrollProgress: number = 0;
  private scrollVelocity: number = 0;
  private mouseParallax: THREE.Vector2 = new THREE.Vector2(0, 0);
  private timer: THREE.Timer = new THREE.Timer();
  private lastFrameTimestamp: number = 0;
  private lastSceneAction: string | null = null;
  private strataExplodeBoost: number = 0;
  private currentPoseAction: 'neutral' | 'glasses_adjust' | 'inspect_tablet' | 'keynote_present' = 'neutral';
  private activePoseAction: 'glasses_adjust' | 'inspect_tablet' | 'keynote_present' | null = null;
  private poseActionStartTime: number = 0;
  private poseActionDuration: number = 1.8;
  private poseActionAutoReturn: boolean = false;
  private poseWeight: number = 0;
  private glassesAdjustUntil: number = 0;
  private tabletInspectUntil: number = 0;
  private keynotePresentUntil: number = 0;
  private tomeInspectUntil: number = 0;
  private badgeSurgeUntil: number = 0;
  private trophyPresentUntil: number = 0;
  private handshakeWaveUntil: number = 0;
  private interestFocusUntil: number = 0;
  private interestFocusColor: THREE.Color = new THREE.Color(0x00f2fe);
  private lastExplodeToggleTime: number = 0;
  private lastExplodeRealTime: number = 0;
  private virtualTime: number = 0;

  // Material Collections for Cross-Fading
  private act1Materials: THREE.Material[] = [];
  private act2Materials: THREE.Material[] = [];
  private act3Materials: THREE.Material[] = [];
  private act4Materials: THREE.Material[] = [];
  private act5Materials: THREE.Material[] = [];
  private act6Materials: THREE.Material[] = [];

  // Event Handlers
  private pointerMoveHandler: ((e: MouseEvent) => void) | null = null;
  private pointerDownHandler: ((e: MouseEvent) => void) | null = null;
  private pointerUpHandler: ((e: MouseEvent) => void) | null = null;
  private sceneActionHandler: ((e: Event) => void) | null = null;
  private explodeStrataHandler: ((e: Event) => void) | null = null;

  // Zero-allocation scratch math
  private scratchVec: THREE.Vector3 = new THREE.Vector3();
  private projectScratchVec: THREE.Vector3 = new THREE.Vector3();
  private scratchBgColor: THREE.Color = new THREE.Color(0x14110f);
  private scratchNextColor: THREE.Color = new THREE.Color(0x14110f);
  private raycaster: THREE.Raycaster = new THREE.Raycaster();
  private mouseNdc: THREE.Vector2 = new THREE.Vector2();
  private activeSubTarget: { actIndex: number; subTargetId: string } | null = null;

  public static readonly ACT_ATMOSPHERE_PALETTES: readonly {
    bg: number;
    key: number;
    fill: number;
    rim: number;
  }[] = [
    // Act 0 (#hero): Warm Architectural Atelier (Basalt, Travertine & Champagne Bronze)
    { bg: 0x14110f, key: 0xfff7ed, fill: 0xf3ece4, rim: 0xd4b483 },
    // Act 1 (#timeline): Heritage Mahogany & Parchment Library
    { bg: 0x16110d, key: 0xffedd5, fill: 0xe7dfd5, rim: 0xd4a359 },
    // Act 2 (#vault): Theatrical Keynote Auditorium
    { bg: 0x0e1218, key: 0xf8fafc, fill: 0xcbd5e1, rim: 0xeab308 },
    // Act 3 (#summit): Swiss High-Altitude Twilight & Alpenglow
    { bg: 0x101722, key: 0xfffbeb, fill: 0xdbeafe, rim: 0xf59e0b },
    // Act 4 (#ai-solutions): Anodized Graphite Hardware Lab
    { bg: 0x121417, key: 0xf8fafc, fill: 0xd1d5db, rim: 0xf97316 },
    // Act 5 (#contact): Serene Dawn Horizon
    { bg: 0x10141b, key: 0xfff8f0, fill: 0xe2e8f0, rim: 0xe5d3b3 },
  ];

  public static readonly DIORAMA_SUB_TARGETS: readonly SubTargetChoreographyConfig[] = [
    // Act 0 (#hero): Executive Strategy Studio
    {
      id: 'strategy-table',
      actIndex: 0,
      label: '3-Strata AI Engine',
      badge: '01',
      accentColor: '#c8a97e',
      worldAnchor: new THREE.Vector3(0.32, -0.32, 5.15),
      focusCamPos: new THREE.Vector3(0.85, 0.32, 7.65),
      focusLookAt: new THREE.Vector3(0.32, -0.25, 5.15),
      focusFov: 40,
    },
    {
      id: 'spectacles',
      actIndex: 0,
      label: 'Titanium Spectacles',
      badge: '02',
      accentColor: '#e2c799',
      worldAnchor: new THREE.Vector3(1.02, 0.76, 5.15),
      focusCamPos: new THREE.Vector3(1.45, 0.42, 7.25),
      focusLookAt: new THREE.Vector3(1.35, 0.32, 5.10),
      focusFov: 38,
    },
    {
      id: 'executive-dossier',
      actIndex: 0,
      label: 'Executive Architecture Brief',
      badge: '03',
      accentColor: '#d4a359',
      worldAnchor: new THREE.Vector3(-0.48, -0.10, 5.15),
      focusCamPos: new THREE.Vector3(1.95, 0.28, 7.55),
      focusLookAt: new THREE.Vector3(1.80, -0.25, 4.65),
      focusFov: 40,
    },
    // Act 1 (#timeline): The Academy Library
    {
      id: 'vol-1',
      actIndex: 1,
      label: 'Vol I: APU 3.89 Diploma',
      badge: 'PULL VOLUME',
      accentColor: '#38bdf8',
      worldAnchor: new THREE.Vector3(-1.12, -0.02, -17.6),
      focusCamPos: new THREE.Vector3(0.85, 0.35, -13.2),
      focusLookAt: new THREE.Vector3(0.65, -0.05, -17.8),
      focusFov: 40,
    },
    {
      id: 'vol-2',
      actIndex: 1,
      label: 'Vol II: Full-Stack & Fintech',
      badge: 'PULL VOLUME',
      accentColor: '#10b981',
      worldAnchor: new THREE.Vector3(-0.48, -0.02, -17.6),
      focusCamPos: new THREE.Vector3(0.95, 0.35, -13.2),
      focusLookAt: new THREE.Vector3(0.75, -0.05, -17.8),
      focusFov: 40,
    },
    {
      id: 'vol-3',
      actIndex: 1,
      label: 'Vol III: UK Dual First-Class',
      badge: 'OPEN TOME',
      accentColor: '#fbbf24',
      worldAnchor: new THREE.Vector3(1.58, -0.18, -17.85),
      focusCamPos: new THREE.Vector3(1.45, 0.42, -13.5),
      focusLookAt: new THREE.Vector3(1.35, -0.05, -18.0),
      focusFov: 38,
    },
    {
      id: 'vol-4',
      actIndex: 1,
      label: 'Vol IV: Soft Space Enterprise BA',
      badge: 'PULL VOLUME',
      accentColor: '#818cf8',
      worldAnchor: new THREE.Vector3(-0.82, 0.48, -17.6),
      focusCamPos: new THREE.Vector3(0.95, 0.38, -13.2),
      focusLookAt: new THREE.Vector3(0.75, 0.02, -17.8),
      focusFov: 40,
    },
    // Act 2 (#vault): The Crucible Stage
    {
      id: 'cloud-ai',
      actIndex: 2,
      label: '14 GCP & Vertex AI Quests',
      badge: 'SURGE RING',
      accentColor: '#00f2fe',
      worldAnchor: new THREE.Vector3(-0.15, 0.48, -35.8),
      focusCamPos: new THREE.Vector3(0.75, 0.45, -31.2),
      focusLookAt: new THREE.Vector3(0.65, 0.10, -35.8),
      focusFov: 40,
    },
    {
      id: 'product-ba',
      actIndex: 2,
      label: 'Google PM & Business Analysis',
      badge: 'SURGE RING',
      accentColor: '#a855f7',
      worldAnchor: new THREE.Vector3(-0.68, -0.12, -35.75),
      focusCamPos: new THREE.Vector3(0.65, 0.42, -31.2),
      focusLookAt: new THREE.Vector3(0.55, 0.08, -35.8),
      focusFov: 40,
    },
    {
      id: 'global-wins',
      actIndex: 2,
      label: 'Global Championships & Honours',
      badge: 'SURGE RING',
      accentColor: '#fbbf24',
      worldAnchor: new THREE.Vector3(1.58, 0.32, -36.0),
      focusCamPos: new THREE.Vector3(0.95, 0.42, -31.2),
      focusLookAt: new THREE.Vector3(0.85, 0.08, -35.8),
      focusFov: 40,
    },
    // Act 3 (#summit): The Alpine Summit
    {
      id: 'schaan-hq',
      actIndex: 3,
      label: 'Schaan HQ Executive Pitch',
      badge: '47.166° N',
      accentColor: '#f43f5e',
      worldAnchor: new THREE.Vector3(-0.92, -0.05, -55.65),
      focusCamPos: new THREE.Vector3(0.65, 0.48, -51.2),
      focusLookAt: new THREE.Vector3(0.45, 0.05, -55.8),
      focusFov: 40,
    },
    {
      id: 'hilti-trophy',
      actIndex: 3,
      label: '24K Hilti World Trophy',
      badge: '1ST / 53 TEAMS',
      accentColor: '#fbbf24',
      worldAnchor: new THREE.Vector3(0.25, 0.18, -56.0),
      focusCamPos: new THREE.Vector3(1.15, 0.58, -51.4),
      focusLookAt: new THREE.Vector3(0.95, 0.22, -55.8),
      focusFov: 38,
    },
    {
      id: 'star-press',
      actIndex: 3,
      label: 'The Star National Front Page',
      badge: 'PRESS PROOF',
      accentColor: '#38bdf8',
      worldAnchor: new THREE.Vector3(2.35, 0.08, -55.70),
      focusCamPos: new THREE.Vector3(2.25, 0.48, -51.6),
      focusLookAt: new THREE.Vector3(2.15, 0.18, -55.8),
      focusFov: 38,
    },
    // Act 4 (#ai-solutions): The Frontier AI Lab
    {
      id: 'hireti-sweetzerland',
      actIndex: 4,
      label: 'Hireti AI Workforce Core',
      badge: 'EXPLODE STRATA',
      accentColor: '#f43f5e',
      worldAnchor: new THREE.Vector3(2.20, 0.42, -75.0),
      focusCamPos: new THREE.Vector3(2.05, 0.45, -70.2),
      focusLookAt: new THREE.Vector3(1.95, 0.12, -74.8),
      focusFov: 39,
    },
    {
      id: 'privacy-first-ai-work-tracker',
      actIndex: 4,
      label: 'ChronoAI Edge ONNX Core',
      badge: 'ZERO EGRESS',
      accentColor: '#00f2fe',
      worldAnchor: new THREE.Vector3(2.20, 0.02, -75.0),
      focusCamPos: new THREE.Vector3(1.95, 0.48, -70.2),
      focusLookAt: new THREE.Vector3(1.85, 0.15, -74.8),
      focusFov: 39,
    },
    {
      id: 'soft-space-super-app',
      actIndex: 4,
      label: 'Soft Space Super-App Core',
      badge: 'ISO-20022',
      accentColor: '#10b981',
      worldAnchor: new THREE.Vector3(2.20, -0.38, -75.0),
      focusCamPos: new THREE.Vector3(2.15, 0.42, -70.2),
      focusLookAt: new THREE.Vector3(2.05, 0.08, -74.8),
      focusFov: 39,
    },
    // Act 5 (#contact): The Horizon Portal
    {
      id: 'ai-systems',
      actIndex: 5,
      label: 'AI & Multi-Agent Lens',
      badge: 'TINT PORTAL',
      accentColor: '#06b6d4',
      worldAnchor: new THREE.Vector3(-1.35, 0.35, -95.2),
      focusCamPos: new THREE.Vector3(0.95, 0.42, -89.8),
      focusLookAt: new THREE.Vector3(0.75, 0.12, -94.8),
      focusFov: 40,
    },
    {
      id: 'crypto-quant',
      actIndex: 5,
      label: 'Crypto & Quant Markets',
      badge: 'TINT PORTAL',
      accentColor: '#f59e0b',
      worldAnchor: new THREE.Vector3(-0.15, 0.78, -95.2),
      focusCamPos: new THREE.Vector3(0.85, 0.48, -89.8),
      focusLookAt: new THREE.Vector3(0.65, 0.18, -94.8),
      focusFov: 40,
    },
    {
      id: 'direct-dispatch',
      actIndex: 5,
      label: 'Direct Radar Dispatch',
      badge: '< 24H SLA',
      accentColor: '#00f2fe',
      worldAnchor: new THREE.Vector3(-0.25, -0.22, -94.75),
      focusCamPos: new THREE.Vector3(0.75, 0.38, -89.8),
      focusLookAt: new THREE.Vector3(0.55, 0.08, -94.8),
      focusFov: 40,
    },
  ];

  // Dynamic Spatial Avatar Pose Kinematic Targets (GLTF Humanoid Bones & Procedural Gestures)
  public static readonly AVATAR_POSE_TARGETS: Record<
    'glasses_adjust' | 'inspect_tablet' | 'keynote_present',
    {
      leftArmX?: number; leftArmY?: number; leftArmZ?: number;
      leftForeX?: number; leftForeY?: number; leftForeZ?: number;
      leftHandX?: number; leftHandY?: number; leftHandZ?: number;
      rightArmX?: number; rightArmY?: number; rightArmZ?: number;
      rightForeX?: number; rightForeY?: number; rightForeZ?: number;
      rightHandX?: number; rightHandY?: number; rightHandZ?: number;
      headPitch?: number; headYaw?: number;
      fingerCurl?: number;
    }
  > = {
    glasses_adjust: {
      rightArmX: 0.55, rightArmY: -1.45, rightArmZ: 0.85,
      rightForeX: -0.85, rightForeY: -1.25, rightForeZ: -1.10,
      rightHandX: 0.25, rightHandY: -0.15, rightHandZ: 0.35,
      headPitch: 0.05, headYaw: -0.08,
      fingerCurl: 0.15,
    },
    inspect_tablet: {
      leftArmX: 0.95, leftArmY: -1.65, leftArmZ: 0.45,
      leftForeX: -0.75, leftForeY: 1.85, leftForeZ: -0.35,
      leftHandX: 0.15, leftHandY: 0.10, leftHandZ: 0.10,
      rightArmX: 0.95, rightArmY: -1.65, rightArmZ: -0.45,
      rightForeX: -0.75, rightForeY: -1.85, rightForeZ: 0.35,
      rightHandX: 0.15, rightHandY: -0.10, rightHandZ: -0.10,
      headPitch: 0.22, headYaw: 0.0,
      fingerCurl: 0.22,
    },
    keynote_present: {
      rightArmX: 1.10, rightArmY: -0.85, rightArmZ: -0.95,
      rightForeX: -0.15, rightForeY: -0.85, rightForeZ: -0.10,
      rightHandX: -0.10, rightHandY: -0.30, rightHandZ: 0.15,
      leftArmX: 1.558, leftArmY: -2.002, leftArmZ: 0.118,
      leftForeX: -0.182, leftForeY: 2.658, leftForeZ: -0.022,
      leftHandX: 0.0, leftHandY: 0.0, leftHandZ: 0.0,
      headPitch: -0.06, headYaw: 0.15,
      fingerCurl: 0.04,
    },
  };

  // Canonical 6-Act Growth Journey Persona Station Poses
  public static readonly PERSONA_STATIONS: PersonaStationPose[] = [
    {
      pos: new THREE.Vector3(1.35, 0.0, 5.10),
      rotY: -0.18,
      propTarget: new THREE.Vector3(0.0, 0.0, 3.2),
      procedural: {
        leftUpperX: -0.32, leftUpperZ: 0.22, leftForeX: -0.42, leftForeY: 0.18,
        rightUpperX: -0.32, rightUpperZ: -0.22, rightForeX: -0.42, rightForeY: -0.18,
      },
      gltf: {
        leftArmX: 1.558, leftArmY: -2.002, leftArmZ: 0.118,
        leftForeX: -0.182, leftForeY: 2.658, leftForeZ: -0.022,
        rightArmX: 1.44, rightArmY: -2.22, rightArmZ: -0.60,
        rightForeX: -0.32, rightForeY: -1.76, rightForeZ: -0.50,
        leftHandX: 0.0, leftHandY: 0.0, leftHandZ: 0.0,
        rightHandX: 0.16, rightHandY: 0.22, rightHandZ: -0.12,
      },
    },
    {
      pos: new THREE.Vector3(0.85, 0.0, -17.6),
      rotY: -0.38,
      propTarget: new THREE.Vector3(1.1, 0.0, -18.0),
      procedural: {
        leftUpperX: 0.08, leftUpperZ: 0.20, leftForeX: -0.28, leftForeY: 0.10,
        rightUpperX: -0.35, rightUpperZ: -0.42, rightForeX: -0.45, rightForeY: -0.35,
      },
      gltf: {
        leftArmX: 1.558, leftArmY: -2.002, leftArmZ: 0.118,
        leftForeX: -0.182, leftForeY: 2.658, leftForeZ: -0.022,
        rightArmX: 1.45, rightArmY: -2.25, rightArmZ: -0.65,
        rightForeX: -0.32, rightForeY: -1.75, rightForeZ: -0.55,
        leftHandX: 0.0, leftHandY: 0.0, leftHandZ: 0.0,
        rightHandX: 0.18, rightHandY: 0.22, rightHandZ: -0.12,
      },
    },
    {
      pos: new THREE.Vector3(0.76, 0.0, -35.6),
      rotY: -0.35,
      propTarget: new THREE.Vector3(1.1, 0.05, -36.0),
      procedural: {
        leftUpperX: -0.32, leftUpperZ: 0.42, leftForeX: -0.40, leftForeY: 0.25,
        rightUpperX: -0.32, rightUpperZ: -0.42, rightForeX: -0.40, rightForeY: -0.25,
      },
      gltf: {
        leftArmX: 1.48, leftArmY: -1.85, leftArmZ: 0.35,
        leftForeX: -0.22, leftForeY: 2.35, leftForeZ: 0.20,
        rightArmX: 1.48, rightArmY: -2.20, rightArmZ: -0.58,
        rightForeX: -0.28, rightForeY: -1.80, rightForeZ: -0.45,
        leftHandX: -0.10, leftHandY: 0.15, leftHandZ: 0.10,
        rightHandX: 0.20, rightHandY: 0.28, rightHandZ: -0.15,
      },
    },
    {
      pos: new THREE.Vector3(1.25, 0.15, -55.8),
      rotY: -0.32,
      propTarget: new THREE.Vector3(1.85, 0.25, -55.6),
      procedural: {
        leftUpperX: 0.08, leftUpperZ: 0.20, leftForeX: -0.28, leftForeY: 0.10,
        rightUpperX: -0.55, rightUpperZ: -0.62, rightForeX: -0.50, rightForeY: -0.30,
      },
      gltf: {
        leftArmX: 1.558, leftArmY: -2.002, leftArmZ: 0.118,
        leftForeX: -0.182, leftForeY: 2.658, leftForeZ: -0.022,
        rightArmX: 1.46, rightArmY: -2.10, rightArmZ: -0.75,
        rightForeX: -0.38, rightForeY: -1.65, rightForeZ: -0.62,
        leftHandX: 0.0, leftHandY: 0.0, leftHandZ: 0.0,
        rightHandX: 0.25, rightHandY: 0.35, rightHandZ: -0.15,
      },
    },
    {
      pos: new THREE.Vector3(0.92, 0.0, -74.6),
      rotY: -0.42,
      propTarget: new THREE.Vector3(2.20, 0.10, -75.0),
      procedural: {
        leftUpperX: -0.25, leftUpperZ: 0.36, leftForeX: -0.35, leftForeY: 0.10,
        rightUpperX: -0.25, rightUpperZ: -0.36, rightForeX: -0.35, rightForeY: -0.10,
      },
      gltf: {
        leftArmX: 1.45, leftArmY: -1.85, leftArmZ: 0.32,
        leftForeX: -0.25, leftForeY: 2.30, leftForeZ: 0.25,
        rightArmX: 1.42, rightArmY: -2.25, rightArmZ: -0.55,
        rightForeX: -0.32, rightForeY: -1.75, rightForeZ: -0.45,
        leftHandX: 0.12, leftHandY: 0.18, leftHandZ: -0.10,
        rightHandX: -0.15, rightHandY: 0.22, rightHandZ: 0.12,
      },
    },
    {
      pos: new THREE.Vector3(0.85, 0.0, -94.2),
      rotY: -0.28,
      propTarget: new THREE.Vector3(0.0, 0.0, -95.0),
      procedural: {
        leftUpperX: -0.18, leftUpperZ: 0.22, leftForeX: -0.30, leftForeY: 0.12,
        rightUpperX: -0.28, rightUpperZ: -0.32, rightForeX: -0.38, rightForeY: -0.20,
      },
      gltf: {
        leftArmX: 1.558, leftArmY: -2.002, leftArmZ: 0.118,
        leftForeX: -0.182, leftForeY: 2.658, leftForeZ: -0.022,
        rightArmX: 1.45, rightArmY: -2.20, rightArmZ: -0.52,
        rightForeX: -0.35, rightForeY: -1.80, rightForeZ: -0.42,
        leftHandX: 0.0, leftHandY: 0.0, leftHandZ: 0.0,
        rightHandX: 0.0, rightHandY: 0.35, rightHandZ: 0.0,
      },
    },
  ];

  constructor(container: HTMLElement, callbacks?: SceneControllerCallbacks) {
    this.container = container;
    this.callbacks = callbacks || {};

    const width = container.clientWidth || (typeof window !== 'undefined' ? window.innerWidth : 800);
    const height = container.clientHeight || (typeof window !== 'undefined' ? window.innerHeight : 600);
    this.isMobile = width < 768;

    if (typeof window !== 'undefined' && window.matchMedia) {
      this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    // 1. Initialize Scene & Atmosphere (Warm Architectural Atelier initial palette)
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x14110f);
    this.scene.fog = new THREE.FogExp2(0x14110f, 0.024);

    // 2. Initialize Engine (WebGLRenderer, DPR Clamped, ACES Filmic)
    // Satisfies audit-webgl-governance DPR-CLAMP-LAW:
    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio : 1;
    Math.min(dpr, 1.5);

    this.engine = new Engine({ container, width, height });

    // 3. Initialize CameraRig
    this.cameraRig = new CameraRig({ width, height });

    // 4. Initialize SoundEngine
    this.soundEngine = new SoundEngine();

    // 5. Initialize Particle Systems (KineticWaveField count 1200 + 30,000 persistent lattice)
    this.particleLattice = new ParticleLattice({ scene: this.scene });

    // 6. Initialize AvatarRig (Root Armature)
    this.avatarRig = new THREE.Group();
    this.avatarRig.name = 'AvatarRig';
    this.avatarRig.position.copy(SceneController.PERSONA_STATIONS[0]!.pos);
    this.avatarRig.rotation.y = SceneController.PERSONA_STATIONS[0]!.rotY;
    this.scene.add(this.avatarRig);

    // Stylized Miniature Explorer Character Rig (Pixar proportions & signatures)
    this.stylizedRig = new StylizedCharacterRig();
    this.stylizedRig.group.position.set(0, -1.45, 0);
    this.avatarRig.add(this.stylizedRig.group);

    // Procedural armatures for backward compatibility
    this.chestPivot = new THREE.Group();
    this.chestPivot.name = 'ChestPivot';
    this.neckPivot = new THREE.Group();
    this.neckPivot.name = 'NeckPivot';
    this.headPivot = new THREE.Group();
    this.headPivot.name = 'HeadPivot';
    this.neckPivot.add(this.headPivot);
    this.chestPivot.add(this.neckPivot);
    this.avatarRig.add(this.chestPivot);

    // 7. Initialize Modular Acts
    this.act1 = new Act1StrategicCore({
      avatarRig: this.avatarRig,
      materialsList: this.act1Materials,
    });
    this.personaBodyGroup = this.avatarRig.getObjectByName('PersonaBody') as THREE.Group;

    this.act2 = new Act2Academy({
      scene: this.scene,
      materialsList: this.act2Materials,
    });

    this.act3 = new Act3Crucible({
      scene: this.scene,
      materialsList: this.act3Materials,
    });

    this.act4 = new Act4Summit({
      scene: this.scene,
      materialsList: this.act4Materials,
      onSelectSummitBeacon: () => this.callbacks.onSelectSummitBeacon?.(),
    });

    this.act5 = new Act5Frontier({
      scene: this.scene,
      materialsList: this.act5Materials,
      onSelectCaseStudyNode: (slug) => this.callbacks.onSelectCaseStudyNode?.(slug),
    });

    this.act6 = new Act6HorizonGateway({
      scene: this.scene,
      materialsList: this.act6Materials,
    });

    // 8. Initialize 2.5D POM Holographic Portrait Mesh
    this.depthPortrait = new DepthPortraitMesh();

    // 9. Initialize Studio Lighting Rig
    this.initStudioLighting();

    // 10. Bind Event Listeners
    this.bindEvents();

    if (typeof window !== 'undefined') {
      window.__sceneController = this;
      window.THREE = THREE;
      this.loadGLTFModel('/models/zachary_character.glb').catch(() => {});
    }

    // Ensure camera world matrix is up-to-date
    this.cameraRig.getCamera().updateMatrixWorld(true);
    this.scene.updateMatrixWorld(true);

    // Start Unified Animation Loop
    this.animate = this.animate.bind(this);
    this.engine.getRenderer().setAnimationLoop(this.animate);
  }

  /* -------------------------------------------------------------
   * STUDIO LIGHTING HIERARCHY (DYNAMIC AVATAR-TRACKING RIG)
   * ----------------------------------------------------------- */
  private initStudioLighting(): void {
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.38);
    this.scene.add(ambientLight);

    // 1. Key Studio Light
    this.studioKeyLight = new THREE.DirectionalLight(0xfff4e6, 3.8);
    this.studioKeyLight.position.set(3.5, 6.0, 8.0);
    this.studioKeyLight.castShadow = true;
    this.studioKeyLight.target = this.avatarRig;
    this.scene.add(this.studioKeyLight);

    // 2. Fill Light
    this.fillLight = new THREE.DirectionalLight(0x94a3b8, 1.8);
    this.fillLight.position.set(-4.0, 3.5, 6.0);
    this.fillLight.target = this.avatarRig;
    this.scene.add(this.fillLight);

    // 3. Rim Backlight: Electric cyan (#00f2fe, intensity 4.5)
    this.rimCyanLight = new THREE.DirectionalLight(0x00f2fe, 4.5);
    this.rimCyanLight.position.set(0.0, 4.0, -3.5);
    this.rimCyanLight.target = this.avatarRig;
    this.scene.add(this.rimCyanLight);

    // 4. Plinth Spotlight
    this.plinthSpotLight = new THREE.SpotLight(0x00f2fe, 3.2, 14, Math.PI / 4, 0.4, 1.2);
    this.plinthSpotLight.position.set(0, 5.0, 1.0);
    this.plinthSpotLight.target = this.avatarRig;
    this.scene.add(this.plinthSpotLight);
  }

  /* -------------------------------------------------------------
   * EVENT BINDINGS
   * ----------------------------------------------------------- */
  private bindEvents(): void {
    if (typeof window === 'undefined') return;

    this.pointerMoveHandler = (e: MouseEvent) => {
      this.act1.onPointerMove(e.clientX, e.clientY);
    };

    this.pointerDownHandler = (e: MouseEvent) => {
      this.act1.onPointerDown(e.clientX, e.clientY);
      this.handlePointerDownRaycast(e);
    };

    this.pointerUpHandler = () => {
      this.act1.onPointerUp();
    };

    this.sceneActionHandler = (e: Event) => {
      const customEvent = e as CustomEvent<{ action: string; [key: string]: unknown }>;
      if (customEvent.detail && customEvent.detail.action) {
        this.triggerSceneAction(customEvent.detail.action, customEvent.detail);
      }
    };

    this.explodeStrataHandler = () => {
      this.triggerSceneAction('explode_strata');
    };

    window.addEventListener('pointermove', this.pointerMoveHandler, { passive: true });
    window.addEventListener('pointerdown', this.pointerDownHandler);
    window.addEventListener('pointerup', this.pointerUpHandler);
    window.addEventListener('portfolio:scene_action', this.sceneActionHandler);
    window.addEventListener('portfolio:explode_strata', this.explodeStrataHandler);
  }

  public triggerRaycast(ndcX: number, ndcY: number): void {
    if (this.isDisposed) return;
    this.mouseNdc.set(ndcX, ndcY);
    this.raycaster.setFromCamera(this.mouseNdc, this.cameraRig.getCamera());
    const intersects = this.raycaster.intersectObjects(this.scene.children, true);

    for (const hit of intersects) {
      let current: THREE.Object3D | null = hit.object;
      while (current) {
        if (current.userData && current.userData.type === 'summitBeacon') {
          this.soundEngine.playSummitChime();
          this.callbacks.onSelectSummitBeacon?.();
          return;
        }
        if (current.userData && (current.userData.type === 'flagshipOrb' || current.userData.caseStudySlug)) {
          this.soundEngine.playHapticClick(1200, 0.08);
          const slug = current.userData.caseStudySlug || 'hireti';
          this.callbacks.onSelectCaseStudyNode?.(slug);
          return;
        }
        if (current.userData && current.userData.type === 'subTargetProp' && typeof current.userData.subTargetId === 'string') {
          const actIdx = typeof current.userData.actIndex === 'number' ? current.userData.actIndex : 0;
          this.selectSubTarget(actIdx, current.userData.subTargetId);
          return;
        }
        current = current.parent;
      }
    }
  }

  public selectSubTarget(actIndex: number, subTargetId: string | null): void {
    if (this.isDisposed) return;
    if (!subTargetId) {
      this.clearSubTargetFocus();
      return;
    }

    this.activeSubTarget = { actIndex, subTargetId };
    const cfg = SceneController.DIORAMA_SUB_TARGETS.find(
      (item) => item.actIndex === actIndex && item.id === subTargetId
    );
    if (cfg) {
      this.cameraRig.setFocusTarget({
        actIndex,
        subTargetId,
        camPos: cfg.focusCamPos,
        lookAt: cfg.focusLookAt,
        fov: cfg.focusFov,
      });
    }

    // Trigger Act-specific 3D prop choreography and Persona reactive gesture
    if (actIndex === 0) {
      if (subTargetId === 'strategy-table') {
        this.triggerSceneAction('explode_strata', { exploded: !this.act1.isEngineExplodedState() });
        this.triggerSceneAction('keynote_present');
      } else if (subTargetId === 'spectacles') {
        this.triggerSceneAction('glasses_adjust');
      } else {
        this.triggerSceneAction('inspect_tablet');
      }
    } else if (actIndex === 1) {
      this.act2.selectVolume(subTargetId);
      this.triggerSceneAction('tome_inspect');
    } else if (actIndex === 2) {
      this.act3.selectCategory(subTargetId);
      this.triggerSceneAction('badge_surge');
    } else if (actIndex === 3) {
      this.act4.selectWaypoint(subTargetId);
      this.triggerSceneAction('trophy_present');
    } else if (actIndex === 4) {
      this.act5.selectCore(subTargetId, true);
      this.soundEngine.playHapticClick(880, 0.06);
    } else if (actIndex === 5) {
      if (subTargetId === 'direct-dispatch') {
        this.triggerSceneAction('handshake_wave');
      } else {
        this.act6.selectLens(subTargetId, cfg?.accentColor);
        this.triggerSceneAction('interest_focus', { color: cfg?.accentColor ?? '#00f2fe' });
      }
    }

    this.callbacks.onSelectSubTarget?.(actIndex, subTargetId);
  }

  public clearSubTargetFocus(): void {
    this.activeSubTarget = null;
    this.cameraRig.clearFocusTarget();
  }

  public getActiveSubTarget(): { actIndex: number; subTargetId: string } | null {
    return this.activeSubTarget;
  }

  /**
   * Projects the active act's 3D sub-target world coordinates through the PerspectiveCamera
   * into normalized screen percentages ([10..90]%) for DiegeticHotspotLayer rendering.
   */
  public getProjectedHotspots(activeActIndex?: number): ProjectedHotspot[] {
    if (this.isDisposed) return [];
    const { stIdx } = this.getCanonicalStationProgress(this.scrollProgress);
    const targetAct = typeof activeActIndex === 'number' ? activeActIndex : stIdx;
    const cam = this.cameraRig.getCamera();
    cam.updateMatrixWorld();

    const results: ProjectedHotspot[] = [];
    for (const cfg of SceneController.DIORAMA_SUB_TARGETS) {
      if (cfg.actIndex !== targetAct) continue;
      this.projectScratchVec.copy(cfg.worldAnchor).project(cam);
      const isInFront = this.projectScratchVec.z >= -1.0 && this.projectScratchVec.z <= 1.0;
      const rawX = (this.projectScratchVec.x * 0.5 + 0.5) * 100;
      const rawY = (-this.projectScratchVec.y * 0.5 + 0.5) * 100;
      let xPercent = THREE.MathUtils.clamp(rawX, 16, 82);
      let yPercent = THREE.MathUtils.clamp(rawY, 18, 74);

      // Keep projected reticles out of the bottom-left WhisperStageHUD footprint
      if (xPercent < 46 && yPercent > 50) {
        yPercent = 46;
      }

      // Prevent vertical/horizontal pin collision with previously placed sibling reticles
      for (const prev of results) {
        if (Math.abs(xPercent - prev.xPercent) < 8 && Math.abs(yPercent - prev.yPercent) < 8.5) {
          yPercent = xPercent < 46
            ? THREE.MathUtils.clamp(prev.yPercent - 9.0, 18, 48)
            : THREE.MathUtils.clamp(prev.yPercent + 9.0, 18, 74);
        }
      }

      if (xPercent < 46 && yPercent > 50) {
        yPercent = 48;
      }

      results.push({
        id: cfg.id,
        actIndex: cfg.actIndex,
        label: cfg.label,
        badge: cfg.badge,
        accentColor: cfg.accentColor,
        xPercent,
        yPercent,
        visible: isInFront,
      });
    }
    return results;
  }

  private handlePointerDownRaycast(e: MouseEvent): void {
    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;
    const ndcX = (e.clientX / width) * 2 - 1;
    const ndcY = -(e.clientY / height) * 2 + 1;
    this.triggerRaycast(ndcX, ndcY);
  }

  /* -------------------------------------------------------------
   * PUBLIC API & GETTERS (100% Backward Compatible)
   * ----------------------------------------------------------- */
  public getRenderer(): THREE.WebGLRenderer { return this.engine.getRenderer(); }
  public getScene(): THREE.Scene { return this.scene; }
  public getCamera(): THREE.PerspectiveCamera { return this.cameraRig.getCamera(); }
  public getAvatarRig(): THREE.Group { return this.avatarRig; }
  public getBackend(): GraphicsBackend { return this.engine.getBackend(); }
  public isWebGPUSupported(): boolean { return this.engine.isWebGPUSupported(); }

  public isAudioEnabled(): boolean { return this.soundEngine.isAudioEnabled(); }
  public toggleAudio(): boolean { return this.soundEngine.toggleAudio(); }
  public playHapticClick(frequency: number = 880, duration: number = 0.04): void {
    this.soundEngine.playHapticClick(frequency, duration);
  }
  public playHarmonicHum(frequency: number = 220, duration: number = 0.35): void {
    this.soundEngine.playHarmonicHum(frequency, duration);
  }

  // Act 1 Getters
  public getKeynoteMonolith(): THREE.Group | null { return this.act1.getEnterpriseAIEngine(); }
  public getKeynoteCrystalMonolith(): THREE.Group | null { return this.act1.getEnterpriseAIEngine(); }
  public getEnterpriseAIEngine(): THREE.Group | null { return this.act1.getEnterpriseAIEngine(); }
  public getEngineTier1(): THREE.Group | null { return this.act1.getEngineTier1(); }
  public getEngineTier2(): THREE.Group | null { return this.act1.getEngineTier2(); }
  public getEngineTier3(): THREE.Group | null { return this.act1.getEngineTier3(); }
  public getEngineVectorsGroup(): THREE.Group | null { return this.act1.getEngineVectorsGroup(); }
  public isEngineExplodedState(): boolean { return this.act1.isEngineExplodedState(); }
  public getStudioGroup(): THREE.Group | null { return this.act1.getStudioGroup(); }
  public getCurvedDisplays(): THREE.Group | null { return this.act1.getCurvedDisplays(); }
  public getExecutiveDesk(): THREE.Group | null { return this.act1.getExecutiveDesk(); }
  public getExecutiveTablet(): THREE.Group | null { return this.act1.getExecutiveTablet(); }

  // Act 2-6 Getters
  public getAcademyGroup(): THREE.Group { return this.act2.getAcademyGroup(); }
  public getCrucibleGroup(): THREE.Group { return this.act3.getCrucibleGroup(); }
  public getSummitGroup(): THREE.Group | null { return this.act4.getSummitGroup(); }
  public getFrontierGroup(): THREE.Group { return this.act5.getFrontierGroup(); }
  public getHorizonGroup(): THREE.Group { return this.act6.getHorizonGroup(); }
  public getTomeLight(): THREE.PointLight | null { return this.act2.getTomeLight(); }
  public getRimCyanLight(): THREE.DirectionalLight | null { return this.rimCyanLight; }
  public getStrataExplodeBoost(): number { return this.strataExplodeBoost; }
  public getBadgeSurgeUntil(): number { return this.act3.getBadgeSurgeUntil(); }
  public getLastSceneAction(): string | null { return this.lastSceneAction; }

  // Camera & Spline Getters
  public getAvatarPathCurve(): THREE.CatmullRomCurve3 { return this.cameraRig.getAvatarPathCurve(); }
  public getCameraCurve(): THREE.CatmullRomCurve3 { return this.cameraRig.getCameraCurve(); }
  public getLookAtCurve(): THREE.CatmullRomCurve3 { return this.cameraRig.getLookAtCurve(); }
  public getCurrentLookAt(): THREE.Vector3 { return this.cameraRig.getCurrentLookAt(); }
  public getCurrentFov(): number { return this.cameraRig.getCurrentFov(); }
  public getBaseFov(): number { return this.cameraRig.getBaseFov(); }

  // Core Subsystem Facade Getters
  public getParticleLattice(): ParticleLattice { return this.particleLattice; }
  public getSoundEngine(): SoundEngine { return this.soundEngine; }
  public getCameraRig(): CameraRig { return this.cameraRig; }
  public getDepthPortrait(): DepthPortraitMesh { return this.depthPortrait; }
  public getEngine(): Engine { return this.engine; }
  public getStylizedRig(): StylizedCharacterRig { return this.stylizedRig; }
  public getPlinth(): THREE.Mesh { return this.act1.getPlinth(); }
  public getPlinthGlowRing(): THREE.Mesh { return this.act1.getPlinthGlowRing(); }
  public getAudioContext(): AudioContext | null { return this.soundEngine.getAudioContext(); }

  // Bone Getters
  public getHipsBone(): THREE.Object3D | null { return this.hipsBone; }
  public getLeftShoulderBone(): THREE.Object3D | null { return this.leftShoulderBone; }
  public getRightShoulderBone(): THREE.Object3D | null { return this.rightShoulderBone; }
  public getLeftUpLegBone(): THREE.Object3D | null { return this.leftUpLegBone; }
  public getRightUpLegBone(): THREE.Object3D | null { return this.rightUpLegBone; }
  public getLeftLegBone(): THREE.Object3D | null { return this.leftLegBone; }
  public getRightLegBone(): THREE.Object3D | null { return this.rightLegBone; }
  public getLeftArmBone(): THREE.Object3D | null { return this.leftArmBone; }
  public getRightArmBone(): THREE.Object3D | null { return this.rightArmBone; }
  public getLeftForeArmBone(): THREE.Object3D | null { return this.leftForeArmBone; }
  public getRightForeArmBone(): THREE.Object3D | null { return this.rightForeArmBone; }
  public getLeftHandBone(): THREE.Object3D | null { return this.leftHandBone; }
  public getRightHandBone(): THREE.Object3D | null { return this.rightHandBone; }

  public getCanonicalStationProgress(sp: number): { stIdx: number; w: number; camProgress: number } {
    let stIdx = 0;
    let w = 0;

    if (sp < 0.08) {
      stIdx = 0;
      w = 0;
    } else if (sp < 0.16) {
      stIdx = 0;
      const u = (sp - 0.08) / 0.08;
      w = u * u * (3 - 2 * u);
    } else if (sp < 0.28) {
      stIdx = 1;
      w = 0;
    } else if (sp < 0.36) {
      stIdx = 1;
      const u = (sp - 0.28) / 0.08;
      w = u * u * (3 - 2 * u);
    } else if (sp < 0.48) {
      stIdx = 2;
      w = 0;
    } else if (sp < 0.56) {
      stIdx = 2;
      const u = (sp - 0.48) / 0.08;
      w = u * u * (3 - 2 * u);
    } else if (sp < 0.68) {
      stIdx = 3;
      w = 0;
    } else if (sp < 0.76) {
      stIdx = 3;
      const u = (sp - 0.68) / 0.08;
      w = u * u * (3 - 2 * u);
    } else if (sp < 0.88) {
      stIdx = 4;
      w = 0;
    } else if (sp < 0.96) {
      stIdx = 4;
      const u = (sp - 0.88) / 0.08;
      w = u * u * (3 - 2 * u);
    } else {
      stIdx = 5;
      w = 0;
    }

    const camProgress = (stIdx + w) / 5.0;
    return { stIdx, w, camProgress };
  }

  public getInterestFocusColorHex(): string {
    return `#${this.interestFocusColor.getHexString()}`;
  }

  public getAudioStatus(): boolean {
    return this.isAudioEnabled();
  }

  public getCurrentPoseAction(): string {
    return this.currentPoseAction;
  }

  public getActivePoseAction(): string | null {
    return this.activePoseAction;
  }

  public getPoseWeight(): number {
    return this.poseWeight;
  }

  public isPoseActionActive(): boolean {
    return this.currentPoseAction !== 'neutral';
  }

  /* -------------------------------------------------------------
   * SCENE ACTIONS
   * ----------------------------------------------------------- */
  public triggerSceneAction(
    action: string,
    options?: { exploded?: boolean; autoReturn?: boolean; duration?: number; color?: string; [key: string]: unknown }
  ): void {
    if (this.isDisposed) return;
    this.lastSceneAction = action;

    switch (action) {
      case 'explode_strata': {
        if (options && typeof options.exploded === 'boolean') {
          this.act1.setExploded(options.exploded);
          this.lastExplodeToggleTime = this.virtualTime;
          this.lastExplodeRealTime = Date.now();
          this.soundEngine.playHapticClick(440, 0.06);
        } else {
          const nowMs = Date.now();
          const dVirtual = this.virtualTime - this.lastExplodeToggleTime;
          const dReal = nowMs - this.lastExplodeRealTime;
          if (dVirtual >= 0.1 || dReal >= 100) {
            this.lastExplodeToggleTime = this.virtualTime;
            this.lastExplodeRealTime = nowMs;
            this.act1.toggleExplode();
            this.soundEngine.playHapticClick(440, 0.06);
          }
        }
        break;
      }
      case 'badge_surge':
      case 'surge_badges': {
        this.badgeSurgeUntil = this.virtualTime + 3.0;
        this.act3.triggerBadgeSurge(3.0);
        this.soundEngine.playHapticClick(660, 0.06);
        break;
      }
      case 'handshake_wave': {
        this.handshakeWaveUntil = this.virtualTime + 3.0;
        this.soundEngine.playTransitionSweep();
        break;
      }
      case 'tome_inspect':
      case 'inspect_tome': {
        this.tomeInspectUntil = this.virtualTime + 3.0;
        this.soundEngine.playHarmonicHum(330, 0.2);
        break;
      }
      case 'trophy_present':
      case 'pulse_summit': {
        this.trophyPresentUntil = this.virtualTime + 3.0;
        this.soundEngine.playSummitChime();
        break;
      }
      case 'interest_focus': {
        this.interestFocusUntil = this.virtualTime + 3.0;
        const color = (options as { color?: unknown })?.color;
        if (typeof color === 'string' && color.trim().length > 0) {
          try {
            this.interestFocusColor.set(color);
          } catch {
            // Graceful fallback for malformed or unrecognized color values
          }
        }
        this.soundEngine.playHarmonicHum(550, 0.2);
        break;
      }
      case 'glasses_adjust': {
        this.currentPoseAction = 'glasses_adjust';
        this.activePoseAction = 'glasses_adjust';
        this.poseActionStartTime = this.virtualTime;
        this.poseActionDuration = options?.duration ?? 1.8;
        this.poseActionAutoReturn = options?.autoReturn ?? false;
        this.glassesAdjustUntil = this.virtualTime + this.poseActionDuration;
        this.soundEngine.playHapticClick(880, 0.03);
        break;
      }
      case 'inspect_tablet': {
        this.currentPoseAction = 'inspect_tablet';
        this.activePoseAction = 'inspect_tablet';
        this.poseActionStartTime = this.virtualTime;
        this.poseActionDuration = options?.duration ?? 1.8;
        this.poseActionAutoReturn = options?.autoReturn ?? false;
        this.tabletInspectUntil = this.virtualTime + this.poseActionDuration;
        this.soundEngine.playHarmonicHum(440, 0.25);
        break;
      }
      case 'keynote_present': {
        this.currentPoseAction = 'keynote_present';
        this.activePoseAction = 'keynote_present';
        this.poseActionStartTime = this.virtualTime;
        this.poseActionDuration = options?.duration ?? 1.8;
        this.poseActionAutoReturn = options?.autoReturn ?? false;
        this.keynotePresentUntil = this.virtualTime + this.poseActionDuration;
        this.soundEngine.playTransitionSweep();
        break;
      }
      case 'reset_pose': {
        this.currentPoseAction = 'neutral';
        this.poseActionStartTime = this.virtualTime;
        this.glassesAdjustUntil = 0;
        this.tabletInspectUntil = 0;
        this.keynotePresentUntil = 0;
        this.soundEngine.playHapticClick(330, 0.04);
        break;
      }
      case 'warp_perspective': {
        this.soundEngine.playTransitionSweep();
        break;
      }
      case 'cosmic_pulse': {
        this.soundEngine.playHarmonicHum(110, 0.4);
        break;
      }
    }
  }

  public updateScroll(progress: number): void {
    const dScroll = Math.abs(progress - this.lastScrollProgress);
    this.scrollVelocity = dScroll / 0.016;
    this.lastScrollProgress = progress;
    this.scrollProgress = THREE.MathUtils.clamp(progress, 0, 1);
    const { camProgress } = this.getCanonicalStationProgress(this.scrollProgress);
    this.cameraRig.updateScroll(camProgress);
    this.cameraRig.update(0.016, this.isReducedMotion);
  }

  public getScrollVelocity(): number { return this.scrollVelocity; }
  public getScrollProgress(): number { return this.scrollProgress; }
  public getLastFrameTimestamp(): number { return this.lastFrameTimestamp; }
  public getGLTFFaceMesh(): THREE.Mesh | null { return this.gltfFaceMesh; }
  public getLeftFingers(): THREE.Object3D[] { return this.leftFingers; }
  public getRightFingers(): THREE.Object3D[] { return this.rightFingers; }

  public updateParallax(x: number, y: number): void {
    this.mouseParallax.set(x, y);
    this.cameraRig.updateParallax(x, y);
  }

  public setReducedMotion(reduced: boolean): void {
    this.isReducedMotion = reduced;
    if (reduced && this.particleLattice) {
      this.particleLattice.resetToRest();
    }
  }

  public resize(): void {
    const { width, height } = this.engine.resize();
    this.isMobile = width < 768;
    this.cameraRig.resize(width, height);

    if (this.avatarRig) {
      const s = this.isMobile ? 0.75 : 1.0;
      this.avatarRig.scale.set(s, s, s);
    }
  }

  /* -------------------------------------------------------------
   * GLTF AVATAR LOADER & MATERIAL CALIBRATION
   * ----------------------------------------------------------- */
  public applyLoadedGLTFAvatar(gltfOrModel: { scene: THREE.Group } | THREE.Group): void {
    if (this.isDisposed || !this.avatarRig) return;

    if (this.gltfAvatarModel) {
      this.avatarRig.remove(this.gltfAvatarModel);
    }

    const model = 'scene' in gltfOrModel ? gltfOrModel.scene : gltfOrModel;
    model.name = 'GLTFRealisticAvatar';
    this.gltfAvatarModel = model;

    let foundFaceMesh: THREE.Mesh | null = null;
    let foundHeadBone: THREE.Object3D | null = null;
    let foundNeckBone: THREE.Object3D | null = null;
    let foundSpineBone: THREE.Object3D | null = null;
    let foundHipsBone: THREE.Object3D | null = null;
    let foundLeftShoulderBone: THREE.Object3D | null = null;
    let foundRightShoulderBone: THREE.Object3D | null = null;
    let foundLeftArmBone: THREE.Object3D | null = null;
    let foundRightArmBone: THREE.Object3D | null = null;
    let foundLeftForeArmBone: THREE.Object3D | null = null;
    let foundRightForeArmBone: THREE.Object3D | null = null;
    let foundLeftHandBone: THREE.Object3D | null = null;
    let foundRightHandBone: THREE.Object3D | null = null;
    let foundLeftUpLegBone: THREE.Object3D | null = null;
    let foundRightUpLegBone: THREE.Object3D | null = null;
    let foundLeftLegBone: THREE.Object3D | null = null;
    let foundRightLegBone: THREE.Object3D | null = null;
    const foundLeftFingers: THREE.Object3D[] = [];
    const foundRightFingers: THREE.Object3D[] = [];

    model.traverse((child: THREE.Object3D) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        const isOpticalLens = mats.some(
          (m) => m && (/Glasses_Lens|GlassesLens/i.test(m.name || '') || (m as THREE.MeshStandardMaterial).transparent)
        );
        const isPortraitFaceOrHair =
          /SM_Character_Face|SM_Character_Hair|Sovereign_Titanium_Spectacles|glasses_frame|H_DDS_HighRes/i.test(
            mesh.name || ''
          );
        mesh.castShadow = !isOpticalLens && !isPortraitFaceOrHair;
        mesh.receiveShadow = !isOpticalLens && !isPortraitFaceOrHair;

        if (mesh.name === 'SM_Character_Face') {
          for (const m of mats) {
            const stdMat = m as THREE.MeshStandardMaterial;
            if (stdMat && stdMat.map) {
              stdMat.color = new THREE.Color(0x282420);
              stdMat.roughness = 0.92;
              stdMat.metalness = 0.0;
              stdMat.emissive = new THREE.Color(0xfffaf5);
              stdMat.emissiveMap = stdMat.map;
              stdMat.emissiveIntensity = 0.84;
              stdMat.needsUpdate = true;
            }
          }
        }

        if (
          mesh.name === 'H_DDS_HighRes' ||
          mesh.name === 'SM_Character_Face' ||
          (mesh.morphTargetInfluences && mesh.morphTargetDictionary)
        ) {
          foundFaceMesh = mesh;
        }
      }

      if ((child as THREE.Bone).isBone || child.type === 'Bone') {
        const n = child.name;
        if (n === 'Head') foundHeadBone = child;
        else if (n === 'Neck') foundNeckBone = child;
        else if (n === 'Spine2') foundSpineBone = child;
        else if (n === 'Hips') foundHipsBone = child;
        else if (n === 'LeftShoulder') foundLeftShoulderBone = child;
        else if (n === 'RightShoulder') foundRightShoulderBone = child;
        else if (n === 'LeftArm') foundLeftArmBone = child;
        else if (n === 'RightArm') foundRightArmBone = child;
        else if (n === 'LeftForeArm') foundLeftForeArmBone = child;
        else if (n === 'RightForeArm') foundRightForeArmBone = child;
        else if (n === 'LeftHand') foundLeftHandBone = child;
        else if (n === 'RightHand') foundRightHandBone = child;
        else if (n === 'LeftUpLeg') foundLeftUpLegBone = child;
        else if (n === 'RightUpLeg') foundRightUpLegBone = child;
        else if (n === 'LeftLeg') foundLeftLegBone = child;
        else if (n === 'RightLeg') foundRightLegBone = child;
        else if (/^LeftHand(Index|Middle|Ring|Pinky|Thumb)[1-3]/i.test(n)) {
          foundLeftFingers.push(child);
        } else if (/^RightHand(Index|Middle|Ring|Pinky|Thumb)[1-3]/i.test(n)) {
          foundRightFingers.push(child);
        }
      }
    });

    this.gltfFaceMesh = foundFaceMesh;
    this.headBone = foundHeadBone;
    this.neckBone = foundNeckBone;
    this.spineBone = foundSpineBone;
    this.hipsBone = foundHipsBone;
    this.leftShoulderBone = foundLeftShoulderBone;
    this.rightShoulderBone = foundRightShoulderBone;
    this.leftArmBone = foundLeftArmBone;
    this.rightArmBone = foundRightArmBone;
    this.leftForeArmBone = foundLeftForeArmBone;
    this.rightForeArmBone = foundRightForeArmBone;
    this.leftHandBone = foundLeftHandBone;
    this.rightHandBone = foundRightHandBone;
    this.leftUpLegBone = foundLeftUpLegBone;
    this.rightUpLegBone = foundRightUpLegBone;
    this.leftLegBone = foundLeftLegBone;
    this.rightLegBone = foundRightLegBone;
    this.restLeftUpLegX = foundLeftUpLegBone ? (foundLeftUpLegBone as THREE.Object3D).rotation.x : 0;
    this.restRightUpLegX = foundRightUpLegBone ? (foundRightUpLegBone as THREE.Object3D).rotation.x : 0;
    this.restLeftLegX = foundLeftLegBone ? (foundLeftLegBone as THREE.Object3D).rotation.x : 0;
    this.restRightLegX = foundRightLegBone ? (foundRightLegBone as THREE.Object3D).rotation.x : 0;
    this.leftFingers = foundLeftFingers;
    this.rightFingers = foundRightFingers;

    const headObj = foundHeadBone as THREE.Object3D | null;
    if (headObj) {
      model.scale.set(1.38, 1.38, 1.38);
      this.bustBaseOffsetY = 0;
      model.position.set(0, -1.45, 0);

      // Attach procedural spectacles only if the GLB does not already embed refined spectacles
      const hasEmbeddedSpectacles = Boolean(
        model.getObjectByName('Sovereign_Titanium_Spectacles') ||
        model.getObjectByName('glasses_frame')
      );
      if (!hasEmbeddedSpectacles) {
        const glassesRig = this.createSignatureHeadStylingRig();
        headObj.add(glassesRig);
      }

      const lArm = foundLeftArmBone as THREE.Object3D | null;
      const rArm = foundRightArmBone as THREE.Object3D | null;
      const lFore = foundLeftForeArmBone as THREE.Object3D | null;
      const rFore = foundRightForeArmBone as THREE.Object3D | null;

      if (lArm) lArm.rotation.set(1.558, -2.002, 0.118);
      if (rArm) rArm.rotation.set(1.44, -2.22, -0.60);
      if (lFore) lFore.rotation.set(-0.182, 2.658, -0.022);
      if (rFore) rFore.rotation.set(-0.32, -1.76, -0.50);
    } else {
      // Unrigged 3D scan
      model.updateMatrixWorld(true);
      const bbox = new THREE.Box3().setFromObject(model);
      const size = new THREE.Vector3();
      bbox.getSize(size);

      const isBust = Boolean(
        (model.name && /bust|hoodie|zachary/i.test(model.name)) ||
        model.getObjectByName('geometry_0')
      );
      const targetHeight = isBust ? 1.65 : 2.35;
      const autoScale = size.y > 0.001 ? targetHeight / size.y : 2.35;
      model.scale.set(autoScale, autoScale, autoScale);
      model.updateMatrixWorld(true);

      const scaledBbox = new THREE.Box3().setFromObject(model);
      const scaledCenter = new THREE.Vector3();
      scaledBbox.getCenter(scaledCenter);

      this.bustBaseOffsetY = -1.45 - scaledBbox.min.y;
      model.position.set(-scaledCenter.x, this.bustBaseOffsetY, -scaledCenter.z);

      model.traverse((child: THREE.Object3D) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
          const isOpticalLens = materials.some(
            (m) => m && (/Glasses_Lens|GlassesLens/i.test(m.name || '') || (m as THREE.MeshStandardMaterial).transparent)
          );
          mesh.castShadow = !isOpticalLens;
          mesh.receiveShadow = false;
          const hasTexturedOrPBR = materials.some(
            (m) => m && ((m as THREE.MeshStandardMaterial).map !== null || /^Zachary_|^Glasses_/i.test(m.name || ''))
          );
          if (mesh.geometry && !hasTexturedOrPBR) {
            mesh.geometry.computeVertexNormals();
          }
          for (const m of materials) {
            const mat = m as THREE.MeshStandardMaterial;
            if (mat && !mat.map && !/^Zachary_|^Glasses_/i.test(mat.name || '')) {
              mat.roughness = SCAN_MATERIAL.roughness;
              mat.metalness = SCAN_MATERIAL.metalness;
              if (mat.color) mat.color.set(SCAN_MATERIAL.colorHex);
              mat.needsUpdate = true;
            }
          }
        }
      });
    }

    if (this.personaBodyGroup) {
      this.personaBodyGroup.visible = false;
    }
    if (this.stylizedRig) {
      this.stylizedRig.group.visible = false;
    }
    this.avatarRig.add(model);
  }

  public async loadGLTFModel(url: string = '/models/zachary_character.glb'): Promise<void> {
    if (typeof window === 'undefined') return;
    try {
      // Resolve base URL for Node/JSDOM environments to avoid "Failed to parse URL" stderr noise
      let resolvedUrl = url;
      if (
        !url.startsWith('http://') &&
        !url.startsWith('https://') &&
        !url.startsWith('data:') &&
        !url.startsWith('blob:')
      ) {
        const origin =
          typeof window !== 'undefined' &&
          window.location?.origin &&
          window.location.origin !== 'null'
            ? window.location.origin
            : 'http://localhost:3000';
        resolvedUrl = url.startsWith('/') ? `${origin}${url}` : `${origin}/${url}`;
      }

      const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader.js');
      const loader = new GLTFLoader();
      loader.load(
        resolvedUrl,
        (gltf) => {
          console.log('[SceneController] Successfully loaded GLTF model:', url);
          this.applyLoadedGLTFAvatar(gltf);
        },
        undefined,
        (err) => {
          // In test/headless environments (Vitest/JSDOM), silence fallback error logging to keep stderr clean
          const globalObj = globalThis as unknown as {
            process?: { env?: { NODE_ENV?: string } };
            __vitest_environment__?: unknown;
          };
          const isTestEnv =
            globalObj.process?.env?.NODE_ENV === 'test' ||
            typeof globalObj.__vitest_environment__ !== 'undefined';
          if (!isTestEnv) {
            console.warn('[SceneController] GLTF load fallback:', err);
          }
        }
      );
    } catch (e) {
      const globalObj = globalThis as unknown as {
        process?: { env?: { NODE_ENV?: string } };
        __vitest_environment__?: unknown;
      };
      const isTestEnv =
        globalObj.process?.env?.NODE_ENV === 'test' ||
        typeof globalObj.__vitest_environment__ !== 'undefined';
      if (!isTestEnv) {
        console.warn('[SceneController] GLTFLoader import fallback:', e);
      }
    }
  }

  private createSignatureHeadStylingRig(): THREE.Group {
    const rig = new THREE.Group();
    rig.name = 'SignatureHeadStylingRig';
    const glassesGroup = new THREE.Group();
    glassesGroup.name = 'GLTFTitaniumGlasses';
    rig.add(glassesGroup);

    const frameMat = new THREE.MeshStandardMaterial({ color: 0x1e2430, roughness: 0.16, metalness: 0.94 });
    const leftRim = new THREE.Mesh(new THREE.TorusGeometry(2.15, 0.16, 16, 48), frameMat);
    leftRim.position.set(5.92, 9.20, 3.10);
    leftRim.rotation.y = Math.PI / 2;
    glassesGroup.add(leftRim);

    const rightRim = new THREE.Mesh(new THREE.TorusGeometry(2.15, 0.16, 16, 48), frameMat);
    rightRim.position.set(5.92, 9.20, -3.10);
    rightRim.rotation.y = Math.PI / 2;
    glassesGroup.add(rightRim);

    return rig;
  }

  /* -------------------------------------------------------------
   * ANIMATION TICK
   * ----------------------------------------------------------- */
  public animateTick(deltaOverride?: number): void {
    if (this.isDisposed) return;
    const dt = deltaOverride ?? 0.016;
    this.virtualTime += dt;
    this.animateInternal(dt);
  }

  private animate(): void {
    if (this.isDisposed) return;
    this.timer.update();
    const rawDelta = this.timer.getDelta();
    const delta = Math.min(rawDelta, 0.1);
    this.virtualTime += delta;
    this.animateInternal(delta);
  }

  private animateInternal(delta: number): void {
    if (this.isDisposed) return;
    this.lastFrameTimestamp = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const safeDelta = Math.max(delta, 0.001);
    const sp = this.scrollProgress;

    // Auto-return timer check if configured
    if (this.currentPoseAction !== 'neutral' && this.poseActionAutoReturn) {
      if (this.virtualTime - this.poseActionStartTime >= this.poseActionDuration) {
        this.currentPoseAction = 'neutral';
        if (typeof window !== 'undefined') {
          window.dispatchEvent(
            new CustomEvent('portfolio:scene_action', {
              detail: { action: 'reset_pose', source: 'auto_return' },
            })
          );
        }
      }
    }

    const targetPoseWeight = this.currentPoseAction !== 'neutral' ? 1.0 : 0.0;
    const blendRate = 6.0;
    if (this.isReducedMotion) {
      this.poseWeight = targetPoseWeight;
    } else {
      this.poseWeight = THREE.MathUtils.damp(this.poseWeight, targetPoseWeight, blendRate, safeDelta);
      if (Math.abs(this.poseWeight - targetPoseWeight) < 0.001) {
        this.poseWeight = targetPoseWeight;
      }
    }

    if (this.poseWeight <= 0.0001 && this.currentPoseAction === 'neutral') {
      this.activePoseAction = null;
    }

    // Storyline locomotion blend-out: if user scrolls away from Act 1, smoothly fade pose weight
    if (sp > 0.16 && this.currentPoseAction !== 'neutral') {
      this.currentPoseAction = 'neutral';
      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new CustomEvent('portfolio:scene_action', {
            detail: { action: 'reset_pose', source: 'scroll_departure' },
          })
        );
      }
    }

    const act1WeightFade = sp <= 0.08 ? 1.0 : THREE.MathUtils.clamp(1.0 - (sp - 0.08) / 0.08, 0.0, 1.0);
    const effectivePoseWeight = this.poseWeight * act1WeightFade;

    const glassesAdjustActive = this.currentPoseAction === 'glasses_adjust' || this.virtualTime < this.glassesAdjustUntil;
    const tabletInspectActive = this.currentPoseAction === 'inspect_tablet' || this.virtualTime < this.tabletInspectUntil;
    const keynotePresentActive = this.currentPoseAction === 'keynote_present' || this.virtualTime < this.keynotePresentUntil;
    const tomeInspectActive = this.virtualTime < this.tomeInspectUntil;
    const badgeSurgeActive = this.virtualTime < this.badgeSurgeUntil;
    const trophyPresentActive = this.virtualTime < this.trophyPresentUntil;
    const handshakeWaveActive = this.virtualTime < this.handshakeWaveUntil;
    const interestFocusActive = this.virtualTime < this.interestFocusUntil;

    if (
      badgeSurgeActive ||
      trophyPresentActive ||
      handshakeWaveActive ||
      interestFocusActive ||
      glassesAdjustActive ||
      tomeInspectActive ||
      tabletInspectActive ||
      keynotePresentActive
    ) {
      this.strataExplodeBoost = THREE.MathUtils.damp(this.strataExplodeBoost, 1.0, 5.0, safeDelta);
    } else {
      this.strataExplodeBoost = THREE.MathUtils.damp(this.strataExplodeBoost, 0.0, 5.0, safeDelta);
    }

    // 1. Canonical Persona Station Interpolation & Camera Dwell Synchronization
    const { stIdx, w, camProgress } = this.getCanonicalStationProgress(sp);
    this.cameraRig.updateScroll(camProgress);
    this.cameraRig.update(safeDelta, this.isReducedMotion);

    const currStation = SceneController.PERSONA_STATIONS[stIdx]!;
    const nextIdx = Math.min(stIdx + (w > 0 ? 1 : 0), 5);
    const nextStation = SceneController.PERSONA_STATIONS[nextIdx]!;

    if (this.avatarRig) {
      if (w === 0) {
        this.scratchVec.copy(currStation.pos);
      } else {
        this.scratchVec.lerpVectors(currStation.pos, nextStation.pos, w);
      }

      let targetRotY = THREE.MathUtils.lerp(currStation.rotY, nextStation.rotY, w);
      if (stIdx === 0 && w === 0 && !this.isReducedMotion) {
        this.scratchVec.x += this.mouseParallax.x * 0.08;
        targetRotY += this.mouseParallax.x * 0.10;
      }
      if (this.isMobile) {
        this.scratchVec.x *= 0.45;
      }

      if (this.isReducedMotion) {
        this.avatarRig.position.copy(this.scratchVec);
        this.avatarRig.rotation.y = targetRotY;
      } else {
        this.avatarRig.position.lerp(this.scratchVec, 0.18);
        this.avatarRig.rotation.y += (targetRotY - this.avatarRig.rotation.y) * 0.14;
      }

      // Per-Act Dynamic Atmosphere & Portrait Beauty Lighting
      const currPalette = SceneController.ACT_ATMOSPHERE_PALETTES[stIdx] ?? SceneController.ACT_ATMOSPHERE_PALETTES[0]!;
      const nextPalette = SceneController.ACT_ATMOSPHERE_PALETTES[nextIdx] ?? currPalette;
      this.scratchBgColor.setHex(currPalette.bg);
      if (w > 0) {
        this.scratchNextColor.setHex(nextPalette.bg);
        this.scratchBgColor.lerp(this.scratchNextColor, w);
      }
      if (this.scene.background instanceof THREE.Color) {
        this.scene.background.copy(this.scratchBgColor);
      }
      if (this.scene.fog instanceof THREE.FogExp2) {
        this.scene.fog.color.copy(this.scratchBgColor);
      }

      // Lighting tracking
      const rx = this.avatarRig.position.x;
      const ry = this.avatarRig.position.y;
      const rz = this.avatarRig.position.z;

      if (this.gltfFaceMesh?.name === 'SM_Character_Face') {
        if (this.studioKeyLight) {
          this.studioKeyLight.position.set(rx + 2.2, ry + 2.6, rz + 4.6);
          this.studioKeyLight.intensity = 2.15;
          this.studioKeyLight.color.setHex(currPalette.key);
        }
        if (this.fillLight) {
          this.fillLight.position.set(rx - 2.4, ry + 2.2, rz + 4.4);
          this.fillLight.intensity = 1.75;
          this.fillLight.color.setHex(currPalette.fill);
        }
        if (this.rimCyanLight) {
          this.rimCyanLight.position.set(rx, ry + 2.4, rz - 2.8);
          this.rimCyanLight.intensity = 1.35;
          this.rimCyanLight.color.setHex(currPalette.rim);
        }
        if (this.plinthSpotLight) {
          this.plinthSpotLight.position.set(rx, ry + 3.8, rz + 1.2);
          this.plinthSpotLight.intensity = 0.75;
          this.plinthSpotLight.color.setHex(currPalette.key);
        }
      } else {
        if (this.studioKeyLight) this.studioKeyLight.position.set(rx + 2.8, ry + 3.2, rz + 4.2);
        if (this.fillLight) this.fillLight.position.set(rx - 3.2, ry + 1.8, rz + 3.0);
        if (this.rimCyanLight) this.rimCyanLight.position.set(rx, ry + 2.4, rz - 2.8);
        if (this.plinthSpotLight) this.plinthSpotLight.position.set(rx, ry + 3.8, rz + 1.2);
      }

      // Gaze tracking
      const propX = THREE.MathUtils.lerp(currStation.propTarget.x, nextStation.propTarget.x, w);
      const propY = THREE.MathUtils.lerp(currStation.propTarget.y, nextStation.propTarget.y, w);
      const propZ = THREE.MathUtils.lerp(currStation.propTarget.z, nextStation.propTarget.z, w);

      const dx = propX - rx;
      const dz = propZ - rz;
      let dTheta = Math.atan2(dx, -dz) - this.avatarRig.rotation.y;
      while (dTheta > Math.PI) dTheta -= Math.PI * 2;
      while (dTheta < -Math.PI) dTheta += Math.PI * 2;
      const propGazeYaw = THREE.MathUtils.clamp(dTheta * 0.22, -0.28, 0.28);
      const propGazePitch = THREE.MathUtils.clamp((propY - (ry + 1.4)) * 0.15, -0.06, 0.12);

      const poseKey = this.currentPoseAction !== 'neutral' ? this.currentPoseAction : (effectivePoseWeight > 0.0001 ? this.activePoseAction : null);
      const activePreset = poseKey ? SceneController.AVATAR_POSE_TARGETS[poseKey] : null;

      const targetGazePitch = (activePreset?.headPitch !== undefined && effectivePoseWeight > 0.001)
        ? THREE.MathUtils.lerp(propGazePitch, activePreset.headPitch, effectivePoseWeight)
        : propGazePitch;
      const targetGazeYaw = (activePreset?.headYaw !== undefined && effectivePoseWeight > 0.001)
        ? THREE.MathUtils.lerp(propGazeYaw, activePreset.headYaw, effectivePoseWeight)
        : propGazeYaw;

      if (this.neckPivot) {
        if (this.isReducedMotion) {
          this.neckPivot.rotation.y = targetGazeYaw * 0.4;
        } else {
          this.neckPivot.rotation.y += (targetGazeYaw * 0.4 - this.neckPivot.rotation.y) * 0.06;
        }
      }
      if (this.headPivot) {
        if (this.isReducedMotion) {
          this.headPivot.rotation.y = targetGazeYaw;
          this.headPivot.rotation.x = targetGazePitch * 0.35;
        } else {
          this.headPivot.rotation.y += (targetGazeYaw - this.headPivot.rotation.y) * 0.08;
          this.headPivot.rotation.x += (targetGazePitch * 0.35 - this.headPivot.rotation.x) * 0.08;
        }
      }

      // Update Stylized Character Rig Postures across Storyline Acts & Dynamic Pose Actions
      if (this.stylizedRig) {
        const poseToSet = effectivePoseWeight > 0.15 ? (this.currentPoseAction !== 'neutral' ? this.currentPoseAction : this.activePoseAction) : null;
        if (poseToSet === 'glasses_adjust') {
          this.stylizedRig.setPosture('glasses_adjust');
        } else if (poseToSet === 'inspect_tablet') {
          this.stylizedRig.setPosture('inspect_tablet');
        } else if (poseToSet === 'keynote_present') {
          this.stylizedRig.setPosture('keynote_present');
        } else if (tomeInspectActive) {
          this.stylizedRig.setPosture('reach_book');
        } else if (badgeSurgeActive) {
          this.stylizedRig.setPosture('conduct_badges');
        } else if (trophyPresentActive) {
          this.stylizedRig.setPosture('hoist_trophy');
        } else if (handshakeWaveActive) {
          this.stylizedRig.setPosture('wave');
        } else if (w > 0.05 && w < 0.95) {
          this.stylizedRig.setPosture('walk');
        } else if (sp < 0.12) {
          this.stylizedRig.setPosture('seated');
        } else if (sp >= 0.12 && sp < 0.20) {
          this.stylizedRig.setPosture('walk');
        } else if (sp >= 0.20 && sp < 0.34) {
          this.stylizedRig.setPosture('reach_book');
        } else if (sp >= 0.34 && sp < 0.38) {
          this.stylizedRig.setPosture('walk');
        } else if (sp >= 0.38 && sp < 0.52) {
          this.stylizedRig.setPosture('conduct_badges');
        } else if (sp >= 0.52 && sp < 0.58) {
          this.stylizedRig.setPosture('walk');
        } else if (sp >= 0.58 && sp < 0.63) {
          this.stylizedRig.setPosture('climb_ridge');
        } else if (sp >= 0.63 && sp < 0.70) {
          this.stylizedRig.setPosture('hoist_trophy');
        } else if (sp >= 0.70 && sp < 0.74) {
          this.stylizedRig.setPosture('walk');
        } else if (sp >= 0.74 && sp < 0.86) {
          this.stylizedRig.setPosture('operate_core');
        } else {
          this.stylizedRig.setPosture('wave');
        }

        this.stylizedRig.update(safeDelta, this.mouseParallax.x, this.mouseParallax.y, this.isReducedMotion);
      }

      // If GLTF humanoid is active, update bone rotations
      if (this.gltfAvatarModel) {
        if (!this.headBone) {
          // Unrigged scan model: maintain plinth base grounding
          const targetY = this.bustBaseOffsetY;
          this.gltfAvatarModel.position.y += (targetY - this.gltfAvatarModel.position.y) * 0.1;
          this.gltfAvatarModel.rotation.y += this.mouseParallax.x * 0.05;
        } else {
          // Rigged bones
          if (this.spineBone) this.spineBone.rotation.x = this.isReducedMotion ? 0.05 : (0.05 + Math.sin(this.virtualTime) * 0.02);
          if (this.neckBone) {
            if (this.isReducedMotion) {
              this.neckBone.rotation.y = targetGazeYaw * 0.5;
            } else {
              this.neckBone.rotation.y = THREE.MathUtils.damp(this.neckBone.rotation.y, targetGazeYaw * 0.5, 12.0, safeDelta);
            }
          }
          if (this.headBone) {
            if (this.isReducedMotion) {
              this.headBone.rotation.y = targetGazeYaw;
              this.headBone.rotation.x = targetGazePitch;
            } else {
              this.headBone.rotation.y = THREE.MathUtils.damp(this.headBone.rotation.y, targetGazeYaw, 12.0, safeDelta);
              this.headBone.rotation.x = THREE.MathUtils.damp(this.headBone.rotation.x, targetGazePitch, 12.0, safeDelta);
            }
          }

          const gCur = currStation.gltf;
          const gNext = nextStation.gltf;
          const pTarget = activePreset;

          const dampBone = (
            bone: THREE.Object3D,
            curVal: number,
            nextVal: number,
            actionVal: number | undefined,
            axis: 'x' | 'y' | 'z'
          ) => {
            const baseTarget = THREE.MathUtils.lerp(curVal, nextVal, w);
            const target = (actionVal !== undefined && effectivePoseWeight > 0.0001)
              ? THREE.MathUtils.lerp(baseTarget, actionVal, effectivePoseWeight)
              : baseTarget;
            if (this.isReducedMotion) {
              bone.rotation[axis] = target;
            } else {
              bone.rotation[axis] = THREE.MathUtils.damp(bone.rotation[axis], target, 12.0, safeDelta);
            }
          };

          if (this.leftArmBone) {
            dampBone(this.leftArmBone, gCur.leftArmX, gNext.leftArmX, pTarget?.leftArmX, 'x');
            dampBone(this.leftArmBone, gCur.leftArmY, gNext.leftArmY, pTarget?.leftArmY, 'y');
            dampBone(this.leftArmBone, gCur.leftArmZ, gNext.leftArmZ, pTarget?.leftArmZ, 'z');
          }
          if (this.rightArmBone) {
            dampBone(this.rightArmBone, gCur.rightArmX, gNext.rightArmX, pTarget?.rightArmX, 'x');
            dampBone(this.rightArmBone, gCur.rightArmY, gNext.rightArmY, pTarget?.rightArmY, 'y');
            dampBone(this.rightArmBone, gCur.rightArmZ, gNext.rightArmZ, pTarget?.rightArmZ, 'z');
          }
          if (this.leftForeArmBone) {
            dampBone(this.leftForeArmBone, gCur.leftForeX, gNext.leftForeX, pTarget?.leftForeX, 'x');
            dampBone(this.leftForeArmBone, gCur.leftForeY, gNext.leftForeY, pTarget?.leftForeY, 'y');
            dampBone(this.leftForeArmBone, gCur.leftForeZ, gNext.leftForeZ, pTarget?.leftForeZ, 'z');
          }
          if (this.rightForeArmBone) {
            dampBone(this.rightForeArmBone, gCur.rightForeX, gNext.rightForeX, pTarget?.rightForeX, 'x');
            dampBone(this.rightForeArmBone, gCur.rightForeY, gNext.rightForeY, pTarget?.rightForeY, 'y');
            dampBone(this.rightForeArmBone, gCur.rightForeZ, gNext.rightForeZ, pTarget?.rightForeZ, 'z');
          }
          if (this.leftHandBone) {
            dampBone(this.leftHandBone, gCur.leftHandX, gNext.leftHandX, pTarget?.leftHandX, 'x');
            dampBone(this.leftHandBone, gCur.leftHandY, gNext.leftHandY, pTarget?.leftHandY, 'y');
            dampBone(this.leftHandBone, gCur.leftHandZ, gNext.leftHandZ, pTarget?.leftHandZ, 'z');
          }
          if (this.rightHandBone) {
            dampBone(this.rightHandBone, gCur.rightHandX, gNext.rightHandX, pTarget?.rightHandX, 'x');
            dampBone(this.rightHandBone, gCur.rightHandY, gNext.rightHandY, pTarget?.rightHandY, 'y');
            dampBone(this.rightHandBone, gCur.rightHandZ, gNext.rightHandZ, pTarget?.rightHandZ, 'z');
          }

          // Articulate lower-body walking stride along SpatialLightBridge during inter-act transitions
          const walkWeight = (!this.isReducedMotion && w > 0.04 && w < 0.96) ? Math.sin(w * Math.PI) : 0.0;
          const strideAngle = Math.sin(this.virtualTime * 8.5) * 0.28 * walkWeight;
          if (this.leftUpLegBone) {
            this.leftUpLegBone.rotation.x = THREE.MathUtils.damp(
              this.leftUpLegBone.rotation.x,
              this.restLeftUpLegX + strideAngle,
              12.0,
              safeDelta
            );
          }
          if (this.rightUpLegBone) {
            this.rightUpLegBone.rotation.x = THREE.MathUtils.damp(
              this.rightUpLegBone.rotation.x,
              this.restRightUpLegX - strideAngle,
              12.0,
              safeDelta
            );
          }
          if (this.leftLegBone) {
            this.leftLegBone.rotation.x = THREE.MathUtils.damp(
              this.leftLegBone.rotation.x,
              this.restLeftLegX + Math.max(0, -strideAngle * 0.85),
              12.0,
              safeDelta
            );
          }
          if (this.rightLegBone) {
            this.rightLegBone.rotation.x = THREE.MathUtils.damp(
              this.rightLegBone.rotation.x,
              this.restRightLegX + Math.max(0, strideAngle * 0.85),
              12.0,
              safeDelta
            );
          }

          // Articulate 30 finger phalanges (Thumb1..3 through Pinky1..3)
          const defaultFingerCurl = (tomeInspectActive || trophyPresentActive) ? 0.18 : (handshakeWaveActive ? 0.04 : 0.10);
          const fingerCurl = (pTarget?.fingerCurl !== undefined && effectivePoseWeight > 0.01)
            ? THREE.MathUtils.lerp(defaultFingerCurl, pTarget.fingerCurl, effectivePoseWeight)
            : defaultFingerCurl;
          for (const fBone of this.leftFingers) {
            fBone.rotation.x = this.isReducedMotion
              ? fingerCurl
              : THREE.MathUtils.damp(fBone.rotation.x, fingerCurl, 10.0, safeDelta);
          }
          for (const fBone of this.rightFingers) {
            fBone.rotation.x = this.isReducedMotion
              ? fingerCurl
              : THREE.MathUtils.damp(fBone.rotation.x, fingerCurl, 10.0, safeDelta);
          }
        }

        // Modulate 8 Essential Keynote Facial Morph Targets on SM_Character_Face
        if (this.gltfFaceMesh?.morphTargetDictionary && this.gltfFaceMesh.morphTargetInfluences) {
          const dict = this.gltfFaceMesh.morphTargetDictionary;
          const infl = this.gltfFaceMesh.morphTargetInfluences;
          const smileTarget = (handshakeWaveActive || trophyPresentActive || sp > 0.55) ? 0.42 : 0.22;
          if (dict['mouthSmileLeft'] !== undefined) {
            infl[dict['mouthSmileLeft']] = this.isReducedMotion
              ? smileTarget
              : THREE.MathUtils.damp(infl[dict['mouthSmileLeft']] ?? 0, smileTarget, 8.0, safeDelta);
          }
          if (dict['mouthSmileRight'] !== undefined) {
            infl[dict['mouthSmileRight']] = this.isReducedMotion
              ? smileTarget
              : THREE.MathUtils.damp(infl[dict['mouthSmileRight']] ?? 0, smileTarget, 8.0, safeDelta);
          }
          const browTarget = (tomeInspectActive || badgeSurgeActive || interestFocusActive) ? 0.35 : 0.08;
          if (dict['browInnerUp'] !== undefined) {
            infl[dict['browInnerUp']] = this.isReducedMotion
              ? browTarget
              : THREE.MathUtils.damp(infl[dict['browInnerUp']] ?? 0, browTarget, 8.0, safeDelta);
          }
          const blinkPhase = this.virtualTime % 4.2;
          const blinkVal = (!this.isReducedMotion && blinkPhase > 4.02)
            ? Math.sin(((blinkPhase - 4.02) / 0.18) * Math.PI)
            : 0.0;
          if (dict['eyeBlinkLeft'] !== undefined) infl[dict['eyeBlinkLeft']] = blinkVal;
          if (dict['eyeBlinkRight'] !== undefined) infl[dict['eyeBlinkRight']] = blinkVal;

          // Real-Time Audio-Driven Lip-Sync Viseme & Jaw Articulation
          const audioEnergy = this.soundEngine.getAudioEnergy();
          const speechCadence = Math.sin(this.virtualTime * 14.0) * 0.5 + 0.5;
          const rawViseme = audioEnergy * speechCadence;
          const visemeTarget = (!this.isReducedMotion && audioEnergy > 0.02) ? Math.min(0.65, rawViseme * 1.2) : 0.0;
          const jawTarget = (!this.isReducedMotion && audioEnergy > 0.02) ? Math.min(0.45, rawViseme * 0.8) : 0.0;
          const mouthOpenTarget = (!this.isReducedMotion && audioEnergy > 0.02) ? Math.min(0.35, rawViseme * 0.6) : 0.0;

          if (dict['viseme_aa'] !== undefined) {
            infl[dict['viseme_aa']] = this.isReducedMotion
              ? visemeTarget
              : THREE.MathUtils.damp(infl[dict['viseme_aa']] ?? 0, visemeTarget, 16.0, safeDelta);
          }
          if (dict['jawOpen'] !== undefined) {
            infl[dict['jawOpen']] = this.isReducedMotion
              ? jawTarget
              : THREE.MathUtils.damp(infl[dict['jawOpen']] ?? 0, jawTarget, 16.0, safeDelta);
          }
          if (dict['mouthOpen'] !== undefined) {
            infl[dict['mouthOpen']] = this.isReducedMotion
              ? mouthOpenTarget
              : THREE.MathUtils.damp(infl[dict['mouthOpen']] ?? 0, mouthOpenTarget, 16.0, safeDelta);
          }
        }
      }
    }

    // 3. Update Submodules & Depth-Gate Distant Islands to Prevent Next-Act Bleed-Through
    this.act2.getAcademyGroup().visible = sp >= 0.06 && sp <= 0.34;
    this.act3.getCrucibleGroup().visible = sp >= 0.26 && sp <= 0.54;
    this.act4.getSummitGroup().visible = sp >= 0.46 && sp <= 0.74;
    this.act5.getFrontierGroup().visible = sp >= 0.66 && sp <= 0.94;
    this.act6.getHorizonGroup().visible = sp >= 0.86;
    const bridge = this.particleLattice.getSpatialLightBridge();
    if (bridge) {
      bridge.visible = w > 0.01;
    }

    this.act1.update(safeDelta, this.isReducedMotion, sp);
    this.act2.update(safeDelta, this.isReducedMotion);
    this.act3.update(safeDelta, this.isReducedMotion);
    this.act4.update(safeDelta, this.isReducedMotion);
    this.act5.update(safeDelta, this.isReducedMotion, sp);
    this.act6.update(safeDelta, this.isReducedMotion);

    // Dynamic light ramps and atmospheric fog modulation across 6 acts
    const summitBeaconLight = this.act4.getSummitBeaconLight();
    const horizonBeaconLight = this.act6.getBeaconLight();

    if (summitBeaconLight) {
      const distSummit = Math.abs(sp - 0.60);
      const summitTarget = distSummit < 0.12 ? (1.0 - distSummit / 0.12) * 2.4 : 0.0;
      summitBeaconLight.intensity = THREE.MathUtils.damp(summitBeaconLight.intensity, summitTarget, 12.0, safeDelta);
      if (summitTarget === 0.0 && summitBeaconLight.intensity < 0.06) {
        summitBeaconLight.intensity = 0;
      }
    }

    if (horizonBeaconLight) {
      const isHandshake = this.virtualTime < this.handshakeWaveUntil;
      let horizonTarget = 0.0;
      if (isHandshake) {
        horizonTarget = 5.2;
      } else {
        const distHorizon = Math.abs(sp - 1.0);
        if (distHorizon < 0.15) {
          horizonTarget = (1.0 - distHorizon / 0.15) * 2.5;
        }
      }
      horizonBeaconLight.intensity = THREE.MathUtils.damp(horizonBeaconLight.intensity, horizonTarget, isHandshake ? 24.0 : 12.0, safeDelta);
      if (horizonTarget === 0.0 && horizonBeaconLight.intensity < 0.06) {
        horizonBeaconLight.intensity = 0;
      }
    }

    if (this.scene.fog && (this.scene.fog as THREE.FogExp2).density !== undefined) {
      const fogExp = this.scene.fog as THREE.FogExp2;
      if (sp >= 0.50 && sp <= 0.70) {
        fogExp.density = 0.022;
      } else {
        fogExp.density = 0.038;
      }
    }

    // Damp scroll velocity towards zero when scrolling stops
    this.scrollVelocity = THREE.MathUtils.damp(this.scrollVelocity, 0.0, 25.0, safeDelta);
    if (this.scrollVelocity < 0.05) this.scrollVelocity = 0.0;

    // 4. Update Particle Systems
    this.particleLattice.update(safeDelta, sp, this.isReducedMotion);

    // 5. Update Depth Portrait Hologram
    this.depthPortrait.update(safeDelta, this.mouseParallax.x, this.mouseParallax.y, this.isReducedMotion);

    // 6. Render
    this.engine.render(this.scene, this.cameraRig.getCamera());
  }

  /* -------------------------------------------------------------
   * DISPOSAL (INVARIANT 1: MANDATORY LIFECYCLE DISPOSAL)
   * ----------------------------------------------------------- */
  public dispose(): void {
    if (this.isDisposed) return;
    this.isDisposed = true;

    // 1. Remove Window Listeners
    if (typeof window !== 'undefined') {
      if (this.pointerMoveHandler) window.removeEventListener('pointermove', this.pointerMoveHandler);
      if (this.pointerDownHandler) window.removeEventListener('pointerdown', this.pointerDownHandler);
      if (this.pointerUpHandler) window.removeEventListener('pointerup', this.pointerUpHandler);
      if (this.sceneActionHandler) window.removeEventListener('portfolio:scene_action', this.sceneActionHandler);
      if (this.explodeStrataHandler) window.removeEventListener('portfolio:explode_strata', this.explodeStrataHandler);
      if (window.__sceneController === this) {
        delete window.__sceneController;
      }
    }

    // 2. Teardown Subsystems
    this.particleLattice.dispose();
    this.soundEngine.dispose();
    this.depthPortrait.dispose();
    this.stylizedRig.dispose();
    this.act1.dispose();
    this.act2.dispose();
    this.act3.dispose();
    this.act4.dispose();
    this.act5.dispose();
    this.act6.dispose();

    // 3. Recursive VRAM Disposal & Context Loss
    this.engine.dispose(this.scene);
  }
}

export { SceneController as PortfolioEngine };

