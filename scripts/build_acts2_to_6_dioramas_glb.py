"""
Build Acts 2–6 Architectural Diorama GLB Kits in Headless Blender 5.2
=====================================================================
Adheres strictly to `.agents/rules/blender-3d.md`:
- 100% context-free `bmesh` geometry construction (zero `bpy.ops.mesh.primitive_*`)
- Automated `BEVEL` + `WEIGHTED_NORMAL` modifiers on every architectural mesh
- Multi-material PBR slots tailored to each Act's unique architectural palette:
  * Act 2 (`act2_academy.glb`): Heritage Mahogany, Warm Parchment, Antique Brass & Emerald Glass
  * Act 3 (`act3_crucible.glb`): Theatrical Keynote Slate, Warm Stage Gold, Alabaster Baffles & Sapphire Glass
  * Act 4 (`act4_summit.glb`): Swiss Alpine Gneiss Stone, Snow Veins, Alpenglow Gold & Hilti Crimson
  * Act 5 (`act5_frontier.glb`): Anodized Graphite, CNC Brushed Aluminum, International Orange & Smoked Glass
  * Act 6 (`act6_horizon.glb`): Serene Dawn Travertine, Obsidian Reflection Pool & Champagne Pearl Bronze
- Renders a 6-act Cycles contact sheet (`diorama_6act_contact_sheet.png`) to the artifacts directory.
"""

import os
import math
import shutil
import bpy
import bmesh
from mathutils import Vector, Matrix

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROPS_DIR = os.path.join(PROJECT_ROOT, "public", "models", "props")
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "screenshots")
ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", "")
os.makedirs(PROPS_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def make_pbr_mat(
    name: str,
    base_color=(0.5, 0.5, 0.5, 1.0),
    metallic=0.0,
    roughness=0.5,
    emission_color=(0.0, 0.0, 0.0, 1.0),
    emission_strength=0.0,
    coat_weight=0.0,
    alpha=1.0,
):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = coat_weight
        if alpha < 1.0 and "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
            if hasattr(mat, "blend_method"):
                mat.blend_method = "BLEND"
    return mat


def add_box_part(bm: bmesh.types.BMesh, sx: float, sy: float, sz: float, center: Vector, mat_idx: int = 0, rot_euler=(0.0, 0.0, 0.0)):
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    scale_mat = Matrix.Diagonal(Vector((sx, sy, sz, 1.0)))
    rot_mat = (
        Matrix.Rotation(rot_euler[2], 4, "Z")
        @ Matrix.Rotation(rot_euler[1], 4, "Y")
        @ Matrix.Rotation(rot_euler[0], 4, "X")
    )
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ rot_mat @ scale_mat, verts=verts)
    vert_set = set(verts)
    for f in bm.faces:
        if all(v in vert_set for v in f.verts):
            f.material_index = mat_idx


def add_cyl_part(
    bm: bmesh.types.BMesh,
    r1: float,
    r2: float,
    depth: float,
    segments: int,
    center: Vector,
    mat_idx: int = 0,
    rot_euler=(0.0, 0.0, 0.0),
):
    res = bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=r1,
        radius2=r2,
        depth=depth,
    )
    verts = res["verts"]
    rot_mat = (
        Matrix.Rotation(rot_euler[2], 4, "Z")
        @ Matrix.Rotation(rot_euler[1], 4, "Y")
        @ Matrix.Rotation(rot_euler[0], 4, "X")
    )
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ rot_mat, verts=verts)
    vert_set = set(verts)
    for f in bm.faces:
        if all(v in vert_set for v in f.verts):
            f.material_index = mat_idx


def add_ring_part(
    bm: bmesh.types.BMesh,
    major_r: float,
    minor_r: float,
    height: float,
    segments: int,
    center: Vector,
    mat_idx: int = 0,
    arc_angle: float = math.pi * 2.0,
    rot_euler=(0.0, 0.0, 0.0),
):
    r_in = major_r - minor_r
    r_out = major_r + minor_r
    z_bot = -height / 2.0
    z_top = height / 2.0
    is_closed = abs(arc_angle - math.pi * 2.0) < 1e-4
    ring_verts = []
    count = segments if is_closed else (segments + 1)
    for i in range(count):
        ang = (i / segments) * arc_angle
        ca, sa = math.cos(ang), math.sin(ang)
        v0 = bm.verts.new((ca * r_in, sa * r_in, z_bot))
        v1 = bm.verts.new((ca * r_out, sa * r_out, z_bot))
        v2 = bm.verts.new((ca * r_out, sa * r_out, z_top))
        v3 = bm.verts.new((ca * r_in, sa * r_in, z_top))
        ring_verts.append((v0, v1, v2, v3))

    loop_cnt = segments
    for i in range(loop_cnt):
        a0, a1, a2, a3 = ring_verts[i]
        b0, b1, b2, b3 = ring_verts[(i + 1) % len(ring_verts)]
        for quad in [(a0, b0, b1, a1), (a1, b1, b2, a2), (a2, b2, b3, a3), (a3, b3, b0, a0)]:
            try:
                f = bm.faces.new(quad)
                f.material_index = mat_idx
            except ValueError:
                pass

    if not is_closed and len(ring_verts) >= 2:
        s0, s1, s2, s3 = ring_verts[0]
        e0, e1, e2, e3 = ring_verts[-1]
        for cap in [(s0, s1, s2, s3), (e3, e2, e1, e0)]:
            try:
                f = bm.faces.new(cap)
                f.material_index = mat_idx
            except ValueError:
                pass

    flat_verts = [v for tup in ring_verts for v in tup]
    rot_mat = (
        Matrix.Rotation(rot_euler[2], 4, "Z")
        @ Matrix.Rotation(rot_euler[1], 4, "Y")
        @ Matrix.Rotation(rot_euler[0], 4, "X")
    )
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ rot_mat, verts=flat_verts)


def add_alpine_peak(
    bm: bmesh.types.BMesh,
    base_center: Vector,
    rx: float,
    ry: float,
    height: float,
    crest_offset: tuple[float, float] = (0.08, 0.04),
    ridge_angle: float = 0.0,
    snow_ratio: float = 0.56,
    seed: float = 0.0,
    rock_mat_idx: int = 0,
    snow_mat_idx: int = 1,
):
    """Sculpt a chiseled stratified Swiss granite alpine peak with cirque shoulders in context-free bmesh."""
    segments = 26
    ca_r, sa_r = math.cos(ridge_angle), math.sin(ridge_angle)

    def rot_xy(x: float, y: float) -> tuple[float, float]:
        return (x * ca_r - y * sa_r, x * sa_r + y * ca_r)

    base_verts = []
    terrace_verts = []
    snow_verts = []
    upper_snow_verts = []
    cx, cy, cz = base_center.x, base_center.y, base_center.z

    for i in range(segments):
        ang = (i / segments) * math.pi * 2.0
        # Multi-harmonic ridge crag ribs & glacier cirque asymmetry so facets read like chiseled Swiss granite
        rad_jit = (
            1.0
            + 0.22 * math.sin(ang * 2.0 + seed)
            + 0.16 * math.cos(ang * 3.0 - seed * 1.7)
            + 0.11 * math.cos(ang * 4.0 + seed * 0.9)
            + 0.09 * math.sin(ang * 5.0 + seed * 2.3)
            + 0.07 * math.sin(ang * 7.0 - seed * 1.3)
        )
        rad_jit = max(0.62, min(1.32, rad_jit))
        bx_local = math.cos(ang) * rx * rad_jit
        by_local = math.sin(ang) * ry * rad_jit
        bx, by = rot_xy(bx_local, by_local)
        vb = bm.verts.new((cx + bx, cy + by, cz - 0.02))
        base_verts.append(vb)

        # Mid-elevation stratified granite cliff terrace step
        t_scale = 0.68 + 0.08 * math.cos(ang * 4.0 + seed * 0.5) + 0.04 * math.sin(ang * 7.0 - seed)
        tx_local = bx_local * t_scale + crest_offset[0] * 0.25
        ty_local = by_local * t_scale + crest_offset[1] * 0.25
        tx_r, ty_r = rot_xy(tx_local, ty_local)
        tz = cz + min(0.46, height * 0.28)
        vt = bm.verts.new((cx + tx_r, cy + ty_r, tz))
        terrace_verts.append(vt)

        # Modulated cirque snowline transition between lower gneiss skirt and crisp alpine snow cap
        mod = 0.12 * math.sin(ang * 2.0 + seed) + 0.07 * math.cos(ang * 4.0 - seed) + 0.04 * math.sin(ang * 7.0 + seed)
        snow_scale = 0.44 + 0.07 * math.cos(ang * 2.0 + seed * 0.8) + 0.04 * math.cos(ang * 4.0 - seed)
        sx_local = bx_local * snow_scale + crest_offset[0] * 0.55
        sy_local = by_local * snow_scale + crest_offset[1] * 0.55
        sx, sy = rot_xy(sx_local, sy_local)
        sz = max(cz + 0.52, min(cz + height * 0.72, cz + height * (snow_ratio + mod)))
        vs = bm.verts.new((cx + sx, cy + sy, sz))
        snow_verts.append(vs)

        # Upper fluted arête snow shoulder
        upper_scale = 0.22 + 0.05 * math.sin(ang * 5.0 + seed * 1.3) + 0.03 * math.sin(ang * 7.0 + seed)
        ux_local = bx_local * upper_scale + crest_offset[0] * 0.80
        uy_local = by_local * upper_scale + crest_offset[1] * 0.80
        ux, uy = rot_xy(ux_local, uy_local)
        uz = max(sz + 0.14, min(cz + height * 0.89, cz + height * (0.78 + 0.05 * math.sin(ang * 3.0 + seed))))
        vu = bm.verts.new((cx + ux, cy + uy, uz))
        upper_snow_verts.append(vu)

    # Knife-edge asymmetric ridge crest (two separated apex vertices forming an elongated alpine arête)
    spine_half = max(0.12, min(rx, ry) * 0.36)
    c1x, c1y = rot_xy(crest_offset[0] - spine_half, crest_offset[1] - spine_half * 0.25)
    c2x, c2y = rot_xy(crest_offset[0] + spine_half, crest_offset[1] + spine_half * 0.25)
    v_crest_a = bm.verts.new((cx + c1x, cy + c1y, cz + height * 0.94))
    v_crest_b = bm.verts.new((cx + c2x, cy + c2y, cz + height))

    # Triangulate lower basalt skirt + mid contour terrace step -> upper travertine transition
    for i in range(segments):
        nxt = (i + 1) % segments
        b0, b1 = base_verts[i], base_verts[nxt]
        t0, t1 = terrace_verts[i], terrace_verts[nxt]
        s0, s1 = snow_verts[i], snow_verts[nxt]
        for tri in [(b0, b1, t1), (b0, t1, t0), (t0, t1, s1), (t0, s1, s0)]:
            try:
                f = bm.faces.new(tri)
                f.material_index = rock_mat_idx
            except ValueError:
                pass

    # Cap underside cleanly
    try:
        f_bot = bm.faces.new(list(reversed(base_verts)))
        f_bot.material_index = rock_mat_idx
    except ValueError:
        pass

    # Triangulate fluted upper snow strata (snowline -> upper shoulder -> ridge crest)
    crest_for_seg = [
        v_crest_b if math.cos(((k + 0.5) / segments) * math.pi * 2.0) >= 0.0 else v_crest_a
        for k in range(segments)
    ]
    for i in range(segments):
        nxt = (i + 1) % segments
        s0, s1 = snow_verts[i], snow_verts[nxt]
        u0, u1 = upper_snow_verts[i], upper_snow_verts[nxt]
        c_cur = crest_for_seg[i]
        c_nxt = crest_for_seg[nxt]
        is_rock_couloir = (i % 3 == 0) and (max(s0.co.z, s1.co.z, u0.co.z, u1.co.z) <= 2.35)
        mid_mat = rock_mat_idx if is_rock_couloir else snow_mat_idx
        for tri in [(s0, s1, u1), (s0, u1, u0)]:
            try:
                f = bm.faces.new(tri)
                f.material_index = mid_mat
            except ValueError:
                pass
        try:
            f_top = bm.faces.new((u0, u1, c_cur))
            f_top.material_index = snow_mat_idx
        except ValueError:
            pass
        if c_cur != c_nxt:
            try:
                f_ridge = bm.faces.new((u1, c_nxt, c_cur))
                f_ridge.material_index = snow_mat_idx
            except ValueError:
                pass


