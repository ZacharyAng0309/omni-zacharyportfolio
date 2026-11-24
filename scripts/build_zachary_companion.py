#!/usr/bin/env python3
"""
Builds the Designer Vinyl / Stylized Walking Companion (`zachary_companion.glb`)
100% from scratch in Blender 5.2 using strict Data-First APIs (`bpy.data` + `bmesh`).

v2 Craft Refinement:
- Clean unified porcelain skin head with sculpted V-jaw, prominent soft nose,
  subtle sculptural smile crease & corner dimples (zero flat decal patches).
- Full overlapping plush curtain-hair clumps matching `reference_portrait.jpg`.
- Expressive glossy dark-espresso eyes snugly nested with thin curved lash-rimmed lids
  and champagne-titanium round spectacles (`51mm` optical scale).
- Box-extruded Subsurf(2) bifurcated tailored trousers (zero pelvis diaper seam),
  tapered architectural overshirt over high-contrast warm ivory inner tee, and
  clean court sneakers grounded strictly flush at Z = 0.000.
- 4 mathematically verified glTF NLA skeletal animation clips (`Idle_Breathing`,
  `Walk_Forward`, `Gesture_Present`, `Turn_Greet`).
"""
from __future__ import annotations

import math
import os
import bpy
import bmesh
from mathutils import Euler, Matrix, Vector


# ==============================================================================
# PROPORTION & LANDMARK CONSTANTS (Metric meters, Z-up, Facing -Y -> glTF +Z)
# ==============================================================================
HEAD_CENTER_Y = -0.008
HEAD_CENTER_Z = 1.425
EYE_X = 0.0385
EYE_Y = -0.0978
EYE_Z = 1.428

SHOULDER_L_POS = Vector((0.156, 0.004, 1.196))
ELBOW_L_POS = Vector((0.236, 0.010, 0.994))
WRIST_L_POS = Vector((0.294, -0.016, 0.812))

HIP_L_POS = Vector((0.088, 0.0, 0.785))
KNEE_L_POS = Vector((0.090, -0.014, 0.435))
ANKLE_L_POS = Vector((0.092, 0.006, 0.092))


# ==============================================================================
# SCENE CLEANUP & DATA-FIRST HELPERS
# ==============================================================================
def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for lgt in list(bpy.data.lights):
        bpy.data.lights.remove(lgt)


def srgb_to_linear(c: tuple[float, float, float]) -> tuple[float, float, float]:
    out = []
    for ch in c:
        if ch <= 0.04045:
            out.append(ch / 12.92)
        else:
            out.append(((ch + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2])


def make_pbr_material(
    name: str,
    srgb_color: tuple[float, float, float],
    *,
    alpha: float = 1.0,
    metallic: float = 0.0,
    roughness: float = 0.5,
    coat_weight: float = 0.0,
    coat_roughness: float = 0.1,
    ior: float = 1.46,
    is_linear: bool = False,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")

    lin = srgb_color if is_linear else srgb_to_linear(srgb_color)
    bsdf.inputs["Base Color"].default_value = (lin[0], lin[1], lin[2], alpha)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Alpha"].default_value = alpha
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat_weight
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = coat_roughness
    if alpha < 0.99 and hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"
    return mat


def create_material_library() -> dict[str, bpy.types.Material]:
    return {
        # Warm healthy matte porcelain-vinyl skin tone matching reference_portrait.jpg
        "skin": make_pbr_material(
            "Mat_Companion_Skin",
            (0.895, 0.720, 0.605),
            roughness=0.54,
            metallic=0.0,
            coat_weight=0.0,
            ior=1.40,
        ),
        # Subtle warm dark-espresso curtain hair with silky satin sheen
        "hair": make_pbr_material(
            "Mat_Companion_Hair",
            (0.205, 0.155, 0.130),
            roughness=0.42,
            coat_weight=0.14,
            coat_roughness=0.28,
        ),
        # Glossy deep espresso-obsidian eyes with strong clearcoat studio catchlights
        "eyes": make_pbr_material(
            "Mat_Companion_Eyes",
            (0.042, 0.034, 0.030),
            roughness=0.04,
            coat_weight=1.0,
            coat_roughness=0.02,
            ior=1.54,
        ),
        # Slender warm terracotta smile arc line
        "smile_line": make_pbr_material(
            "Mat_Companion_SmileLine",
            (0.565, 0.360, 0.310),
            roughness=0.48,
        ),
        "brows": make_pbr_material(
            "Mat_Companion_Brows",
            (0.175, 0.130, 0.108),
            roughness=0.52,
        ),
        # Signature champagne-titanium frame echoing Act 1 Titanium Atelier brass accents
        "glasses_metal": make_pbr_material(
            "Mat_Companion_GlassesMetal",
            (0.825, 0.728, 0.578),
            metallic=0.94,
            roughness=0.18,
            coat_weight=0.08,
            coat_roughness=0.08,
        ),
        "glasses_lens": make_pbr_material(
            "Mat_Companion_GlassesLens",
            (0.95, 0.98, 1.0),
            alpha=0.02,
            metallic=0.0,
            roughness=0.015,
            coat_weight=0.85,
            coat_roughness=0.02,
            ior=1.50,
            is_linear=True,
        ),
        # Crisp warm-ivory crew tee creating editorial chest contrast against dark backdrop
        "inner_tee": make_pbr_material(
            "Mat_Companion_InnerTee",
            (0.875, 0.855, 0.820),
            roughness=0.78,
        ),
        # Tailored charcoal-slate architectural overshirt
        "jacket": make_pbr_material(
            "Mat_Companion_Jacket",
            (0.255, 0.275, 0.315),
            roughness=0.56,
            metallic=0.06,
            coat_weight=0.04,
            coat_roughness=0.35,
        ),
        # Deep slate tailored trousers
        "trousers": make_pbr_material(
            "Mat_Companion_Trousers",
            (0.185, 0.200, 0.232),
            roughness=0.66,
            metallic=0.02,
        ),
        # Matte charcoal sneaker upper + crisp ivory court sole
        "shoe_upper": make_pbr_material(
            "Mat_Companion_ShoeUpper",
            (0.225, 0.242, 0.275),
            roughness=0.60,
        ),
        "shoe_sole": make_pbr_material(
            "Mat_Companion_ShoeSole",
            (0.890, 0.870, 0.835),
            roughness=0.40,
        ),
    }


def append_bmesh(
    dst: bmesh.types.BMesh,
    src: bmesh.types.BMesh,
    *,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    euler: tuple[float, float, float] = (0.0, 0.0, 0.0),
    mat_idx: int | None = None,
) -> list[bmesh.types.BMVert]:
    rot_m = Euler(euler, "XYZ").to_matrix().to_4x4()
    loc_v = Vector(location)
    vmap: dict[bmesh.types.BMVert, bmesh.types.BMVert] = {}
    new_verts: list[bmesh.types.BMVert] = []
    for sv in src.verts:
        nv = dst.verts.new((rot_m @ sv.co) + loc_v)
        vmap[sv] = nv
        new_verts.append(nv)
    for sf in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in sf.verts])
            nf.material_index = sf.material_index if mat_idx is None else mat_idx
            nf.smooth = True
        except ValueError:
            pass
    return new_verts


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge1 == edge0:
        return 1.0 if x >= edge1 else 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def build_object_from_bmesh(
    name: str,
    bm: bmesh.types.BMesh,
    materials: list[bpy.types.Material],
    *,
    subsurf_levels: int = 0,
) -> bpy.types.Object:
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    for m in materials:
        obj.data.materials.append(m)
    bpy.context.scene.collection.objects.link(obj)

    if subsurf_levels > 0:
        sub = obj.modifiers.new(name="BakeSubsurf", type="SUBSURF")
        sub.levels = subsurf_levels
        sub.render_levels = subsurf_levels
        sub.boundary_smooth = "PRESERVE_CORNERS"
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        baked_mesh = bpy.data.meshes.new_from_object(
            obj_eval, preserve_all_data_layers=True, depsgraph=depsgraph
        )
        for p in baked_mesh.polygons:
            p.use_smooth = True
        baked_mesh.update()
        old_mesh = obj.data
        obj.modifiers.remove(sub)
        obj.data = baked_mesh
        bpy.data.meshes.remove(old_mesh)
        obj.data.name = name

    return obj


def loft_tube(
    bm: bmesh.types.BMesh,
    rings: list[tuple[Vector, Vector, Vector, float, float]],
    *,
    segments: int = 16,
    cap_start: bool = True,
    cap_end: bool = True,
    mat_idx: int = 0,
) -> None:
    loop_verts: list[list[bmesh.types.BMVert]] = []
    for c, tu, tv, ru, rv in rings:
        ring: list[bmesh.types.BMVert] = []
        for s in range(segments):
            ang = (2.0 * math.pi * s) / segments
            pt = c + tu * (math.cos(ang) * ru) + tv * (math.sin(ang) * rv)
            ring.append(bm.verts.new(pt))
        loop_verts.append(ring)

    for i in range(len(loop_verts) - 1):
        r0 = loop_verts[i]
        r1 = loop_verts[i + 1]
        for s in range(segments):
            sn = (s + 1) % segments
            f = bm.faces.new((r0[s], r0[sn], r1[sn], r1[s]))
            f.material_index = mat_idx
            f.smooth = True

    if cap_start and loop_verts:
        f = bm.faces.new(list(reversed(loop_verts[0])))
        f.material_index = mat_idx
        f.smooth = True
    if cap_end and loop_verts:
        f = bm.faces.new(loop_verts[-1])
        f.material_index = mat_idx
        f.smooth = True


