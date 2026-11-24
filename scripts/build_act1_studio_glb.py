"""
Headless Blender 5.x Builder & 4-Angle Visual QA Renderer for Act 1:
`public/models/props/act1_studio.glb` (Warm Architectural Executive Atelier).

Art Direction:
- Warm Architectural Editorial (Matte Basalt Stone #141312, Warm Walnut #3A2418,
  Brushed Champagne Bronze #C8A97E, Matte Obsidian Anodized Aluminum #1C1C1E,
  Smoked Architectural Glass, and Warm 3000K Tungsten Gallery Lighting).
- Zero cheesy sci-fi neon cyan laser rings or cyberpunk clichés.
- Exports `act1_studio.glb` and immediately re-imports the exported `.glb` binary
  to render a 4-angle studio QA sheet (`Front`, `3/4 Isometric`, `Side Profile`, `Close-Up`).
"""

import bpy
import bmesh
import math
import os
import shutil
from mathutils import Vector, Matrix

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_GLB_DIR = os.path.join(PROJECT_ROOT, "public", "models", "props")
OUT_GLB_PATH = os.path.join(OUT_GLB_DIR, "act1_studio.glb")
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "screenshots")
ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", "")
OUT_SHEET_PATH = os.path.join(SCREENSHOT_DIR, "act1_studio_4angle_sheet.png")


def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam, do_unlink=True)
    for lgt in list(bpy.data.lights):
        bpy.data.lights.remove(lgt, do_unlink=True)