def finalize_bmesh_object(
    bm: bmesh.types.BMesh,
    name: str,
    materials: list,
    bevel_width: float = 0.008,
    smooth: bool = True,
) -> bpy.types.Object:
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    for poly in mesh.polygons:
        poly.use_smooth = smooth

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for m in materials:
        obj.data.materials.append(m)

    if bevel_width > 0:
        bev = obj.modifiers.new(name="Bevel", type="BEVEL")
        bev.width = bevel_width
        bev.segments = 2 if smooth else 1
        bev.limit_method = "ANGLE"
        bev.angle_limit = math.radians(32.0)
        bev.use_clamp_overlap = True
        if smooth:
            bev.harden_normals = True

        if smooth:
            wn = obj.modifiers.new(name="WeightedNormal", type="WEIGHTED_NORMAL")
            wn.keep_sharp = True

    return obj


def export_glb(filename: str):
    out_path = os.path.join(PROPS_DIR, filename)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_meshopt_compression_enable=True,
        export_meshopt_extension="EXT_meshopt_compression",
    )
    size_kb = os.path.getsize(out_path) / 1024.0
    print(f"[DioramaBuilder] Exported {out_path} ({size_kb:.1f} KB)")
    return out_path


# ==============================================================================
# ACT 2: THE ACADEMY LIBRARY (Heritage Mahogany, Parchment, Brass & Emerald)
# ==============================================================================
def build_act2_academy():
    clear_scene()
    m_mahogany = make_pbr_mat("M_Heritage_Mahogany", (0.14, 0.09, 0.06, 1.0), metallic=0.04, roughness=0.42, coat_weight=0.18)
    m_parchment = make_pbr_mat("M_Warm_Parchment_Stone", (0.22, 0.20, 0.18, 1.0), metallic=0.02, roughness=0.64)
    m_brass = make_pbr_mat("M_Antique_Brass", (0.76, 0.61, 0.36, 1.0), metallic=0.88, roughness=0.25)
    m_emerald = make_pbr_mat("M_Banker_Emerald_Glass", (0.06, 0.34, 0.22, 1.0), metallic=0.12, roughness=0.22, emission_color=(0.08, 0.68, 0.42, 1.0), emission_strength=0.45)
    m_dark_basalt = make_pbr_mat("M_Library_Basalt", (0.075, 0.070, 0.068, 1.0), metallic=0.12, roughness=0.60)

    # 1. SM_Island_Act2 (Monolithic Museum Amphitheater & Tonal Stone Archive Piers)
    bm = bmesh.new()
    add_cyl_part(bm, 5.55, 5.40, 0.16, 64, Vector((0.35, 0.0, -0.18)), mat_idx=1)
    add_cyl_part(bm, 5.20, 5.15, 0.04, 64, Vector((0.35, 0.0, -0.09)), mat_idx=3)
    add_cyl_part(bm, 2.75, 2.62, 0.18, 64, Vector((0.35, 0.0, -0.09)), mat_idx=0)
    add_cyl_part(bm, 2.45, 2.45, 0.02, 64, Vector((0.35, 0.0, 0.005)), mat_idx=1)
    for rr, rt, rz in [(1.55, 0.010, 0.017), (2.46, 0.014, 0.017), (3.40, 0.014, -0.066), (4.60, 0.016, -0.066)]:
        add_ring_part(bm, rr, rt, 0.012, 64, Vector((0.35, 0.0, rz)), mat_idx=2)
    # 12-spoke antique-brass floor compass rose inlay on central scholar dais
    for sp_i in range(12):
        sp_ang = (sp_i / 12.0) * math.pi * 2.0
        add_box_part(
            bm,
            0.88,
            0.014,
            0.010,
            Vector((0.35 + math.cos(sp_ang) * 1.98, math.sin(sp_ang) * 1.98, 0.015)),
            mat_idx=2,
            rot_euler=(0.0, 0.0, sp_ang),
        )
    # Two subdued stepped circular museum amphitheater ledges (obsidian basalt + warm travertine, open vista behind center)
    for tier_i, (tr_in, tr_out, tr_z) in enumerate([
        (3.25, 3.85, 0.22),
        (3.85, 4.45, 0.46),
    ]):
        add_ring_part(bm, (tr_in + tr_out) * 0.5, (tr_out - tr_in) * 0.5, tr_z, 48, Vector((0.35, 0.0, tr_z * 0.5 - 0.08)), mat_idx=1 if tier_i == 0 else 3, arc_angle=math.pi * 0.88, rot_euler=(0, 0, math.pi * 0.06))
        add_ring_part(bm, tr_in + 0.02, 0.016, 0.014, 48, Vector((0.35, 0.0, tr_z - 0.075)), mat_idx=2, arc_angle=math.pi * 0.88, rot_euler=(0, 0, math.pi * 0.06))

    # Six monolithic travertine & mahogany museum archive piers with recessed book-tier rows & brass cornice caps
    for ang_deg in (36.0, 54.0, 72.0, 108.0, 126.0, 144.0):
        ang_w = math.radians(ang_deg)
        r_w = 4.05
        wx = 0.35 + math.cos(ang_w) * r_w
        wy = math.sin(ang_w) * r_w
        rot_w = (0, 0, ang_w + math.pi / 2)
        add_box_part(bm, 0.52, 0.26, 0.14, Vector((wx, wy, 0.46)), mat_idx=1, rot_euler=rot_w)
        add_box_part(bm, 0.48, 0.22, 1.52, Vector((wx, wy, 1.24)), mat_idx=3, rot_euler=rot_w)
        add_box_part(bm, 0.50, 0.06, 1.56, Vector((0.35 + math.cos(ang_w) * (r_w - 0.09), math.sin(ang_w) * (r_w - 0.09), 1.24)), mat_idx=0, rot_euler=rot_w)
        add_box_part(bm, 0.03, 0.24, 1.54, Vector((wx, wy, 1.24)), mat_idx=2, rot_euler=rot_w)
        add_box_part(bm, 0.56, 0.28, 0.045, Vector((wx, wy, 2.02)), mat_idx=2, rot_euler=rot_w)
        for shelf_z in (0.78, 1.14, 1.50, 1.86):
            add_box_part(
                bm,
                0.48,
                0.025,
                0.018,
                Vector((0.35 + math.cos(ang_w) * (r_w - 0.125), math.sin(ang_w) * (r_w - 0.125), shelf_z)),
                mat_idx=2,
                rot_euler=rot_w,
            )
            if shelf_z < 1.80:
                for b_sub in (-0.13, 0.0, 0.13):
                    off_x = math.cos(rot_w[2]) * b_sub
                    off_y = math.sin(rot_w[2]) * b_sub
                    add_box_part(
                        bm,
                        0.095,
                        0.055,
                        0.24,
                        Vector((0.35 + math.cos(ang_w) * (r_w - 0.125) + off_x, math.sin(ang_w) * (r_w - 0.125) + off_y, shelf_z + 0.14)),
                        mat_idx=0 if abs(b_sub) > 0.05 else 3,
                        rot_euler=rot_w,
                    )

    # Suspended 3-Ring Antique-Brass Armillary Sphere & Central Celestial Core crowning the central amphitheater
    arm_center = Vector((0.35, 2.35, 2.65))
    add_ring_part(bm, 0.88, 0.022, 0.028, 48, arm_center, mat_idx=2, rot_euler=(math.radians(65.0), math.radians(18.0), 0))
    add_ring_part(bm, 0.72, 0.018, 0.022, 48, arm_center, mat_idx=2, rot_euler=(math.radians(72.0), math.radians(-26.0), math.radians(32.0)))
    add_ring_part(bm, 0.56, 0.015, 0.018, 48, arm_center, mat_idx=2, rot_euler=(math.radians(-42.0), math.radians(24.0), math.radians(-18.0)))
    core_sp = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.14)
    core_verts = core_sp["verts"]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(arm_center), verts=core_verts)
    core_set = set(core_verts)
    for f in bm.faces:
        if all(v in core_set for v in f.verts):
            f.material_index = 2
    finalize_bmesh_object(bm, "SM_Island_Act2", [m_mahogany, m_dark_basalt, m_brass, m_parchment, m_emerald], bevel_width=0.006)

    # 2. SM_Arched_Bookshelf (Left side X = -0.85, Blender Y = 0.15 -> Three Z = -0.15)
    bm_shelf = bmesh.new()
    bx, by = -0.85, 0.15
    # Outer fluted mahogany pilasters, antique-brass capitals & base collars, and cornice
    for p_side in (-0.52, 0.52):
        add_box_part(bm_shelf, 0.12, 0.38, 1.95, Vector((bx + p_side, by, 0.975)), mat_idx=0)
        add_box_part(bm_shelf, 0.14, 0.40, 0.055, Vector((bx + p_side, by, 0.16)), mat_idx=2)
        add_box_part(bm_shelf, 0.14, 0.40, 0.055, Vector((bx + p_side, by, 1.90)), mat_idx=2)
        for fl_off in (-0.026, 0.0, 0.026):
            add_box_part(bm_shelf, 0.012, 0.024, 1.62, Vector((bx + p_side + fl_off, by - 0.195, 1.03)), mat_idx=2)
    add_box_part(bm_shelf, 1.18, 0.42, 0.12, Vector((bx, by, 1.98)), mat_idx=0)
    add_box_part(bm_shelf, 1.22, 0.44, 0.03, Vector((bx, by, 2.05)), mat_idx=2)
    add_ring_part(bm_shelf, 0.54, 0.048, 0.38, 36, Vector((bx, by, 2.02)), mat_idx=0, arc_angle=math.pi, rot_euler=(math.pi / 2, 0, 0))
    add_ring_part(bm_shelf, 0.48, 0.018, 0.40, 36, Vector((bx, by, 2.02)), mat_idx=2, arc_angle=math.pi, rot_euler=(math.pi / 2, 0, 0))
    add_ring_part(bm_shelf, 0.245, 0.235, 0.34, 36, Vector((bx, by + 0.02, 2.02)), mat_idx=0, arc_angle=math.pi, rot_euler=(math.pi / 2, 0, 0))
    # Ornate 8-ray brass astrolabe medallion & concentric bezel in arched pediment
    add_cyl_part(bm_shelf, 0.12, 0.10, 0.04, 24, Vector((bx, by - 0.16, 2.24)), mat_idx=2, rot_euler=(math.pi / 2, 0, 0))
    add_ring_part(bm_shelf, 0.21, 0.014, 0.028, 32, Vector((bx, by - 0.16, 2.22)), mat_idx=2, rot_euler=(math.pi / 2, 0, 0))
    for ray_i in range(8):
        rad_a = math.radians(15.0 + ray_i * (150.0 / 7.0))
        add_box_part(
            bm_shelf,
            0.016,
            0.022,
            0.38,
            Vector((bx + math.cos(rad_a) * 0.28, by - 0.155, 2.02 + math.sin(rad_a) * 0.28)),
            mat_idx=2,
            rot_euler=(0.0, math.pi / 2 - rad_a, 0.0),
        )
    add_box_part(bm_shelf, 0.08, 0.42, 0.09, Vector((bx, by, 2.56)), mat_idx=2)
    add_box_part(bm_shelf, 1.04, 0.04, 1.92, Vector((bx, by + 0.16, 0.96)), mat_idx=0)
    # Base plinth & 3 shelves
    add_box_part(bm_shelf, 1.16, 0.40, 0.14, Vector((bx, by, 0.07)), mat_idx=0)
    for s_idx, sz in enumerate([0.52, 1.02, 1.50]):
        add_box_part(bm_shelf, 1.02, 0.34, 0.035, Vector((bx, by, sz)), mat_idx=0)
        add_box_part(bm_shelf, 1.02, 0.015, 0.012, Vector((bx, by - 0.17, sz)), mat_idx=2)
    # Companion heritage library volumes flanking the interactive folio volumes (varied heights + gilt spine bands)
    companion_books = [
        (bx - 0.38, 0.69, 0.075, 0.31, 0),
        (bx - 0.10, 0.675, 0.070, 0.27, 1),
        (bx - 0.01, 0.70, 0.078, 0.33, 0),
        (bx + 0.08, 0.68, 0.070, 0.28, 0),
        (bx - 0.13, 1.185, 0.072, 0.28, 0),
        (bx - 0.04, 1.205, 0.078, 0.32, 1),
        (bx + 0.06, 1.18, 0.070, 0.27, 0),
        (bx + 0.22, 1.195, 0.085, 0.30, 1),
        (bx + 0.36, 1.175, 0.075, 0.26, 0),
        (bx - 0.32, 1.665, 0.080, 0.29, 0),
        (bx - 0.22, 1.65, 0.070, 0.26, 1),
        (bx - 0.12, 1.675, 0.082, 0.31, 0),
        (bx + 0.06, 1.655, 0.075, 0.27, 1),
    ]
    for cx_b, cz_b, cw_b, ch_b, cmat_b in companion_books:
        add_box_part(bm_shelf, cw_b, 0.21, ch_b, Vector((cx_b, by + 0.01, cz_b)), mat_idx=cmat_b)
        add_box_part(bm_shelf, cw_b + 0.004, 0.014, 0.018, Vector((cx_b, by - 0.095, cz_b + ch_b * 0.26)), mat_idx=2)
        add_box_part(bm_shelf, cw_b + 0.004, 0.014, 0.018, Vector((cx_b, by - 0.095, cz_b - ch_b * 0.26)), mat_idx=2)
    finalize_bmesh_object(bm_shelf, "SM_Arched_Bookshelf", [m_mahogany, m_parchment, m_brass], bevel_width=0.005)

    # 3. 4 Interactive Milestone Folio Volumes (Prop_Book_Vol1..4)
    vol_configs = [
        ("Prop_Book_Vol1", (0.08, 0.14, 0.28, 1.0), Vector((bx - 0.28, by - 0.02, 1.22))),
        ("Prop_Book_Vol2", (0.06, 0.20, 0.12, 1.0), Vector((bx + 0.22, by - 0.02, 1.69))),
        ("Prop_Book_Vol3", (0.30, 0.08, 0.10, 1.0), Vector((bx - 0.24, by - 0.02, 0.72))),
        ("Prop_Book_Vol4", (0.24, 0.14, 0.08, 1.0), Vector((bx + 0.24, by - 0.02, 0.72))),
    ]
    for v_name, v_col, v_pos in vol_configs:
        m_leather = make_pbr_mat(f"M_{v_name}", v_col, metallic=0.15, roughness=0.35)
        bm_v = bmesh.new()
        add_box_part(bm_v, 0.11, 0.24, 0.34, Vector((0, 0, 0)), mat_idx=0)
        add_box_part(bm_v, 0.09, 0.22, 0.32, Vector((0, -0.005, 0)), mat_idx=1)
        add_box_part(bm_v, 0.114, 0.02, 0.03, Vector((0, -0.115, 0.08)), mat_idx=2)
        add_box_part(bm_v, 0.114, 0.02, 0.03, Vector((0, -0.115, -0.08)), mat_idx=2)
        obj_v = finalize_bmesh_object(bm_v, v_name, [m_leather, m_parchment, m_brass], bevel_width=0.004)
        obj_v.location = v_pos

    # 4. SM_Pedestal_Lectern & SM_Banker_Lamp (Right side X = 1.55, Blender Y = -0.15 -> Three Z = +0.15)
    lx, ly = 1.55, -0.15
    bm_lec = bmesh.new()
    add_box_part(bm_lec, 0.62, 0.56, 0.08, Vector((lx, ly, 0.04)), mat_idx=0)
    add_box_part(bm_lec, 0.56, 0.50, 0.025, Vector((lx, ly, 0.09)), mat_idx=2)
    add_cyl_part(bm_lec, 0.145, 0.115, 0.92, 8, Vector((lx, ly, 0.55)), mat_idx=0)
    add_ring_part(bm_lec, 0.148, 0.016, 0.026, 8, Vector((lx, ly, 0.14)), mat_idx=2)
    add_ring_part(bm_lec, 0.135, 0.015, 0.024, 8, Vector((lx, ly, 0.54)), mat_idx=2)
    add_ring_part(bm_lec, 0.125, 0.015, 0.03, 8, Vector((lx, ly, 0.98)), mat_idx=2)
    for b_side in (-0.20, 0.20):
        add_box_part(bm_lec, 0.036, 0.28, 0.18, Vector((lx + b_side, ly - 0.04, 0.92)), mat_idx=2, rot_euler=(math.radians(18.0), 0, 0))
    add_box_part(bm_lec, 0.68, 0.52, 0.045, Vector((lx, ly, 1.05)), mat_idx=0, rot_euler=(math.radians(18.0), 0, 0))
    add_box_part(bm_lec, 0.68, 0.03, 0.03, Vector((lx, ly - 0.24, 0.97)), mat_idx=2)
    finalize_bmesh_object(bm_lec, "SM_Pedestal_Lectern", [m_mahogany, m_parchment, m_brass], bevel_width=0.005)

    bm_lamp = bmesh.new()
    add_cyl_part(bm_lamp, 0.075, 0.062, 0.03, 24, Vector((lx - 0.20, ly + 0.16, 1.12)), mat_idx=0)
    add_ring_part(bm_lamp, 0.056, 0.012, 0.022, 24, Vector((lx - 0.20, ly + 0.16, 1.142)), mat_idx=0)
    add_cyl_part(bm_lamp, 0.013, 0.013, 0.30, 16, Vector((lx - 0.20, ly + 0.16, 1.28)), mat_idx=0)
    hood_cx, hood_cy, hood_cz = lx - 0.17, ly + 0.13, 1.43
    hood_yaw = math.radians(12.0)
    add_box_part(bm_lamp, 0.035, 0.045, 0.024, Vector((hood_cx - 0.015, hood_cy + 0.02, 1.425)), mat_idx=0)
    add_ring_part(
        bm_lamp,
        0.055,
        0.014,
        0.22,
        24,
        Vector((hood_cx, hood_cy, hood_cz)),
        mat_idx=1,
        arc_angle=math.pi,
        rot_euler=(math.pi / 2, 0.0, math.pi / 2 + hood_yaw),
    )
    add_ring_part(
        bm_lamp,
        0.068,
        0.005,
        0.016,
        24,
        Vector((hood_cx, hood_cy, hood_cz)),
        mat_idx=0,
        arc_angle=math.pi,
        rot_euler=(math.pi / 2, 0.0, math.pi / 2 + hood_yaw),
    )
    add_cyl_part(bm_lamp, 0.0035, 0.0035, 0.11, 8, Vector((hood_cx + 0.06, hood_cy - 0.02, hood_cz - 0.06)), mat_idx=0)
    add_cyl_part(bm_lamp, 0.009, 0.006, 0.018, 12, Vector((hood_cx + 0.06, hood_cy - 0.02, hood_cz - 0.12)), mat_idx=0)
    for side in (-1.0, 1.0):
        cap_x = hood_cx + side * 0.114 * math.cos(hood_yaw)
        cap_y = hood_cy + side * 0.114 * math.sin(hood_yaw)
        add_cyl_part(
            bm_lamp,
            0.056,
            0.056,
            0.016,
            24,
            Vector((cap_x, cap_y, hood_cz + 0.014)),
            mat_idx=0,
            rot_euler=(0.0, math.pi / 2, hood_yaw),
        )
    add_cyl_part(bm_lamp, 0.014, 0.014, 0.035, 16, Vector((hood_cx, hood_cy, hood_cz + 0.072)), mat_idx=0)
    finalize_bmesh_object(bm_lamp, "SM_Banker_Lamp", [m_brass, m_emerald], bevel_width=0.003)

    return export_glb("act2_academy.glb")


