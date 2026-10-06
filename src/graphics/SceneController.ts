import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export interface SceneControllerCallbacks {
  onSelectSummitBeacon?: () => void;
  onSelectCaseStudyNode?: (slug: string) => void;
}

export class SceneController {
  private container: HTMLElement;
  private renderer: THREE.WebGLRenderer;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private animId: number = 0;
  private isDisposed: boolean = false;
  private isReducedMotion: boolean = false;

  // 3D Avatar Host & Rig
  private avatarRig!: THREE.Group;
  private avatarModel: THREE.Group | null = null;
  private headBone: THREE.Object3D | null = null;
  private neckBone: THREE.Object3D | null = null;
  private spineBone: THREE.Object3D | null = null;
  private leftArmBone: THREE.Object3D | null = null;
  private rightArmBone: THREE.Object3D | null = null;

  // Scene entities: Titanium Core, Alps, Neural Mesh & Medallions
  private stars!: THREE.Points;
  private gyroscopeGroup!: THREE.Group;
  private gyroRings: THREE.Mesh[] = [];
  private gyroCore!: THREE.Mesh;

  // Alpine Relief & Summit Beacon
  private mountainMesh!: THREE.Mesh;
  private mountainWire!: THREE.LineSegments;
  private summitBeacon!: THREE.Mesh;
  private summitHalo!: THREE.Mesh;

  // Neural Nodes & Constellation
  private constellationGroup!: THREE.Group;
  private flagshipOrb!: THREE.Mesh;

  // Gyroscopic Medallions (Credentials)
  private medallionsGroup!: THREE.Group;
  private medGCP!: THREE.Group;
  private medHilti!: THREE.Group;
  private medAPU!: THREE.Group;

  // Studio Lighting
  private studioKeyLight!: THREE.DirectionalLight;
  private rimBlueLight!: THREE.DirectionalLight;
  private fillPurpleLight!: THREE.DirectionalLight;
  private warmPointLight!: THREE.PointLight;

  // Camera & animation targets
  private scrollProgress: number = 0;
  private mouseParallax: THREE.Vector2 = new THREE.Vector2(0, 0);
  private clock: THREE.Clock = new THREE.Clock();

  constructor(container: HTMLElement, _callbacks?: SceneControllerCallbacks) {
    this.container = container;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // 1. Scene & Camera
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x020617, 0.04);

    this.camera = new THREE.PerspectiveCamera(46, width / height, 0.1, 120);
    this.camera.position.set(0, 0, 8.5);

    // 2. WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(width, height);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    container.appendChild(this.renderer.domElement);

    // 3. Build Scene Entities
    this.initStudioLighting();
    this.initSubtleStarfield();
    this.initHumanAvatarRig();
    this.initSwissAlpsRelief();
    this.initTitaniumGyroCore();
    this.initFlagshipSystemNodes();
    this.initGyroscopicMedallions();

    // 4. Attach Event Listeners
    this.bindEvents();

