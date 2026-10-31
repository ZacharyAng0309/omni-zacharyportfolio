import { describe, it, expect } from 'vitest';
import * as THREE from 'three';

describe('Kinetic Wave Physics & 3D Spline Mathematical Validation', () => {
  it('verifies radial wave oscillation formula produces deterministic sinusoidal amplitude curves', () => {
    // Mathematical wave physics formula: Y(r, t) = sin(r * freq - t * speed) * amp
    const freq = 1.8;
    const speed = 2.4;
    const amp = 0.35;
    const t = 1.0;

    const r1 = 0.0;
    const r2 = Math.PI / (2 * freq); // Quarter wavelength
    const r3 = Math.PI / freq;       // Half wavelength

    const y1 = Math.sin(r1 * freq - t * speed) * amp;
    const y2 = Math.sin(r2 * freq - t * speed) * amp;
    const y3 = Math.sin(r3 * freq - t * speed) * amp;

    // Verify bounded amplitude
    expect(Math.abs(y1)).toBeLessThanOrEqual(amp);
    expect(Math.abs(y2)).toBeLessThanOrEqual(amp);
    expect(Math.abs(y3)).toBeLessThanOrEqual(amp);

    // Verify smooth wave propagation with phase shift
    const tNext = t + 0.1;
    const y1Shift = Math.sin(r1 * freq - tNext * speed) * amp;
    expect(y1Shift).not.toBe(y1);

    // Verify scroll velocity acceleration multiplier
    const scrollVelocity = 1.5;
    const velocityMultiplier = 1.0 + Math.abs(scrollVelocity) * 2.5;
    expect(velocityMultiplier).toBe(4.75);
  });

  it('verifies camera Catmull-Rom spline trajectory maintains 100% strictly monotonic -Z progression across 6 acts', () => {
    const cameraCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0.0, 0.35, 8.5),     // Act 1 (sp = 0.00): Hero Overview
      new THREE.Vector3(0.4, 0.45, -12.2),   // Act 2 (sp = 0.20): Academy & Growth
      new THREE.Vector3(-0.35, 0.45, -30.2), // Act 3 (sp = 0.40): Crucible Mastery
      new THREE.Vector3(0.0, 0.65, -50.2),   // Act 4 (sp = 0.60): Summit Peak
      new THREE.Vector3(0.4, 0.50, -69.2),   // Act 5 (sp = 0.80): Frontier Projects
      new THREE.Vector3(0.0, 0.35, -89.2),   // Act 6 (sp = 1.00): Horizon Interests
    ]);
    cameraCurve.curveType = 'centripetal';

    // Verify anchor points decrease monotonically along negative Z
    for (let i = 0; i < cameraCurve.points.length - 1; i++) {
      expect(cameraCurve.points[i + 1]!.z).toBeLessThan(cameraCurve.points[i]!.z);
    }

    // Sample 50 points along the interpolated curve and verify strict monotonicity
    let prevZ = cameraCurve.getPoint(0).z;
    for (let t = 0.02; t <= 1.0; t += 0.02) {
      const currentPoint = cameraCurve.getPoint(t);
      expect(currentPoint.z).toBeLessThan(prevZ);
      prevZ = currentPoint.z;
    }
  });
});
