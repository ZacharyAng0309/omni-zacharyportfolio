uniform vec3 uZenithColor;
uniform vec3 uHorizonColor;
uniform vec3 uGlowColor;
uniform vec3 uNadirColor;
uniform vec3 uSunDir;
uniform float uGlowIntensity;
uniform float uNebulaIntensity;
uniform float uStarIntensity;
uniform float uTime;

varying vec3 vWorldDir;

float hash31(vec3 p) {
  p = fract(p * 0.1031);
  p += dot(p, p.yzx + 33.33);
  return fract((p.x + p.y) * p.z);
}

void main() {
  vec3 dir = normalize(vWorldDir);
  float y = dir.y;

  // Base vertical sky / atmospheric gradient
  float upperBlend = clamp(1.0 - exp(-max(y, 0.0) * 3.4), 0.0, 1.0);
  float lowerBlend = clamp(1.0 - exp(-max(-y, 0.0) * 5.2), 0.0, 1.0);
  vec3 skyCol = mix(uHorizonColor, uZenithColor, upperBlend);
  skyCol = mix(skyCol, uNadirColor, lowerBlend);

  // Luminous atmospheric horizon airglow band
  float horizonBand = exp(-abs(y + 0.015) * 9.5);
  skyCol += uGlowColor * horizonBand * (0.35 + 0.35 * uGlowIntensity);

  // Wide & mid Mie atmospheric bloom toward celestial / studio source direction
  float sunCos = max(dot(dir, normalize(uSunDir)), 0.0);
  float wideHaze = pow(sunCos, 6.0) * 0.42;
  float coreScatter = pow(sunCos, 38.0) * 0.65;
  skyCol += uGlowColor * (wideHaze + coreScatter) * uGlowIntensity;

  // Flowing cinema nebula / volumetric spotlight wash in mid-upper sky
  float azimuth = atan(dir.z, dir.x);
  float waveA = sin(azimuth * 3.0 + uTime * 0.06 + y * 5.0);
  float waveB = cos(azimuth * 5.0 - uTime * 0.04 + y * 3.5);
  float auroraRibbon = smoothstep(-0.15, 0.85, waveA * waveB) * smoothstep(0.0, 0.45, y) * (1.0 - smoothstep(0.45, 0.92, y));
  skyCol += mix(uGlowColor, uHorizonColor * 1.4, 0.4) * auroraRibbon * 0.28 * uNebulaIntensity;

  // Subtle pinpoint stars in upper celestial sky (zero flicker in reduced motion since uTime can pause)
  if (uStarIntensity > 0.01 && y > 0.04) {
    vec3 starCell = floor(dir * 165.0);
    float seed = hash31(starCell);
    if (seed > 0.992) {
      vec3 cellFrac = fract(dir * 165.0) - 0.5;
      float dist = length(cellFrac);
      float twinkle = 0.72 + 0.28 * sin(uTime * 1.8 + seed * 120.0);
      float starMask = smoothstep(0.28, 0.02, dist) * smoothstep(0.04, 0.38, y);
      skyCol += vec3(0.95, 0.97, 1.0) * starMask * twinkle * uStarIntensity;
    }
  }

  gl_FragColor = vec4(skyCol, 1.0);
}
