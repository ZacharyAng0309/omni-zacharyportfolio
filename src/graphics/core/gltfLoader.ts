import * as THREE from 'three';
import type { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

/**
 * Resolves relative asset paths cleanly against browser or headless JSDOM origins.
 */
export function resolveAssetUrl(url: string): string {
  if (
    url.startsWith('http://') ||
    url.startsWith('https://') ||
    url.startsWith('data:') ||
    url.startsWith('blob:')
  ) {
    return url;
  }
  const origin =
    typeof window !== 'undefined' &&
    window.location?.origin &&
    window.location.origin !== 'null'
      ? window.location.origin
      : 'http://localhost:3000';
  return url.startsWith('/') ? `${origin}${url}` : `${origin}/${url}`;
}

/**
 * Creates a GLTFLoader configured with Three.js MeshoptDecoder so all
 * EXT_meshopt_compression GLB assets decode cleanly across Acts 1-6 and
 * the companion character without bundle bloat.
 */
export async function createGltfLoader(): Promise<GLTFLoader> {
  const [{ GLTFLoader: LoaderClass }, { MeshoptDecoder }] = await Promise.all([
    import('three/examples/jsm/loaders/GLTFLoader.js'),
    import('three/examples/jsm/libs/meshopt_decoder.module.js'),
  ]);
  await MeshoptDecoder.ready;
  const loader = new LoaderClass();
  loader.setMeshoptDecoder(MeshoptDecoder);
  return loader;
}

/**
 * Applies the procedural PMREM studio EnvMap per-material across diorama GLBs and fallbacks,
 * keeping scene.environment strictly null while delivering glossy/metallic specular highlights.
 */
export function applyStudioEnvMapToRoot(
  root: THREE.Object3D,
  envMap: THREE.Texture | null
): void {
  root.traverse((child) => {
    if (!(child as THREE.Mesh).isMesh) return;
    const mesh = child as THREE.Mesh;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const mat of mats) {
      if (!mat) continue;
      const stdMat = mat as THREE.MeshStandardMaterial;
      if (stdMat.isMeshStandardMaterial) {
        stdMat.envMap = envMap;
        const isGlossyOrMetal = stdMat.metalness > 0.25 || stdMat.roughness < 0.42;
        stdMat.envMapIntensity = isGlossyOrMetal ? 1.15 : 0.42;
        stdMat.needsUpdate = true;
      }
    }
  });
}