# ==============================================================================
# ACT 3: THE CRUCIBLE STAGE (Theatrical Keynote Slate, Stage Gold & Alabaster)
# ==============================================================================
def build_act3_crucible():
    clear_scene()
    m_slate = make_pbr_mat("M_Keynote_Slate", (0.09, 0.10, 0.12, 1.0), metallic=0.22, roughness=0.52)
    m_gold = make_pbr_mat("M_Stage_Gold", (0.74, 0.60, 0.36, 1.0), metallic=0.88, roughness=0.26, emission_color=(0.74, 0.60, 0.36, 1.0), emission_strength=0.08)
    m_alabaster = make_pbr_mat("M_Acoustic_Alabaster", (0.25, 0.23, 0.21, 1.0), metallic=0.04, roughness=0.60)
    m_smoked_bronze = make_pbr_mat("M_Smoked_Bronze_Glass", (0.12, 0.11, 0.10, 1.0), metallic=0.35, roughness=0.22, emission_color=(0.74, 0.60, 0.36, 1.0), emission_strength=0.10)

    # 1. SM_Island_Act3 (Sculpted Keynote Rotunda & 12 Multi-Tier Tapered Acoustic Louver Ribs)
    bm = bmesh.new()
    add_cyl_part(bm, 5.55, 5.40, 0.16, 64, Vector((0.15, 0.0, -0.18)), mat_idx=0)
    add_ring_part(bm, 4.95, 0.022, 0.014, 64, Vector((0.15, 0.0, -0.092)), mat_idx=1)
    add_ring_part(bm, 4.55, 0.018, 0.016, 64, Vector((0.15, 0.0, -0.090)), mat_idx=1)
    add_ring_part(bm, 3.65, 0.016, 0.012, 64, Vector((0.15, 0.0, -0.092)), mat_idx=1)
    add_cyl_part(bm, 2.75, 2.60, 0.18, 64, Vector((0.15, 0.0, -0.09)), mat_idx=0)
    add_cyl_part(bm, 2.05, 2.05, 0.012, 64, Vector((0.15, 0.0, 0.002)), mat_idx=3)
    add_ring_part(bm, 2.52, 0.016, 0.012, 64, Vector((0.15, 0.0, 0.006)), mat_idx=1)
    add_ring_part(bm, 2.06, 0.014, 0.012, 64, Vector((0.15, 0.0, 0.008)), mat_idx=1)
    add_ring_part(bm, 1.45, 0.012, 0.010, 64, Vector((0.15, 0.0, 0.008)), mat_idx=1)
    # Grounded semicircular stepped travertine-and-obsidian museum rotunda parapet
    add_ring_part(bm, 3.45, 0.44, 0.16, 56, Vector((0.15, 0.0, -0.02)), mat_idx=0, arc_angle=math.pi * 0.86, rot_euler=(0, 0, math.pi * 0.07))
    add_ring_part(bm, 3.96, 0.44, 0.56, 56, Vector((0.15, 0.0, 0.22)), mat_idx=2, arc_angle=math.pi * 0.84, rot_euler=(0, 0, math.pi * 0.08))
    add_ring_part(bm, 3.74, 0.020, 0.020, 56, Vector((0.15, 0.0, 0.51)), mat_idx=1, arc_angle=math.pi * 0.84, rot_euler=(0, 0, math.pi * 0.08))
    add_ring_part(bm, 4.18, 0.024, 0.024, 56, Vector((0.15, 0.0, 0.51)), mat_idx=1, arc_angle=math.pi * 0.84, rot_euler=(0, 0, math.pi * 0.08))
    # 12 sculpted multi-tiered tapered acoustic louver ribs with angled alabaster diffusers & gold light channels
    for fi in range(12):
        ang_f = math.radians(22.0 + (fi / 11.0) * 136.0)
        rot_f = (0, 0, ang_f)
        # Rear stepped slate structural spine
        fx_sp = 0.15 + math.cos(ang_f) * 4.24
        fy_sp = math.sin(ang_f) * 4.24
        add_box_part(bm, 0.42, 0.12, 1.66, Vector((fx_sp, fy_sp, 0.90)), mat_idx=0, rot_euler=rot_f)
        # Twin angled alabaster acoustic diffuser blades pitched subtly to catch stage key light
        for b_idx, (br_off, bz_h, bz_c) in enumerate([(4.02, 1.46, 0.96), (3.88, 1.18, 0.82)]):
            fx_b = 0.15 + math.cos(ang_f) * br_off
            fy_b = math.sin(ang_f) * br_off
            add_box_part(
                bm,
                0.28,
                0.08,
                bz_h,
                Vector((fx_b, fy_b, bz_c)),
                mat_idx=2 if (fi + b_idx) % 2 == 0 else 0,
                rot_euler=(0.0, 0.0, ang_f + math.radians(10.0 if b_idx == 0 else -8.0)),
            )
        # Vertical champagne-gold leading-edge light channel + top chamfered crown brace
        fx_ch = 0.15 + math.cos(ang_f) * 3.80
        fy_ch = math.sin(ang_f) * 3.80
        add_box_part(bm, 0.026, 0.042, 1.42, Vector((fx_ch, fy_ch, 0.88)), mat_idx=1, rot_euler=rot_f)
        fx_cr = 0.15 + math.cos(ang_f) * 4.04
        fy_cr = math.sin(ang_f) * 4.04
        add_box_part(bm, 0.56, 0.16, 0.045, Vector((fx_cr, fy_cr, 1.74)), mat_idx=1, rot_euler=rot_f)
        # Lower parapet buttress & gold inlay cap
        bx_r = 0.15 + math.cos(ang_f) * 3.46
        by_r = math.sin(ang_f) * 3.46
        add_box_part(bm, 0.38, 0.14, 0.46, Vector((bx_r, by_r, 0.23)), mat_idx=0, rot_euler=rot_f)
        add_box_part(bm, 0.032, 0.15, 0.48, Vector((0.15 + math.cos(ang_f) * 3.28, math.sin(ang_f) * 3.28, 0.23)), mat_idx=1, rot_euler=rot_f)
    finalize_bmesh_object(bm, "SM_Island_Act3", [m_slate, m_gold, m_alabaster, m_smoked_bronze], bevel_width=0.006)

    # 2. SM_GDSC_Lectern (Cantilevered Executive Keynote Command Podium w/ Dual Wings & Gooseneck Mics)
    bm_lec = bmesh.new()
    lx, ly = -0.65, -0.25
    add_box_part(bm_lec, 0.72, 0.52, 0.06, Vector((lx, ly, 0.03)), mat_idx=0)
    add_box_part(bm_lec, 0.64, 0.46, 0.022, Vector((lx, ly, 0.072)), mat_idx=1)
    lec_rot_z = math.radians(-12.0)
    lec_tilt_x = math.radians(-8.0)
    lec_rot_mat = Matrix.Rotation(lec_rot_z, 4, "Z") @ Matrix.Rotation(lec_tilt_x, 4, "X")
    lec_center = Vector((lx, ly, 0.52))
    add_box_part(bm_lec, 0.42, 0.24, 0.98, lec_center, mat_idx=0, rot_euler=(lec_tilt_x, 0, lec_rot_z))
    # Swept sculpted side acoustic wings with smoked-bronze inset plates
    for w_side in (-1.0, 1.0):
        w_pos = lec_center + (lec_rot_mat @ Vector((w_side * 0.245, -0.015, 0.04)))
        add_box_part(
            bm_lec,
            0.055,
            0.28,
            0.88,
            w_pos,
            mat_idx=3,
            rot_euler=(lec_tilt_x, w_side * math.radians(-6.0), lec_rot_z),
        )
        w_trim_pos = lec_center + (lec_rot_mat @ Vector((w_side * 0.275, -0.02, 0.05)))
        add_box_part(
            bm_lec,
            0.016,
            0.22,
            0.84,
            w_trim_pos,
            mat_idx=1,
            rot_euler=(lec_tilt_x, w_side * math.radians(-6.0), lec_rot_z),
        )
    # Vertical champagne-gold fluted front inlays + sculpted V-shaped GDSC chevron crest on podium front face
    for fx_off, f_z, f_h in [(-0.14, -0.04, 0.74), (0.0, -0.18, 0.44), (0.14, -0.04, 0.74)]:
        flute_pos = lec_center + (lec_rot_mat @ Vector((fx_off, -0.126, f_z)))
        add_box_part(bm_lec, 0.020, 0.020, f_h, flute_pos, mat_idx=1, rot_euler=(lec_tilt_x, 0, lec_rot_z))
    for chev_side in (-1.0, 1.0):
        chev_euler = tuple((lec_rot_mat @ Matrix.Rotation(chev_side * math.radians(32.0), 4, "Y")).to_euler("XYZ"))
        chev_pos = lec_center + (lec_rot_mat @ Vector((chev_side * 0.048, -0.132, 0.20)))
        add_box_part(bm_lec, 0.12, 0.020, 0.026, chev_pos, mat_idx=1, rot_euler=chev_euler)
    # Dark obsidian slate reading desk top with recessed brushed-gold edge bezel + twin gooseneck microphones
    desk_euler = (math.radians(16.0), 0, math.radians(-12.0))
    desk_rot = Matrix.Rotation(desk_euler[2], 4, "Z") @ Matrix.Rotation(desk_euler[0], 4, "X")
    add_box_part(bm_lec, 0.68, 0.46, 0.028, Vector((lx, ly, 1.015)), mat_idx=1, rot_euler=desk_euler)
    add_box_part(bm_lec, 0.63, 0.42, 0.024, Vector((lx, ly, 1.032)), mat_idx=0, rot_euler=desk_euler)
    add_box_part(bm_lec, 0.48, 0.014, 0.012, Vector((lx, ly - 0.14, 1.06)), mat_idx=1, rot_euler=desk_euler)
    for mic_side in (-1.0, 1.0):
        mic_base = Vector((lx, ly, 1.04)) + (desk_rot @ Vector((mic_side * 0.21, 0.14, 0.02)))
        add_cyl_part(bm_lec, 0.018, 0.015, 0.03, 12, mic_base, mat_idx=1, rot_euler=desk_euler)
        add_cyl_part(bm_lec, 0.007, 0.006, 0.14, 10, mic_base + Vector((0, -0.02, 0.07)), mat_idx=0, rot_euler=(math.radians(-22.0), 0, lec_rot_z))
        add_cyl_part(bm_lec, 0.011, 0.008, 0.032, 12, mic_base + Vector((0, -0.045, 0.135)), mat_idx=1, rot_euler=(math.radians(-42.0), 0, lec_rot_z))
    finalize_bmesh_object(bm_lec, "SM_GDSC_Lectern", [m_slate, m_gold, m_alabaster, m_smoked_bronze], bevel_width=0.005)

    # 3. SM_Hologram_Projector_Ring (Floor Emitter Well w/ 6 Bus-Bars + 4 Astrolabe Constellation Gimbal Rings)
    bm_ring = bmesh.new()
    add_ring_part(bm_ring, 0.78, 0.028, 0.020, 48, Vector((0.15, 0.0, 0.012)), mat_idx=0)
    add_ring_part(bm_ring, 0.72, 0.020, 0.026, 48, Vector((0.15, 0.0, 0.018)), mat_idx=1)
    add_ring_part(bm_ring, 0.66, 0.014, 0.028, 48, Vector((0.15, 0.0, 0.022)), mat_idx=3)
    add_cyl_part(bm_ring, 0.28, 0.22, 0.032, 24, Vector((0.15, 0.0, 0.018)), mat_idx=0)
    add_ring_part(bm_ring, 0.26, 0.012, 0.036, 24, Vector((0.15, 0.0, 0.020)), mat_idx=1)
    for sp_i in range(6):
        sp_ang = (sp_i / 6.0) * math.pi * 2.0
        add_box_part(
            bm_ring,
            0.44,
            0.020,
            0.016,
            Vector((0.15 + math.cos(sp_ang) * 0.48, math.sin(sp_ang) * 0.48, 0.020)),
            mat_idx=1,
            rot_euler=(0, 0, sp_ang),
        )
    constellation_center = Vector((0.15, 0.85, 1.82))
    add_ring_part(bm_ring, 1.44, 0.016, 0.020, 64, constellation_center, mat_idx=1, rot_euler=(math.radians(52.0), math.radians(-10.0), 0))
    add_ring_part(bm_ring, 1.28, 0.015, 0.018, 64, constellation_center, mat_idx=1, rot_euler=(math.radians(68.0), math.radians(16.0), 0))
    add_ring_part(bm_ring, 1.12, 0.013, 0.016, 64, constellation_center, mat_idx=3, rot_euler=(math.radians(74.0), math.radians(-22.0), math.radians(24.0)))
    add_ring_part(bm_ring, 0.96, 0.012, 0.015, 56, constellation_center, mat_idx=1, rot_euler=(math.radians(84.0), math.radians(32.0), math.radians(-18.0)))
    stud_rot = Matrix.Rotation(math.radians(-10.0), 4, "Y") @ Matrix.Rotation(math.radians(52.0), 4, "X")
    for st_i in range(8):
        st_ang = (st_i / 8.0) * math.pi * 2.0
        st_pos = constellation_center + (stud_rot @ Vector((math.cos(st_ang) * 1.44, math.sin(st_ang) * 1.44, 0.0)))
        add_cyl_part(bm_ring, 0.022, 0.016, 0.036, 8, st_pos, mat_idx=1)
    finalize_bmesh_object(bm_ring, "SM_Hologram_Projector_Ring", [m_slate, m_gold, m_alabaster, m_smoked_bronze], bevel_width=0.003)

    return export_glb("act3_crucible.glb")


