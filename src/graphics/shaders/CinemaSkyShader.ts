import * as THREE from 'three';
import cinemaSkyVert from './cinemaSky.vert.glsl?raw';
import cinemaSkyFrag from './cinemaSky.frag.glsl?raw';

export interface CinemaSkyPalette {
  zenith: number;
  horizon: number;
  glow: number;
  nadir: number;
  sunDir: readonly [number, number, number];
  glowIntensity: number;
  nebulaIntensity: number;
  starIntensity: number;
}

export const CINEMA_SKY_PALETTES: readonly CinemaSkyPalette[] = [
  // Act 0 (#hero): Sovereign Titanium Atelier Studio Cyclorama
  {
    zenith: 0x05060a,
    horizon: 0x11131b,
    glow: 0xc8a97e,
    nadir: 0x040508,
    sunDir: [0.18, 0.14, -1.0],
    glowIntensity: 0.24,
    nebulaIntensity: 0.06,
    starIntensity: 0.0,
  },
  // Act 1 (#timeline): Grand Cathedral Library
  {
    zenith: 0x0d0907,
    horizon: 0x2b190d,
    glow: 0xd4964a,
    nadir: 0x070504,
    sunDir: [0.04, 0.24, -1.0],
    glowIntensity: 0.56,
    nebulaIntensity: 0.14,
    starIntensity: 0.10,
  },
  // Act 2 (#vault): IMAX Keynote Arena
  {
    zenith: 0x050a18,
    horizon: 0x102b4d,
    glow: 0x38bdf8,
    nadir: 0x040710,
    sunDir: [0.0, 0.28, -1.0],
    glowIntensity: 0.80,
    nebulaIntensity: 0.52,
    starIntensity: 0.14,
  },
  // Act 3 (#summit): Swiss Alps Golden Sunrise
  {
    zenith: 0x112038,
    horizon: 0x804720,
    glow: 0xf7be5c,
    nadir: 0x0d131f,
    sunDir: [-0.22, 0.16, -1.0],
    glowIntensity: 0.88,
    nebulaIntensity: 0.32,
    starIntensity: 0.14,
  },
  // Act 4 (#ai-solutions): Cyber-Amber AI Reactor Vault
  {
    zenith: 0x090606,
    horizon: 0x2b130a,
    glow: 0xd97724,
    nadir: 0x060404,
    sunDir: [0.10, 0.12, -1.0],
    glowIntensity: 0.66,
    nebulaIntensity: 0.38,
    starIntensity: 0.06,
  },
  // Act 5 (#contact): Cosmic Solar-Eclipse Horizon
  {
    zenith: 0x030710,
    horizon: 0x082638,
    glow: 0x2dd4bf,
    nadir: 0x02050a,
    sunDir: [-0.02, 0.18, -1.0],
    glowIntensity: 0.78,
    nebulaIntensity: 0.78,
    starIntensity: 0.95,
  },
] as const;

export interface CinemaSkyController {
  mesh: THREE.Mesh;
  material: THREE.ShaderMaterial;
  update: (scrollProgress: number, cameraPos: THREE.Vector3, time: number, isReducedMotion: boolean) => void;
  dispose: () => void;
}

export function createCinemaSkyDome(): CinemaSkyController {
  const geo = new THREE.SphereGeometry(88, 32, 20);
  const first = CINEMA_SKY_PALETTES[0]!;

  const uniforms: { [uniform: string]: THREE.IUniform } = {
    uZenithColor: { value: new THREE.Color(first.zenith) },
    uHorizonColor: { value: new THREE.Color(first.horizon) },
    uGlowColor: { value: new THREE.Color(first.glow) },
    uNadirColor: { value: new THREE.Color(first.nadir) },
    uSunDir: { value: new THREE.Vector3(first.sunDir[0], first.sunDir[1], first.sunDir[2]).normalize() },
    uGlowIntensity: { value: first.glowIntensity },
    uNebulaIntensity: { value: first.nebulaIntensity },
    uStarIntensity: { value: first.starIntensity },
    uTime: { value: 0 },
  };

  const material = new THREE.ShaderMaterial({
    vertexShader: cinemaSkyVert,
    fragmentShader: cinemaSkyFrag,
    uniforms,
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
  });

  const mesh = new THREE.Mesh(geo, material);
  mesh.name = 'CinemaSkyDome';
  mesh.renderOrder = -20;
  mesh.frustumCulled = false;

  const nextZenith = new THREE.Color();
  const nextHorizon = new THREE.Color();
  const nextGlow = new THREE.Color();
  const nextNadir = new THREE.Color();
  const nextSun = new THREE.Vector3();

  const update = (
    scrollProgress: number,
    cameraPos: THREE.Vector3,
    time: number,
    isReducedMotion: boolean
  ): void => {
    mesh.position.copy(cameraPos);

    const clampedSp = THREE.MathUtils.clamp(scrollProgress, 0, 1);
    const segment = clampedSp * 5.0;
    const idx = Math.min(Math.floor(segment), 4);
    const w = segment - idx;

    const a = CINEMA_SKY_PALETTES[idx]!;
    const b = CINEMA_SKY_PALETTES[idx + 1]!;

    (uniforms['uZenithColor']!.value as THREE.Color)
      .setHex(a.zenith)
      .lerp(nextZenith.setHex(b.zenith), w);
    (uniforms['uHorizonColor']!.value as THREE.Color)
      .setHex(a.horizon)
      .lerp(nextHorizon.setHex(b.horizon), w);
    (uniforms['uGlowColor']!.value as THREE.Color)
      .setHex(a.glow)
      .lerp(nextGlow.setHex(b.glow), w);
    (uniforms['uNadirColor']!.value as THREE.Color)
      .setHex(a.nadir)
      .lerp(nextNadir.setHex(b.nadir), w);

    const sunVec = uniforms['uSunDir']!.value as THREE.Vector3;
    sunVec.set(a.sunDir[0], a.sunDir[1], a.sunDir[2]);
    nextSun.set(b.sunDir[0], b.sunDir[1], b.sunDir[2]);
    sunVec.lerp(nextSun, w).normalize();

    uniforms['uGlowIntensity']!.value = THREE.MathUtils.lerp(a.glowIntensity, b.glowIntensity, w);
    uniforms['uNebulaIntensity']!.value = THREE.MathUtils.lerp(a.nebulaIntensity, b.nebulaIntensity, w);
    uniforms['uStarIntensity']!.value = THREE.MathUtils.lerp(a.starIntensity, b.starIntensity, w);
    uniforms['uTime']!.value = isReducedMotion ? 0 : time;
  };

  const dispose = (): void => {
    geo.dispose();
    material.dispose();
  };

  return { mesh, material, update, dispose };
}