    // 5. Start Render Loop
    this.animate = this.animate.bind(this);
    this.animId = requestAnimationFrame(this.animate);
  }

  private initStudioLighting(): void {
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    this.scene.add(ambientLight);

    // Key Spotlight with soft shadows
    this.studioKeyLight = new THREE.DirectionalLight(0xfff7ed, 3.2);
    this.studioKeyLight.position.set(4, 12, 10);
    this.studioKeyLight.castShadow = true;
    this.scene.add(this.studioKeyLight);

    // Cool Cyan Rim Light
    this.rimBlueLight = new THREE.DirectionalLight(0x00f2fe, 3.6);
    this.rimBlueLight.position.set(-8, 5, -4);
    this.scene.add(this.rimBlueLight);

    // Accent Purple Fill
    this.fillPurpleLight = new THREE.DirectionalLight(0x818cf8, 1.8);
    this.fillPurpleLight.position.set(6, -4, -3);
    this.scene.add(this.fillPurpleLight);

    // Warm Plinth Ambient Glow
    this.warmPointLight = new THREE.PointLight(0x00f2fe, 1.4, 16);
    this.warmPointLight.position.set(0, -2.4, 2);
    this.scene.add(this.warmPointLight);
  }

  private initSubtleStarfield(): void {
    const starCount = 800;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 80;
      positions[i + 1] = (Math.random() - 0.5) * 60;
      positions[i + 2] = -Math.random() * 80;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color: 0x94a3b8,
      size: 0.12,
      transparent: true,
      opacity: 0.6,
    });

    this.stars = new THREE.Points(geometry, material);
    this.scene.add(this.stars);
  }

  private initHumanAvatarRig(): void {
    this.avatarRig = new THREE.Group();
    this.avatarRig.position.set(2.0, -0.2, 0);
    this.scene.add(this.avatarRig);

    // Frosted Glass Plinth
    const plinth = new THREE.Mesh(
      new THREE.CylinderGeometry(2.2, 2.5, 0.18, 64),
      new THREE.MeshStandardMaterial({
        color: 0x090d1a,
        metalness: 0.85,
        roughness: 0.2,
        transparent: true,
        opacity: 0.88,
      })
    );
    plinth.position.y = -2.8;
    plinth.receiveShadow = true;
    this.avatarRig.add(plinth);

    const glowRing = new THREE.Mesh(
      new THREE.TorusGeometry(2.38, 0.025, 16, 80),
      new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.85 })
    );
    glowRing.rotation.x = Math.PI / 2;
    glowRing.position.y = -2.71;
    this.avatarRig.add(glowRing);

    // Load High-Class GLB Avatar
    const loader = new GLTFLoader();
    loader.load(
      '/models/Asian_M_3_Busi.glb',
      (gltf) => {
        if (this.isDisposed) return;
        this.avatarModel = gltf.scene;
        this.avatarModel.scale.set(3.0, 3.0, 3.0);
        this.avatarModel.position.set(0, -2.8, 0);

        this.avatarModel.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            if (mesh.material) {
              const mat = mesh.material as THREE.MeshStandardMaterial;
              mat.roughness = 0.65;
              mat.metalness = 0.15;
            }
          }
          if (child.name === 'Head') this.headBone = child;
          if (child.name === 'Neck') this.neckBone = child;
          if (child.name === 'Spine1' || child.name === 'Spine') this.spineBone = child;
          if (child.name === 'LeftArm') this.leftArmBone = child;
          if (child.name === 'RightArm') this.rightArmBone = child;
        });

        // Attach Zachary's Signature Titanium Round Glasses to Head Bone
        if (this.headBone) {
          const glassesGroup = new THREE.Group();
          glassesGroup.position.set(0, 0.09, 0.145);
          glassesGroup.rotation.x = 0.05;

          const titaniumMat = new THREE.MeshStandardMaterial({
            color: 0x1e293b,
            metalness: 0.95,
            roughness: 0.15,
          });
          const lensMat = new THREE.MeshPhysicalMaterial({
            color: 0x38bdf8,
            transmission: 0.85,
            roughness: 0.05,
            transparent: true,
            opacity: 0.4,
          });

          const rimGeo = new THREE.TorusGeometry(0.042, 0.0035, 16, 36);
          const lensGeo = new THREE.CircleGeometry(0.041, 32);

          const leftRim = new THREE.Mesh(rimGeo, titaniumMat);
          leftRim.position.x = -0.055;
          glassesGroup.add(leftRim);

          const leftLens = new THREE.Mesh(lensGeo, lensMat);
          leftLens.position.x = -0.055;
          glassesGroup.add(leftLens);

          const rightRim = new THREE.Mesh(rimGeo, titaniumMat);
          rightRim.position.x = 0.055;
          glassesGroup.add(rightRim);

          const rightLens = new THREE.Mesh(lensGeo, lensMat);
          rightLens.position.x = 0.055;
          glassesGroup.add(rightLens);

          const bridge = new THREE.Mesh(
            new THREE.CylinderGeometry(0.003, 0.003, 0.038, 12),
            titaniumMat
          );
          bridge.rotation.z = Math.PI / 2;
          glassesGroup.add(bridge);

          this.headBone.add(glassesGroup);
        }

        // Set natural confident arm poses
        if (this.leftArmBone) this.leftArmBone.rotation.z = 1.25;
        if (this.rightArmBone) this.rightArmBone.rotation.z = -1.25;

        this.avatarRig.add(this.avatarModel);
      },
      undefined,
      (err) => {
        console.warn('Fallback GLB loader notice:', err);
      }
    );
  }

  private initSwissAlpsRelief(): void {
    const reliefGroup = new THREE.Group();
    reliefGroup.position.set(-4.2, -2, -25);
    this.scene.add(reliefGroup);

    const mountainGeo = new THREE.PlaneGeometry(36, 24, 28, 20);
    const pos = mountainGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const y = pos.getY(i);
      let peak = Math.sin(x * 0.35) * Math.cos(y * 0.4) * 3.6;
      peak += Math.sin(x * 0.75) * 1.5;
      if (Math.abs(x) < 4.2 && y > 0) peak += (4.2 - Math.abs(x)) * 2.4;
      pos.setZ(i, peak);
    }
    mountainGeo.computeVertexNormals();

    const mountainMat = new THREE.MeshStandardMaterial({
      color: 0x091428,
      roughness: 0.55,
      metalness: 0.25,
      flatShading: true,
    });
    this.mountainMesh = new THREE.Mesh(mountainGeo, mountainMat);
    this.mountainMesh.rotation.x = -Math.PI / 2.3;
    reliefGroup.add(this.mountainMesh);

    this.mountainWire = new THREE.LineSegments(
      new THREE.WireframeGeometry(mountainGeo),
      new THREE.LineBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.2 })
    );
    this.mountainWire.rotation.x = -Math.PI / 2.3;
    reliefGroup.add(this.mountainWire);

    // Glowing Golden Summit Beacon: Mount Pilatus
    const beaconGeo = new THREE.SphereGeometry(0.35, 16, 16);
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
    this.summitBeacon = new THREE.Mesh(beaconGeo, beaconMat);
    this.summitBeacon.position.set(0.5, 6.2, 0);
    reliefGroup.add(this.summitBeacon);

    const haloGeo = new THREE.TorusGeometry(0.7, 0.03, 16, 32);
    const haloMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.7 });
    this.summitHalo = new THREE.Mesh(haloGeo, haloMat);
    this.summitHalo.position.copy(this.summitBeacon.position);
    this.summitHalo.rotation.x = Math.PI / 2;
    reliefGroup.add(this.summitHalo);
  }

  private initTitaniumGyroCore(): void {
    this.gyroscopeGroup = new THREE.Group();
    this.gyroscopeGroup.position.set(3.8, 0, -45);
    this.scene.add(this.gyroscopeGroup);

    const ringRadii = [2.2, 1.7, 1.2];
    const ringThickness = [0.035, 0.03, 0.025];

    ringRadii.forEach((r, idx) => {
      const ringGeom = new THREE.TorusGeometry(r, ringThickness[idx], 24, 72);
      const ringMat = new THREE.MeshStandardMaterial({
        color: idx === 0 ? 0x0284c7 : idx === 1 ? 0xf59e0b : 0x10b981,
        metalness: 0.9,
        roughness: 0.2,
      });
      const ringMesh = new THREE.Mesh(ringGeom, ringMat);
      this.gyroRings.push(ringMesh);
      this.gyroscopeGroup.add(ringMesh);
    });

    const coreGeom = new THREE.IcosahedronGeometry(0.7, 2);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      emissive: 0x0084b4,
      emissiveIntensity: 0.85,
      roughness: 0.1,
      metalness: 0.9,
      wireframe: true,
    });
    this.gyroCore = new THREE.Mesh(coreGeom, coreMat);
    this.gyroscopeGroup.add(this.gyroCore);
  }

  private initFlagshipSystemNodes(): void {
    this.constellationGroup = new THREE.Group();
    this.constellationGroup.position.set(-3.5, 0, -65);
    this.scene.add(this.constellationGroup);

    this.flagshipOrb = new THREE.Mesh(
      new THREE.IcosahedronGeometry(2.4, 2),
      new THREE.MeshPhongMaterial({
        color: 0x00f2fe,
        emissive: 0x024566,
        transparent: true,
        opacity: 0.65,
        wireframe: true,
      })
    );
    this.constellationGroup.add(this.flagshipOrb);

    const innerPulse = new THREE.Mesh(
      new THREE.SphereGeometry(1.2, 20, 20),
      new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
    );
    this.constellationGroup.add(innerPulse);
  }

  private initGyroscopicMedallions(): void {
    this.medallionsGroup = new THREE.Group();
    this.medallionsGroup.position.set(0, 0, -85);
    this.scene.add(this.medallionsGroup);

    // 1. Google Cloud Hexagon (Cyan)
    this.medGCP = new THREE.Group();
    this.medGCP.position.set(-3.8, 1.2, 0);
    this.medGCP.add(
      new THREE.Mesh(
        new THREE.CylinderGeometry(1.8, 1.8, 0.22, 6),
        new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.9, roughness: 0.15, emissive: 0x042f47 })
      )
    );
    this.medGCP.add(
      new THREE.Mesh(new THREE.TorusGeometry(2.1, 0.045, 16, 64), new THREE.MeshBasicMaterial({ color: 0x00f2fe }))
    );
    this.medallionsGroup.add(this.medGCP);

    // 2. Hilti World Champion Laurel Medallion (Gold)
    this.medHilti = new THREE.Group();
    this.medHilti.position.set(0, 1.6, 1);
    this.medHilti.add(
      new THREE.Mesh(
        new THREE.CylinderGeometry(2.1, 2.1, 0.25, 32),
        new THREE.MeshStandardMaterial({ color: 0xd97706, metalness: 0.95, roughness: 0.12, emissive: 0x3b1e04 })
      )
    );
    this.medHilti.add(
      new THREE.Mesh(new THREE.TorusGeometry(2.4, 0.055, 16, 64), new THREE.MeshBasicMaterial({ color: 0xfbbf24 }))
    );
    this.medallionsGroup.add(this.medHilti);

    // 3. APU First Class Academic Seal (Emerald)
    this.medAPU = new THREE.Group();
    this.medAPU.position.set(3.8, 1.2, 0);
    this.medAPU.add(
      new THREE.Mesh(
        new THREE.CylinderGeometry(1.8, 1.8, 0.22, 32),
        new THREE.MeshStandardMaterial({ color: 0x059669, metalness: 0.9, roughness: 0.15, emissive: 0x022c1f })
      )
    );
    this.medAPU.add(
      new THREE.Mesh(new THREE.TorusGeometry(2.1, 0.045, 16, 64), new THREE.MeshBasicMaterial({ color: 0x34d399 }))
    );
    this.medallionsGroup.add(this.medAPU);
  }

  private bindEvents(): void {
    const handlePointerMove = (e: MouseEvent) => {
      const mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      const mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
      this.mouseParallax.set(mouseX, mouseY);
    };

    window.addEventListener('mousemove', handlePointerMove, { passive: true });
  }

  public updateScroll(progress: number): void {
    this.scrollProgress = Math.min(1, Math.max(0, progress));
  }

  public updateParallax(x: number, y: number): void {
    this.mouseParallax.set(x, y);
  }

  public setReducedMotion(isReduced: boolean): void {
    this.isReducedMotion = isReduced;
  }

  public resize(): void {
    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  private animate(): void {
    if (this.isDisposed) return;
    this.animId = requestAnimationFrame(this.animate);

    const delta = this.clock.getDelta();
    const elapsedTime = this.clock.getElapsedTime();
    const sp = this.scrollProgress;

    // Camera positioning interpolated along storyline depth
    const targetZ = 8.5 - sp * 100;
    const targetX = Math.sin(sp * Math.PI * 2.5) * 2.2 + this.mouseParallax.x * 0.4;
    const targetY = -sp * 4 - this.mouseParallax.y * 0.3;

    this.camera.position.z += (targetZ - this.camera.position.z) * 0.08;
    this.camera.position.x += (targetX - this.camera.position.x) * 0.08;
    this.camera.position.y += (targetY - this.camera.position.y) * 0.08;

    // Companion Avatar Positioning & Rotation
    if (this.avatarRig) {
      this.avatarRig.position.z = this.camera.position.z - 7.5;

      if (sp < 0.18) {
        // Hero: Center-Right
        this.avatarRig.position.x = 2.0 + this.mouseParallax.x * 0.2;
        this.avatarRig.rotation.y = -0.22;
      } else if (sp < 0.38) {
        // The Summit: Stepped right presenting Mount Pilatus
        this.avatarRig.position.x = 2.8;
        this.avatarRig.rotation.y = -0.38;
      } else if (sp < 0.62) {
        // Fintech & Solutions: Stepped left
        this.avatarRig.position.x = -2.8;
        this.avatarRig.rotation.y = 0.38;
      } else if (sp < 0.85) {
        // Credentials: Center-stage
        this.avatarRig.position.x = 0;
        this.avatarRig.rotation.y = 0;
      } else {
        // Action Center: Facing forward
        this.avatarRig.position.x = 2.2;
        this.avatarRig.rotation.y = -0.18;
      }

      // Procedural Bone Breathing & Cursor LookAt
      if (!this.isReducedMotion) {
        if (this.spineBone) {
          this.spineBone.rotation.x = Math.sin(elapsedTime * 1.8) * 0.03;
        }
        if (this.neckBone) {
          const targetNeckYaw = this.mouseParallax.x * 0.2;
          this.neckBone.rotation.y += (targetNeckYaw - this.neckBone.rotation.y) * 0.05;
        }
        if (this.headBone) {
          const targetYaw = this.mouseParallax.x * 0.35;
          const targetPitch = this.mouseParallax.y * 0.25;
          this.headBone.rotation.y += (targetYaw - this.headBone.rotation.y) * 0.08;
          this.headBone.rotation.x += (targetPitch - this.headBone.rotation.x) * 0.08;
        }
      }
    }

    // Secondary Asset Rotations
    if (!this.isReducedMotion) {
      this.gyroRings.forEach((ring, idx) => {
        ring.rotation.x += delta * (0.4 + idx * 0.15);
        ring.rotation.y += delta * (0.3 + idx * 0.2);
      });
      if (this.gyroCore) {
        this.gyroCore.rotation.y += delta * 0.5;
      }
      if (this.summitHalo) {
        this.summitHalo.rotation.z += delta * 0.6;
        const scale = 1 + Math.sin(elapsedTime * 3) * 0.12;
        this.summitHalo.scale.set(scale, scale, scale);
      }
      if (this.flagshipOrb) {
        this.flagshipOrb.rotation.y += delta * 0.4;
      }
      if (this.medGCP) this.medGCP.rotation.y += delta * 0.8;
      if (this.medHilti) this.medHilti.rotation.y -= delta * 0.9;
      if (this.medAPU) this.medAPU.rotation.y += delta * 0.7;
    }

    this.renderer.render(this.scene, this.camera);
  }

  public dispose(): void {
    this.isDisposed = true;
    cancelAnimationFrame(this.animId);
    if (this.renderer.domElement.parentElement) {
      this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
    }
    this.renderer.dispose();
  }
}
