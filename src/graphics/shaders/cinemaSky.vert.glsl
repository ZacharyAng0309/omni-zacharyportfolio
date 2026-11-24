varying vec3 vWorldDir;

void main() {
  vWorldDir = position;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
