import type * as THREE from 'three';
import type { SceneController } from '../graphics/SceneController';

declare global {
  interface Window {
    __sceneController?: SceneController;
    THREE?: typeof THREE;
  }

  interface Navigator {
    gpu?: unknown;
  }
}

export {};