# ==============================================================================
# ACT 4: THE ALPINE SUMMIT (Swiss Gneiss Stone, Alpenglow Gold & Hilti Crimson)
# ==============================================================================
def build_act4_summit():
    clear_scene()
    m_gneiss = make_pbr_mat("M_Alpine_Gneiss_Stone", (0.050, 0.058, 0.075, 1.0), metallic=0.14, roughness=0.74)
    m_snow = make_pbr_mat("M_Alpine_Snow_Marble", (0.74, 0.76, 0.80, 1.0), metallic=0.08, roughness=0.36, emission_color=(0.65, 0.72, 0.85, 1.0), emission_strength=0.06)
    m_gold = make_pbr_mat("M_24K_Hilti_Gold", (0.80, 0.63, 0.28, 1.0), metallic=0.90, roughness=0.24, emission_color=(0.70, 0.48, 0.12, 1.0), emission_strength=0.10)
    m_crimson = make_pbr_mat("M_Hilti_Crimson", (0.72, 0.12, 0.14, 1.0), metallic=0.35, roughness=0.30, emission_color=(0.65, 0.08, 0.10, 1.0), emission_strength=0.25)

    # 1. SM_Island_Act4: Dark Obsidian Topographic Plinth & Sleek Bronze Curb
    bm = bmesh.new()
    add_cyl_part(bm, 5.55, 5.35, 0.18, 64, Vector((0.65, 0.25, -0.20)), mat_idx=0)
    add_cyl_part(bm, 5.05, 5.00, 0.04, 64, Vector((0.65, 0.25, -0.09)), mat_idx=0)
    add_cyl_part(bm, 2.85, 2.70, 0.18, 64, Vector((0.85, 0.0, -0.09)), mat_idx=0)
    add_cyl_part(bm, 2.15, 2.05, 0.06, 48, Vector((0.65, 0.15, 0.03)), mat_idx=0)
    add_cyl_part(bm, 1.35, 1.28, 0.06, 48, Vector((0.45, 0.25, 0.09)), mat_idx=0)
    add_ring_part(bm, 4.82, 0.018, 0.014, 64, Vector((0.65, 0.25, -0.068)), mat_idx=2)
    add_ring_part(bm, 3.65, 0.014, 0.012, 64, Vector((0.65, 0.25, -0.068)), mat_idx=2)
    add_ring_part(bm, 2.62, 0.012, 0.012, 64, Vector((0.85, 0.0, 0.002)), mat_idx=2)
    add_ring_part(bm, 2.02, 0.010, 0.010, 48, Vector((0.65, 0.15, 0.062)), mat_idx=2)
    add_ring_part(bm, 1.26, 0.010, 0.010, 48, Vector((0.45, 0.25, 0.122)), mat_idx=2)
    # Sleek double-rail 0.42m dark stone & museum-bronze perimeter curb
    add_ring_part(bm, 4.92, 0.020, 0.022, 64, Vector((0.65, 0.25, 0.34)), mat_idx=2, arc_angle=math.pi * 1.12, rot_euler=(0, 0, -math.pi * 0.06))
    add_ring_part(bm, 4.92, 0.012, 0.014, 64, Vector((0.65, 0.25, 0.20)), mat_idx=2, arc_angle=math.pi * 1.12, rot_euler=(0, 0, -math.pi * 0.06))
    for st_i in range(13):
        ang_st = math.radians(-8.0 + (st_i / 12.0) * 196.0)
        st_x = 0.65 + math.cos(ang_st) * 4.92
        st_y = 0.25 + math.sin(ang_st) * 4.92
        add_box_part(bm, 0.045, 0.045, 0.42, Vector((st_x, st_y, 0.12)), mat_idx=0, rot_euler=(0, 0, ang_st + math.pi / 2))
    finalize_bmesh_object(bm, "SM_Island_Act4", [m_gneiss, m_snow, m_gold], bevel_width=0.006)

    # 2. SM_Mount_Pilatus_Massif (Wide Panoramic 9-Peak Sculpted Swiss Alpine Mountain Range w/ Central Sunrise Saddle at X = -0.35)
    # Strictly preserves 2 materials (M_Alpine_Gneiss_Stone & M_Alpine_Snow_Marble), snow_min > 0.45m, crest > 1.8m
    bm_mtn = bmesh.new()
    alpine_peaks = [
        # Far-left Western Glacier Massif
        (Vector((-3.60, 2.40, 0.04)), 1.55, 0.92, 2.18, (0.24, 0.12), math.radians(22.0), 0.58, 0.3),
        # Left Oberhaupt Interlocking Ridge
        (Vector((-2.35, 2.35, 0.04)), 1.52, 0.90, 2.46, (0.20, 0.08), math.radians(15.0), 0.54, 1.1),
        # Left Esel Ridge Spire (parted left to open the central X=-0.35 sunrise saddle)
        (Vector((-1.32, 2.55, 0.06)), 1.48, 0.92, 2.66, (0.12, 0.06), math.radians(10.0), 0.50, 2.0),
        # Foreground Left Spur (dark gneiss granite framing Pin 01 Schaan HQ Pitch Console cleanly)
        (Vector((-1.58, 1.48, 0.06)), 0.84, 0.50, 1.16, (0.14, 0.06), math.radians(22.0), 0.68, 0.7),
        # Central Tomlishorn Dominant Broad Swiss Massif (shifted right of saddle X=-0.35, 2.98m crest)
        (Vector((0.52, 2.82, 0.06)), 1.82, 1.08, 2.98, (0.10, -0.05), math.radians(-6.0), 0.48, 3.1),
        # Mid-Right Kulm Summit Crest
        (Vector((1.65, 2.52, 0.06)), 1.65, 0.96, 2.62, (-0.16, 0.06), math.radians(-14.0), 0.52, 4.4),
        # Foreground Right Spur
        (Vector((1.65, 1.36, 0.06)), 0.86, 0.50, 1.16, (-0.14, 0.05), math.radians(-26.0), 0.60, 5.2),
        # Right Matthorn Alpine Massif
        (Vector((2.78, 2.32, 0.04)), 1.60, 0.94, 2.36, (-0.22, 0.08), math.radians(-20.0), 0.56, 6.1),
        # Far-right East Ridge Buttress
        (Vector((3.88, 2.40, 0.04)), 1.58, 0.92, 2.05, (-0.26, 0.10), math.radians(-30.0), 0.58, 7.3),
    ]
    for p_center, rx, ry, h, crest_off, r_ang, s_ratio, p_seed in alpine_peaks:
        add_alpine_peak(
            bm_mtn,
            base_center=p_center,
            rx=rx,
            ry=ry,
            height=h,
            crest_offset=crest_off,
            ridge_angle=r_ang,
            snow_ratio=s_ratio,
            seed=p_seed,
            rock_mat_idx=0,
            snow_mat_idx=1,
        )
    finalize_bmesh_object(bm_mtn, "SM_Mount_Pilatus_Massif", [m_gneiss, m_snow, m_gold], bevel_width=0.005, smooth=False)

    # 3. Prop_Beacon_Schaan (Sculpted Hilti Schaan HQ Executive Pitch Console at X = -0.95, Y = -0.35 -> Three Z = +0.35)
    bm_sch = bmesh.new()
    sx, sy = -0.95, -0.35
    sch_yaw = math.radians(16.0)
    sch_yaw_rot = Matrix.Rotation(sch_yaw, 4, "Z")
    add_cyl_part(bm_sch, 0.30, 0.25, 0.08, 8, Vector((sx, sy, 0.04)), mat_idx=0, rot_euler=(0, 0, sch_yaw))
    add_cyl_part(bm_sch, 0.24, 0.22, 0.032, 8, Vector((sx, sy, 0.095)), mat_idx=2, rot_euler=(0, 0, sch_yaw))
    add_cyl_part(bm_sch, 0.145, 0.105, 0.78, 8, Vector((sx, sy, 0.50)), mat_idx=0, rot_euler=(0, 0, sch_yaw))
    for w_side in (-1.0, 1.0):
        wing_pos = Vector((sx, sy, 0.52)) + (sch_yaw_rot @ Vector((w_side * 0.145, 0.0, 0.0)))
        add_box_part(bm_sch, 0.045, 0.16, 0.62, wing_pos, mat_idx=3, rot_euler=(0, w_side * math.radians(-8.0), sch_yaw))
        add_box_part(bm_sch, 0.016, 0.14, 0.58, wing_pos + (sch_yaw_rot @ Vector((w_side * 0.024, 0.0, 0.0))), mat_idx=2, rot_euler=(0, w_side * math.radians(-8.0), sch_yaw))
    add_box_part(bm_sch, 0.18, 0.03, 0.56, Vector((sx, sy, 0.52)) + (sch_yaw_rot @ Vector((0, -0.09, 0))), mat_idx=3, rot_euler=(0, 0, sch_yaw))
    add_cyl_part(bm_sch, 0.135, 0.135, 0.035, 8, Vector((sx, sy, 0.895)), mat_idx=2, rot_euler=(0, 0, sch_yaw))
    # Angled brushed-gold & crimson executive pitch display deck at Z = 0.94m
    deck_euler = (math.radians(20.0), 0.0, sch_yaw)
    add_box_part(bm_sch, 0.44, 0.30, 0.026, Vector((sx, sy, 0.935)), mat_idx=2, rot_euler=deck_euler)
    add_box_part(bm_sch, 0.39, 0.25, 0.018, Vector((sx, sy, 0.948)), mat_idx=0, rot_euler=deck_euler)
    add_box_part(bm_sch, 0.34, 0.04, 0.014, Vector((sx, sy, 0.952)), mat_idx=3, rot_euler=deck_euler)
    finalize_bmesh_object(bm_sch, "Prop_Beacon_Schaan", [m_gneiss, m_snow, m_gold, m_crimson], bevel_width=0.005)

    # 4. Prop_Trophy_Hilti24k & Plinth (Multi-Tiered 24K Championship Cup w/ Wing Handles, Globe Crown & Heraldic Plaques)
    bm_tr = bmesh.new()
    tx, ty = 0.25, 0.0
    add_cyl_part(bm_tr, 0.38, 0.32, 0.95, 8, Vector((tx, ty, 0.475)), mat_idx=0)
    for pil_ang_deg in (45.0, 135.0, 225.0, 315.0):
        pa = math.radians(pil_ang_deg)
        add_box_part(
            bm_tr,
            0.042,
            0.042,
            0.90,
            Vector((tx + math.cos(pa) * 0.335, ty + math.sin(pa) * 0.335, 0.47)),
            mat_idx=2,
            rot_euler=(0.0, 0.0, pa),
        )
    add_ring_part(bm_tr, 0.355, 0.014, 0.026, 8, Vector((tx, ty, 0.48)), mat_idx=2)
    # Hilti-crimson heraldic plaque inset inside 24K gold front/side medallions
    add_box_part(bm_tr, 0.28, 0.032, 0.18, Vector((tx, ty - 0.318, 0.66)), mat_idx=2)
    add_box_part(bm_tr, 0.22, 0.038, 0.13, Vector((tx, ty - 0.322, 0.66)), mat_idx=3)
    add_ring_part(bm_tr, 0.33, 0.012, 0.025, 8, Vector((tx, ty, 0.96)), mat_idx=2)
    add_cyl_part(bm_tr, 0.18, 0.15, 0.08, 24, Vector((tx, ty, 1.01)), mat_idx=2)
    add_cyl_part(bm_tr, 0.045, 0.065, 0.22, 24, Vector((tx, ty, 1.16)), mat_idx=2)
    add_cyl_part(bm_tr, 0.08, 0.20, 0.34, 32, Vector((tx, ty, 1.42)), mat_idx=2)
    add_ring_part(bm_tr, 0.215, 0.016, 0.022, 32, Vector((tx, ty, 1.56)), mat_idx=2)
    # Twin swept wing handles cradling championship chalice
    for h_side in (-1.0, 1.0):
        add_ring_part(
            bm_tr,
            0.145,
            0.014,
            0.022,
            24,
            Vector((tx + h_side * 0.185, ty, 1.41)),
            mat_idx=2,
            arc_angle=math.pi * 1.15,
            rot_euler=(math.pi / 2, 0.0, math.pi * 0.925 if h_side > 0 else -math.pi * 0.075),
        )
    # Faceted 24K Gold World Globe & Laurel Crown (dynamic orbital rings are driven cleanly by TrophyVictoryCrown)
    globe_res = bmesh.ops.create_icosphere(bm_tr, subdivisions=2, radius=0.078)
    g_verts = globe_res["verts"]
    bmesh.ops.transform(bm_tr, matrix=Matrix.Translation((tx, ty, 1.60)), verts=g_verts)
    g_set = set(g_verts)
    for f in bm_tr.faces:
        if all(v in g_set for v in f.verts):
            f.material_index = 2
    finalize_bmesh_object(bm_tr, "Prop_Trophy_Hilti24k", [m_gneiss, m_snow, m_gold, m_crimson], bevel_width=0.004)

    # 5. Prop_Star_PressFrame (Sculpted Gneiss & Brass Museum Exhibition Vitrine Plinth, strictly pressMaxY <= 1.65)
    bm_pr = bmesh.new()
    px, py = 2.35, -0.25
    yaw = math.radians(-16.0)
    ca_y, sa_y = math.cos(yaw), math.sin(yaw)
    add_box_part(bm_pr, 0.58, 0.42, 0.08, Vector((px, py, 0.04)), mat_idx=0, rot_euler=(0, 0, yaw))
    add_box_part(bm_pr, 0.52, 0.36, 0.025, Vector((px, py, 0.092)), mat_idx=2, rot_euler=(0, 0, yaw))
    add_box_part(bm_pr, 0.22, 0.16, 0.84, Vector((px, py, 0.52)), mat_idx=0, rot_euler=(0, 0, yaw))
    add_box_part(bm_pr, 0.025, 0.175, 0.82, Vector((px - 0.115 * ca_y, py - 0.115 * sa_y, 0.52)), mat_idx=2, rot_euler=(0, 0, yaw))
    add_box_part(bm_pr, 0.025, 0.175, 0.82, Vector((px + 0.115 * ca_y, py + 0.115 * sa_y, 0.52)), mat_idx=2, rot_euler=(0, 0, yaw))
    add_box_part(bm_pr, 0.38, 0.22, 0.04, Vector((px, py, 0.90)), mat_idx=2, rot_euler=(0, 0, yaw))
    # Twin fluted 24K gold museum vitrine columns + stepped brass vitrine bezel around Z = 1.24 + gallery light hood at Z = 1.60 (<= 1.65)
    for col_s in (-0.34, 0.34):
        add_cyl_part(bm_pr, 0.024, 0.020, 0.68, 12, Vector((px + col_s * ca_y, py + col_s * sa_y, 1.25)), mat_idx=2, rot_euler=(0, 0, yaw))
    add_box_part(bm_pr, 0.62, 0.05, 0.64, Vector((px, py, 1.24)), mat_idx=0, rot_euler=(0, 0, yaw))
    add_box_part(bm_pr, 0.66, 0.036, 0.68, Vector((px, py + 0.01, 1.24)), mat_idx=2, rot_euler=(0, 0, yaw))
    # Cantilevered brass museum gallery picture-light hood (center Z = 1.59, top <= 1.62 <= 1.65 contract cap)
    add_box_part(bm_pr, 0.44, 0.11, 0.028, Vector((px + 0.06 * sa_y, py - 0.06 * ca_y, 1.595)), mat_idx=2, rot_euler=(0, 0, yaw))
    finalize_bmesh_object(bm_pr, "Prop_Star_PressFrame", [m_gneiss, m_snow, m_gold], bevel_width=0.005)

    return export_glb("act4_summit.glb")


