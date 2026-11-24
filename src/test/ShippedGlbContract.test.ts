import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

interface GltfAccessor {
  bufferView?: number;
  componentType: number;
  count: number;
  type: string;
  min?: number[];
  max?: number[];
}

interface GltfMaterial {
  name?: string;
  alphaMode?: string;
  doubleSided?: boolean;
  normalTexture?: { index: number; texCoord?: number; scale?: number };
  pbrMetallicRoughness?: {
    baseColorFactor?: number[];
    baseColorTexture?: { index: number; texCoord?: number };
    metallicRoughnessTexture?: { index: number; texCoord?: number };
    roughnessFactor?: number;
    metallicFactor?: number;
  };
  extensions?: {
    KHR_materials_specular?: {
      specularFactor?: number;
      specularTexture?: { index: number; texCoord?: number };
    };
  };
}

interface GltfMesh {
  name?: string;
  extras?: { targetNames?: string[] };
  primitives: Array<{
    attributes: Record<string, number>;
    indices?: number;
    material?: number;
    targets?: Array<Record<string, number>>;
  }>;
}

interface GltfJson {
  asset: { version: string };
  extensionsUsed?: string[];
  nodes?: Array<{
    name?: string;
    mesh?: number;
    children?: number[];
    translation?: number[];
    rotation?: number[];
    scale?: number[];
  }>;
  meshes?: GltfMesh[];
  materials?: GltfMaterial[];
  accessors?: GltfAccessor[];
  images?: Array<{ name?: string; mimeType?: string; bufferView?: number }>;
  bufferViews?: Array<{ buffer?: number; byteOffset?: number; byteLength: number }>;
  animations?: Array<{
    name?: string;
    channels: Array<unknown>;
    samplers: Array<unknown>;
  }>;
}

const GLB_MAGIC = 0x46546c67; // "glTF"
const GLB_JSON_CHUNK = 0x4e4f534a; // "JSON"
const PUBLIC_MODELS_DIR = path.resolve(process.cwd(), 'public', 'models');
const ARCHIVED_MODELS_DIR = path.resolve(process.cwd(), 'artifacts', 'archived_public', 'models');

function parseBinaryGlb(
  relativeModelPath: string,
  baseDir: string = PUBLIC_MODELS_DIR
): { byteSize: number; json: GltfJson; binChunk: Buffer } {
  const fullPath = path.join(baseDir, relativeModelPath);
  expect(fs.existsSync(fullPath), `Missing GLB at ${fullPath}`).toBe(true);

  const buf = fs.readFileSync(fullPath);
  expect(buf.length).toBeGreaterThan(20);
  expect(buf.readUInt32LE(0)).toBe(GLB_MAGIC);
  expect(buf.readUInt32LE(4)).toBe(2);
  expect(buf.readUInt32LE(8)).toBe(buf.length);

  const jsonChunkLength = buf.readUInt32LE(12);
  const jsonChunkType = buf.readUInt32LE(16);
  expect(jsonChunkType).toBe(GLB_JSON_CHUNK);

  const jsonText = buf.subarray(20, 20 + jsonChunkLength).toString('utf8').replace(/\0+$/, '');
  const json = JSON.parse(jsonText) as GltfJson;
  expect(json.asset?.version).toBe('2.0');

  const binHeaderOffset = 20 + jsonChunkLength;
  const binChunkLength = buf.readUInt32LE(binHeaderOffset);
  const binChunk = buf.subarray(binHeaderOffset + 8, binHeaderOffset + 8 + binChunkLength);

  return { byteSize: buf.length, json, binChunk };
}