def sweep_curve_ribbon(
    bm: bmesh.types.BMesh,
    pts: list[tuple[Vector, float, float, float]],
    *,
    profile_type: str = "almond",
    segments: int = 8,
    cap_ends: bool = True,
    mat_idx: int = 0,
) -> None:
    n = len(pts)
    if n < 2:
        return
    rings: list[list[bmesh.types.BMVert]] = []
    for i, (p, w, th, roll) in enumerate(pts):
        if i == 0:
            tan = (pts[1][0] - p).normalized()
        elif i == n - 1:
            tan = (p - pts[n - 2][0]).normalized()
        else:
            tan = (pts[i + 1][0] - pts[i - 1][0]).normalized()

        radial = p - Vector((0.0, HEAD_CENTER_Y, HEAD_CENTER_Z))
        if radial.length < 1e-4:
            radial = Vector((0.0, -1.0, 0.0))
        radial.normalize()
        binorm = radial.cross(tan)
        if binorm.length < 1e-4:
            binorm = Vector((1.0, 0.0, 0.0))
        binorm.normalize()
        out_n = tan.cross(binorm).normalized()

        if abs(roll) > 1e-4:
            rot_axis = Matrix.Rotation(roll, 3, tan)
            binorm = (rot_axis @ binorm).normalized()
            out_n = (rot_axis @ out_n).normalized()

        ring: list[bmesh.types.BMVert] = []
        for s in range(segments):
            ang = (2.0 * math.pi * s) / segments
            ca = math.cos(ang)
            sa = math.sin(ang)
            if profile_type == "almond":
                pinch = 0.76 + 0.24 * (1.0 - ca * ca)
                offset_b = ca * w * 0.5
                offset_n = (sa * th * 0.5 * pinch) + (0.14 * th * (1.0 - ca * ca))
            else:
                offset_b = ca * w * 0.5
                offset_n = sa * th * 0.5
            ring.append(bm.verts.new(p + binorm * offset_b + out_n * offset_n))
        rings.append(ring)

    for i in range(len(rings) - 1):
        r0 = rings[i]
        r1 = rings[i + 1]
        for s in range(segments):
            sn = (s + 1) % segments
            f = bm.faces.new((r0[s], r0[sn], r1[sn], r1[s]))
            f.material_index = mat_idx
            f.smooth = True

    if cap_ends:
        f_s = bm.faces.new(list(reversed(rings[0])))
        f_s.material_index = mat_idx
        f_s.smooth = True
        f_e = bm.faces.new(rings[-1])
        f_e.material_index = mat_idx
        f_e.smooth = True