# ==============================================================================
# ACT 5: THE FRONTIER AI LAB (Anodized Graphite, CNC Aluminum & Intl Orange)
# ==============================================================================
def build_act5_frontier():
    clear_scene()
    m_graphite = make_pbr_mat("M_Anodized_Graphite", (0.08, 0.09, 0.11, 1.0), metallic=0.60, roughness=0.40)
    m_alu = make_pbr_mat("M_CNC_Brushed_Aluminum", (0.28, 0.27, 0.25, 1.0), metallic=0.82, roughness=0.28)
    m_orange = make_pbr_mat("M_International_Orange", (0.76, 0.48, 0.24, 1.0), metallic=0.45, roughness=0.24, emission_color=(0.95, 0.52, 0.16, 1.0), emission_strength=0.68)
    m_glass = make_pbr_mat("M_Lab_Quartz_Glass", (0.62, 0.68, 0.74, 1.0), metallic=0.15, roughness=0.14, coat_weight=1.0)

    # 1. SM_Island_Act5 (Monolithic Dark Obsidian & Brushed Titanium Steles — Zero Floating Bricks)
    bm = bmesh.new()
    add_cyl_part(bm, 5.65, 5.45, 0.18, 64, Vector((1.15, 0.0, -0.20)), mat_idx=0)
    add_cyl_part(bm, 2.75, 2.60, 0.18, 64, Vector((1.35, 0.0, -0.09)), mat_idx=0)
    add_ring_part(bm, 2.50, 0.014, 0.012, 64, Vector((1.35, 0.0, 0.002)), mat_idx=1)
    add_ring_part(bm, 1.65, 0.010, 0.010, 64, Vector((1.35, 0.0, 0.002)), mat_idx=2)
    add_ring_part(bm, 3.65, 0.016, 0.012, 64, Vector((1.15, 0.0, -0.105)), mat_idx=1)
    add_ring_part(bm, 4.95, 0.018, 0.014, 64, Vector((1.15, 0.0, -0.105)), mat_idx=2)
    # Low Curved AI Telemetry Console Arc behind Zachary (waist height Z = 0.0 .. 0.76m)
    add_ring_part(bm, 2.65, 0.24, 0.74, 48, Vector((1.15, 0.0, 0.28)), mat_idx=0, arc_angle=math.pi * 0.56, rot_euler=(0, 0, math.pi * 0.22))
    add_ring_part(bm, 2.65, 0.26, 0.03, 48, Vector((1.15, 0.0, 0.66)), mat_idx=1, arc_angle=math.pi * 0.56, rot_euler=(0, 0, math.pi * 0.22))
    add_ring_part(bm, 2.40, 0.018, 0.024, 48, Vector((1.15, 0.0, 0.60)), mat_idx=2, arc_angle=math.pi * 0.54, rot_euler=(0, 0, math.pi * 0.23))
    # Rear grounded stone-and-titanium plinth ring + 6 vertical monolithic compute steles rising cleanly from it
    add_ring_part(bm, 3.95, 0.34, 0.18, 48, Vector((1.15, 0.0, -0.02)), mat_idx=0, arc_angle=math.pi * 0.84, rot_euler=(0, 0, math.pi * 0.08))
    for si, ang_deg in enumerate((22.0, 38.0, 54.0, 132.0, 148.0, 164.0)):
        ang_s = math.radians(ang_deg)
        r_s = 3.95
        sx = 1.15 + math.cos(ang_s) * r_s
        sy = math.sin(ang_s) * r_s
        rot_s = (0, 0, ang_s + math.pi / 2)
        h_s = 1.18 if si in (0, 5) else (1.30 if si in (1, 4) else 1.42)
        add_box_part(bm, 0.54, 0.22, h_s, Vector((sx, sy, h_s * 0.5 - 0.05)), mat_idx=0, rot_euler=rot_s)
        add_box_part(bm, 0.56, 0.24, 0.04, Vector((sx, sy, h_s - 0.04)), mat_idx=1, rot_euler=rot_s)
        add_box_part(bm, 0.028, 0.23, h_s * 0.78, Vector((sx, sy, h_s * 0.48)), mat_idx=2, rot_euler=rot_s)
    finalize_bmesh_object(bm, "SM_Island_Act5", [m_graphite, m_alu, m_orange], bevel_width=0.005)

    # 2. SM_Orbital_Lab_Rings (Engineering Worktable w/ Cooling Fins, Collared Guide Columns & Emitter Struts on Crown Halo)
    bm_lab = bmesh.new()
    kx, ky = 2.20, 0.0
    add_cyl_part(bm_lab, 0.62, 0.56, 0.76, 32, Vector((kx, ky, 0.38)), mat_idx=0)
    add_cyl_part(bm_lab, 0.66, 0.66, 0.04, 32, Vector((kx, ky, 0.78)), mat_idx=1)
    add_ring_part(bm_lab, 0.64, 0.012, 0.02, 32, Vector((kx, ky, 0.805)), mat_idx=2)
    add_ring_part(bm_lab, 0.61, 0.012, 0.022, 32, Vector((kx, ky, 0.42)), mat_idx=2)
    add_ring_part(bm_lab, 0.635, 0.014, 0.024, 32, Vector((kx, ky, 0.14)), mat_idx=1)
    for fin_i in range(8):
        f_ang = (fin_i / 8.0) * math.pi * 2.0
        add_box_part(
            bm_lab,
            0.09,
            0.026,
            0.66,
            Vector((kx + math.cos(f_ang) * 0.61, ky + math.sin(f_ang) * 0.61, 0.38)),
            mat_idx=1,
            rot_euler=(0.0, 0.0, f_ang),
        )
    for dx in (-0.26, 0.26):
        for dy in (-0.18, 0.18):
            add_cyl_part(bm_lab, 0.016, 0.016, 0.78, 16, Vector((kx + dx, ky + dy, 1.17)), mat_idx=1)
            for c_z in (0.92, 1.24, 1.56):
                add_cyl_part(bm_lab, 0.028, 0.028, 0.032, 12, Vector((kx + dx, ky + dy, c_z)), mat_idx=2)
    # Sleek lowered Halo crowning Prop_Core_Hireti_T1..3 at Z = 2.22m (r=0.76m keeps left rim x>=1.44m clear of avatar head)
    add_ring_part(bm_lab, 0.76, 0.026, 0.034, 6, Vector((kx, ky, 2.22)), mat_idx=1)
    add_ring_part(bm_lab, 0.68, 0.014, 0.018, 6, Vector((kx, ky, 2.18)), mat_idx=2)
    for st_i in range(6):
        s_ang = (st_i / 6.0) * math.pi * 2.0
        add_box_part(
            bm_lab,
            0.22,
            0.026,
            0.020,
            Vector((kx + math.cos(s_ang) * 0.66, ky + math.sin(s_ang) * 0.66, 2.20)),
            mat_idx=2,
            rot_euler=(0.0, 0.0, s_ang),
        )
    finalize_bmesh_object(bm_lab, "SM_Orbital_Lab_Rings", [m_graphite, m_alu, m_orange], bevel_width=0.005)

    # 3. 3 Distinct Explodable Architectural Hardware Strata at X = 2.20 (Prop_Core_Hireti_T1..3)
    # Tier 3 (03 Soft Space Super-App Core at Z = 0.92: Octagonal ISO-20022 Cryptographic Ledger Vault w/ 8 HSM Security Modules)
    bm_t3 = bmesh.new()
    add_cyl_part(bm_t3, 0.42, 0.40, 0.042, 8, Vector((0, 0, 0)), mat_idx=0)
    add_cyl_part(bm_t3, 0.36, 0.36, 0.026, 8, Vector((0, 0, 0.032)), mat_idx=1)
    add_cyl_part(bm_t3, 0.22, 0.19, 0.085, 8, Vector((0, 0, 0.072)), mat_idx=0)
    add_ring_part(bm_t3, 0.24, 0.022, 0.022, 16, Vector((0, 0, 0.095)), mat_idx=2)
    add_ring_part(bm_t3, 0.38, 0.014, 0.018, 8, Vector((0, 0, 0.024)), mat_idx=2)
    for hsm_i in range(8):
        h_ang = (hsm_i / 8.0) * math.pi * 2.0
        hx, hy = math.cos(h_ang) * 0.30, math.sin(h_ang) * 0.30
        add_box_part(bm_t3, 0.075, 0.055, 0.052, Vector((hx, hy, 0.068)), mat_idx=1, rot_euler=(0, 0, h_ang))
        add_box_part(bm_t3, 0.080, 0.058, 0.014, Vector((hx, hy, 0.098)), mat_idx=2, rot_euler=(0, 0, h_ang))
    obj_t3 = finalize_bmesh_object(bm_t3, "Prop_Core_Hireti_T3", [m_graphite, m_alu, m_orange], bevel_width=0.004)
    obj_t3.location = Vector((kx, ky, 0.92))

    # Tier 2 (02 ChronoAI Edge ONNX Core at Z = 1.24: Octagonal Silicon Tensor Processor Die w/ 12 CNC Heatsink Fins & 4 HBM Stacks)
    bm_t2 = bmesh.new()
    add_cyl_part(bm_t2, 0.36, 0.35, 0.034, 8, Vector((0, 0, 0)), mat_idx=1)
    add_box_part(bm_t2, 0.30, 0.24, 0.062, Vector((0, 0, 0.044)), mat_idx=0)
    add_box_part(bm_t2, 0.24, 0.18, 0.022, Vector((0, 0, 0.082)), mat_idx=2)
    add_ring_part(bm_t2, 0.31, 0.014, 0.016, 8, Vector((0, 0, 0.022)), mat_idx=2)
    for fin_x in (-0.21, -0.17, -0.13, -0.09, -0.05, -0.01, 0.03, 0.07, 0.11, 0.15, 0.19, 0.23):
        add_box_part(bm_t2, 0.014, 0.34, 0.052, Vector((fin_x - 0.01, 0, 0.056)), mat_idx=1)
    for hx_s in (-0.18, 0.18):
        for hy_s in (-0.14, 0.14):
            add_box_part(bm_t2, 0.065, 0.065, 0.048, Vector((hx_s, hy_s, 0.045)), mat_idx=2)
    obj_t2 = finalize_bmesh_object(bm_t2, "Prop_Core_Hireti_T2", [m_graphite, m_alu, m_orange], bevel_width=0.004)
    obj_t2.location = Vector((kx, ky, 1.24))

    # Tier 1 (01 Hireti AI Workforce Core at Z = 1.56: Quartz-Glass Multi-Agent Orchestration Wafer w/ 6 Radial Agent Node Domes)
    bm_t1 = bmesh.new()
    add_cyl_part(bm_t1, 0.34, 0.32, 0.028, 8, Vector((0, 0, 0)), mat_idx=3)
    add_ring_part(bm_t1, 0.32, 0.016, 0.020, 8, Vector((0, 0, 0.014)), mat_idx=1)
    # Central optical transceiver turret
    add_cyl_part(bm_t1, 0.11, 0.085, 0.072, 16, Vector((0, 0, 0.046)), mat_idx=0)
    add_cyl_part(bm_t1, 0.072, 0.052, 0.032, 16, Vector((0, 0, 0.092)), mat_idx=2)
    for ag_i in range(6):
        a_ang = (ag_i / 6.0) * math.pi * 2.0
        ax, ay = math.cos(a_ang) * 0.215, math.sin(a_ang) * 0.215
        add_box_part(bm_t1, 0.12, 0.016, 0.012, Vector((ax * 0.55, ay * 0.55, 0.022)), mat_idx=1, rot_euler=(0, 0, a_ang))
        add_cyl_part(bm_t1, 0.036, 0.026, 0.042, 12, Vector((ax, ay, 0.036)), mat_idx=2)
        add_cyl_part(bm_t1, 0.022, 0.014, 0.024, 12, Vector((ax, ay, 0.066)), mat_idx=3)
    obj_t1 = finalize_bmesh_object(bm_t1, "Prop_Core_Hireti_T1", [m_graphite, m_alu, m_orange, m_glass], bevel_width=0.004)
    obj_t1.location = Vector((kx, ky, 1.56))

    return export_glb("act5_frontier.glb")


