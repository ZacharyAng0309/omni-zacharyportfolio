/**
 * Resolves static `public/` asset paths against Vite's configured `BASE_URL`
 * (`./` in production builds, `/` in Vitest/dev), preventing root-absolute `/...`
 * 404s when hosted on project subpaths such as GitHub Pages (`/omni-zacharyportfolio/`).
 */
export function assetUrl(relativePath: string, baseOverride?: string): string {
  const clean = relativePath.replace(/^\/+/, '');
  const base = baseOverride ?? import.meta.env.BASE_URL ?? './';
  const normalizedBase = base.endsWith('/') ? base : `${base}/`;
  return `${normalizedBase}${clean}`;
}