# ==============================================================================
# SCULPTED STYLIZED HEAD, EYES, LASH-LIDS, BROWS, HAIR & GLASSES
# ==============================================================================
def build_head_and_neck(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """
    SM_Companion_Head: Clean pure porcelain-vinyl sculpted head with youthful V-tapered jaw,
    defined under-chin shelf in profile, gentle cheekbones, prominent sculpted stylized nose,
    and subtle sculptural smile contour (100% pure skin material — zero flat pink patch!).
    """
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=10, use_grid_fill=True)
    bm.verts.ensure_lookup_table()

    for v in bm.verts:
        p = v.co.normalized()
        # Slightly fuller editorial head (~202mm W x 210mm D x 258mm H -> 1:6.1 figurine scale)
        x = p.x * 0.101
        y = p.y * 0.105
        z = p.z * 0.129
        zn = max(-1.0, min(1.0, z / 0.129))

        # 1. Clean youthful V-tapered jaw + sharp yet soft chin silhouette in profile
        if zn < 0.0:
            t_low = -zn
            x *= 1.0 - 0.38 * (t_low ** 1.30)
            if y < 0.0:
                y *= 1.0 - 0.16 * (t_low ** 1.55)
            else:
                y *= 1.0 - 0.36 * (t_low ** 1.15)
            # Subtle forward rounded chin poise
            chin_w = math.exp(-((zn + 0.80) / 0.22) ** 2) * math.exp(-(abs(x) / 0.036) ** 2)
            y -= 0.010 * chin_w
        else:
            x *= 1.0 - 0.05 * (zn ** 2.2)

        # 2. Gentle front face plane + friendly plump cheek volume (matching reference_portrait.jpg)
        if y < -0.025:
            malar = math.exp(-((abs(x) - 0.050) / 0.026) ** 2) * math.exp(-((zn + 0.22) / 0.24) ** 2)
            y -= 0.0085 * malar

        # 3. Gentle orbital socket recesses so glossy eyes & snug lids seat deeply with clean wide exposure
        if y < -0.04:
            for sx in (-1.0, 1.0):
                dx = (x - sx * EYE_X) / 0.024
                dz = (z - (EYE_Z - HEAD_CENTER_Z)) / 0.019
                d2 = dx * dx + dz * dz
                if d2 < 2.4:
                    y += 0.0095 * math.exp(-d2 * 1.05)
            bx = max(0.0, 1.0 - ((abs(x) - EYE_X) / 0.036) ** 2)
            bz = math.exp(-((z - (EYE_Z - HEAD_CENTER_Z + 0.031)) / 0.014) ** 2)
            y -= 0.0055 * bx * bz

        # 4. Crisp sculpted stylized nose bridge & soft rounded nose tip
        if y < -0.05:
            nx = abs(x) / 0.0148
            bridge_w = math.exp(-(nx ** 2)) * max(0.0, 1.0 - abs(z - (-0.014)) / 0.036)
            tip_w = math.exp(-((z - (-0.034)) / 0.016) ** 2) * math.exp(-(abs(x) / 0.0148) ** 2)
            y -= (0.0255 * tip_w + 0.0145 * bridge_w * smoothstep(0.026, -0.032, z))
            # Soft subtle nose wings
            if -0.046 <= z <= -0.026:
                ala = math.exp(-((abs(x) - 0.0122) / 0.0058) ** 2) * math.exp(-((z + 0.037) / 0.0085) ** 2)
                y -= 0.0062 * ala

        # 5. Subtle friendly lower-lip pillow contour & corner dimple warmth
        if y < -0.045:
            mouth_x = abs(x) / 0.024
            smile_arc_z = -0.068 + 0.0068 * (min(1.15, mouth_x) ** 2)
            if mouth_x < 1.25 and abs(z - smile_arc_z) < 0.015:
                w_m = math.exp(-(mouth_x ** 2) * 1.35)
                crease = math.exp(-((z - smile_arc_z) / 0.0022) ** 2)
                lower_lip = math.exp(-((z - (smile_arc_z - 0.0062)) / 0.0044) ** 2)
                upper_lip = math.exp(-((z - (smile_arc_z + 0.0042)) / 0.0036) ** 2)
                y += 0.0048 * w_m * crease - 0.0028 * w_m * lower_lip - 0.0020 * w_m * upper_lip

        v.co = Vector((x, y + HEAD_CENTER_Y, z + HEAD_CENTER_Z))

    # Add delicate sculpted smile-line ribbon seated flush along smile_arc_z (clean curved line!)
    smile_pts: list[tuple[Vector, float, float, float]] = []
    for k in range(9):
        t = (k / 8.0) * 2.0 - 1.0  # -1..+1
        sx = t * 0.0205
        sz = HEAD_CENTER_Z - 0.068 + 0.0055 * (t * t)
        sy = -0.1028 + 0.0102 * (t * t)
        th = 0.0019 * (1.0 - 0.42 * (t * t))
        smile_pts.append((Vector((sx, sy, sz)), th, th, 0.0))
    smile_bm = bmesh.new()
    sweep_curve_ribbon(smile_bm, smile_pts, profile_type="round", segments=6, cap_ends=True, mat_idx=1)
    append_bmesh(bm, smile_bm, mat_idx=1)
    smile_bm.free()

    # Sculpted ears seated symmetrically for temple-arm support
    for sx in (-1.0, 1.0):
        ebm = bmesh.new()
        bmesh.ops.create_cube(ebm, size=1.0)
        bmesh.ops.subdivide_edges(ebm, edges=list(ebm.edges), cuts=4, use_grid_fill=True)
        for ev in ebm.verts:
            q = ev.co.normalized()
            ex = q.x * 0.013
            ey = q.y * 0.018
            ez = q.z * 0.028
            if sx * q.x > 0.35 and abs(q.z) < 0.65 and abs(q.y) < 0.65:
                ex -= sx * 0.005
            ev.co = Vector((ex, ey, ez))
        append_bmesh(
            bm,
            ebm,
            location=(sx * 0.097, HEAD_CENTER_Y + 0.008, HEAD_CENTER_Z - 0.014),
            euler=(math.radians(6.0), 0.0, sx * math.radians(-16.0)),
            mat_idx=0,
        )
        ebm.free()

    # Tapered sleek neck column
    neck_bm = bmesh.new()
    neck_rings = [
        (Vector((0.0, 0.014, 1.225)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.056, 0.052),
        (Vector((0.0, 0.010, 1.258)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.047, 0.044),
        (Vector((0.0, 0.007, 1.295)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.045, 0.043),
        (Vector((0.0, 0.002, 1.335)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.048, 0.046),
        (Vector((0.0, -0.003, 1.362)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.052, 0.050),
    ]
    loft_tube(neck_bm, neck_rings, segments=20, cap_start=True, cap_end=True, mat_idx=0)
    append_bmesh(bm, neck_bm, mat_idx=0)
    neck_bm.free()

    for f in bm.faces:
        if f.material_index not in (0, 1):
            f.material_index = 0
        f.smooth = True

    return build_object_from_bmesh("SM_Companion_Head", bm, [mats["skin"], mats["smile_line"]], subsurf_levels=1)


def build_eyes(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Companion_Eyes: Crisp glossy dark-espresso vertical ovoid eyes nested cleanly in orbits."""
    bm = bmesh.new()
    for sx in (-1.0, 1.0):
        ebm = bmesh.new()
        bmesh.ops.create_cube(ebm, size=1.0)
        bmesh.ops.subdivide_edges(ebm, edges=list(ebm.edges), cuts=4, use_grid_fill=True)
        for v in ebm.verts:
            p = v.co.normalized()
            v.co = Vector((p.x * 0.0132, p.y * 0.0102, p.z * 0.0155))
        append_bmesh(
            bm,
            ebm,
            location=(sx * EYE_X, EYE_Y, EYE_Z),
            euler=(0.0, 0.0, sx * math.radians(-4.0)),
            mat_idx=0,
        )
        ebm.free()
    return build_object_from_bmesh("SM_Companion_Eyes", bm, [mats["eyes"]], subsurf_levels=1)


def build_eyelids(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """
    SM_Companion_Eyelids: Flush-fitted curved porcelain upper lids recessed behind brow/lid crest
    in Basis (clear open glossy eyes) with `eyeBlinkLeft` and `eyeBlinkRight` closing smoothly.
    """
    bm = bmesh.new()
    segs_u = 12
    segs_v = 6
    for sx in (-1.0, 1.0):
        grid: list[list[bmesh.types.BMVert]] = []
        # Keep Basis eyelid lifted high above the expressive oval eye crest (phi >= 0.92), sweeping full-travel down on blink
        for iv in range(segs_v + 1):
            frac_v = iv / segs_v
            phi = 0.92 + frac_v * 0.65
            row: list[bmesh.types.BMVert] = []
            for iu in range(segs_u + 1):
                u = (iu / segs_u - 0.5) * math.pi * 0.96
                rx, ry, rz = 0.0138, 0.0108, 0.0160
                px = sx * EYE_X + math.sin(u) * math.cos(phi) * rx
                py = EYE_Y - math.cos(u) * math.cos(phi) * ry
                pz = EYE_Z + math.sin(phi) * rz
                row.append(bm.verts.new((px, py, pz)))
            grid.append(row)
        for iv in range(segs_v):
            for iu in range(segs_u):
                f = bm.faces.new((grid[iv][iu], grid[iv][iu + 1], grid[iv + 1][iu + 1], grid[iv + 1][iu]))
                f.material_index = 0
                f.smooth = True

    obj = build_object_from_bmesh("SM_Companion_Eyelids", bm, [mats["skin"]], subsurf_levels=1)
    sk_basis = obj.shape_key_add(name="Basis", from_mix=False)
    sk_left = obj.shape_key_add(name="eyeBlinkLeft", from_mix=False)
    sk_right = obj.shape_key_add(name="eyeBlinkRight", from_mix=False)

    for idx, v in enumerate(obj.data.vertices):
        co = v.co
        is_left = co.x > 0.0
        target_sk = sk_left if is_left else sk_right
        center = Vector((EYE_X if is_left else -EYE_X, EYE_Y, EYE_Z))
        rel = co - center
        rot_angle = math.radians(-102.0) * smoothstep(-0.002, 0.009, -rel.y)
        rot_m = Matrix.Rotation(rot_angle, 3, Vector((1.0, 0.0, 0.0)))
        target_sk.data[idx].co = center + (rot_m @ rel)
        sk_basis.data[idx].co = co.copy()

    return obj


def build_brows(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Companion_Brows: Clean arched sculpted brows sitting proud above orbital ridge & below curtain part."""
    bm = bmesh.new()
    for sx in (-1.0, 1.0):
        pts: list[tuple[Vector, float, float, float]] = []
        for k in range(6):
            t = k / 5.0
            x = sx * (0.019 + t * 0.036)
            arch = math.sin(t * math.pi * 0.88)
            z = EYE_Z + 0.031 + arch * 0.0055 - t * 0.0020
            y = -0.1075 + 0.0145 * (t ** 1.65)
            w = 0.0052 if k < 4 else 0.0036 * (1.0 - (t - 0.6) * 0.8)
            th = 0.0046 * (1.0 - 0.35 * abs(t - 0.35))
            pts.append((Vector((x, y, z)), w, max(0.0026, th), 0.0))
        sweep_curve_ribbon(bm, pts, profile_type="round", segments=8, cap_ends=True, mat_idx=0)
    return build_object_from_bmesh("SM_Companion_Brows", bm, [mats["brows"]], subsurf_levels=1)


def build_hair(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """
    SM_Companion_Hair: Lush cohesive dark-espresso sculpted hair shell + broad overlapping
    swept curtain-fringe clumps descending softly to frame forehead & temples above glasses.
    """
    bm = bmesh.new()

    # 1. Plump sculpted hair base cap with thick natural edge hugging crown, temples & nape
    cap_bm = bmesh.new()
    bmesh.ops.create_cube(cap_bm, size=1.0)
    bmesh.ops.subdivide_edges(cap_bm, edges=list(cap_bm.edges), cuts=7, use_grid_fill=True)
    for v in cap_bm.verts:
        p = v.co.normalized()
        x = p.x * 0.108
        y = p.y * 0.114 + HEAD_CENTER_Y + 0.005
        z = p.z * 0.136 + HEAD_CENTER_Z + 0.010
        v.co = Vector((x, y, z))

    faces_to_del = []
    for f in cap_bm.faces:
        c = f.calc_center_median()
        rel_y = c.y - HEAD_CENTER_Y
        rel_z = c.z - HEAD_CENTER_Z
        front_factor = smoothstep(0.04, -0.05, rel_y)
        # Keep front base cap recessed slightly above the parting fringe so locks define the natural front hairline!
        hairline_z = -0.072 + front_factor * 0.148
        ear_cut = (abs(c.x) > 0.078) and (-0.045 < rel_y < 0.025) and (rel_z < 0.024)
        if rel_z < hairline_z or ear_cut:
            faces_to_del.append(f)
    bmesh.ops.delete(cap_bm, geom=faces_to_del, context="FACES")
    append_bmesh(bm, cap_bm, mat_idx=0)
    cap_bm.free()

    cap_obj = build_object_from_bmesh("SM_Companion_HairCapTemp", bm, [mats["hair"]], subsurf_levels=1)
    sol = cap_obj.modifiers.new("CapThick", type="SOLIDIFY")
    sol.thickness = 0.014
    sol.offset = 1.0
    deps = bpy.context.evaluated_depsgraph_get()
    ev = cap_obj.evaluated_get(deps)
    bm_solid = bmesh.new()
    bm_solid.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    bpy.data.objects.remove(cap_obj, do_unlink=True)

    # 2. Broad, soft overlapping ribbon clumps (ZERO isolated gaps or spiky thin strings!)
    def project_scalp(pt: Vector, lift: float) -> Vector:
        c = Vector((0.0, HEAD_CENTER_Y + 0.005, HEAD_CENTER_Z + 0.008))
        rad = pt - c
        rx, ry, rz = 0.108 + lift, 0.114 + lift, 0.136 + lift
        s = math.sqrt((rad.x / rx) ** 2 + (rad.y / ry) ** 2 + (rad.z / rz) ** 2)
        return pt if s < 1e-4 else c + Vector((rad.x / s, rad.y / s, rad.z / s))

    def add_clump(pts_lift: list[tuple[float, float, float, float]], w: float, th: float, roll: float = 0.0) -> None:
        c_pts = []
        n = len(pts_lift)
        for i, (tx, ty, tz, lift) in enumerate(pts_lift):
            frac = i / max(n - 1, 1)
            pos = project_scalp(Vector((tx, ty, tz)), lift)
            ws = 0.85 + 0.28 * math.sin(frac * math.pi * 0.8)
            if frac > 0.65:
                ws *= max(0.32, 1.0 - (frac - 0.65) / 0.40)
            ts = 0.85 + 0.25 * math.sin(frac * math.pi * 0.8)
            if frac > 0.72:
                ts *= max(0.35, 1.0 - (frac - 0.72) / 0.35)
            c_pts.append((pos, w * ws, th * ts, roll))
        sweep_curve_ribbon(bm_solid, c_pts, profile_type="almond", segments=8, cap_ends=True, mat_idx=0)

    # Parted 60/40 Curtain Fringe opening cleanly above the inner brows & glasses bridge (matching reference_portrait.jpg)
    # Left sweep from off-center part (-0.018)
    add_clump([(-0.018, -0.025, 1.568, 0.015), (0.014, -0.092, 1.535, 0.018), (0.040, -0.108, 1.494, 0.017), (0.050, -0.102, 1.462, 0.012)], 0.044, 0.020, 0.06)
    add_clump([(-0.008, -0.022, 1.566, 0.015), (0.032, -0.086, 1.528, 0.018), (0.060, -0.096, 1.484, 0.016), (0.072, -0.084, 1.448, 0.011)], 0.046, 0.020, 0.08)
    add_clump([(0.004, -0.014, 1.564, 0.015), (0.050, -0.070, 1.520, 0.017), (0.080, -0.076, 1.474, 0.015), (0.088, -0.060, 1.440, 0.010)], 0.044, 0.018, 0.04)
    add_clump([(0.014, -0.006, 1.560, 0.014), (0.064, -0.054, 1.514, 0.016), (0.092, -0.054, 1.466, 0.015), (0.098, -0.038, 1.428, 0.010)], 0.042, 0.017, 0.02)

    # Delicate asymmetric sweeping locks cleanly covering center hairline without hiding arched brows
    add_clump([(-0.018, -0.028, 1.564, 0.016), (-0.006, -0.094, 1.532, 0.018), (0.008, -0.112, 1.498, 0.016), (0.018, -0.110, 1.472, 0.011)], 0.040, 0.018, 0.03)
    add_clump([(-0.020, -0.028, 1.564, 0.016), (-0.026, -0.096, 1.530, 0.018), (-0.032, -0.112, 1.496, 0.016), (-0.036, -0.110, 1.470, 0.011)], 0.040, 0.018, -0.03)

    # Right sweep from part (-0.018)
    add_clump([(-0.022, -0.025, 1.566, 0.016), (-0.046, -0.094, 1.528, 0.018), (-0.062, -0.100, 1.486, 0.016), (-0.068, -0.088, 1.454, 0.011)], 0.044, 0.020, -0.06)
    add_clump([(-0.024, -0.018, 1.564, 0.015), (-0.062, -0.078, 1.520, 0.017), (-0.084, -0.078, 1.476, 0.015), (-0.088, -0.062, 1.442, 0.010)], 0.044, 0.019, -0.08)
    add_clump([(-0.028, -0.010, 1.560, 0.014), (-0.074, -0.056, 1.512, 0.016), (-0.094, -0.052, 1.466, 0.015), (-0.098, -0.038, 1.428, 0.010)], 0.042, 0.017, -0.04)

    # Temple & Ear-Framing Side Clumps
    for sx in (-1.0, 1.0):
        add_clump([(sx * 0.035, 0.004, 1.556, 0.014), (sx * 0.088, -0.024, 1.506, 0.016), (sx * 0.102, -0.026, 1.455, 0.014), (sx * 0.096, -0.018, 1.415, 0.010)], 0.038, 0.017, sx * 0.04)
        add_clump([(sx * 0.038, 0.025, 1.552, 0.014), (sx * 0.094, 0.024, 1.495, 0.016), (sx * 0.102, 0.030, 1.430, 0.015), (sx * 0.088, 0.034, 1.365, 0.011)], 0.044, 0.018, 0.0)

    # Seamless Back Occipital Crown & Nape Clumps (overlapping cleanly to Z=1.340)
    for deg in (-66, -44, -22, 0, 22, 44, 66):
        ang = math.radians(deg)
        sa, ca = math.sin(ang), math.cos(ang)
        add_clump(
            [
                (-0.014 + sa * 0.030, 0.008 + ca * 0.026, 1.558, 0.015),
                (sa * 0.086, 0.020 + ca * 0.076, 1.500, 0.017),
                (sa * 0.096, 0.022 + ca * 0.092, 1.425, 0.016),
                (sa * 0.068, 0.012 + ca * 0.072, 1.345, 0.011),
            ],
            0.054,
            0.020,
            0.0,
        )

    return build_object_from_bmesh("SM_Companion_Hair", bm_solid, [mats["hair"]], subsurf_levels=1)


def build_glasses(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Companion_Glasses: Signature champagne-titanium round wire spectacles centered cleanly on eyes."""
    bm = bmesh.new()
    mat_list = [mats["glasses_metal"], mats["glasses_lens"], mats["trousers"]]

    rim_r = 0.0268
    wire_r = 0.00155
    lens_y = -0.1155
    lens_z = 1.428

    for sx in (-1.0, 1.0):
        cx = sx * EYE_X
        rim_segs = 36
        tube_segs = 10
        rim_rings: list[list[bmesh.types.BMVert]] = []
        for s in range(rim_segs):
            th = (2.0 * math.pi * s) / rim_segs
            ring_c = Vector((cx + math.cos(th) * rim_r, lens_y, lens_z + math.sin(th) * rim_r))
            rad_dir = Vector((math.cos(th), 0.0, math.sin(th)))
            fwd_dir = Vector((0.0, -1.0, 0.0))
            ring = []
            for ts in range(tube_segs):
                a = (2.0 * math.pi * ts) / tube_segs
                pt = ring_c + rad_dir * (math.cos(a) * wire_r * 0.95) + fwd_dir * (math.sin(a) * wire_r * 1.15)
                ring.append(bm.verts.new(pt))
            rim_rings.append(ring)
        for s in range(rim_segs):
            sn = (s + 1) % rim_segs
            for ts in range(tube_segs):
                tsn = (ts + 1) % tube_segs
                f = bm.faces.new((rim_rings[s][ts], rim_rings[sn][ts], rim_rings[sn][tsn], rim_rings[s][tsn]))
                f.material_index = 0
                f.smooth = True

        # Transparent optical lens discs
        for cap_y_off, flip in ((-0.0005, True), (0.0005, False)):
            lring = [
                bm.verts.new((cx + math.cos(2 * math.pi * s / 32) * (rim_r - 0.0008), lens_y + cap_y_off, lens_z + math.sin(2 * math.pi * s / 32) * (rim_r - 0.0008)))
                for s in range(32)
            ]
            f_l = bm.faces.new(list(reversed(lring)) if flip else lring)
            f_l.material_index = 1
            f_l.smooth = True

        # Nose pads & arms
        pad_pts = [
            (Vector((sx * 0.0135, lens_y + 0.001, lens_z - 0.001)), 0.0013, 0.0013, 0.0),
            (Vector((sx * 0.0110, lens_y + 0.006, lens_z - 0.004)), 0.0012, 0.0012, 0.0),
        ]
        sweep_curve_ribbon(bm, pad_pts, profile_type="round", segments=6, cap_ends=True, mat_idx=0)
        pbm = bmesh.new()
        bmesh.ops.create_cube(pbm, size=1.0)
        bmesh.ops.subdivide_edges(pbm, edges=list(pbm.edges), cuts=2, use_grid_fill=True)
        for pv in pbm.verts:
            q = pv.co.normalized()
            pv.co = Vector((q.x * 0.0018, q.y * 0.0022, q.z * 0.0042))
        append_bmesh(bm, pbm, location=(sx * 0.0108, lens_y + 0.0065, lens_z - 0.005), mat_idx=2)
        pbm.free()

        # Temple arms resting cleanly on ears
        ear_x = sx * 0.099
        ear_y = HEAD_CENTER_Y + 0.008
        ear_z = HEAD_CENTER_Z + 0.005
        temple_pts = [
            (Vector((cx + sx * (rim_r + 0.0005), lens_y, lens_z + 0.0045)), 0.0025, 0.0020, 0.0),
            (Vector((sx * 0.078, lens_y + 0.006, lens_z + 0.0045)), 0.0025, 0.0020, 0.0),
            (Vector((sx * 0.097, lens_y + 0.058, lens_z + 0.0040)), 0.0021, 0.0018, 0.0),
            (Vector((ear_x, ear_y - 0.004, ear_z)), 0.0020, 0.0018, 0.0),
            (Vector((ear_x - sx * 0.004, ear_y + 0.015, ear_z - 0.009)), 0.0022, 0.0020, 0.0),
            (Vector((ear_x - sx * 0.006, ear_y + 0.019, ear_z - 0.020)), 0.0020, 0.0018, 0.0),
        ]
        sweep_curve_ribbon(bm, temple_pts, profile_type="round", segments=8, cap_ends=True, mat_idx=0)

    # Arched keyhole center bridge
    bridge_pts = []
    for k in range(7):
        t = k / 6.0
        bx = -0.0125 + t * 0.0250
        arch = math.sin(t * math.pi)
        bridge_pts.append((Vector((bx, lens_y - arch * 0.0015, lens_z + 0.0045 + arch * 0.0038)), 0.0022, 0.0018, 0.0))
    sweep_curve_ribbon(bm, bridge_pts, profile_type="round", segments=8, cap_ends=True, mat_idx=0)

    return build_object_from_bmesh("SM_Companion_Glasses", bm, mat_list, subsurf_levels=0)


# ==============================================================================
# TAILORED APPAREL & FOOTWEAR
# ==============================================================================
def build_inner_tee(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Companion_InnerTee: Crisp light warm-ivory crew-neck tee with natural chest depth."""
    bm = bmesh.new()
    rings = []
    specs = [
        (0.790, 0.126, 0.088, 0.000),
        (0.870, 0.124, 0.088, 0.000),
        (0.960, 0.128, 0.092, 0.000),
        (1.060, 0.138, 0.098, 0.000),
        (1.155, 0.142, 0.096, 0.002),
        (1.215, 0.106, 0.076, 0.004),
        (1.242, 0.064, 0.058, 0.006),
        (1.258, 0.056, 0.054, 0.008),
    ]
    for z, rx, ry, y_off in specs:
        rings.append((Vector((0.0, y_off, z)), Vector((1, 0, 0)), Vector((0, 1, 0)), rx, ry))
    loft_tube(bm, rings, segments=24, cap_start=True, cap_end=True, mat_idx=0)

    collar_rings = []
    for k in range(5):
        ang = (k / 4.0) * math.pi
        z_c = 1.246 + math.sin(ang) * 0.009
        r_extra = 0.005 * math.sin(ang) + 0.002
        collar_rings.append(
            (Vector((0.0, 0.006, z_c)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.058 + r_extra, 0.055 + r_extra)
        )
    loft_tube(bm, collar_rings, segments=24, cap_start=True, cap_end=True, mat_idx=0)
    return build_object_from_bmesh("SM_Companion_InnerTee", bm, [mats["inner_tee"]], subsurf_levels=1)


def build_jacket(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """
    SM_Companion_Jacket: Tailored charcoal overshirt with sculpted lapel/collar,
    tapered waist contour, flared natural deltoids, smooth sleeves, and cuff studs.
    """
    bm = bmesh.new()
    mat_list = [mats["jacket"], mats["glasses_metal"]]

    profile_levels = [
        # (z, rx, ry, gap_half_x, thick, y_shift)
        (0.768, 0.148, 0.104, 0.050, 0.011, 0.002),
        (0.840, 0.140, 0.098, 0.044, 0.011, 0.000),
        (0.955, 0.142, 0.100, 0.042, 0.011, 0.000),
        (1.065, 0.156, 0.108, 0.044, 0.011, 0.001),
        (1.170, 0.168, 0.106, 0.046, 0.012, 0.004),
        (1.222, 0.152, 0.092, 0.048, 0.012, 0.006),
        (1.250, 0.092, 0.070, 0.048, 0.010, 0.010),
    ]

    n_arc = 19
    wall_loops: list[list[bmesh.types.BMVert]] = []
    for z, rx, ry, gap_x, thick, y_s in profile_levels:
        start_a = -math.pi * 0.5 + math.asin(min(0.85, gap_x / max(rx, 0.05)))
        end_a = math.pi * 1.5 - math.asin(min(0.85, gap_x / max(rx, 0.05)))
        op, ip = [], []
        for k in range(n_arc):
            a = start_a + (k / (n_arc - 1)) * (end_a - start_a)
            op.append(Vector((math.cos(a) * rx, math.sin(a) * ry + y_s, z)))
            ip.append(Vector((math.cos(a) * (rx - thick), math.sin(a) * (ry - thick) + y_s, z)))
        wall_loops.append([bm.verts.new(p) for p in (op + list(reversed(ip)))])

    n_loop = n_arc * 2
    for li in range(len(wall_loops) - 1):
        r0, r1 = wall_loops[li], wall_loops[li + 1]
        for s in range(n_loop):
            sn = (s + 1) % n_loop
            f = bm.faces.new((r0[s], r0[sn], r1[sn], r1[s]))
            f.material_index = 0
            f.smooth = True

    for r_end, flip in ((wall_loops[0], True), (wall_loops[-1], False)):
        for k in range(n_arc - 1):
            a0, a1, b1, b0 = r_end[k], r_end[k + 1], r_end[n_loop - 2 - k], r_end[n_loop - 1 - k]
            f = bm.faces.new((a0, b0, b1, a1) if flip else (a0, a1, b1, b0))
            f.material_index = 0
            f.smooth = True

    # Tailored folded shirt collar
    collar_levels = [
        (1.242, 0.070, 0.064, 0.044, 0.009, 0.010),
        (1.268, 0.078, 0.070, 0.046, 0.008, 0.010),
        (1.282, 0.074, 0.068, 0.050, 0.007, 0.010),
    ]
    c_loops = []
    for z, rx, ry, gap_x, thick, y_s in collar_levels:
        start_a = -math.pi * 0.5 + math.asin(min(0.85, gap_x / max(rx, 0.05)))
        end_a = math.pi * 1.5 - math.asin(min(0.85, gap_x / max(rx, 0.05)))
        op, ip = [], []
        for k in range(13):
            a = start_a + (k / 12.0) * (end_a - start_a)
            op.append(Vector((math.cos(a) * rx, math.sin(a) * ry + y_s, z)))
            ip.append(Vector((math.cos(a) * (rx - thick), math.sin(a) * (ry - thick) + y_s, z)))
        c_loops.append([bm.verts.new(p) for p in (op + list(reversed(ip)))])
    for li in range(len(c_loops) - 1):
        for s in range(26):
            sn = (s + 1) % 26
            f = bm.faces.new((c_loops[li][s], c_loops[li][sn], c_loops[li + 1][sn], c_loops[li + 1][s]))
            f.material_index = 0
            f.smooth = True
    for r_end, flip in ((c_loops[0], True), (c_loops[-1], False)):
        for k in range(12):
            a0, a1, b1, b0 = r_end[k], r_end[k + 1], r_end[24 - k], r_end[25 - k]
            f = bm.faces.new((a0, b0, b1, a1) if flip else (a0, a1, b1, b0))
            f.material_index = 0
            f.smooth = True

    # Subtle chest welt pocket detail (+X left breast)
    p_bm = bmesh.new()
    bmesh.ops.create_cube(p_bm, size=1.0)
    for pv in p_bm.verts:
        pv.co = Vector((pv.co.x * 0.044, pv.co.y * 0.008, pv.co.z * 0.012))
    append_bmesh(bm, p_bm, location=(0.095, -0.088, 1.115), euler=(0.0, 0.0, math.radians(22.0)), mat_idx=0)
    p_bm.free()

    # Smooth natural sleeves flaring softly out of torso
    for sx in (-1.0, 1.0):
        sh = Vector((sx * SHOULDER_L_POS.x, SHOULDER_L_POS.y, SHOULDER_L_POS.z))
        el = Vector((sx * ELBOW_L_POS.x, ELBOW_L_POS.y, ELBOW_L_POS.z))
        wr = Vector((sx * WRIST_L_POS.x, WRIST_L_POS.y, WRIST_L_POS.z))
        anchor = Vector((sx * 0.118, 0.005, 1.186))

        stations = [
            (anchor, 0.072, 0.068),
            (sh, 0.060, 0.058),
            (sh.lerp(el, 0.5), 0.054, 0.054),
            (el, 0.050, 0.050),
            (el.lerp(wr, 0.55), 0.045, 0.045),
            (wr.lerp(el, 0.08), 0.042, 0.040),
            (wr, 0.043, 0.041),
            (wr + (wr - el).normalized() * 0.006, 0.036, 0.034),
            (wr - (wr - el).normalized() * 0.025, 0.030, 0.028),
        ]
        s_rings = []
        for i, (pt, ru, rv) in enumerate(stations):
            ax = (stations[min(i + 1, 6)][0] - (stations[i][0] if i == 0 else stations[i - 1][0])).normalized() if i < 7 else (wr - el).normalized()
            tu = Vector((0.0, -1.0, 0.0))
            tv = tu.cross(ax).normalized()
            tu = ax.cross(tv).normalized()
            s_rings.append((pt, tu, tv, ru, rv))
        loft_tube(bm, s_rings, segments=18, cap_start=True, cap_end=True, mat_idx=0)

        stud_bm = bmesh.new()
        bmesh.ops.create_icosphere(stud_bm, subdivisions=1, radius=0.0052)
        append_bmesh(bm, stud_bm, location=(wr.x + sx * 0.039, wr.y + 0.005, wr.z + 0.025), mat_idx=1)
        stud_bm.free()

    return build_object_from_bmesh("SM_Companion_Jacket", bm, mat_list, subsurf_levels=1)


def build_hands(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Companion_Hands: Sleek sculpted designer-vinyl hands emerging from cuffs."""
    bm = bmesh.new()
    for sx in (-1.0, 1.0):
        wr = Vector((sx * WRIST_L_POS.x, WRIST_L_POS.y, WRIST_L_POS.z))
        el = Vector((sx * ELBOW_L_POS.x, ELBOW_L_POS.y, ELBOW_L_POS.z))
        fore_dir = (wr - el).normalized()

        hand_bm = bmesh.new()
        palm_rings = [
            (Vector((0.0, 0.0, -0.022)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.024, 0.022),
            (Vector((0.0, 0.0, 0.000)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.025, 0.022),
            (Vector((0.0, 0.0, 0.028)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.018, 0.031),
            (Vector((sx * -0.003, 0.0, 0.056)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.016, 0.030),
        ]
        loft_tube(hand_bm, palm_rings, segments=14, cap_start=True, cap_end=True, mat_idx=0)

        thumb_rings = [
            (Vector((sx * -0.004, -0.023, 0.022)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0105, 0.0115),
            (Vector((sx * -0.010, -0.034, 0.044)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0092, 0.0100),
            (Vector((sx * -0.016, -0.040, 0.064)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0075, 0.0080),
            (Vector((sx * -0.018, -0.042, 0.072)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0045, 0.0048),
        ]
        loft_tube(hand_bm, thumb_rings, segments=10, cap_start=True, cap_end=True, mat_idx=0)

        idx_rings = [
            (Vector((sx * -0.004, -0.018, 0.050)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0082, 0.0088),
            (Vector((sx * -0.012, -0.020, 0.074)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0074, 0.0078),
            (Vector((sx * -0.022, -0.020, 0.095)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0060, 0.0063),
            (Vector((sx * -0.026, -0.020, 0.104)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0036, 0.0038),
        ]
        loft_tube(hand_bm, idx_rings, segments=10, cap_start=True, cap_end=True, mat_idx=0)

        mid_rings = [
            (Vector((sx * -0.004, 0.009, 0.050)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0096, 0.0215),
            (Vector((sx * -0.014, 0.010, 0.075)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0084, 0.0190),
            (Vector((sx * -0.025, 0.010, 0.096)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0068, 0.0150),
            (Vector((sx * -0.030, 0.010, 0.105)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.0042, 0.0092),
        ]
        loft_tube(hand_bm, mid_rings, segments=12, cap_start=True, cap_end=True, mat_idx=0)

        quat = Vector((0.0, 0.0, 1.0)).rotation_difference(fore_dir)
        append_bmesh(bm, hand_bm, location=tuple(wr), euler=tuple(quat.to_euler("XYZ")), mat_idx=0)
        hand_bm.free()

    return build_object_from_bmesh("SM_Companion_Hands", bm, [mats["skin"]], subsurf_levels=1)


def build_trousers(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """
    SM_Companion_Trousers: True manifold Subsurf-baked bifurcated quad cage trousers!
    Builds one clean 3-column pelvis grid (Right lobe, narrow high crotch bridge, Left lobe)
    and extrudes downward through thigh -> knee -> calf -> tapered cuff with ZERO diaper bulge!
    """
    bm = bmesh.new()

    # Pelvis X columns: [-0.145, -0.018, +0.018, +0.145] | Y rows: [-0.088, +0.088] | Z: [0.740, 0.855]
    xs = [-0.145, -0.018, 0.018, 0.145]
    ys = [-0.088, -0.010, 0.088]  # 2 quads deep in Y so Subsurf rounds nicely into ellipse!
    zs = [0.742, 0.800, 0.855]

    # Create grid of boundary faces on pelvis box (clean 3x2x2 cage)
    grid: dict[tuple[int, int, int], bmesh.types.BMVert] = {}
    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            for iz, z in enumerate(zs):
                # Pull outer corners gently inward so cross-section pre-curves into tailored hips
                px, py = x, y
                if abs(ix - 1.5) > 1.0 and abs(iy - 1) > 0.5:
                    px *= 0.90
                    py *= 0.86
                # Lift middle crotch edge slightly higher than thighs for crisp modern pant fit
                pz = z + (0.018 if (iz == 0 and ix in (1, 2)) else 0.0)
                grid[(ix, iy, iz)] = bm.verts.new((px, py, pz))

    # Build top cap faces (iz=2)
    for ix in range(3):
        for iy in range(2):
            bm.faces.new((grid[(ix, iy, 2)], grid[(ix + 1, iy, 2)], grid[(ix + 1, iy + 1, 2)], grid[(ix, iy + 1, 2)]))

    # Build front (iy=0) and back (iy=2) walls
    for ix in range(3):
        for iz in range(2):
            bm.faces.new((grid[(ix, 0, iz)], grid[(ix + 1, 0, iz)], grid[(ix + 1, 0, iz + 1)], grid[(ix, 0, iz + 1)]))
            bm.faces.new((grid[(ix + 1, 2, iz)], grid[(ix, 2, iz)], grid[(ix, 2, iz + 1)], grid[(ix + 1, 2, iz + 1)]))

    # Build right (ix=0) and left (ix=3) side walls
    for iy in range(2):
        for iz in range(2):
            bm.faces.new((grid[(0, iy + 1, iz)], grid[(0, iy, iz)], grid[(0, iy, iz + 1)], grid[(0, iy + 1, iz + 1)]))
            bm.faces.new((grid[(3, iy, iz)], grid[(3, iy + 1, iz)], grid[(3, iy + 1, iz + 1)], grid[(3, iy, iz + 1)]))

    # Crotch center arch bottom faces (ix=1 only -> ix 1..2 bridge)
    for iy in range(2):
        bm.faces.new((grid[(1, iy + 1, 0)], grid[(2, iy + 1, 0)], grid[(2, iy, 0)], grid[(1, iy, 0)]))

    # Extrude Right (ix=0..1) and Left (ix=2..3) leg perimeter loops cleanly down through thigh -> knee -> ankle!
    def extrude_leg_from_perimeter(perim_top: list[bmesh.types.BMVert], sx: float) -> None:
        # perim_top has 8 verts ordered CCW around -Z (looking from top)
        # Wait: let's extrude cleanly step by step keeping exact 8-vert octagonal loops!
        leg_specs = [
            # (z, cx, cy, rx, ry)
            (0.680, sx * 0.084, 0.000, 0.072, 0.078),
            (0.560, sx * 0.086, -0.006, 0.066, 0.070),
            (0.435, sx * 0.090, -0.014, 0.058, 0.062),
            (0.280, sx * 0.091, -0.004, 0.054, 0.056),
            (0.125, sx * 0.092, 0.005, 0.045, 0.047),
            (0.092, sx * 0.092, 0.006, 0.043, 0.045),
        ]
        prev_loop = perim_top
        for z, cx, cy, rx, ry in leg_specs:
            # Map 8 perimeter verts around octagon centered at (cx, cy, z)
            # Determine angle around centroid of perim_top
            ring = []
            # Fixed angle mapping matching perim_top order:
            # [front-out, front-mid, front-in, mid-in, back-in, back-mid, back-out, mid-out]
            angles_ccw = (
                [(-1.0, -1.0), (-0.1, -1.0), (1.0, -1.0), (1.0, 0.0), (1.0, 1.0), (-0.1, 1.0), (-1.0, 1.0), (-1.0, 0.0)]
                if sx > 0
                else [(-1.0, -1.0), (0.1, -1.0), (1.0, -1.0), (1.0, 0.0), (1.0, 1.0), (0.1, 1.0), (-1.0, 1.0), (-1.0, 0.0)]
            )
            for ax, ay in angles_ccw:
                norm = math.hypot(ax, ay)
                ring.append(bm.verts.new((cx + (ax / norm) * rx, cy + (ay / norm) * ry, z)))

            for s in range(8):
                sn = (s + 1) % 8
                bm.faces.new((prev_loop[s], prev_loop[sn], ring[sn], ring[s]))
            prev_loop = ring

        # Close ankle cuff inside shoe collar
        in_ring = []
        c_pt = Vector((sx * 0.092, 0.006, 0.072))
        for v in prev_loop:
            in_ring.append(bm.verts.new(v.co.lerp(c_pt, 0.35)))
        for s in range(8):
            sn = (s + 1) % 8
            bm.faces.new((prev_loop[s], prev_loop[sn], in_ring[sn], in_ring[s]))
        bm.faces.new(list(reversed(in_ring)))

    # Order 8-vert loops cleanly so normals point strictly outward!
    right_perim = [
        grid[(0, 0, 0)], grid[(0, 0, 0)],  # wait avoid duplicate!
    ]
    # Better: look at the 8 boundary verts of Right box bottom (ix in {0,1}, iy in {0,1,2}):
    # (0,0,0), mid? ix=0..1 has NO mid in X! Only 6 boundary verts:
    # (0,0), (1,0), (1,1), (1,2), (0,2), (0,1) -> That's 6 verts!!
    # So each leg tube is a crisp 6-gon (hexagonal cage -> Subsurf(2) turns 6-gon into ultra-smooth cylinder)!
    right_hex = [
        grid[(0, 0, 0)],
        grid[(1, 0, 0)],
        grid[(1, 1, 0)],
        grid[(1, 2, 0)],
        grid[(0, 2, 0)],
        grid[(0, 1, 0)],
    ]
    left_hex = [
        grid[(2, 0, 0)],
        grid[(3, 0, 0)],
        grid[(3, 1, 0)],
        grid[(3, 2, 0)],
        grid[(2, 2, 0)],
        grid[(2, 1, 0)],
    ]

    def extrude_hex_leg(prev_loop: list[bmesh.types.BMVert], sx: float) -> None:
        # Angle coords matching hex loop CCW around -Z (verified from indices above: FL -> FR -> BR -> BL)
        hex_dirs = [
            (-0.78, -0.78),
            (0.78, -0.78),
            (1.00, 0.00),
            (0.78, 0.78),
            (-0.78, 0.78),
            (-1.00, 0.00),
        ]
        leg_specs = [
            (0.680, sx * 0.084, 0.000, 0.072, 0.076),
            (0.560, sx * 0.086, -0.006, 0.066, 0.070),
            (0.435, sx * 0.090, -0.014, 0.058, 0.062),
            (0.280, sx * 0.091, -0.004, 0.054, 0.056),
            (0.130, sx * 0.092, 0.005, 0.045, 0.047),
            (0.092, sx * 0.092, 0.006, 0.043, 0.045),
        ]
        for z, cx, cy, rx, ry in leg_specs:
            ring = []
            for dx, dy in hex_dirs:
                n = math.hypot(dx, dy)
                ring.append(bm.verts.new((cx + (dx / n) * rx, cy + (dy / n) * ry, z)))
            for s in range(6):
                sn = (s + 1) % 6
                bm.faces.new((ring[s], ring[sn], prev_loop[sn], prev_loop[s]))
            prev_loop = ring

        # Close hem cuff cleanly inside shoe collar
        in_ring = [bm.verts.new(Vector((sx * 0.092, 0.006, 0.074)).lerp(v.co, 0.65)) for v in prev_loop]
        for s in range(6):
            sn = (s + 1) % 6
            bm.faces.new((in_ring[s], in_ring[sn], prev_loop[sn], prev_loop[s]))
        bm.faces.new(list(reversed(in_ring)))

    extrude_hex_leg(right_hex, -1.0)
    extrude_hex_leg(left_hex, 1.0)

    for f in bm.faces:
        f.material_index = 0
        f.smooth = True

    return build_object_from_bmesh("SM_Companion_Trousers", bm, [mats["trousers"]], subsurf_levels=2)


def build_footwear(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """
    SM_Companion_Footwear: Sleek low-top architectural court sneakers with bold clean
    ivory midsoles resting flat at Z = 0.000 and subtle champagne heel tabs.
    """
    bm = bmesh.new()
    mat_list = [mats["shoe_upper"], mats["shoe_sole"], mats["glasses_metal"]]

    for sx in (-1.0, 1.0):
        s_bm = bmesh.new()
        bmesh.ops.create_cube(s_bm, size=1.0)
        bmesh.ops.subdivide_edges(s_bm, edges=list(s_bm.edges), cuts=4, use_grid_fill=True)

        for v in s_bm.verts:
            p = v.co.normalized()
            zn = (p.z + 1.0) * 0.5
            # Generous iconic designer court sneaker footprint: length 20.8cm (-0.154 toe to +0.054 heel)
            y_pos = -0.050 + p.y * 0.104
            fore_bulge = 1.0 - 0.18 * smoothstep(-0.04, 0.05, y_pos) - 0.28 * smoothstep(-0.10, -0.155, y_pos)
            x_pos = p.x * 0.049 * fore_bulge

            heel_rise = smoothstep(-0.12, 0.025, y_pos)
            z_height = 0.054 + heel_rise * 0.048
            if zn < 0.18:
                z_pos = 0.000 + (zn / 0.18) * 0.015
            else:
                z_pos = 0.015 + ((zn - 0.18) / 0.82) * (z_height - 0.015)
            if zn < 0.12 and y_pos < -0.125:
                z_pos += 0.005 * ((-0.125 - y_pos) / 0.030)
            v.co = Vector((x_pos, y_pos, z_pos))

        for f in s_bm.faces:
            fc = f.calc_center_median()
            f.material_index = 1 if fc.z < 0.028 else 0
            f.smooth = True

        tab_bm = bmesh.new()
        bmesh.ops.create_cube(tab_bm, size=1.0)
        for tv in tab_bm.verts:
            tv.co = Vector((tv.co.x * 0.030, tv.co.y * 0.008, tv.co.z * 0.024))
        append_bmesh(s_bm, tab_bm, location=(0.0, 0.051, 0.070), mat_idx=2)
        tab_bm.free()

        append_bmesh(
            bm,
            s_bm,
            location=(sx * ANKLE_L_POS.x, 0.0, 0.0),
            euler=(0.0, 0.0, sx * math.radians(-5.0)),
        )
        s_bm.free()

    obj = build_object_from_bmesh("SM_Companion_Footwear", bm, mat_list, subsurf_levels=1)
    min_z = min(v.co.z for v in obj.data.vertices)
    if abs(min_z) > 1e-5:
        for v in obj.data.vertices:
            v.co.z -= min_z
        obj.data.update()
    return obj


# ==============================================================================
# ARMATURE RIG & DETERMINISTIC ANALYTICAL SKIN WEIGHTS
# ==============================================================================
def build_armature() -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("CompanionRig")
    arm_obj = bpy.data.objects.new("CompanionArmature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)

    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    eb = arm_data.edit_bones

    def add_bone(
        name: str,
        head: tuple[float, float, float],
        tail: tuple[float, float, float],
        parent: bpy.types.EditBone | None = None,
        *,
        connected: bool = False,
    ) -> bpy.types.EditBone:
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        b.roll = 0.0
        if parent is not None:
            b.parent = parent
            b.use_connect = connected
        return b

    hips = add_bone("Hips", (0.0, 0.0, 0.785), (0.0, 0.0, 0.905))
    spine = add_bone("Spine", (0.0, 0.0, 0.905), (0.0, 0.002, 1.055), hips, connected=True)
    spine1 = add_bone("Spine1", (0.0, 0.002, 1.055), (0.0, 0.005, 1.235), spine, connected=True)
    neck = add_bone("Neck", (0.0, 0.005, 1.235), (0.0, 0.000, 1.320), spine1, connected=True)
    add_bone("Head", (0.0, 0.000, 1.320), (0.0, -0.006, 1.545), neck, connected=True)

    for side, sx in (("Left", 1.0), ("Right", -1.0)):
        sh_b = add_bone(
            f"{side}Shoulder",
            (sx * 0.045, 0.005, 1.196),
            (sx * SHOULDER_L_POS.x, SHOULDER_L_POS.y, SHOULDER_L_POS.z),
            spine1,
        )
        arm_b = add_bone(
            f"{side}Arm",
            (sx * SHOULDER_L_POS.x, SHOULDER_L_POS.y, SHOULDER_L_POS.z),
            (sx * ELBOW_L_POS.x, ELBOW_L_POS.y, ELBOW_L_POS.z),
            sh_b,
            connected=True,
        )
        fore_b = add_bone(
            f"{side}ForeArm",
            (sx * ELBOW_L_POS.x, ELBOW_L_POS.y, ELBOW_L_POS.z),
            (sx * WRIST_L_POS.x, WRIST_L_POS.y, WRIST_L_POS.z),
            arm_b,
            connected=True,
        )
        wr = Vector((sx * WRIST_L_POS.x, WRIST_L_POS.y, WRIST_L_POS.z))
        el = Vector((sx * ELBOW_L_POS.x, ELBOW_L_POS.y, ELBOW_L_POS.z))
        hand_tail = wr + (wr - el).normalized() * 0.105
        add_bone(f"{side}Hand", tuple(wr), tuple(hand_tail), fore_b, connected=True)

        up_b = add_bone(
            f"{side}UpLeg",
            (sx * HIP_L_POS.x, HIP_L_POS.y, HIP_L_POS.z),
            (sx * KNEE_L_POS.x, KNEE_L_POS.y, KNEE_L_POS.z),
            hips,
        )
        leg_b = add_bone(
            f"{side}Leg",
            (sx * KNEE_L_POS.x, KNEE_L_POS.y, KNEE_L_POS.z),
            (sx * ANKLE_L_POS.x, ANKLE_L_POS.y, ANKLE_L_POS.z),
            up_b,
            connected=True,
        )
        add_bone(
            f"{side}Foot",
            (sx * ANKLE_L_POS.x, ANKLE_L_POS.y, ANKLE_L_POS.z),
            (sx * ANKLE_L_POS.x, -0.105, 0.015),
            leg_b,
            connected=True,
        )

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def assign_weights_dict(obj: bpy.types.Object, arm_obj: bpy.types.Object, weight_fn) -> None:
    vg_map = {b.name: obj.vertex_groups.new(name=b.name) for b in arm_obj.data.bones}
    for v in obj.data.vertices:
        weights = weight_fn(v.co)
        total = sum(max(0.0, w) for w in weights.values())
        if total <= 1e-6:
            weights = {"Hips": 1.0}
            total = 1.0
        for bname, w in weights.items():
            nw = max(0.0, w) / total
            if nw > 1e-4:
                vg_map[bname].add([v.index], nw, "REPLACE")

    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    mod.use_vertex_groups = True


def weight_rigid_head(_co: Vector) -> dict[str, float]:
    return {"Head": 1.0}


def weight_head_and_neck(co: Vector) -> dict[str, float]:
    z = co.z
    if z >= 1.320:
        return {"Head": 1.0}
    elif z >= 1.245:
        t = smoothstep(1.245, 1.320, z)
        return {"Head": t, "Neck": 1.0 - t}
    else:
        t = smoothstep(1.210, 1.245, z)
        return {"Neck": t, "Spine1": 1.0 - t}


def weight_torso_tee(co: Vector) -> dict[str, float]:
    z = co.z
    if z < 0.905:
        t = smoothstep(0.790, 0.905, z)
        return {"Hips": 1.0 - t, "Spine": t}
    elif z < 1.060:
        t = smoothstep(0.960, 1.060, z)
        return {"Spine": 1.0 - t, "Spine1": t}
    elif z < 1.225:
        return {"Spine1": 1.0}
    else:
        t = smoothstep(1.225, 1.265, z)
        return {"Spine1": 1.0 - t, "Neck": t}


def weight_jacket(co: Vector) -> dict[str, float]:
    ax = abs(co.x)
    side = "Left" if co.x >= 0.0 else "Right"
    z = co.z
    if ax <= 0.142 or (ax <= 0.175 and z < 1.05):
        return weight_torso_tee(Vector((co.x, co.y, min(z, 1.25))))

    sh = Vector((SHOULDER_L_POS.x if co.x >= 0 else -SHOULDER_L_POS.x, SHOULDER_L_POS.y, SHOULDER_L_POS.z))
    el = Vector((ELBOW_L_POS.x if co.x >= 0 else -ELBOW_L_POS.x, ELBOW_L_POS.y, ELBOW_L_POS.z))
    wr = Vector((WRIST_L_POS.x if co.x >= 0 else -WRIST_L_POS.x, WRIST_L_POS.y, WRIST_L_POS.z))

    arm_vec = el - sh
    u_arm = (co - sh).dot(arm_vec.normalized()) / arm_vec.length
    w_limb = smoothstep(0.142, 0.180, ax)
    base_torso = weight_torso_tee(Vector((co.x, co.y, min(z, 1.25))))

    if u_arm < 0.08:
        limb_w = {f"{side}Shoulder": 0.45, f"{side}Arm": 0.55}
    elif u_arm < 0.80:
        limb_w = {f"{side}Arm": 1.0}
    else:
        fore_vec = wr - el
        u_fore = (co - el).dot(fore_vec.normalized()) / fore_vec.length
        t_fore = smoothstep(-0.18, 0.18, u_fore)
        if u_fore < 0.86:
            limb_w = {f"{side}Arm": 1.0 - t_fore, f"{side}ForeArm": t_fore}
        else:
            t_hand = smoothstep(0.86, 1.04, u_fore)
            limb_w = {f"{side}ForeArm": 1.0 - t_hand, f"{side}Hand": t_hand}

    merged: dict[str, float] = {}
    for k, v in base_torso.items():
        merged[k] = merged.get(k, 0.0) + v * (1.0 - w_limb)
    for k, v in limb_w.items():
        merged[k] = merged.get(k, 0.0) + v * w_limb
    return merged


def weight_hands(co: Vector) -> dict[str, float]:
    side = "Left" if co.x >= 0.0 else "Right"
    el = Vector((ELBOW_L_POS.x if co.x >= 0 else -ELBOW_L_POS.x, ELBOW_L_POS.y, ELBOW_L_POS.z))
    wr = Vector((WRIST_L_POS.x if co.x >= 0 else -WRIST_L_POS.x, WRIST_L_POS.y, WRIST_L_POS.z))
    u_past = (co - wr).dot((wr - el).normalized())
    t_hand = smoothstep(-0.025, 0.008, u_past)
    return {f"{side}ForeArm": 1.0 - t_hand, f"{side}Hand": t_hand}


def weight_trousers(co: Vector) -> dict[str, float]:
    z = co.z
    if z >= 0.785:
        return {"Hips": 1.0}
    side = "Left" if co.x >= 0.0 else "Right"
    if z >= 0.710:
        t_leg = smoothstep(0.785, 0.710, z)
        return {"Hips": 1.0 - t_leg, f"{side}UpLeg": t_leg}
    elif z > 0.485:
        return {f"{side}UpLeg": 1.0}
    elif z >= 0.385:
        t_knee = smoothstep(0.485, 0.385, z)
        return {f"{side}UpLeg": 1.0 - t_knee, f"{side}Leg": t_knee}
    elif z >= 0.115:
        return {f"{side}Leg": 1.0}
    else:
        t_foot = smoothstep(0.115, 0.080, z)
        return {f"{side}Leg": 1.0 - t_foot, f"{side}Foot": t_foot}


def weight_footwear(co: Vector) -> dict[str, float]:
    side = "Left" if co.x >= 0.0 else "Right"
    if co.z <= 0.075:
        return {f"{side}Foot": 1.0}
    t_ankle = smoothstep(0.075, 0.110, co.z)
    return {f"{side}Foot": 1.0 - 0.35 * t_ankle, f"{side}Leg": 0.35 * t_ankle}


# ==============================================================================
# BAKED SKELETAL ANIMATION CLIPS (Verified Right-Hand World Axes)
# Around +X: NEGATIVE swings -Z toward -Y (FORWARD!). POSITIVE bends knee (+Z -> +Y BACKWARD!).
# Around +Y: +angle lowers LeftArm (+X -> -Z), -angle lowers RightArm (-X -> -Z).
# ==============================================================================
def create_slotted_nla_action(arm_obj: bpy.types.Object, name: str, frame_end: int, keyframe_fn) -> None:
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    act = bpy.data.actions.new(name)
    slot = act.slots.new(id_type="OBJECT", name=arm_obj.name)
    arm_obj.animation_data.action = act
    arm_obj.animation_data.action_slot = slot

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)

    keyframe_fn(arm_obj, frame_end)

    tr = arm_obj.animation_data.nla_tracks.new()
    tr.name = name
    st = tr.strips.new(name, 1, act)
    st.action_slot = slot
    arm_obj.animation_data.action = None

    for pb in arm_obj.pose.bones:
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)


def key_pose(
    arm_obj: bpy.types.Object,
    frame: int,
    world_rots: dict[str, tuple[float, float, float]],
    *,
    hips_world_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    order = [
        ("Hips", None),
        ("Spine", "Hips"),
        ("Spine1", "Spine"),
        ("Neck", "Spine1"),
        ("Head", "Neck"),
        ("LeftShoulder", "Spine1"),
        ("LeftArm", "LeftShoulder"),
        ("LeftForeArm", "LeftArm"),
        ("LeftHand", "LeftForeArm"),
        ("RightShoulder", "Spine1"),
        ("RightArm", "RightShoulder"),
        ("RightForeArm", "RightArm"),
        ("RightHand", "RightForeArm"),
        ("LeftUpLeg", "Hips"),
        ("LeftLeg", "LeftUpLeg"),
        ("LeftFoot", "LeftLeg"),
        ("RightUpLeg", "Hips"),
        ("RightLeg", "RightUpLeg"),
        ("RightFoot", "RightLeg"),
    ]
    accum_mat: dict[str, Matrix] = {}
    for bname, pname in order:
        pb = arm_obj.pose.bones[bname]
        b = arm_obj.data.bones[bname]
        rest_mat = b.matrix_local.to_3x3()
        des_deg = world_rots.get(bname, (0.0, 0.0, 0.0))
        r_des = Euler(tuple(math.radians(a) for a in des_deg), "XYZ").to_matrix()
        r_par = accum_mat[pname] if pname else Matrix.Identity(3)
        r_delta = r_par.inverted() @ r_des
        r_local = rest_mat.inverted() @ r_delta @ rest_mat
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = r_local.to_euler("XYZ")
        accum_mat[bname] = r_des
        pb.keyframe_insert("rotation_euler", frame=frame)
        if bname == "Hips":
            pb.location = rest_mat.inverted() @ Vector(hips_world_offset)
            pb.keyframe_insert("location", frame=frame)


def author_animations(arm_obj: bpy.types.Object) -> None:
    # Note: bind pose arms are ~20 deg down; rotating +14 deg Y lowers LeftArm naturally right beside jacket hem!
    # 1. Idle_Breathing (frames 1..73, 3.0s loop)
    def anim_idle(arm: bpy.types.Object, f_end: int) -> None:
        for f in (1, 19, 37, 55, 73):
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            br = math.sin(ph)
            rots = {
                "Hips": (0.0, -1.5, 2.0),
                "Spine": (1.0, 0.0, 1.5),
                "Spine1": (1.5 + br * 1.4, 0.5, 1.0),
                "Neck": (-1.0 - br * 0.5, 0.0, -1.5),
                "Head": (1.5 - br * 0.6, 0.6 * math.cos(ph), -2.5),
                # Natural arms hanging gracefully near thighs with relaxed slight forward elbow bend
                "LeftShoulder": (0.0, 3.0, 0.0),
                "LeftArm": (-3.0, 19.0 + br * 0.8, 2.0),
                "LeftForeArm": (-16.0 - br * 1.5, 13.0, 4.0),
                "LeftHand": (-14.0, 9.0, 5.0),
                "RightShoulder": (0.0, -3.0, 0.0),
                "RightArm": (-2.0, -19.0 - br * 0.8, -2.0),
                "RightForeArm": (-15.0 - br * 1.5, -13.0, -4.0),
                "RightHand": (-12.0, -9.0, -5.0),
                # Clean balanced grounded stance
                "LeftUpLeg": (-1.0, 1.2, 0.0),
                "LeftLeg": (2.0, 0.0, 0.0),
                "LeftFoot": (0.0, 0.0, 2.0),
                "RightUpLeg": (1.0, -0.5, 0.0),
                "RightLeg": (2.0, 0.0, 0.0),
                "RightFoot": (0.0, 0.0, -2.0),
            }
            key_pose(arm, f, rots, hips_world_offset=(0.003, 0.0, br * 0.003))

    create_slotted_nla_action(arm_obj, "Idle_Breathing", 73, anim_idle)

    # 2. Walk_Forward (frames 1..25, verified right-hand X: NEGATIVE X swings leg FORWARD (-Y), POSITIVE X bends knee BACK!)
    def anim_walk(arm: bpy.types.Object, f_end: int) -> None:
        frames = [1, 4, 7, 10, 13, 16, 19, 22, 25]
        for f in frames:
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            s = math.sin(ph)
            c = math.cos(ph)
            # Peaks (+) at passing stance (ph=0, pi), dips slightly (-) at max stride contact (ph=pi/2, 3*pi/2)
            bounce = math.cos(2.0 * ph)

            # Left leg forward at s=+1 -> -24 deg X! Right leg forward at s=-1 -> +s*24 deg X!
            l_thigh_x = -s * 24.0
            r_thigh_x = s * 24.0
            # Knee bend (+X bends lower shin toward +Y back!) peaks during swing recovery
            l_knee_flex = max(4.0, 38.0 * math.sin(ph + 0.55) if math.sin(ph + 0.55) > 0 else 5.0)
            r_knee_flex = max(4.0, 38.0 * math.sin(ph + math.pi + 0.55) if math.sin(ph + math.pi + 0.55) > 0 else 5.0)
            l_shin_x = l_thigh_x + l_knee_flex
            r_shin_x = r_thigh_x + r_knee_flex
            l_foot_x = l_thigh_x * 0.25 + c * 8.0
            r_foot_x = r_thigh_x * 0.25 - c * 8.0

            # Counter-swinging arms: when Left leg swings forward (s=+1), Right arm swings forward (-X!) & Left arm swings back (+X!)
            l_arm_x = s * 18.0 - 2.0
            r_arm_x = -s * 18.0 - 2.0

            rots = {
                "Hips": (-2.0, c * 1.8, -s * 4.5),
                "Spine": (-2.0, -c * 1.0, -s * 2.0),
                "Spine1": (-3.0, -c * 1.2, s * 4.5),
                "Neck": (0.0, 0.0, s * 1.5),
                "Head": (2.0, 0.0, s * 1.5),
                "LeftShoulder": (0.0, 2.0, s * 2.0),
                "LeftArm": (l_arm_x, 18.0, 0.0),
                "LeftForeArm": (l_arm_x - 20.0 - max(0.0, -s) * 8.0, 14.0, 3.0),
                "LeftHand": (l_arm_x - 18.0, 10.0, 4.0),
                "RightShoulder": (0.0, -2.0, s * 2.0),
                "RightArm": (r_arm_x, -18.0, 0.0),
                "RightForeArm": (r_arm_x - 20.0 - max(0.0, s) * 8.0, -14.0, -3.0),
                "RightHand": (r_arm_x - 18.0, -10.0, -4.0),
                "LeftUpLeg": (l_thigh_x, 0.0, -s * 2.0),
                "LeftLeg": (l_shin_x, 0.0, 0.0),
                "LeftFoot": (l_foot_x, 0.0, 0.0),
                "RightUpLeg": (r_thigh_x, 0.0, -s * 2.0),
                "RightLeg": (r_shin_x, 0.0, 0.0),
                "RightFoot": (r_foot_x, 0.0, 0.0),
            }
            # Ground heel contact near Z=0 at max stride, lift slightly at passing
            z_bob = 0.004 + bounce * 0.016
            key_pose(arm, f, rots, hips_world_offset=(c * 0.010, 0.0, z_bob))

    create_slotted_nla_action(arm_obj, "Walk_Forward", 25, anim_walk)

    # 3. Gesture_Present (frames 1..49): RightArm (-X) reaches invitingly forward & toward sculpture (-X) with open palm!
    def anim_present(arm: bpy.types.Object, f_end: int) -> None:
        for f in (1, 13, 25, 37, 49):
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            hold = 0.72 + 0.28 * (0.5 - 0.5 * math.cos(ph))
            rots = {
                "Hips": (0.0, 0.0, -4.0 * hold),
                "Spine": (1.0, 0.0, -6.0 * hold),
                "Spine1": (2.0, 0.0, -10.0 * hold),
                "Neck": (0.0, 0.0, -4.0 * hold),
                "Head": (2.0, 0.0, -2.0 * hold),
                "LeftShoulder": (0.0, 2.0, 0.0),
                "LeftArm": (-3.0, 14.0, 2.0),
                "LeftForeArm": (-18.0, 11.0, 4.0),
                "LeftHand": (-15.0, 8.0, 4.0),
                # Negative X swings forward (-Y); moderate Y keeps presenting open palm clearly clear of nearby 3D sculptural props
                "RightShoulder": (0.0, 3.0 * hold, -3.0 * hold),
                "RightArm": (-36.0 * hold, 11.0 * hold - 14.0 * (1.0 - hold), -10.0 * hold),
                "RightForeArm": (-76.0 * hold, 8.0 * hold - 11.0 * (1.0 - hold), -8.0 * hold),
                "RightHand": (-72.0 * hold, 6.0 * hold, 24.0 * hold),
                "LeftUpLeg": (-1.0, 1.2, 0.0),
                "LeftLeg": (2.0, 0.0, 0.0),
                "LeftFoot": (0.0, 0.0, 3.0),
                "RightUpLeg": (1.0, -0.5, 0.0),
                "RightLeg": (2.0, 0.0, 0.0),
                "RightFoot": (0.0, 0.0, -4.0),
            }
            key_pose(arm, f, rots, hips_world_offset=(0.0, 0.0, 0.002 * hold))

    create_slotted_nla_action(arm_obj, "Gesture_Present", 49, anim_present)

    # 4. Turn_Greet (frames 1..49): Poised keynote welcoming raise of LeftHand (+X) & gentle nod
    def anim_greet(arm: bpy.types.Object, f_end: int) -> None:
        for f in (1, 13, 25, 37, 49):
            ph = 2.0 * math.pi * ((f - 1) / (f_end - 1))
            lift = 0.5 - 0.5 * math.cos(ph)
            wave = math.sin(ph * 2.0) * 8.0 * lift
            rots = {
                "Hips": (0.0, 0.0, 3.0 * lift),
                "Spine": (1.0, 0.0, 4.0 * lift),
                "Spine1": (2.0, 0.0, 5.0 * lift),
                "Neck": (-1.0, 0.0, 2.0 * lift),
                "Head": (-4.0 * lift + 1.5, 3.0 * lift, 0.0),
                "LeftShoulder": (0.0, -4.0 * lift, 0.0),
                "LeftArm": (-42.0 * lift - 3.0, -10.0 * lift + 14.0 * (1.0 - lift), 12.0 * lift),
                "LeftForeArm": (-98.0 * lift - 16.0 * (1.0 - lift), 12.0 + wave, 14.0 * lift),
                "LeftHand": (-100.0 * lift - 14.0 * (1.0 - lift), 10.0 + wave * 1.3, -18.0 * lift),
                "RightShoulder": (0.0, -2.0, 0.0),
                "RightArm": (-3.0, -14.0, -2.0),
                "RightForeArm": (-16.0, -11.0, -4.0),
                "RightHand": (-14.0, -8.0, -5.0),
                "LeftUpLeg": (0.0, 1.0, 0.0),
                "LeftLeg": (1.5, 0.0, 0.0),
                "LeftFoot": (0.0, 0.0, 2.0),
                "RightUpLeg": (0.0, -1.0, 0.0),
                "RightLeg": (1.5, 0.0, 0.0),
                "RightFoot": (0.0, 0.0, -2.0),
            }
            key_pose(arm, f, rots)

    create_slotted_nla_action(arm_obj, "Turn_Greet", 49, anim_greet)


def main() -> None:
    clear_scene()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.scene.render.fps = 24

    mats = create_material_library()
    arm_obj = build_armature()

    head_obj = build_head_and_neck(mats)
    eyes_obj = build_eyes(mats)
    eyelids_obj = build_eyelids(mats)
    brows_obj = build_brows(mats)
    hair_obj = build_hair(mats)
    glasses_obj = build_glasses(mats)
    tee_obj = build_inner_tee(mats)
    jacket_obj = build_jacket(mats)
    hands_obj = build_hands(mats)
    trousers_obj = build_trousers(mats)
    footwear_obj = build_footwear(mats)

    assign_weights_dict(head_obj, arm_obj, weight_head_and_neck)
    assign_weights_dict(eyes_obj, arm_obj, weight_rigid_head)
    assign_weights_dict(eyelids_obj, arm_obj, weight_rigid_head)
    assign_weights_dict(brows_obj, arm_obj, weight_rigid_head)
    assign_weights_dict(hair_obj, arm_obj, weight_rigid_head)
    assign_weights_dict(glasses_obj, arm_obj, weight_rigid_head)
    assign_weights_dict(tee_obj, arm_obj, weight_torso_tee)
    assign_weights_dict(jacket_obj, arm_obj, weight_jacket)
    assign_weights_dict(hands_obj, arm_obj, weight_hands)
    assign_weights_dict(trousers_obj, arm_obj, weight_trousers)
    assign_weights_dict(footwear_obj, arm_obj, weight_footwear)

    author_animations(arm_obj)

    mesh_objs = [
        head_obj,
        eyes_obj,
        eyelids_obj,
        brows_obj,
        hair_obj,
        glasses_obj,
        tee_obj,
        jacket_obj,
        hands_obj,
        trousers_obj,
        footwear_obj,
    ]
    total_verts = 0
    for mo in mesh_objs:
        total_verts += len(mo.data.vertices)
        zs = [v.co.z for v in mo.data.vertices]
        print(f"  Mesh {mo.name:24s} | verts={len(mo.data.vertices):5d} | Z=[{min(zs):.4f}, {max(zs):.4f}]")
    print(f"Total companion vertices: {total_verts} | Bones: {len(arm_obj.data.bones)} | NLA Clips: {len(arm_obj.animation_data.nla_tracks)}")

    out_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "public", "models", "zachary_companion.glb")
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        export_yup=True,
        export_apply=False,
        export_materials="EXPORT",
        export_skins=True,
        export_morph=True,
        export_animations=True,
        export_animation_mode="NLA_TRACKS",
        export_nla_strips=True,
    )
    size_bytes = os.path.getsize(out_path)
    print(f"Exported {out_path}: {size_bytes} bytes ({size_bytes / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