describe('Shipped Binary GLB Contract Verification', () => {
  it('validates archived legacy zachary_character.glb skeleton, meshes, materials, skin continuity, morph targets & eye-fix invariants, and 3.0 MB budget', () => {
    const { byteSize, json, binChunk } = parseBinaryGlb('zachary_character.glb', ARCHIVED_MODELS_DIR);

    // Tiered rigged humanoid avatar GLB budget <= 3.0 MB
    expect(byteSize).toBeLessThanOrEqual(3.0 * 1024 * 1024);

    const nodeNames = new Set((json.nodes ?? []).map((n) => n.name).filter(Boolean));
    const requiredBones = [
      'Hips',
      'Spine',
      'Spine1',
      'Spine2',
      'Neck',
      'Head',
      'LeftShoulder',
      'RightShoulder',
      'LeftArm',
      'RightArm',
      'LeftForeArm',
      'RightForeArm',
      'LeftHand',
      'RightHand',
      'LeftUpLeg',
      'RightUpLeg',
      'LeftLeg',
      'RightLeg',
      'LeftFoot',
      'RightFoot',
    ];
    for (const bone of requiredBones) {
      expect(nodeNames.has(bone), `Missing skeleton bone node "${bone}"`).toBe(true);
    }

    // 30 finger phalanges (Thumb/Index/Middle/Ring/Pinky 1..3 on both hands)
    const fingerGroups = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'] as const;
    for (const side of ['LeftHand', 'RightHand'] as const) {
      for (const finger of fingerGroups) {
        for (const phalanx of [1, 2, 3]) {
          const fingerNode = `${side}${finger}${phalanx}`;
          expect(nodeNames.has(fingerNode), `Missing finger bone "${fingerNode}"`).toBe(true);
        }
      }
    }

    // Required mesh nodes (v38 Schema v4 — 14 mesh nodes)
    const requiredMeshes = [
      'SM_Character_Face',
      'SM_Character_Hair',
      'SM_Character_Hands',
      'SM_Cloth_Hoodie',
      'SM_Cloth_Trousers',
      'SM_Cloth_Footwear',
      'Sovereign_Titanium_Spectacles',
      'SM_Character_OralCavity',
      'SM_Character_UpperTeeth',
      'SM_Character_LowerTeeth',
      'SM_Character_Tongue',
      'SM_Character_Eyelids',
      'SM_Character_EyeRight',
      'SM_Character_EyeLeft',
    ];
    for (const meshName of requiredMeshes) {
      expect(nodeNames.has(meshName), `Missing character mesh node "${meshName}"`).toBe(true);
    }

    // Multi-primitive Sovereign_Titanium_Spectacles (metal frame, dark nose/temple pads, transparent lenses)
    const glassesMesh = (json.meshes ?? []).find((m) => m.name === 'Sovereign_Titanium_Spectacles');
    expect(glassesMesh).toBeDefined();
    expect(glassesMesh!.primitives.length).toBe(3);

    // Material slot contracts & skin tone / PBR texture continuity (v40 UV2 base color + UV1 hair detail maps)
    const materials = json.materials ?? [];
    const matMap = new Map(materials.map((m) => [m.name, m]));
    const requiredMaterials = [
      'Zachary_Face_Albedo',
      'M_Hair_v38_CurtainFlow',
      'Zachary_Hands_Albedo',
      'Zachary_Cloth_Hoodie',
      'Zachary_Cloth_Trousers',
      'Zachary_Cloth_Footwear',
      'Glasses_Metal',
      'Glasses_Black',
      'Glasses_Lens',
      'Zachary_Oral_Cavity',
      'Zachary_Enamel',
      'Zachary_Tongue',
      'M_Eyelids_v36',
      'M_Eyes_v36',
    ];
    for (const matName of requiredMaterials) {
      expect(matMap.has(matName), `Missing material slot "${matName}"`).toBe(true);
    }

    const faceMat = matMap.get('Zachary_Face_Albedo')!;
    const eyelidsMat = matMap.get('M_Eyelids_v36')!;
    const handsMat = matMap.get('Zachary_Hands_Albedo')!;
    const hairMat = matMap.get('M_Hair_v38_CurtainFlow')!;
    expect(faceMat.pbrMetallicRoughness?.baseColorTexture).toBeDefined();
    expect(faceMat.pbrMetallicRoughness?.baseColorTexture?.texCoord).toBe(2);
    expect(eyelidsMat.pbrMetallicRoughness?.baseColorTexture).toBeDefined();
    expect(handsMat.pbrMetallicRoughness?.baseColorTexture).toBeDefined();
    expect(handsMat.pbrMetallicRoughness?.metallicRoughnessTexture).toBeDefined();
    expect(hairMat.pbrMetallicRoughness?.baseColorTexture).toBeDefined();
    expect(hairMat.pbrMetallicRoughness?.baseColorTexture?.texCoord).toBe(2);
    expect(hairMat.pbrMetallicRoughness?.metallicRoughnessTexture).toBeDefined();
    expect(hairMat.pbrMetallicRoughness?.metallicRoughnessTexture?.texCoord).toBe(1);
    expect(hairMat.normalTexture).toBeDefined();
    expect(hairMat.normalTexture?.texCoord).toBe(1);
    expect(hairMat.extensions?.KHR_materials_specular?.specularTexture?.texCoord).toBe(1);
    expect(faceMat.pbrMetallicRoughness?.roughnessFactor).toBeCloseTo(0.65, 2);
    expect(eyelidsMat.pbrMetallicRoughness?.roughnessFactor).toBeCloseTo(0.65, 2);
    expect(handsMat.pbrMetallicRoughness?.roughnessFactor).toBeCloseTo(1.0, 2);

    // v40 dedicated fringe UV repair requires TEXCOORD_2 on both SM_Character_Face and SM_Character_Hair while retaining TEXCOORD_0/1
    const faceMeshObj = (json.meshes ?? []).find((m) => m.name === 'SM_Character_Face')!;
    const hairMeshObj = (json.meshes ?? []).find((m) => m.name === 'SM_Character_Hair')!;
    expect(faceMeshObj.primitives[0]?.attributes.TEXCOORD_0).toBeDefined();
    expect(faceMeshObj.primitives[0]?.attributes.TEXCOORD_1).toBeDefined();
    expect(faceMeshObj.primitives[0]?.attributes.TEXCOORD_2).toBeDefined();
    expect(hairMeshObj.primitives[0]?.attributes.TEXCOORD_0).toBeDefined();
    expect(hairMeshObj.primitives[0]?.attributes.TEXCOORD_1).toBeDefined();
    expect(hairMeshObj.primitives[0]?.attributes.TEXCOORD_2).toBeDefined();

    // Every embedded texture stays under 100 KB governance budget
    for (const img of json.images ?? []) {
      const bv = img.bufferView !== undefined ? json.bufferViews?.[img.bufferView] : undefined;
      expect(bv, `Missing bufferView for image "${img.name}"`).toBeDefined();
      expect(bv!.byteLength, `Embedded image "${img.name}" exceeds 100 KB`).toBeLessThanOrEqual(100 * 1024);
    }

    // Optical lenses must be transparent BLEND so eyes stay unobstructed
    const lensMat = matMap.get('Glasses_Lens')!;
    expect(lensMat.alphaMode).toBe('BLEND');
    expect(lensMat.pbrMetallicRoughness?.baseColorFactor?.[3] ?? 1).toBeLessThan(0.05);

    // Schema v4: all 6 facial morph meshes share identical 8 target names & synchronized blink deltas
    const expectedMorphs = [
      'mouthSmileLeft',
      'mouthSmileRight',
      'mouthOpen',
      'jawOpen',
      'eyeBlinkLeft',
      'eyeBlinkRight',
      'browInnerUp',
      'viseme_aa',
    ];
    const facialMorphMeshNames = [
      'SM_Character_Face',
      'SM_Character_OralCavity',
      'SM_Character_UpperTeeth',
      'SM_Character_LowerTeeth',
      'SM_Character_Tongue',
      'SM_Character_Eyelids',
    ];
    for (const morphMeshName of facialMorphMeshNames) {
      const morphMesh = (json.meshes ?? []).find((m) => m.name === morphMeshName);
      expect(morphMesh, `Missing Schema-v4 morph mesh "${morphMeshName}"`).toBeDefined();
      expect(morphMesh!.extras?.targetNames).toEqual(expectedMorphs);
      expect(morphMesh!.primitives[0]?.targets?.length).toBe(expectedMorphs.length);
    }

    const accessors = json.accessors ?? [];
    for (const blinkMeshName of ['SM_Character_Face', 'SM_Character_Eyelids'] as const) {
      const blinkMesh = (json.meshes ?? []).find((m) => m.name === blinkMeshName)!;
      const targetNames = blinkMesh.extras?.targetNames ?? [];
      const primTargets = blinkMesh.primitives[0]?.targets ?? [];
      for (const blinkName of ['eyeBlinkLeft', 'eyeBlinkRight']) {
        const idx = targetNames.indexOf(blinkName);
        const posAccessorIdx = primTargets[idx]?.POSITION;
        expect(posAccessorIdx).toBeDefined();
        const acc = accessors[posAccessorIdx!]!;
        // Eye blink morph target must encode downward/upward eyelid displacement on Y without horizontal distortion
        expect(acc.min?.[1] ?? 0).toBeLessThan(-0.005);
        expect(acc.max?.[1] ?? 0).toBeGreaterThan(0.005);
      }
    }

    // v41 Facial Anatomy & Eye Likeness Contracts:
    // 1. Symmetric forward-facing corneal dome normals, matched left/right eye Z depth, and calibrated warm dark-espresso iris colors
    const bufferViews = json.bufferViews ?? [];
    const eyePoleZ: Record<string, number> = {};
    for (const eyeName of ['SM_Character_EyeRight', 'SM_Character_EyeLeft'] as const) {
      const eyeMesh = (json.meshes ?? []).find((m) => m.name === eyeName)!;
      const posAccIdx = eyeMesh.primitives[0]?.attributes.POSITION;
      const normAccIdx = eyeMesh.primitives[0]?.attributes.NORMAL;
      const colAccIdx = eyeMesh.primitives[0]?.attributes.COLOR_0;
      expect(posAccIdx).toBeDefined();
      expect(normAccIdx).toBeDefined();
      expect(colAccIdx).toBeDefined();
      const posAcc = accessors[posAccIdx!]!;
      const normAcc = accessors[normAccIdx!]!;
      const colAcc = accessors[colAccIdx!]!;
      const posBase = bufferViews[posAcc.bufferView!]!.byteOffset ?? 0;
      const normBase = bufferViews[normAcc.bufferView!]!.byteOffset ?? 0;
      const colBase = bufferViews[colAcc.bufferView!]!.byteOffset ?? 0;
      eyePoleZ[eyeName] = binChunk.readFloatLE(posBase + 8);
      const nx = binChunk.readFloatLE(normBase);
      const ny = binChunk.readFloatLE(normBase + 4);
      const nz = binChunk.readFloatLE(normBase + 8);
      expect(Math.abs(nx), `${eyeName} pupil normal skewed in X (${nx})`).toBeLessThan(0.01);
      expect(Math.abs(ny), `${eyeName} pupil normal skewed in Y (${ny})`).toBeLessThan(0.01);
      expect(nz, `${eyeName} pupil normal must point straight forward (+Z)`).toBeGreaterThan(0.999);
      // Iris rings 1..2 (vertices 33..96) must not crush to black under ACES Filmic (linear R in [0.035, 0.10])
      let irisRSum = 0;
      for (let vi = 33; vi < 97; vi++) {
        irisRSum += binChunk.readFloatLE(colBase + vi * 12);
      }
      const irisRMean = irisRSum / 64;
      expect(irisRMean, `${eyeName} iris linear R (${irisRMean.toFixed(4)}) crushed too dark`).toBeGreaterThanOrEqual(0.035);
      expect(irisRMean, `${eyeName} iris linear R (${irisRMean.toFixed(4)}) too bright`).toBeLessThanOrEqual(0.10);
    }
    expect(
      Math.abs(eyePoleZ.SM_Character_EyeLeft! - eyePoleZ.SM_Character_EyeRight!),
      'Left and right eye globes must share symmetric Z depth (< 0.1mm)'
    ).toBeLessThan(0.0001);

    // 1b. Zero stray (0, 0) TEXCOORD_2 coordinates on SM_Character_Face triangles (eliminates black UV-void lip sampling)
    const fUv2Acc = accessors[faceMeshObj.primitives[0]!.attributes.TEXCOORD_2!]!;
    const fIdxAcc = accessors[faceMeshObj.primitives[0]!.indices!]!;
    const fUv2Base = bufferViews[fUv2Acc.bufferView!]!.byteOffset ?? 0;
    const fIdxBase = bufferViews[fIdxAcc.bufferView!]!.byteOffset ?? 0;
    let zeroUv2Verts = 0;
    const checkedFaceVerts = new Set<number>();
    for (let k = 0; k < fIdxAcc.count; k++) {
      const vi = fIdxAcc.componentType === 5123
        ? binChunk.readUInt16LE(fIdxBase + k * 2)
        : binChunk.readUInt32LE(fIdxBase + k * 4);
      if (checkedFaceVerts.has(vi)) continue;
      checkedFaceVerts.add(vi);
      const u = binChunk.readFloatLE(fUv2Base + vi * 8);
      const v = binChunk.readFloatLE(fUv2Base + vi * 8 + 4);
      if (u < 1e-4 && v < 1e-4) zeroUv2Verts++;
    }
    expect(zeroUv2Verts, 'SM_Character_Face triangles contain stray (0,0) TEXCOORD_2 vertices').toBe(0);

    // 2. Front chin & lower jaw vertices (Y >= 1.478, Z >= 0.068) follow Head bone 100% (eliminates chin shear under yaw/pitch)
    const skins = (json as unknown as { skins?: Array<{ joints: number[] }> }).skins ?? [];
    const headJointIdx = skins[0]!.joints.findIndex((nodeIdx) => json.nodes?.[nodeIdx]?.name === 'Head');
    expect(headJointIdx).toBeGreaterThanOrEqual(0);
    const fPosAcc = accessors[faceMeshObj.primitives[0]!.attributes.POSITION!]!;
    const fJntAcc = accessors[faceMeshObj.primitives[0]!.attributes.JOINTS_0!]!;
    const fWgtAcc = accessors[faceMeshObj.primitives[0]!.attributes.WEIGHTS_0!]!;
    const fPosBase = bufferViews[fPosAcc.bufferView!]!.byteOffset ?? 0;
    const fJntBase = bufferViews[fJntAcc.bufferView!]!.byteOffset ?? 0;
    const fWgtBase = bufferViews[fWgtAcc.bufferView!]!.byteOffset ?? 0;
    let chinVertsChecked = 0;
    let minChinHeadWeight = 1.0;
    for (let v = 0; v < fPosAcc.count; v++) {
      const y = binChunk.readFloatLE(fPosBase + v * 12 + 4);
      const z = binChunk.readFloatLE(fPosBase + v * 12 + 8);
      if (y >= 1.478 && z >= 0.068) {
        chinVertsChecked++;
        let hw = 0;
        for (let k = 0; k < 4; k++) {
          const j = fJntAcc.componentType === 5121
            ? binChunk.readUInt8(fJntBase + v * 4 + k)
            : binChunk.readUInt16LE(fJntBase + v * 8 + k * 2);
          const w = binChunk.readFloatLE(fWgtBase + v * 16 + k * 4);
          if (j === headJointIdx) hw += w;
        }
        if (hw < minChinHeadWeight) minChinHeadWeight = hw;
      }
    }
    expect(chinVertsChecked).toBeGreaterThan(1000);
    expect(minChinHeadWeight).toBeGreaterThan(0.999);
  });

  it('validates shipped Acts 1–6 diorama GLB nodes, material slots, SM_Mount_Pilatus_Massif alpine geometry, and 1.5 MB prop budgets', () => {
    const dioramaContracts: Array<{
      file: string;
      requiredNodes: string[];
      requiredMaterials: string[];
    }> = [
      {
        file: 'props/act1_studio.glb',
        requiredNodes: [
          'SM_Island_Act1',
          'SM_Atelier_Pedestal',
          'Prop_Blueprint_Tier1',
          'Prop_Blueprint_Tier2',
          'Prop_Blueprint_Tier3',
          'SM_Core_Nucleus',
          'SM_Core_Filament',
          'SM_Gyro_Gimbal_Outer',
          'SM_Gyro_Gimbal_Inner',
        ],
        requiredMaterials: [
          'Mat_Act1_ObsidianBasalt',
          'Mat_Act1_BrushedTitanium',
          'Mat_Act1_NaturalTitanium',
          'Mat_Act1_ChampagneBrass',
          'Mat_Act1_OpticalGlass',
          'Mat_Act1_WarmCove',
        ],
      },
      {
        file: 'props/act2_academy.glb',
        requiredNodes: [
          'SM_Island_Act2',
          'SM_Arched_Bookshelf',
          'SM_Pedestal_Lectern',
          'SM_Banker_Lamp',
          'Prop_Book_Vol1',
          'Prop_Book_Vol2',
          'Prop_Book_Vol3',
          'Prop_Book_Vol4',
        ],
        requiredMaterials: [
          'M_Heritage_Mahogany',
          'M_Warm_Parchment_Stone',
          'M_Antique_Brass',
          'M_Banker_Emerald_Glass',
          'M_Prop_Book_Vol1',
          'M_Prop_Book_Vol2',
          'M_Prop_Book_Vol3',
          'M_Prop_Book_Vol4',
        ],
      },
      {
        file: 'props/act3_crucible.glb',
        requiredNodes: ['SM_Island_Act3', 'SM_GDSC_Lectern', 'SM_Hologram_Projector_Ring'],
        requiredMaterials: [
          'M_Keynote_Slate',
          'M_Stage_Gold',
          'M_Acoustic_Alabaster',
          'M_Smoked_Bronze_Glass',
        ],
      },
      {
        file: 'props/act4_summit.glb',
        requiredNodes: [
          'SM_Island_Act4',
          'SM_Mount_Pilatus_Massif',
          'Prop_Beacon_Schaan',
          'Prop_Trophy_Hilti24k',
          'Prop_Star_PressFrame',
        ],
        requiredMaterials: [
          'M_Alpine_Gneiss_Stone',
          'M_Alpine_Snow_Marble',
          'M_24K_Hilti_Gold',
          'M_Hilti_Crimson',
        ],
      },
      {
        file: 'props/act5_frontier.glb',
        requiredNodes: [
          'SM_Island_Act5',
          'SM_Orbital_Lab_Rings',
          'Prop_Core_Hireti_T1',
          'Prop_Core_Hireti_T2',
          'Prop_Core_Hireti_T3',
        ],
        requiredMaterials: [
          'M_Anodized_Graphite',
          'M_CNC_Brushed_Aluminum',
          'M_International_Orange',
          'M_Lab_Quartz_Glass',
        ],
      },
      {
        file: 'props/act6_horizon.glb',
        requiredNodes: [
          'SM_Island_Act6',
          'SM_Stargate_PortalArch',
          'SM_Portal_InnerRing',
          'Prop_Beacon_Dispatch',
        ],
        requiredMaterials: [
          'M_Dawn_Travertine',
          'M_Obsidian_Reflection',
          'M_Champagne_Pearl_Bronze',
        ],
      },
    ];

    for (const contract of dioramaContracts) {
      const { byteSize, json } = parseBinaryGlb(contract.file);
      expect(byteSize, `${contract.file} exceeds 1.5 MB prop budget`).toBeLessThanOrEqual(
        1.5 * 1024 * 1024
      );

      const nodeByName = new Map((json.nodes ?? []).filter((n) => n.name).map((n) => [n.name!, n]));
      const accessors = json.accessors ?? [];
      for (const reqNode of contract.requiredNodes) {
        const node = nodeByName.get(reqNode);
        expect(node, `${contract.file} missing node "${reqNode}"`).toBeDefined();
        expect(node!.mesh, `${contract.file} node "${reqNode}" has no mesh`).toBeDefined();
        const mesh = json.meshes?.[node!.mesh!];
        expect(mesh, `${contract.file} missing mesh for node "${reqNode}"`).toBeDefined();
        expect(mesh!.primitives.length, `${contract.file} "${reqNode}" has 0 primitives`).toBeGreaterThanOrEqual(1);
        const firstPosIdx = mesh!.primitives[0]?.attributes.POSITION;
        expect(firstPosIdx, `${contract.file} "${reqNode}" missing POSITION attribute`).toBeDefined();
        expect(accessors[firstPosIdx!]?.count ?? 0, `${contract.file} "${reqNode}" has 0 vertices`).toBeGreaterThan(0);
      }

      const matNames = new Set((json.materials ?? []).map((m) => m.name).filter(Boolean));
      for (const reqMat of contract.requiredMaterials) {
        expect(matNames.has(reqMat), `${contract.file} missing material "${reqMat}"`).toBe(true);
      }

      if (contract.file === 'props/act4_summit.glb') {
        const massifNode = nodeByName.get('SM_Mount_Pilatus_Massif')!;
        if (massifNode.scale) {
          for (const s of massifNode.scale) expect(s).toBeCloseTo(1, 3);
        }
        if (massifNode.translation) {
          for (const t of massifNode.translation) expect(t).toBeCloseTo(0, 3);
        }

        const massifMesh = json.meshes![massifNode.mesh!]!;

        // Upgraded sculpted 5-peak faceted alpine massif exports as exactly 2 primitives (gneiss rock + snow cap),
        // replacing the legacy 3-primitive stacked boxes.
        expect(massifMesh.primitives.length).toBe(2);

        const primByMaterial = new Map(
          massifMesh.primitives.map((prim) => {
            const matName = prim.material !== undefined ? json.materials?.[prim.material]?.name : undefined;
            return [matName, prim] as const;
          })
        );
        expect(primByMaterial.has('M_Alpine_Gneiss_Stone')).toBe(true);
        expect(primByMaterial.has('M_Alpine_Snow_Marble')).toBe(true);
        expect(primByMaterial.has('M_24K_Hilti_Gold')).toBe(false);

        const rockPrim = primByMaterial.get('M_Alpine_Gneiss_Stone')!;
        const snowPrim = primByMaterial.get('M_Alpine_Snow_Marble')!;
        expect(rockPrim.attributes.NORMAL).toBeDefined();
        expect(snowPrim.attributes.NORMAL).toBeDefined();
        const rockPos = accessors[rockPrim.attributes.POSITION]!;
        const snowPos = accessors[snowPrim.attributes.POSITION]!;
        const rockIdx = rockPrim.indices !== undefined ? accessors[rockPrim.indices] : undefined;
        const snowIdx = snowPrim.indices !== undefined ? accessors[snowPrim.indices] : undefined;

        // Sculpted 5-peak faceted ridge density far exceeds simple stacked-box primitives
        expect(rockPos.count).toBeGreaterThanOrEqual(400);
        expect(snowPos.count).toBeGreaterThanOrEqual(200);
        expect(rockIdx?.count ?? 0).toBeGreaterThanOrEqual(600);
        expect(snowIdx?.count ?? 0).toBeGreaterThanOrEqual(300);

        // Stratified alpine elevation: base seated near island surface, snowline elevated, Tomlishorn crest > 1.8m
        expect(rockPos.min?.[1] ?? 1).toBeLessThan(0.15);
        expect(snowPos.min?.[1] ?? 0).toBeGreaterThan(0.45);
        expect(snowPos.max?.[1] ?? 0).toBeGreaterThan((rockPos.max?.[1] ?? 99) + 0.5);
        expect(snowPos.max?.[1] ?? 0).toBeGreaterThan(1.8);

        // Broad 5-peak lateral span across the rear horizon with non-degenerate Z ridge depth
        const minX = Math.min(rockPos.min?.[0] ?? 0, snowPos.min?.[0] ?? 0);
        const maxX = Math.max(rockPos.max?.[0] ?? 0, snowPos.max?.[0] ?? 0);
        const minZ = Math.min(rockPos.min?.[2] ?? 0, snowPos.min?.[2] ?? 0);
        const maxZ = Math.max(rockPos.max?.[2] ?? 0, snowPos.max?.[2] ?? 0);
        expect(maxX - minX).toBeGreaterThan(3.2);
        expect(maxZ - minZ).toBeGreaterThan(1.0);
        expect(maxZ).toBeLessThan(-0.5);

        // Low-profile gneiss-and-brass Star Press museum exhibition plinth
        const pressNode = nodeByName.get('Prop_Star_PressFrame')!;
        const pressMesh = json.meshes![pressNode.mesh!]!;
        const pressMats = pressMesh.primitives.map((p) =>
          p.material !== undefined ? json.materials?.[p.material]?.name : undefined
        );
        expect(pressMats).toContain('M_Alpine_Gneiss_Stone');
        expect(pressMats).toContain('M_24K_Hilti_Gold');
        const pressMaxY = Math.max(
          ...pressMesh.primitives.map((p) => accessors[p.attributes.POSITION]?.max?.[1] ?? 0)
        );
        expect(pressMaxY).toBeLessThanOrEqual(1.65);
      }
    }
  });

  it('validates public/models/zachary_companion.glb likeness companion meshes, armature bones, calibrated materials, 4 baked glTF animations, Meshopt, <= 100 KB images, morphs, and 3.0 MB budget', () => {
    const { byteSize, json } = parseBinaryGlb('zachary_companion.glb');

    expect(byteSize).toBeLessThanOrEqual(3.0 * 1024 * 1024);
    expect(json.extensionsUsed ?? []).toContain('EXT_meshopt_compression');
    const bvs = json.bufferViews ?? [];
    for (const [idx, img] of (json.images ?? []).entries()) {
      if (img.bufferView !== undefined) {
        const imgBytes = bvs[img.bufferView]?.byteLength ?? 0;
        expect(imgBytes, `zachary_companion.glb image[${idx}] exceeds 100 KB (${imgBytes} bytes)`).toBeLessThanOrEqual(
          100 * 1024
        );
      }
    }

    const nodeNames = new Set((json.nodes ?? []).map((n) => n.name).filter(Boolean));
    const requiredMeshes = ['SM_Companion_Body', 'SM_Companion_Glasses'];
    for (const meshName of requiredMeshes) {
      expect(nodeNames.has(meshName), `Missing companion mesh node "${meshName}"`).toBe(true);
    }
    const bodyNode = (json.nodes ?? []).find((n) => n.name === 'SM_Companion_Body');
    const bodyMesh = bodyNode?.mesh !== undefined ? json.meshes?.[bodyNode.mesh] : undefined;
    const targetNames = (bodyMesh?.extras as { targetNames?: string[] } | undefined)?.targetNames ?? [];
    for (const morph of ['eyeBlinkLeft', 'eyeBlinkRight', 'mouthSmileLeft', 'mouthSmileRight']) {
      expect(targetNames, `Missing SM_Companion_Body morph "${morph}"`).toContain(morph);
    }

    const requiredBones = [
      'Hips',
      'Spine',
      'Spine1',
      'Neck',
      'Head',
      'LeftShoulder',
      'LeftArm',
      'LeftForeArm',
      'LeftHand',
      'RightShoulder',
      'RightArm',
      'RightForeArm',
      'RightHand',
      'LeftUpLeg',
      'LeftLeg',
      'LeftFoot',
      'RightUpLeg',
      'RightLeg',
      'RightFoot',
    ];
    for (const bone of requiredBones) {
      expect(nodeNames.has(bone), `Missing companion skeleton bone "${bone}"`).toBe(true);
    }

    const matMap = new Map((json.materials ?? []).map((m) => [m.name, m]));
    const requiredMaterials = [
      'Mat_Companion_Body',
      'Mat_Companion_Face',
      'Mat_Companion_GlassesMetal',
      'Mat_Companion_GlassesLens',
    ];
    for (const matName of requiredMaterials) {
      expect(matMap.has(matName), `Missing companion material "${matName}"`).toBe(true);
    }

    expect(matMap.get('Mat_Companion_Body')!.pbrMetallicRoughness?.baseColorTexture).toBeDefined();
    expect(matMap.get('Mat_Companion_Face')!.pbrMetallicRoughness?.baseColorTexture).toBeDefined();
    expect(matMap.get('Mat_Companion_Face')!.pbrMetallicRoughness?.metallicRoughnessTexture).toBeDefined();
    expect(matMap.get('Mat_Companion_Face')!.normalTexture).toBeDefined();

    const lensMat = matMap.get('Mat_Companion_GlassesLens')!;
    expect(lensMat.alphaMode).toBe('BLEND');
    expect(lensMat.pbrMetallicRoughness?.baseColorFactor?.[3] ?? 1).toBeLessThan(0.1);

    const animMap = new Map((json.animations ?? []).map((a) => [a.name, a]));
    for (const clipName of ['Idle_Breathing', 'Walk_Forward', 'Gesture_Present', 'Turn_Greet']) {
      const anim = animMap.get(clipName);
      expect(anim, `Missing baked glTF animation clip "${clipName}"`).toBeDefined();
      expect(anim!.channels.length).toBeGreaterThan(0);
    }
  });
});
