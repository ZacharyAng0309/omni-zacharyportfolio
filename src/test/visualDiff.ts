import * as fs from 'node:fs';
import * as path from 'node:path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

export interface VisualDiffOptions {
  readonly threshold?: number;
  readonly maxDiffPixelRatio?: number;
  readonly updateBaselines?: boolean;
}

export interface VisualDiffResult {
  readonly match: boolean;
  readonly diffPixels: number;
  readonly totalPixels: number;
  readonly diffRatio: number;
  readonly baselinePath: string;
  readonly actualPath: string;
  readonly diffPath?: string;
  readonly initializedBaseline?: boolean;
}

/**
 * Deterministically compares a rendered screenshot against a golden baseline PNG.
 * If baseline does not exist (or updateBaselines is true), the current actual screenshot
 * is initialized as the golden reference.
 *
 * Mismatches exceeding maxDiffPixelRatio (default 1.5%) write a diff PNG highlighting
 * altered pixels in neon red (#ff0050) and return match: false.
 */
export function verifyScreenshotAgainstBaseline(
  actualPath: string,
  baselinePath: string,
  diffOutputPath: string,
  options: VisualDiffOptions = {}
): VisualDiffResult {
  const threshold = options.threshold ?? 0.1;
  const maxDiffPixelRatio = options.maxDiffPixelRatio ?? 0.015;
  const shouldUpdate = Boolean(options.updateBaselines || process.env.UPDATE_BASELINES === '1');

  const baselineDir = path.dirname(baselinePath);
  if (!fs.existsSync(baselineDir)) {
    fs.mkdirSync(baselineDir, { recursive: true });
  }

  // 1. First run / baseline initialization or explicit update
  if (!fs.existsSync(baselinePath) || shouldUpdate) {
    fs.copyFileSync(actualPath, baselinePath);
    return {
      match: true,
      diffPixels: 0,
      totalPixels: 0,
      diffRatio: 0,
      baselinePath,
      actualPath,
      initializedBaseline: true,
    };
  }

  // 2. Load and validate both PNG buffers
  const actualPng = PNG.sync.read(fs.readFileSync(actualPath));
  const baselinePng = PNG.sync.read(fs.readFileSync(baselinePath));

  if (actualPng.width !== baselinePng.width || actualPng.height !== baselinePng.height) {
    throw new Error(
      `Visual dimension mismatch for ${path.basename(actualPath)}: actual is ${actualPng.width}x${actualPng.height}, but baseline is ${baselinePng.width}x${baselinePng.height}`
    );
  }

  const { width, height } = actualPng;
  const totalPixels = width * height;
  const diffPng = new PNG({ width, height });

  // 3. Pixel-level comparison with anti-aliasing detection
  const diffPixels = pixelmatch(
    actualPng.data,
    baselinePng.data,
    diffPng.data,
    width,
    height,
    {
      threshold,
      includeAA: false,
      diffColor: [255, 0, 80],
    }
  );

  const diffRatio = diffPixels / totalPixels;
  const match = diffRatio <= maxDiffPixelRatio;

  // 4. Output diff PNG if mismatch exceeds tolerance
  if (!match) {
    const diffDir = path.dirname(diffOutputPath);
    if (!fs.existsSync(diffDir)) {
      fs.mkdirSync(diffDir, { recursive: true });
    }
    fs.writeFileSync(diffOutputPath, PNG.sync.write(diffPng));
    return {
      match: false,
      diffPixels,
      totalPixels,
      diffRatio,
      baselinePath,
      actualPath,
      diffPath: diffOutputPath,
      initializedBaseline: false,
    };
  }

  // Clean up any stale diff file from earlier runs if test now passes
  if (fs.existsSync(diffOutputPath)) {
    try {
      fs.unlinkSync(diffOutputPath);
    } catch {}
  }

  return {
    match: true,
    diffPixels,
    totalPixels,
    diffRatio,
    baselinePath,
    actualPath,
    initializedBaseline: false,
  };
}
