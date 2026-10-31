import * as THREE from 'three';

export type GraphicsBackend = 'webgpu' | 'webgl2';

export interface EngineOptions {
  container: HTMLElement;
  width?: number;
  height?: number;
}

/**
 * Recursive deterministic VRAM disposal of all geometries, materials,
 * textures, and buffers attached to an Object3D hierarchy (Invariant 1).
 */
export function disposeVRAM(root: THREE.Object3D, renderer?: THREE.WebGLRenderer): void {
  root.traverse((object) => {
    // 1. Dispose Geometry
    if ('geometry' in object && object.geometry) {
      const geo = object.geometry as THREE.BufferGeometry;
      geo.dispose();
    }

    // 2. Dispose Materials & Attached Textures
    if ('material' in object && object.material) {
      const rawMat = object.material;
      const materials = Array.isArray(rawMat) ? rawMat : [rawMat];

      for (const mat of materials) {
        if (!mat) continue;

        // Dispose textures on material fields
        const matRecord = mat as unknown as Record<string, unknown>;
        const textureKeys = [
          'map',
          'alphaMap',
          'aoMap',
          'bumpMap',
          'displacementMap',
          'emissiveMap',
          'envMap',
          'lightMap',
          'metalnessMap',
          'normalMap',
          'roughnessMap',
          'specularMap',
          'clearcoatMap',
          'clearcoatRoughnessMap',
          'clearcoatNormalMap',
          'transmissionMap',
          'thicknessMap',
        ];

        for (const key of textureKeys) {
          const val = matRecord[key];
          if (val && typeof val === 'object' && 'dispose' in val && typeof (val as THREE.Texture).dispose === 'function') {
            (val as THREE.Texture).dispose();
          }
        }

        mat.dispose();
      }
    }
  });

  // Clear children
  while (root.children.length > 0) {
    const child = root.children[0];
    if (child) {
      root.remove(child);
    }
  }

  // 3. Dispose WebGLRenderer if provided
  if (renderer) {
    try {
      renderer.setAnimationLoop(null);
      renderer.dispose();
      if (renderer.forceContextLoss) {
        renderer.forceContextLoss();
      }
      if (renderer.domElement && renderer.domElement.parentElement) {
        renderer.domElement.parentElement.removeChild(renderer.domElement);
      }
    } catch {
      // Graceful teardown in headless/JSDOM environments
    }
  }
}

/**
 * Engine
 * Encapsulates the WebGLRenderer lifecycle, ACESFilmic tone mapping,
 * DPR clamping (Math.min(devicePixelRatio, 1.5)), canvas resizing,
 * and 100% deterministic VRAM memory disposal.
 */
export class Engine {
  private container: HTMLElement;
  private renderer: THREE.WebGLRenderer;
  private backend: GraphicsBackend = 'webgl2';
  private width: number;
  private height: number;
  private isDisposed: boolean = false;

  constructor(options: EngineOptions) {
    this.container = options.container;
    this.width = options.width || options.container.clientWidth || (typeof window !== 'undefined' ? window.innerWidth : 800);
    this.height = options.height || options.container.clientHeight || (typeof window !== 'undefined' ? window.innerHeight : 600);

    this.detectGraphicsBackend();

    // 1. WebGL Renderer with High-Precision Standards
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    // Invariant 3: Clamped Device Pixel Ratio (max 1.5)
    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio : 1;
    this.renderer.setPixelRatio(Math.min(dpr, 1.5));
    this.renderer.setSize(this.width, this.height);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;

    this.container.appendChild(this.renderer.domElement);
  }

  private detectGraphicsBackend(): void {
    if (typeof navigator !== 'undefined' && 'gpu' in navigator && Boolean(navigator.gpu)) {
      this.backend = 'webgpu';
    } else {
      this.backend = 'webgl2';
    }
  }

  public getBackend(): GraphicsBackend {
    return this.backend;
  }

  public isWebGPUSupported(): boolean {
    return this.backend === 'webgpu';
  }

  public getRenderer(): THREE.WebGLRenderer {
    return this.renderer;
  }

  public getDomElement(): HTMLCanvasElement {
    return this.renderer.domElement;
  }

  public resize(width?: number, height?: number): { width: number; height: number; aspect: number } {
    if (this.isDisposed) return { width: this.width, height: this.height, aspect: this.width / this.height };

    this.width = width || this.container.clientWidth || (typeof window !== 'undefined' ? window.innerWidth : 800);
    this.height = height || this.container.clientHeight || (typeof window !== 'undefined' ? window.innerHeight : 600);

    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio : 1;
    this.renderer.setPixelRatio(Math.min(dpr, 1.5));
    this.renderer.setSize(this.width, this.height);

    return {
      width: this.width,
      height: this.height,
      aspect: this.width / Math.max(this.height, 1),
    };
  }

  public render(scene: THREE.Scene, camera: THREE.Camera): void {
    if (this.isDisposed) return;
    this.renderer.render(scene, camera);
  }

  public dispose(scene?: THREE.Scene): void {
    if (this.isDisposed) return;
    this.isDisposed = true;

    if (scene) {
      disposeVRAM(scene, this.renderer);
    } else {
      disposeVRAM(new THREE.Group(), this.renderer);
    }
  }
}