# ==============================================================================
# ACT 6: THE HORIZON PORTAL (Serene Dawn Travertine, Obsidian & Champagne Pearl)
# ==============================================================================
def build_act6_horizon():
    clear_scene()
    m_travertine = make_pbr_mat("M_Dawn_Travertine", (0.24, 0.22, 0.20, 1.0), metallic=0.04, roughness=0.62)
    m_obsidian = make_pbr_mat("M_Obsidian_Reflection", (0.065, 0.070, 0.085, 1.0), metallic=0.25, roughness=0.30, coat_weight=0.22)
    m_champagne = make_pbr_mat("M_Champagne_Pearl_Bronze", (0.74, 0.62, 0.38, 1.0), metallic=0.88, roughness=0.24, emission_color=(0.74, 0.62, 0.38, 1.0), emission_strength=0.14)

    # 1. SM_Island_Act6 (Stepped Observatory Platform w/ Compass Deck Inlays & 8 Tapered Octagonal Obelisks)
    bm = bmesh.new()
    add_cyl_part(bm, 5.80, 5.60, 0.18, 64, Vector((0.35, 0.0, -0.20)), mat_idx=0)
    add_cyl_part(bm, 5.48, 5.45, 0.02, 64, Vector((0.35, 0.0, -0.095)), mat_idx=1)
    add_cyl_part(bm, 2.75, 2.60, 0.18, 64, Vector((0.35, 0.0, -0.09)), mat_idx=0)
    add_cyl_part(bm, 2.48, 2.48, 0.02, 64, Vector((0.35, 0.0, 0.005)), mat_idx=1)
    for r in [0.85, 1.45, 2.15, 2.46]:
        add_ring_part(bm, r, 0.012, 0.012, 64, Vector((0.35, 0.0, 0.017)), mat_idx=2)
    for r_out in [3.45, 4.45, 5.38]:
        add_ring_part(bm, r_out, 0.014, 0.012, 64, Vector((0.35, 0.0, -0.082)), mat_idx=2)
    # 12 radial compass degree spokes bridging the outer terrace deck
    for c_i in range(12):
        c_ang = (c_i / 12.0) * math.pi * 2.0
        add_box_part(
            bm,
            2.65,
            0.014,
            0.010,
            Vector((0.35 + math.cos(c_ang) * 4.00, math.sin(c_ang) * 4.00, -0.082)),
            mat_idx=2,
            rot_euler=(0, 0, c_ang),
        )
    # Stepped rear observatory parapet + 8 tapered octagonal astronomical obelisks with bronze meridian light fins
    add_ring_part(bm, 4.08, 0.34, 0.16, 56, Vector((0.35, 0.0, -0.02)), mat_idx=0, arc_angle=math.pi * 0.88, rot_euler=(0, 0, math.pi * 0.06))
    add_ring_part(bm, 4.08, 0.018, 0.016, 56, Vector((0.35, 0.0, 0.068)), mat_idx=2, arc_angle=math.pi * 0.88, rot_euler=(0, 0, math.pi * 0.06))
    for ob_i, ang_deg in enumerate((20.0, 38.0, 56.0, 74.0, 106.0, 124.0, 142.0, 160.0)):
        ang_p = math.radians(ang_deg)
        r_ob = 4.10
        px = 0.35 + math.cos(ang_p) * r_ob
        py = math.sin(ang_p) * r_ob
        rot_p = (0, 0, ang_p + math.pi / 2)
        h_scale = 1.0 + (0.14 if ob_i in (2, 3, 4, 5) else 0.0)
        shaft_h = 1.24 * h_scale
        # Tapered octagonal travertine plinth base + obsidian shaft + bronze collar + cantilevered capital + pyramidion
        add_cyl_part(bm, 0.28, 0.24, 0.16, 8, Vector((px, py, 0.05)), mat_idx=0, rot_euler=rot_p)
        add_cyl_part(bm, 0.21, 0.145, shaft_h, 8, Vector((px, py, 0.13 + shaft_h * 0.5)), mat_idx=1, rot_euler=rot_p)
        add_cyl_part(bm, 0.17, 0.17, 0.036, 8, Vector((px, py, 0.13 + shaft_h + 0.018)), mat_idx=2, rot_euler=rot_p)
        add_cyl_part(bm, 0.18, 0.21, 0.09, 8, Vector((px, py, 0.13 + shaft_h + 0.080)), mat_idx=0, rot_euler=rot_p)
        add_cyl_part(bm, 0.16, 0.015, 0.22, 8, Vector((px, py, 0.13 + shaft_h + 0.235)), mat_idx=2, rot_euler=rot_p)
        # Inner radial brushed-bronze meridian light fin facing the eclipse observatory center
        fx_in = 0.35 + math.cos(ang_p) * (r_ob - 0.185)
        fy_in = math.sin(ang_p) * (r_ob - 0.185)
        add_box_part(bm, 0.022, 0.06, shaft_h * 0.88, Vector((fx_in, fy_in, 0.15 + shaft_h * 0.48)), mat_idx=2, rot_euler=rot_p)
    finalize_bmesh_object(bm, "SM_Island_Act6", [m_travertine, m_obsidian, m_champagne], bevel_width=0.006)

    # 2. SM_Stargate_PortalArch (Sculpted Base Piers + Concentric Astrolabe Arches w/ 9 Radial Calibration Struts)
    bm_arch = bmesh.new()
    for px_s in (-1.98, 1.98):
        add_cyl_part(bm_arch, 0.30, 0.26, 0.16, 8, Vector((px_s, 0.45, 0.08)), mat_idx=0)
        add_cyl_part(bm_arch, 0.22, 0.18, 0.24, 8, Vector((px_s, 0.45, 0.24)), mat_idx=1)
        add_cyl_part(bm_arch, 0.24, 0.24, 0.035, 8, Vector((px_s, 0.45, 0.17)), mat_idx=2)
    # Primary Outer Arch (r = 2.42m, slender 0.042m)
    add_ring_part(bm_arch, 2.42, 0.042, 0.08, 64, Vector((0.0, 0.65, 0.24)), mat_idx=0, arc_angle=math.pi, rot_euler=(math.pi / 2, 0, 0))
    add_ring_part(bm_arch, 2.48, 0.018, 0.03, 64, Vector((0.0, 0.65, 0.24)), mat_idx=2, arc_angle=math.pi, rot_euler=(math.pi / 2, 0, 0))
    # Inner Arch (r = 1.98m, slender 0.042m)
    add_ring_part(bm_arch, 1.98, 0.042, 0.09, 64, Vector((0.0, 0.45, 0.24)), mat_idx=2, arc_angle=math.pi, rot_euler=(math.pi / 2, 0, 0))
    # Lens crystal orbital track
    add_ring_part(bm_arch, 1.92, 0.012, 0.016, 64, Vector((0.0, 0.35, 0.50)), mat_idx=2, arc_angle=math.pi * 1.06, rot_euler=(math.pi / 2, 0, -math.pi * 0.03))
    # 9 Radial Astrolabe Calibration Struts & Nodes bridging Inner (1.98m) and Outer (2.42m) Portal Arches
    for s_i in range(9):
        s_ang = math.radians(20.0 + (s_i / 8.0) * 140.0)
        ca_s, sa_s = math.cos(s_ang), math.sin(s_ang)
        add_box_part(
            bm_arch,
            0.40,
            0.035,
            0.024,
            Vector((ca_s * 2.20, 0.55, 0.24 + sa_s * 2.20)),
            mat_idx=2,
            rot_euler=(0.0, -s_ang, 0.0),
        )
        add_cyl_part(bm_arch, 0.032, 0.032, 0.052, 16, Vector((ca_s * 2.20, 0.55, 0.24 + sa_s * 2.20)), mat_idx=1, rot_euler=(math.pi / 2, 0, 0))
    finalize_bmesh_object(bm_arch, "SM_Stargate_PortalArch", [m_travertine, m_obsidian, m_champagne], bevel_width=0.006)

    # 3. SM_Portal_InnerRing (Concentric Dual Hairline Ring w/ 7 Meridian Tick Markers)
    bm_in = bmesh.new()
    add_ring_part(bm_in, 1.42, 0.022, 0.04, 64, Vector((0.0, 0.42, 0.30)), mat_idx=2, arc_angle=math.pi, rot_euler=(math.pi / 2, 0, 0))
    add_ring_part(bm_in, 1.32, 0.012, 0.024, 64, Vector((0.0, 0.42, 0.30)), mat_idx=2, arc_angle=math.pi, rot_euler=(math.pi / 2, 0, 0))
    for t_i in range(7):
        t_ang = math.radians(22.5 + t_i * 22.5)
        add_box_part(
            bm_in,
            0.12,
            0.032,
            0.016,
            Vector((math.cos(t_ang) * 1.37, 0.42, 0.30 + math.sin(t_ang) * 1.37)),
            mat_idx=2,
            rot_euler=(0.0, -t_ang, 0.0),
        )
    finalize_bmesh_object(bm_in, "SM_Portal_InnerRing", [m_travertine, m_obsidian, m_champagne], bevel_width=0.004)

    # 4. Prop_Beacon_Dispatch (Octagonal Obsidian Radar Command Pedestal w/ Corner Emitter Fins & Telemetry Wings)
    bm_con = bmesh.new()
    cx, cy = -0.25, -0.25
    con_euler = (math.radians(18.0), 0, math.radians(15.0))
    con_rot = Matrix.Rotation(con_euler[2], 4, "Z") @ Matrix.Rotation(con_euler[0], 4, "X")
    con_yaw_rot = Matrix.Rotation(con_euler[2], 4, "Z")
    add_cyl_part(bm_con, 0.28, 0.24, 0.08, 8, Vector((cx, cy, 0.04)), mat_idx=0, rot_euler=(0, 0, con_euler[2]))
    add_cyl_part(bm_con, 0.23, 0.20, 0.04, 8, Vector((cx, cy, 0.095)), mat_idx=2, rot_euler=(0, 0, con_euler[2]))
    add_cyl_part(bm_con, 0.14, 0.105, 0.84, 8, Vector((cx, cy, 0.50)), mat_idx=1, rot_euler=(0, 0, con_euler[2]))
    add_cyl_part(bm_con, 0.15, 0.15, 0.028, 8, Vector((cx, cy, 0.34)), mat_idx=2, rot_euler=(0, 0, con_euler[2]))
    add_cyl_part(bm_con, 0.13, 0.13, 0.028, 8, Vector((cx, cy, 0.72)), mat_idx=2, rot_euler=(0, 0, con_euler[2]))
    # Swept bronze side telemetry wings cradling column
    for wing_s in (-1.0, 1.0):
        w_pos = Vector((cx, cy, 0.66)) + (con_yaw_rot @ Vector((wing_s * 0.145, 0.0, 0.0)))
        add_box_part(bm_con, 0.055, 0.16, 0.38, w_pos, mat_idx=0, rot_euler=(0, wing_s * math.radians(-10.0), con_euler[2]))
        add_box_part(bm_con, 0.018, 0.14, 0.34, w_pos + (con_yaw_rot @ Vector((wing_s * 0.028, 0.0, 0.0))), mat_idx=2, rot_euler=(0, wing_s * math.radians(-10.0), con_euler[2]))
    con_top = Vector((cx, cy, 0.955))
    add_box_part(bm_con, 0.54, 0.40, 0.024, Vector((cx, cy, 0.932)), mat_idx=2, rot_euler=con_euler)
    add_box_part(bm_con, 0.49, 0.35, 0.030, con_top, mat_idx=1, rot_euler=con_euler)
    add_ring_part(
        bm_con,
        0.115,
        0.012,
        0.018,
        32,
        con_top + (con_rot @ Vector((0, 0, 0.018))),
        mat_idx=2,
        rot_euler=con_euler,
    )
    # 4 Angled Champagne-Bronze Corner Emitter Fins cradling the holographic radar dome
    for fin_ang_deg in (45.0, 135.0, 225.0, 315.0):
        fa = math.radians(fin_ang_deg)
        f_off = Vector((math.cos(fa) * 0.185, math.sin(fa) * 0.145, 0.048))
        fin_pos = con_top + (con_rot @ f_off)
        fin_euler = tuple((con_rot @ Matrix.Rotation(fa + math.pi / 2, 4, "Z") @ Matrix.Rotation(math.radians(-24.0), 4, "X")).to_euler("XYZ"))
        add_box_part(bm_con, 0.026, 0.036, 0.095, fin_pos, mat_idx=2, rot_euler=fin_euler)
    finalize_bmesh_object(bm_con, "Prop_Beacon_Dispatch", [m_travertine, m_obsidian, m_champagne], bevel_width=0.004)

    return export_glb("act6_horizon.glb")


