import fs from 'node:fs';

const glbPath = 'C:\\Users\\ziyan\\AppData\\Local\\Temp\\gradio\\5e3142a9a705ff5d2d0e939ff6ff7dabfa233fda841c437f0b29f56e03544a0b\\sample_2026-10-13T194436.622.glb';
const buf = fs.readFileSync(glbPath);

const magic = buf.toString('utf8', 0, 4);
const version = buf.readUInt32LE(4);
const length = buf.readUInt32LE(8);

console.log({ magic, version, length });

const chunk0Length = buf.readUInt32LE(12);
const chunk0Type = buf.toString('utf8', 16, 20);
const jsonStr = buf.toString('utf8', 20, 20 + chunk0Length);
const gltf = JSON.parse(jsonStr);

console.log('Images:', gltf.images);
console.log('Materials:', JSON.stringify(gltf.materials, null, 2));
console.log('BufferViews:', gltf.bufferViews);
console.log('Accessors count:', gltf.accessors?.length);
console.log('Meshes:', JSON.stringify(gltf.meshes, null, 2));

const chunk1Offset = 20 + chunk0Length;
const chunk1Length = buf.readUInt32LE(chunk1Offset);
const chunk1Type = buf.toString('utf8', chunk1Offset + 4, chunk1Offset + 8);
console.log({ chunk1Type, chunk1Length });

if (gltf.images) {
  gltf.images.forEach((img, idx) => {
    const bv = gltf.bufferViews[img.bufferView];
    console.log(`Image ${idx} (${img.mimeType}): offset ${bv.byteOffset || 0}, length ${bv.byteLength}`);
  });
}
