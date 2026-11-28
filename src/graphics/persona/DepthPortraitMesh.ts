import * as THREE from 'three';
import { assetUrl } from '../../utils/assetUrl';

export interface DepthPortraitMeshOptions {
  width?: number;
  height?: number;
  texturePath?: string;
  parallaxScale?: number;
  lazy?: boolean;
}

const vertexShader = /* glsl */ `
varying vec2 vUv;
varying vec3 vViewDir;

void main() {
  vUv = uv;
  vec4 worldPos = modelMatrix * vec4(position, 1.0);
  vViewDir = normalize(cameraPosition - worldPos.xyz);
  gl_Position = projectionMatrix * viewMatrix * worldPos;
}
`;

const fragmentShader = /* glsl */ `
uniform sampler2D uTexture;
uniform vec2 uMouse;
uniform float uTime;
uniform float uParallaxScale;
uniform float uGlintIntensity;

varying vec2 vUv;
varying vec3 vViewDir;

void main() {
  // 1. Ray-Marching 2.5D Parallax Occlusion Mapping (POM)
  float numLayers = 16.0;
  float layerDepth = 1.0 / numLayers;
  float currentLayerDepth = 0.0;

  // View-space parallax offset driven by mouse coordinates
  vec2 p = uMouse * uParallaxScale;
  vec2 deltaTexCoords = p / numLayers;

  vec2 currentTexCoords = vUv;
  float currentDepthMapValue = 1.0 - texture2D(uTexture, currentTexCoords).r * 0.55;

  for (int i = 0; i < 16; i++) {
    if (currentLayerDepth >= currentDepthMapValue) break;
    currentTexCoords -= deltaTexCoords;
    currentDepthMapValue = 1.0 - texture2D(uTexture, currentTexCoords).r * 0.55;
    currentLayerDepth += layerDepth;
  }

  // Edge clamping to prevent UV bleeding
  currentTexCoords = clamp(currentTexCoords, 0.005, 0.995);

  // 2. Base Albedo
  vec4 albedo = texture2D(uTexture, currentTexCoords);

  // 3. Normal reconstruction via screen-space derivatives
  vec3 norm = normalize(cross(dFdx(vViewDir), dFdy(vViewDir)));

  // 4. Titanium Spectacles Dynamic Specular Glint
  // Spectacles region: normalized UV centered around x: 0.50, y: 0.62
  vec2 specCenter = vec2(0.50, 0.62);
  float distToGlasses = length((currentTexCoords - specCenter) * vec2(1.0, 2.2));
  float glassesMask = smoothstep(0.18, 0.02, distToGlasses);

  // Periodic specular light sweep across titanium frames
  float sweep = sin(uTime * 1.8 + currentTexCoords.x * 6.0 - currentTexCoords.y * 3.0);
  float glint = pow(max(0.0, sweep), 8.0) * glassesMask * uGlintIntensity;

  // Subtle cyan edge fresnel
  float fresnel = pow(1.0 - max(0.0, dot(vViewDir, vec3(0.0, 0.0, 1.0))), 3.0) * 0.25;
  vec3 cyanFresnel = vec3(0.0, 0.95, 1.0) * fresnel;

  vec3 finalColor = albedo.rgb + vec3(glint * 1.3, glint * 1.4, glint * 1.5) + cyanFresnel;
  gl_FragColor = vec4(finalColor, albedo.a);
}
`;

/**
 * Creates a 2.5D Parallax Occlusion Mapping (POM) holographic portrait mesh.
 */
export class DepthPortraitMesh {
  private mesh: THREE.Mesh;
  private material: THREE.ShaderMaterial;
  private texture: THREE.Texture;
  private texturePath: string;
  private hasLoadedExternalTexture: boolean = false;

  constructor(options: DepthPortraitMeshOptions = {}) {
    const width = options.width ?? 1.8;
    const height = options.height ?? 2.4;
    this.texturePath = options.texturePath ?? assetUrl('images/zachary_editorial_portrait.webp');
    const parallaxScale = options.parallaxScale ?? 0.038;

    const geometry = new THREE.PlaneGeometry(width, height, 32, 32);
    this.texture = this.createFallbackTexture();

    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTexture: { value: this.texture },
        uMouse: { value: new THREE.Vector2(0, 0) },
        uTime: { value: 0 },
        uParallaxScale: { value: parallaxScale },
        uGlintIntensity: { value: 1.0 },
      },
      transparent: true,
      side: THREE.DoubleSide,
    });

    this.mesh = new THREE.Mesh(geometry, this.material);
    this.mesh.name = 'DepthPortraitHologram';

    if (!options.lazy && typeof document !== 'undefined') {
      this.ensureLoaded();
    }
  }

  public ensureLoaded(): void {
    if (this.hasLoadedExternalTexture || typeof document === 'undefined') return;
    this.hasLoadedExternalTexture = true;
    const prevFallback = this.texture;
    const textureLoader = new THREE.TextureLoader();
    textureLoader.load(
      this.texturePath,
      (loadedTex) => {
        this.texture = loadedTex;
        const texUniform = this.material?.uniforms['uTexture'];
        if (texUniform) {
          texUniform.value = loadedTex;
        }
        prevFallback.dispose();
      },
      undefined,
      () => {
        // Keep procedural fallback texture if offline
      }
    );
  }

  private createFallbackTexture(): THREE.CanvasTexture {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 682;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#0a192f';
      ctx.fillRect(0, 0, 512, 682);
      ctx.fillStyle = '#00f2fe';
      ctx.font = 'bold 24px monospace';
      ctx.fillText('ZACHARY PORTRAIT', 120, 340);
    }
    const tex = new THREE.CanvasTexture(canvas);
    tex.needsUpdate = true;
    return tex;
  }

  public getMesh(): THREE.Mesh {
    return this.mesh;
  }

  public update(delta: number, mouseX: number, mouseY: number, isReducedMotion: boolean = false): void {
    const clampedDelta = Math.min(delta, 0.1);
    const timeUniform = this.material.uniforms['uTime'];
    if (timeUniform && !isReducedMotion) {
      timeUniform.value += clampedDelta;
    }
    const mouseUniform = this.material.uniforms['uMouse']?.value as THREE.Vector2 | undefined;
    if (mouseUniform) {
      mouseUniform.set(
        isReducedMotion ? 0 : THREE.MathUtils.clamp(mouseX, -1, 1),
        isReducedMotion ? 0 : THREE.MathUtils.clamp(mouseY, -1, 1)
      );
    }
  }

  public dispose(): void {
    this.mesh.geometry.dispose();
    this.material.dispose();
    if (this.texture) {
      this.texture.dispose();
    }
  }
}
