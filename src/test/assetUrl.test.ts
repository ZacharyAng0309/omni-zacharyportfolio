import { describe, expect, it } from 'vitest';
import { assetUrl } from '../utils/assetUrl';

describe('assetUrl subpath resolution', () => {
  it('strips leading slashes and uses default test BASE_URL cleanly', () => {
    expect(assetUrl('/images/zachary_editorial_portrait.webp')).toBe(
      '/images/zachary_editorial_portrait.webp'
    );
    expect(assetUrl('models/zachary_companion.glb')).toBe(
      '/models/zachary_companion.glb'
    );
  });

  it('resolves relative production ./ base without creating root-absolute URLs', () => {
    expect(assetUrl('/models/zachary_companion.glb', './')).toBe(
      './models/zachary_companion.glb'
    );
    expect(assetUrl('models/props/act1_studio.glb', '.')).toBe(
      './models/props/act1_studio.glb'
    );
  });

  it('handles GitHub Pages project subpath bases with or without trailing slash', () => {
    expect(assetUrl('/images/zachary_editorial_portrait.webp', '/omni-zacharyportfolio/')).toBe(
      '/omni-zacharyportfolio/images/zachary_editorial_portrait.webp'
    );
    expect(assetUrl('models/props/act6_horizon.glb', '/omni-zacharyportfolio')).toBe(
      '/omni-zacharyportfolio/models/props/act6_horizon.glb'
    );
  });
});