def render_6act_contact_sheet():
    act_files = [
        ("act1_studio.glb", (0.022, 0.020, 0.018, 1.0), (0.0, -5.8, 1.85), (0.0, 0.0, 0.65)),
        ("act2_academy.glb", (0.022, 0.020, 0.018, 1.0), (0.35, -5.8, 1.85), (0.35, 0.0, 0.75)),
        ("act3_crucible.glb", (0.020, 0.022, 0.026, 1.0), (0.15, -5.8, 1.85), (0.15, 0.0, 0.75)),
        ("act4_summit.glb", (0.022, 0.022, 0.026, 1.0), (0.85, -6.2, 2.05), (0.65, 0.4, 0.85)),
        ("act5_frontier.glb", (0.022, 0.020, 0.024, 1.0), (1.35, -5.8, 1.85), (1.35, 0.2, 0.75)),
        ("act6_horizon.glb", (0.020, 0.022, 0.026, 1.0), (0.35, -6.0, 1.90), (0.15, 0.2, 0.80)),
    ]

    w, h = 640, 400
    rendered_paths = []
    for idx, (glb_name, bg_col, cam_pos, target_pos) in enumerate(act_files):
        clear_scene()
        glb_path = os.path.join(PROPS_DIR, glb_name)
        if not os.path.exists(glb_path):
            continue
        bpy.ops.import_scene.gltf(filepath=glb_path)

        scene = bpy.context.scene
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = w
        scene.render.resolution_y = h
        scene.render.film_transparent = False
        try:
            scene.view_settings.view_transform = "AgX"
            scene.view_settings.look = "AgX - Medium Contrast"
            scene.view_settings.exposure = -0.35
        except Exception:
            scene.view_settings.view_transform = "Filmic"
            scene.view_settings.exposure = -0.35

        world = bpy.data.worlds.new(f"World_{idx}")
        scene.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Color"].default_value = bg_col
            bg.inputs["Strength"].default_value = 0.85

        def add_light(name, energy, color, loc, rot_deg):
            ldata = bpy.data.lights.new(name=name, type="AREA")
            ldata.energy = energy
            ldata.color = color
            ldata.size = 4.5
            lobj = bpy.data.objects.new(name=name, object_data=ldata)
            lobj.location = Vector(loc)
            lobj.rotation_euler = tuple(math.radians(a) for a in rot_deg)
            bpy.context.collection.objects.link(lobj)

        add_light("Key", 180.0, (1.0, 0.95, 0.88), (3.2, -3.8, 3.8), (48.0, 0.0, 36.0))
        add_light("Fill", 90.0, (0.90, 0.92, 0.96), (-3.5, -2.8, 2.8), (55.0, 0.0, -42.0))
        add_light("Rim", 140.0, (1.0, 0.88, 0.72), (0.0, 4.2, 3.2), (-45.0, 0.0, 0.0))

        cam_data = bpy.data.cameras.new("QA_Cam")
        cam_data.lens = 36.0
        cam_obj = bpy.data.objects.new("QA_Cam", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        scene.camera = cam_obj
        cam_obj.location = Vector(cam_pos)
        direction = Vector(target_pos) - cam_obj.location
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

        out_p = os.path.join(SCREENSHOT_DIR, f"_tmp_act_{idx + 1}.png")
        scene.render.filepath = out_p
        bpy.ops.render.render(write_still=True)
        rendered_paths.append(out_p)

    if len(rendered_paths) == 6:
        sheet = bpy.data.images.new("Diorama6ActSheet", width=w * 3, height=h * 2, alpha=True)
        sheet_px = [0.0] * (w * 3 * h * 2 * 4)
        slots = [
            (0, h),
            (w, h),
            (w * 2, h),
            (0, 0),
            (w, 0),
            (w * 2, 0),
        ]
        for idx, p in enumerate(rendered_paths):
            img = bpy.data.images.load(p)
            src_px = list(img.pixels)
            qx, qy = slots[idx]
            for row in range(h):
                src_start = row * w * 4
                dst_start = ((qy + row) * (w * 3) + qx) * 4
                sheet_px[dst_start : dst_start + w * 4] = src_px[src_start : src_start + w * 4]
            bpy.data.images.remove(img)
        sheet.pixels[:] = sheet_px
        sheet_out = os.path.join(SCREENSHOT_DIR, "diorama_6act_contact_sheet.png")
        sheet.filepath_raw = sheet_out
        sheet.file_format = "PNG"
        sheet.save()
        print(f"[DioramaBuilder] Saved 6-Act contact sheet to {sheet_out}")
        if ARTIFACT_DIR and os.path.isdir(ARTIFACT_DIR):
            try:
                shutil.copy2(sheet_out, os.path.join(ARTIFACT_DIR, "diorama_6act_contact_sheet.png"))
            except OSError:
                pass


if __name__ == "__main__":
    build_act2_academy()
    build_act3_crucible()
    build_act4_summit()
    build_act5_frontier()
    build_act6_horizon()
    render_6act_contact_sheet()
    print("[DioramaBuilder] All Acts 2–6 GLB kits exported successfully.")