def make_pbr_material(
    name: str,
    base_color: tuple[float, float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.5,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        if emission_color is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0:
        mat.surface_render_method = 'BLENDED' if hasattr(mat, 'surface_render_method') else 'DITHERED'
    return mat


def add_cylinder_part(
    bm: bmesh.types.BMesh,
    radius_bottom: float,
    radius_top: float,
    depth: float,
    segments: int,
    matrix: Matrix,
    mat_index: int = 0,
) -> None:
    res = bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius_bottom,
        radius2=radius_top,
        depth=depth,
        matrix=matrix,
    )
    verts = res["verts"]
    vert_set = set(verts)
    for f in bm.faces:
        if all(v in vert_set for v in f.verts):
            f.material_index = mat_index


def add_box_part(
    bm: bmesh.types.BMesh,
    size_xyz: tuple[float, float, float],
    matrix: Matrix,
    mat_index: int = 0,
    bevel_width: float = 0.0,
    bevel_segments: int = 2,
) -> None:
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    scale_mat = Matrix.Diagonal((size_xyz[0], size_xyz[1], size_xyz[2], 1.0))
    bmesh.ops.transform(bm, matrix=matrix @ scale_mat, verts=verts)
    vert_set = set(verts)
    faces = [f for f in bm.faces if all(v in vert_set for v in f.verts)]
    edges = [e for e in bm.edges if all(v in vert_set for v in e.verts)]
    for f in faces:
        f.material_index = mat_index
    if bevel_width > 0.0 and edges:
        bev = bmesh.ops.bevel(
            bm,
            geom=edges,
            offset=bevel_width,
            offset_type='OFFSET',
            segments=bevel_segments,
            profile=0.5,
            affect='EDGES',
        )
        for f in bev.get("faces", []):
            f.material_index = mat_index


def add_torus_part(
    bm: bmesh.types.BMesh,
    major_radius: float,
    minor_radius: float,
    major_seg: int,
    minor_seg: int,
    matrix: Matrix,
    mat_index: int = 0,
    arc_radians: float = math.pi * 2.0,
) -> None:
    rings = []
    is_closed = abs(arc_radians - math.pi * 2.0) < 1e-4
    steps = major_seg if is_closed else (major_seg + 1)
    for i in range(steps):
        u = (i / major_seg) * arc_radians
        cu, su = math.cos(u), math.sin(u)
        ring = []
        for j in range(minor_seg):
            v = (j / minor_seg) * math.pi * 2.0
            cv, sv = math.cos(v), math.sin(v)
            r = major_radius + minor_radius * cv
            pt = matrix @ Vector((r * cu, r * su, minor_radius * sv))
            ring.append(bm.verts.new(pt))
        rings.append(ring)

    ring_count = len(rings)
    limit = ring_count if is_closed else (ring_count - 1)
    for i in range(limit):
        r1 = rings[i]
        r2 = rings[(i + 1) % ring_count]
        for j in range(minor_seg):
            jn = (j + 1) % minor_seg
            try:
                f = bm.faces.new((r1[j], r2[j], r2[jn], r1[jn]))
                f.material_index = mat_index
            except ValueError:
                pass


def finalize_mesh_object(
    name: str,
    bm: bmesh.types.BMesh,
    materials: list[bpy.types.Material],
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    for m in materials:
        mesh.materials.append(m)

    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(location)
    bpy.context.collection.objects.link(obj)
    return obj


def build_act1_studio() -> None:
    clear_scene()

    # Monolithic Museum Gallery Palette (Deep Obsidian Basalt, Espresso Walnut & Warm Travertine Stone)
    mat_basalt = make_pbr_material("Mat_Act1_WarmBasaltStone", (0.055, 0.050, 0.048, 1.0), metallic=0.15, roughness=0.62)
    mat_anodized = make_pbr_material("Mat_Act1_AnodizedGraphite", (0.10, 0.10, 0.11, 1.0), metallic=0.82, roughness=0.30)
    mat_walnut = make_pbr_material("Mat_Act1_ArchitecturalWalnut", (0.14, 0.09, 0.06, 1.0), metallic=0.03, roughness=0.58)
    mat_leather = make_pbr_material("Mat_Act1_EspressoLeather", (0.065, 0.055, 0.050, 1.0), metallic=0.04, roughness=0.46)
    mat_bronze = make_pbr_material("Mat_Act1_ChampagneBronze", (0.76, 0.62, 0.42, 1.0), metallic=0.90, roughness=0.24)
    mat_travertine = make_pbr_material("Mat_Act1_WarmTravertine", (0.26, 0.24, 0.21, 1.0), metallic=0.04, roughness=0.62)
    mat_smoked_glass = make_pbr_material("Mat_Act1_SmokedArchitecturalGlass", (0.085, 0.080, 0.078, 1.0), metallic=0.18, roughness=0.14)
    mat_warm_led = make_pbr_material(
        "Mat_Act1_WarmTungsten2700K",
        (1.0, 0.89, 0.72, 1.0),
        metallic=0.0,
        roughness=0.18,
        emission_color=(1.0, 0.88, 0.68, 1.0),
        emission_strength=1.4,
    )
    mat_screen_ui = make_pbr_material(
        "Mat_Act1_EditorialMonitorUI",
        (0.04, 0.055, 0.075, 1.0),
        metallic=0.18,
        roughness=0.32,
        emission_color=(0.12, 0.22, 0.32, 1.0),
        emission_strength=0.28,
    )

    # -------------------------------------------------------------------------
    # 1. SM_Island_Act1: Cantilevered Horizon Penthouse & Asymmetric Glass Pavilion
    #    Top floor strictly at Z = 0.000m, left cantilevered walnut & smoked-glass
    #    gallery wing + low-profile horizontal acoustic credenza + open right vista
    # -------------------------------------------------------------------------
    bm_island = bmesh.new()
    # Multi-tiered Travertine & Anodized-Carbon Floating Penthouse Deck (r = 5.65m)
    add_cylinder_part(bm_island, 5.65, 5.50, 0.18, 72, Matrix.Translation((0, 0, -0.22)), mat_index=1)
    add_cylinder_part(bm_island, 5.45, 5.40, 0.04, 72, Matrix.Translation((0, 0, -0.10)), mat_index=3)
    add_cylinder_part(bm_island, 2.76, 2.68, 0.17, 72, Matrix.Translation((0, 0, -0.135)), mat_index=1)
    add_cylinder_part(bm_island, 2.58, 2.52, 0.05, 72, Matrix.Translation((0, 0, -0.025)), mat_index=0)
    # Brushed champagne-bronze architectural floor inlay rings spanning inner & outer terraces
    for ring_r, ring_t, ring_z in [(1.56, 0.008, 0.001), (2.48, 0.012, -0.002), (3.65, 0.014, -0.078), (4.95, 0.016, -0.078)]:
        add_torus_part(bm_island, ring_r, ring_t, 72, 14, Matrix.Translation((0, 0, ring_z)), mat_index=4)

    # Sleek, continuous low-slung curved Museum Travertine & Fluted Walnut Gallery Parapet (ang = 24..156 deg, r = 3.65m)
    # Zero picket-fence balustrades or solar-panel walls; calm horizontal museum horizon framing
    for seg_i in range(24):
        frac_b = seg_i / 23.0
        ang_b = math.radians(24.0 + frac_b * 132.0)
        bx_b = math.cos(ang_b) * 3.65
        by_b = math.sin(ang_b) * 3.65
        rot_b = Matrix.Rotation(ang_b + math.pi * 0.5, 4, 'Z')
        add_box_part(bm_island, (0.34, 0.24, 0.60), Matrix.Translation((bx_b, by_b, 0.22)) @ rot_b, mat_index=3, bevel_width=0.008)
        add_box_part(bm_island, (0.34, 0.26, 0.05), Matrix.Translation((bx_b, by_b, 0.545)) @ rot_b, mat_index=2, bevel_width=0.005)
        add_box_part(bm_island, (0.33, 0.025, 0.022), Matrix.Translation((math.cos(ang_b) * 3.51, math.sin(ang_b) * 3.51, 0.62)) @ rot_b, mat_index=6)

    # Low-profile Sculpted Horizontal Walnut Credenza behind table/hero (Z = 0.0 .. 0.75m, zero floating bars above)
    for cred_i in range(12):
        frac_cr = cred_i / 11.0
        ang_cr = math.radians(52.0 + frac_cr * 78.0)
        cr_r = 2.42
        crx = math.cos(ang_cr) * cr_r
        cry = math.sin(ang_cr) * cr_r
        rot_cr = Matrix.Rotation(ang_cr + math.pi * 0.5, 4, 'Z')
        add_box_part(bm_island, (0.285, 0.24, 0.72), Matrix.Translation((crx, cry, 0.36)) @ rot_cr, mat_index=2, bevel_width=0.008)
        add_box_part(bm_island, (0.29, 0.26, 0.03), Matrix.Translation((crx, cry, 0.735)) @ rot_cr, mat_index=3, bevel_width=0.004)
        add_box_part(bm_island, (0.27, 0.02, 0.022), Matrix.Translation((math.cos(ang_cr) * (cr_r - 0.13), math.sin(ang_cr) * (cr_r - 0.13), 0.70)) @ rot_cr, mat_index=6)

    # Four quiet Monolithic Travertine & Bronze Museum Architectural Steles along rear left-to-center arc
    stele_heights = (1.42, 1.60, 1.78, 1.50)
    for stele_h, ang_deg in zip(stele_heights, (108.0, 126.0, 144.0, 162.0)):
        ang_w = math.radians(ang_deg)
        r_stele = 3.95
        wx = math.cos(ang_w) * r_stele
        wy = math.sin(ang_w) * r_stele
        rot_w = Matrix.Rotation(ang_w + math.pi * 0.5, 4, 'Z')
        add_box_part(bm_island, (0.56, 0.24, 0.14), Matrix.Translation((wx, wy, 0.02)) @ rot_w, mat_index=0, bevel_width=0.006)
        add_box_part(bm_island, (0.52, 0.18, stele_h), Matrix.Translation((wx, wy, stele_h * 0.5 + 0.04)) @ rot_w, mat_index=3, bevel_width=0.008)
        add_box_part(bm_island, (0.54, 0.025, stele_h + 0.02), Matrix.Translation((math.cos(ang_w) * (r_stele - 0.085), math.sin(ang_w) * (r_stele - 0.085), stele_h * 0.5 + 0.04)) @ rot_w, mat_index=4)
        add_box_part(bm_island, (0.38, 0.03, stele_h - 0.24), Matrix.Translation((math.cos(ang_w) * (r_stele - 0.095), math.sin(ang_w) * (r_stele - 0.095), stele_h * 0.5 + 0.08)) @ rot_w, mat_index=2)
        for l_idx in range(4):
            lz = 0.34 + l_idx * ((stele_h - 0.56) / 3.0)
            add_box_part(bm_island, (0.40, 0.036, 0.018), Matrix.Translation((math.cos(ang_w) * (r_stele - 0.10), math.sin(ang_w) * (r_stele - 0.10), lz)) @ rot_w, mat_index=4)

    finalize_mesh_object(
        "SM_Island_Act1",
        bm_island,
        [mat_basalt, mat_anodized, mat_walnut, mat_travertine, mat_bronze, mat_smoked_glass, mat_warm_led],
        location=(0.0, 0.0, 0.0),
    )

    # -------------------------------------------------------------------------
    # 2. SM_Executive_LoungeChair: Sculpted Eames-Style Walnut & Espresso Leather Chair
    #    Staged at (0.35, 0.65, 0.0) angled slightly toward the center
    # -------------------------------------------------------------------------
    bm_chair = bmesh.new()
    chair_yaw = Matrix.Rotation(math.radians(-18.0), 4, 'Z')
    add_cylinder_part(bm_chair, 0.042, 0.036, 0.34, 24, Matrix.Translation((0, 0, 0.19)), mat_index=2)
    for leg_i in range(5):
        ang = (leg_i / 5.0) * math.pi * 2.0
        leg_rot = Matrix.Rotation(ang, 4, 'Z') @ Matrix.Rotation(math.radians(78.0), 4, 'Y')
        leg_pos = Matrix.Translation((math.cos(ang) * 0.19, math.sin(ang) * 0.19, 0.065))
        add_box_part(bm_chair, (0.032, 0.026, 0.36), leg_pos @ leg_rot, mat_index=3, bevel_width=0.005)
        caster_pos = Matrix.Translation((math.cos(ang) * 0.35, math.sin(ang) * 0.35, 0.025))
        add_cylinder_part(bm_chair, 0.024, 0.024, 0.024, 16, caster_pos @ Matrix.Rotation(math.pi * 0.5, 4, 'X'), mat_index=2)

    # Molded walnut seat shell & beveled espresso leather cushion
    add_box_part(bm_chair, (0.64, 0.58, 0.055), chair_yaw @ Matrix.Translation((0, 0, 0.37)), mat_index=1, bevel_width=0.018, bevel_segments=3)
    add_box_part(bm_chair, (0.60, 0.54, 0.105), chair_yaw @ Matrix.Translation((0, -0.01, 0.43)), mat_index=0, bevel_width=0.032, bevel_segments=4)

    recline = Matrix.Rotation(math.radians(-14.0), 4, 'X')
    add_box_part(bm_chair, (0.62, 0.055, 0.44), chair_yaw @ Matrix.Translation((0, 0.27, 0.68)) @ recline, mat_index=1, bevel_width=0.016, bevel_segments=3)
    add_box_part(bm_chair, (0.58, 0.095, 0.40), chair_yaw @ Matrix.Translation((0, 0.22, 0.68)) @ recline, mat_index=0, bevel_width=0.028, bevel_segments=4)

    add_box_part(bm_chair, (0.52, 0.05, 0.24), chair_yaw @ Matrix.Translation((0, 0.34, 1.04)) @ recline, mat_index=1, bevel_width=0.015, bevel_segments=3)
    add_box_part(bm_chair, (0.48, 0.085, 0.21), chair_yaw @ Matrix.Translation((0, 0.29, 1.04)) @ recline, mat_index=0, bevel_width=0.024, bevel_segments=4)

    for side in (-1.0, 1.0):
        arm_pos = chair_yaw @ Matrix.Translation((side * 0.33, 0.02, 0.58))
        add_box_part(bm_chair, (0.075, 0.42, 0.055), arm_pos, mat_index=0, bevel_width=0.018, bevel_segments=3)
        strut_pos = chair_yaw @ Matrix.Translation((side * 0.32, 0.06, 0.47))
        add_box_part(bm_chair, (0.028, 0.055, 0.18), strut_pos, mat_index=3, bevel_width=0.005)

    finalize_mesh_object(
        "SM_Executive_LoungeChair",
        bm_chair,
        [mat_leather, mat_walnut, mat_anodized, mat_bronze],
        location=(0.35, 0.68, 0.0),
    )

    # -------------------------------------------------------------------------
    # 3. SM_Strategy_Table: Architectural Executive Desk & Studio Monitor
    #    Positioned on the left at (-1.12, -0.08, 0.0), angled slightly inward
    # -------------------------------------------------------------------------
    table_loc = (-1.12, -0.08, 0.0)
    desk_rot = Matrix.Rotation(math.radians(16.0), 4, 'Z')
    bm_table = bmesh.new()

    # Architectural anodized graphite slab legs with brushed champagne-bronze foot cuffs
    add_box_part(bm_table, (0.14, 0.58, 0.72), desk_rot @ Matrix.Translation((-0.56, 0.0, 0.36)), mat_index=1, bevel_width=0.012)
    add_box_part(bm_table, (0.15, 0.60, 0.04), desk_rot @ Matrix.Translation((-0.56, 0.0, 0.02)), mat_index=2, bevel_width=0.004)
    add_box_part(bm_table, (0.14, 0.58, 0.72), desk_rot @ Matrix.Translation((0.56, 0.0, 0.36)), mat_index=1, bevel_width=0.012)
    add_box_part(bm_table, (0.15, 0.60, 0.04), desk_rot @ Matrix.Translation((0.56, 0.0, 0.02)), mat_index=2, bevel_width=0.004)
    # Crossbeam stretcher in champagne bronze
    add_box_part(bm_table, (1.02, 0.05, 0.05), desk_rot @ Matrix.Translation((0.0, 0.06, 0.22)), mat_index=2, bevel_width=0.006)

    # Beveled architectural walnut desktop slab (1.42m x 0.74m, Z = 0.72 to 0.77)
    add_box_part(bm_table, (1.42, 0.74, 0.052), desk_rot @ Matrix.Translation((0.0, 0.0, 0.745)), mat_index=0, bevel_width=0.016, bevel_segments=3)
    # Inlaid matte leather desk blotter pad
    add_box_part(bm_table, (1.16, 0.52, 0.008), desk_rot @ Matrix.Translation((0.0, -0.02, 0.774)), mat_index=1, bevel_width=0.003)

    # Sleek architectural studio monitor on the rear-left of the desk (Dark OLED + Bronze UI bars)
    mon_pos = desk_rot @ Matrix.Translation((-0.34, 0.16, 0.775)) @ Matrix.Rotation(math.radians(-12.0), 4, 'Z')
    add_box_part(bm_table, (0.18, 0.14, 0.012), mon_pos @ Matrix.Translation((0, 0, 0.006)), mat_index=2, bevel_width=0.003)
    add_box_part(bm_table, (0.028, 0.028, 0.18), mon_pos @ Matrix.Translation((0, 0.03, 0.09)), mat_index=2, bevel_width=0.004)
    add_box_part(bm_table, (0.62, 0.024, 0.34), mon_pos @ Matrix.Translation((0, 0.0, 0.28)), mat_index=1, bevel_width=0.008)
    add_box_part(bm_table, (0.59, 0.006, 0.31), mon_pos @ Matrix.Translation((0, -0.012, 0.28)), mat_index=4)
    # Architectural UI telemetry sparklines, blueprint widgets & warm header bar on the OLED display face
    add_box_part(bm_table, (0.52, 0.004, 0.012), mon_pos @ Matrix.Translation((0.0, -0.016, 0.39)), mat_index=5)
    add_box_part(bm_table, (0.22, 0.004, 0.14), mon_pos @ Matrix.Translation((-0.14, -0.016, 0.28)), mat_index=2)
    add_box_part(bm_table, (0.03, 0.006, 0.05), mon_pos @ Matrix.Translation((-0.20, -0.018, 0.24)), mat_index=5)
    add_box_part(bm_table, (0.03, 0.006, 0.085), mon_pos @ Matrix.Translation((-0.14, -0.018, 0.258)), mat_index=5)
    add_box_part(bm_table, (0.03, 0.006, 0.11), mon_pos @ Matrix.Translation((-0.08, -0.018, 0.27)), mat_index=5)
    add_box_part(bm_table, (0.24, 0.004, 0.018), mon_pos @ Matrix.Translation((0.13, -0.016, 0.33)), mat_index=5)
    add_box_part(bm_table, (0.24, 0.004, 0.020), mon_pos @ Matrix.Translation((0.13, -0.016, 0.27)), mat_index=2)
    add_box_part(bm_table, (0.18, 0.004, 0.018), mon_pos @ Matrix.Translation((0.10, -0.016, 0.21)), mat_index=5)

    # Architectural model base plinth on the right side of the desk (supports Prop_Blueprint_Tier1..3)
    pad_pos = desk_rot @ Matrix.Translation((0.28, -0.02, 0.785))
    add_box_part(bm_table, (0.48, 0.38, 0.024), pad_pos, mat_index=3, bevel_width=0.006)
    add_box_part(bm_table, (0.44, 0.34, 0.008), pad_pos @ Matrix.Translation((0, 0, 0.014)), mat_index=2, bevel_width=0.002)

    finalize_mesh_object(
        "SM_Strategy_Table",
        bm_table,
        [mat_walnut, mat_anodized, mat_bronze, mat_travertine, mat_screen_ui, mat_warm_led],
        location=table_loc,
    )

    # -------------------------------------------------------------------------
    # 4. Prop_Blueprint_Tier1..3: 3 Physical Architectural Scale-Model Strata
    #    Precision smoked-glass, travertine & champagne-bronze architectural slabs
    #    sitting on the right side of SM_Strategy_Table (explodable vertically)
    # -------------------------------------------------------------------------
    model_offset = Vector(table_loc) + (desk_rot @ Vector((0.28, -0.02, 0.0)))

    # Tier 3 (Foundation Stratum: Travertine & Bronze Settlement Base)
    bm_t3 = bmesh.new()
    add_box_part(bm_t3, (0.38, 0.28, 0.024), desk_rot, mat_index=0, bevel_width=0.005)
    for p_x in (-0.14, 0.0, 0.14):
        for p_y in (-0.09, 0.09):
            add_cylinder_part(bm_t3, 0.012, 0.012, 0.045, 16, desk_rot @ Matrix.Translation((p_x, p_y, 0.025)), mat_index=1)
    finalize_mesh_object(
        "Prop_Blueprint_Tier3",
        bm_t3,
        [mat_travertine, mat_bronze],
        location=(model_offset.x, model_offset.y, 0.83),
    )

    # Tier 2 (Middle Stratum: Smoked Glass & Champagne Bronze Clearing Grid)
    bm_t2 = bmesh.new()
    add_box_part(bm_t2, (0.36, 0.26, 0.016), desk_rot, mat_index=0, bevel_width=0.004)
    add_box_part(bm_t2, (0.38, 0.014, 0.020), desk_rot @ Matrix.Translation((0, -0.13, 0)), mat_index=1)
    add_box_part(bm_t2, (0.38, 0.014, 0.020), desk_rot @ Matrix.Translation((0, 0.13, 0)), mat_index=1)
    add_box_part(bm_t2, (0.18, 0.14, 0.028), desk_rot @ Matrix.Translation((0, 0, 0.018)), mat_index=1, bevel_width=0.005)
    finalize_mesh_object(
        "Prop_Blueprint_Tier2",
        bm_t2,
        [mat_smoked_glass, mat_bronze],
        location=(model_offset.x, model_offset.y, 0.91),
    )

    # Tier 1 (Upper Canopy Stratum: Architectural Cantilever Roof & Warm Core)
    bm_t1 = bmesh.new()
    add_box_part(bm_t1, (0.40, 0.30, 0.018), desk_rot, mat_index=0, bevel_width=0.005)
    add_box_part(bm_t1, (0.24, 0.16, 0.036), desk_rot @ Matrix.Translation((0, 0, 0.022)), mat_index=1, bevel_width=0.006)
    add_cylinder_part(bm_t1, 0.038, 0.038, 0.025, 24, desk_rot @ Matrix.Translation((0, 0, 0.045)), mat_index=2)
    finalize_mesh_object(
        "Prop_Blueprint_Tier1",
        bm_t1,
        [mat_walnut, mat_bronze, mat_warm_led],
        location=(model_offset.x, model_offset.y, 0.99),
    )

    # -------------------------------------------------------------------------
    # 5. SM_Keynote_RingLight: Warm Architectural Atelier Floor Lamp
    #    Travertine base + brushed champagne-bronze stem + warm linen/alabaster shade
    # -------------------------------------------------------------------------
    bm_light = bmesh.new()
    # Heavy travertine cylinder base (Z = 0.0 to 0.18) with fluted champagne-bronze base collars
    add_cylinder_part(bm_light, 0.20, 0.18, 0.18, 36, Matrix.Translation((0, 0, 0.09)), mat_index=0)
    add_torus_part(bm_light, 0.202, 0.010, 48, 12, Matrix.Translation((0, 0, 0.02)), mat_index=1)
    add_torus_part(bm_light, 0.182, 0.009, 48, 12, Matrix.Translation((0, 0, 0.18)), mat_index=1)
    # Brushed bronze collar & slender vertical stem (Z = 0.18 to 1.62)
    add_cylinder_part(bm_light, 0.035, 0.035, 0.04, 24, Matrix.Translation((0, 0, 0.20)), mat_index=1)
    add_cylinder_part(bm_light, 0.016, 0.014, 1.44, 24, Matrix.Translation((0, 0, 0.90)), mat_index=1)
    # Warm architectural linen/travertine drum shade, glowing alabaster diffuser band & 4 brushed-bronze vertical ribs
    add_cylinder_part(bm_light, 0.24, 0.16, 0.28, 48, Matrix.Translation((0, 0, 1.58)), mat_index=0)
    add_torus_part(bm_light, 0.16, 0.008, 48, 12, Matrix.Translation((0, 0, 1.72)), mat_index=1)
    add_torus_part(bm_light, 0.205, 0.012, 48, 12, Matrix.Translation((0, 0, 1.58)), mat_index=2)
    add_torus_part(bm_light, 0.24, 0.008, 48, 12, Matrix.Translation((0, 0, 1.44)), mat_index=1)
    shade_tilt = math.atan2(0.08, 0.28)
    for rib_i in range(4):
        rib_ang = math.radians(45.0 + rib_i * 90.0)
        rx = math.cos(rib_ang) * 0.203
        ry = math.sin(rib_ang) * 0.203
        rib_mat = Matrix.Translation((rx, ry, 1.58)) @ Matrix.Rotation(rib_ang, 4, 'Z') @ Matrix.Rotation(-shade_tilt, 4, 'Y')
        add_box_part(bm_light, (0.010, 0.014, 0.29), rib_mat, mat_index=1)
    add_cylinder_part(bm_light, 0.18, 0.12, 0.22, 36, Matrix.Translation((0, 0, 1.56)), mat_index=2)
    # Refined double-halo bronze chandelier suspended by 3 brushed-bronze cables above the atelier lounge
    halo_cx, halo_cy, halo_cz = -0.35, 0.35, 2.52
    add_torus_part(bm_light, 0.54, 0.018, 64, 14, Matrix.Translation((halo_cx, halo_cy, halo_cz)), mat_index=1)
    add_torus_part(bm_light, 0.49, 0.010, 64, 12, Matrix.Translation((halo_cx, halo_cy, halo_cz - 0.02)), mat_index=2)
    cable_top_z = 3.86
    cable_h = cable_top_z - halo_cz
    cable_mid_z = halo_cz + cable_h * 0.5
    for c_idx in range(3):
        c_ang = math.radians(c_idx * 120.0 + 18.0)
        cx = halo_cx + math.cos(c_ang) * 0.53
        cy = halo_cy + math.sin(c_ang) * 0.53
        add_cylinder_part(bm_light, 0.004, 0.004, cable_h, 8, Matrix.Translation((cx, cy, cable_mid_z)), mat_index=1)
    add_cylinder_part(bm_light, 0.075, 0.065, 0.04, 24, Matrix.Translation((halo_cx, halo_cy, cable_top_z)), mat_index=1)

    finalize_mesh_object(
        "SM_Keynote_RingLight",
        bm_light,
        [mat_travertine, mat_bronze, mat_warm_led],
        location=(1.22, 0.58, 0.0),
    )


def export_act1_glb() -> None:
    os.makedirs(OUT_GLB_DIR, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUT_GLB_PATH,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True,
        export_materials='EXPORT',
    )
    size_kb = os.path.getsize(OUT_GLB_PATH) / 1024.0
    print(f"[Act1Builder] Exported {OUT_GLB_PATH} ({size_kb:.1f} KB)")


def render_4angle_qa_sheet() -> None:
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=OUT_GLB_PATH)

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.film_transparent = False

    # Warm Architectural Atelier World Background
    world = bpy.data.worlds.new("QA_Studio_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.032, 0.028, 0.025, 1.0)
        bg.inputs["Strength"].default_value = 1.0

    def add_light(name: str, ltype: str, energy: float, color: tuple[float, float, float], loc: tuple[float, float, float], rot_deg: tuple[float, float, float]) -> None:
        ldata = bpy.data.lights.new(name=name, type=ltype)
        ldata.energy = energy
        ldata.color = color
        if ltype == 'AREA':
            ldata.size = 4.0
        lobj = bpy.data.objects.new(name=name, object_data=ldata)
        lobj.location = Vector(loc)
        lobj.rotation_euler = (math.radians(rot_deg[0]), math.radians(rot_deg[1]), math.radians(rot_deg[2]))
        bpy.context.collection.objects.link(lobj)

    add_light("KeyLight", "AREA", 420.0, (1.0, 0.94, 0.86), (3.0, -3.8, 3.8), (48.0, 0.0, 36.0))
    add_light("FillLight", "AREA", 240.0, (0.92, 0.90, 0.88), (-3.5, -2.8, 2.8), (55.0, 0.0, -42.0))
    add_light("RimLight", "AREA", 320.0, (1.0, 0.88, 0.72), (0.0, 4.2, 3.2), (-45.0, 0.0, 0.0))

    cam_data = bpy.data.cameras.new("QA_Camera")
    cam_data.lens = 38.0
    cam_obj = bpy.data.objects.new("QA_Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    views = [
        ("view1_front.png", (0.0, -6.0, 1.65), (0.0, 0.0, 0.65), 38.0),
        ("view2_iso.png", (4.5, -4.6, 3.00), (-0.10, 0.1, 0.55), 36.0),
        ("view3_side.png", (-5.6, -1.4, 1.55), (-0.25, 0.1, 0.60), 38.0),
        ("view4_closeup.png", (-2.35, -2.35, 1.38), (-0.85, 0.0, 0.82), 45.0),
    ]

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    rendered_paths = []
    for fname, cam_pos, target_pos, lens in views:
        cam_data.lens = lens
        cam_obj.location = Vector(cam_pos)
        direction = Vector(target_pos) - cam_obj.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()

        out_path = os.path.join(SCREENSHOT_DIR, fname)
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        rendered_paths.append(out_path)

    w, h = 960, 540
    sheet = bpy.data.images.new("Act1_ContactSheet", width=w * 2, height=h * 2, alpha=True)
    sheet_pixels = [0.0] * (w * 2 * h * 2 * 4)

    quadrants = [
        (0, h),
        (w, h),
        (0, 0),
        (w, 0),
    ]

    for idx, img_path in enumerate(rendered_paths):
        img = bpy.data.images.load(img_path)
        src_px = list(img.pixels)
        qx, qy = quadrants[idx]
        for row in range(h):
            src_start = row * w * 4
            src_end = src_start + w * 4
            dst_row = qy + row
            dst_start = (dst_row * (w * 2) + qx) * 4
            sheet_pixels[dst_start : dst_start + w * 4] = src_px[src_start:src_end]
        bpy.data.images.remove(img)

    sheet.pixels[:] = sheet_pixels
    sheet.filepath_raw = OUT_SHEET_PATH
    sheet.file_format = 'PNG'
    sheet.save()
    print(f"[Act1Builder] Saved 4-angle QA sheet to {OUT_SHEET_PATH}")
    if ARTIFACT_DIR and os.path.isdir(ARTIFACT_DIR):
        try:
            shutil.copy2(OUT_SHEET_PATH, os.path.join(ARTIFACT_DIR, "act1_studio_4angle_sheet.png"))
        except OSError:
            pass


if __name__ == "__main__":
    build_act1_studio()
    export_act1_glb()
    render_4angle_qa_sheet()
