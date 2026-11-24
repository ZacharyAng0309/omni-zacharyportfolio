#!/usr/bin/env python3
"""
Authors the Act 1 Sovereign Titanium Atelier architectural hero centerpiece & gallery dais
using strict Data-First Blender 5.2 bmesh/bpy.data APIs (zero bpy.ops mesh/transform ops).
Exports self-contained glTF 2.0 binary to `public/models/props/act1_studio.glb`.
"""
from __future__ import annotations

import math
import os
import sys
import bpy
import bmesh
from mathutils import Euler, Matrix, Vector


# Positioned around glTF local (-0.55, y, -0.10) => Blender (X=-0.55, Y=+0.10, Z=y)
SCULPT_X = -0.55
SCULPT_Y = 0.10


def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for lgt in list(bpy.data.lights):
        bpy.data.lights.remove(lgt)


def make_pbr_material(
    name: str,
    base_color: tuple[float, float, float, float],
    metallic: float,
    roughness: float,
    *,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
    transmission: float = 0.0,
    coat_weight: float = 0.0,
    coat_roughness: float = 0.05,
    ior: float = 1.45,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    if not mat.use_nodes:
        mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")

    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Alpha"].default_value = base_color[3]

    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat_weight
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = coat_roughness
    if emission_color is not None and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = emission_color
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    return mat


def create_material_library() -> dict[str, bpy.types.Material]:
    return {
        "basalt": make_pbr_material(
            "Mat_Act1_ObsidianBasalt",
            (0.036, 0.039, 0.047, 1.0),
            metallic=0.22,
            roughness=0.40,
            coat_weight=0.12,
            coat_roughness=0.28,
        ),
        "brushed_ti": make_pbr_material(
            "Mat_Act1_BrushedTitanium",
            (0.18, 0.195, 0.22, 1.0),
            metallic=0.92,
            roughness=0.22,
            coat_weight=0.08,
            coat_roughness=0.12,
        ),
        "natural_ti": make_pbr_material(
            "Mat_Act1_NaturalTitanium",
            (0.49, 0.50, 0.525, 1.0),
            metallic=0.94,
            roughness=0.17,
            coat_weight=0.12,
            coat_roughness=0.10,
        ),
        "champagne_brass": make_pbr_material(
            "Mat_Act1_ChampagneBrass",
            (0.76, 0.62, 0.42, 1.0),
            metallic=0.96,
            roughness=0.16,
            coat_weight=0.10,
            coat_roughness=0.08,
        ),
        "optical_glass": make_pbr_material(
            "Mat_Act1_OpticalGlass",
            (0.80, 0.87, 0.96, 0.36),
            metallic=0.04,
            roughness=0.05,
            transmission=0.88,
            coat_weight=1.0,
            coat_roughness=0.04,
            ior=1.54,
        ),
        "warm_cove": make_pbr_material(
            "Mat_Act1_WarmCove",
            (1.0, 0.86, 0.66, 1.0),
            metallic=0.05,
            roughness=0.20,
            emission_color=(1.0, 0.79, 0.52, 1.0),
            emission_strength=2.2,
        ),
    }


def add_revolved_profile(
    bm: bmesh.types.BMesh,
    profile: list[tuple[float, float]],
    *,
    segments: int = 72,
    closed_profile: bool = True,
    mat_idx: int = 0,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    """Revolve an (r, z) polyline around local Z axis."""
    rings: list[list[bmesh.types.BMVert]] = []
    cx, cy, cz = center
    for r, z in profile:
        ring: list[bmesh.types.BMVert] = []
        for s in range(segments):
            ang = (2.0 * math.pi * s) / segments
            v = bm.verts.new((cx + math.cos(ang) * r, cy + math.sin(ang) * r, cz + z))
            ring.append(v)
        rings.append(ring)

    n_rings = len(rings)
    span = n_rings if closed_profile else n_rings - 1
    for i in range(span):
        r0 = rings[i]
        r1 = rings[(i + 1) % n_rings]
        for s in range(segments):
            s_next = (s + 1) % segments
            v00 = r0[s]
            v01 = r0[s_next]
            v10 = r1[s]
            v11 = r1[s_next]
            if (v00.co - v10.co).length < 1e-6:
                continue
            try:
                f = bm.faces.new((v00, v01, v11, v10))
                f.material_index = mat_idx
                f.smooth = True
            except ValueError:
                pass


def add_capped_polygon_prism(
    bm: bmesh.types.BMesh,
    *,
    outer_r: float,
    height: float,
    sides: int = 8,
    z_bottom: float = 0.0,
    inner_r: float = 0.0,
    chamfer: float = 0.008,
    rot_z: float = 0.0,
    mat_idx: int = 0,
) -> None:
    """Build a crisp bevelled/chamfered n-gon solid (or annular hollow ring frame) around Z."""
    ch = min(chamfer, height * 0.35, outer_r * 0.2)
    z0 = z_bottom
    z1 = z_bottom + ch
    z2 = z_bottom + height - ch
    z3 = z_bottom + height

    if inner_r > 0.001:
        outer_in = min(outer_r - ch, inner_r + ch + 0.01)
        # Closed cross-section profile rotated around polygon angles (outer chamfered, inner circular/octagonal bore)
        ring_specs = [
            (outer_r - ch, z0),
            (outer_r, z1),
            (outer_r, z2),
            (outer_r - ch, z3),
            (inner_r + ch, z3),
            (inner_r, z2),
            (inner_r, z1),
            (inner_r + ch, z0),
        ]
        # Build with oct/side count for outer, smooth/matching steps for inner
        rings: list[list[bmesh.types.BMVert]] = []
        for r_val, z_val in ring_specs:
            ring = []
            for s in range(sides):
                ang = rot_z + (2.0 * math.pi * s) / sides
                ring.append(bm.verts.new((math.cos(ang) * r_val, math.sin(ang) * r_val, z_val)))
            rings.append(ring)
        for i in range(len(rings)):
            r0 = rings[i]
            r1 = rings[(i + 1) % len(rings)]
            for s in range(sides):
                sn = (s + 1) % sides
                try:
                    f = bm.faces.new((r0[s], r0[sn], r1[sn], r1[s]))
                    f.material_index = mat_idx
                    f.smooth = True
                except ValueError:
                    pass
    else:
        ring_bot_in = [
            bm.verts.new((math.cos(rot_z + 2 * math.pi * s / sides) * (outer_r - ch),
                          math.sin(rot_z + 2 * math.pi * s / sides) * (outer_r - ch), z0))
            for s in range(sides)
        ]
        ring_bot_out = [
            bm.verts.new((math.cos(rot_z + 2 * math.pi * s / sides) * outer_r,
                          math.sin(rot_z + 2 * math.pi * s / sides) * outer_r, z1))
            for s in range(sides)
        ]
        ring_top_out = [
            bm.verts.new((math.cos(rot_z + 2 * math.pi * s / sides) * outer_r,
                          math.sin(rot_z + 2 * math.pi * s / sides) * outer_r, z2))
            for s in range(sides)
        ]
        ring_top_in = [
            bm.verts.new((math.cos(rot_z + 2 * math.pi * s / sides) * (outer_r - ch),
                          math.sin(rot_z + 2 * math.pi * s / sides) * (outer_r - ch), z3))
            for s in range(sides)
        ]

        f_bot = bm.faces.new(list(reversed(ring_bot_in)))
        f_bot.material_index = mat_idx
        f_bot.smooth = True
        f_top = bm.faces.new(ring_top_in)
        f_top.material_index = mat_idx
        f_top.smooth = True

        loop_pairs = [
            (ring_bot_in, ring_bot_out),
            (ring_bot_out, ring_top_out),
            (ring_top_out, ring_top_in),
        ]
        for r0, r1 in loop_pairs:
            for s in range(sides):
                sn = (s + 1) % sides
                f = bm.faces.new((r0[s], r0[sn], r1[sn], r1[s]))
                f.material_index = mat_idx
                f.smooth = True


def add_beveled_box(
    bm: bmesh.types.BMesh,
    size: tuple[float, float, float],
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
    euler: tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel: float = 0.004,
    segments: int = 2,
    mat_idx: int = 0,
) -> None:
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts = ret["verts"]
    sx, sy, sz = size
    for v in verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz

    vert_set = set(verts)
    edges = [e for e in bm.edges if e.verts[0] in vert_set and e.verts[1] in vert_set]
    if bevel > 1e-5:
        bmesh.ops.bevel(
            bm,
            geom=edges,
            offset=bevel,
            offset_type="OFFSET",
            segments=segments,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
        )

    # Re-gather connected faces/verts via BFS from remaining original/new edges? Better: build in scratch bmesh then merge!
    raise RuntimeError("Use add_beveled_box_clean")


def append_bmesh(
    dst: bmesh.types.BMesh,
    src: bmesh.types.BMesh,
    *,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    euler: tuple[float, float, float] = (0.0, 0.0, 0.0),
    mat_idx: int | None = None,
) -> None:
    rot_m = Euler(euler, "XYZ").to_matrix().to_4x4()
    loc_v = Vector(location)
    vmap: dict[bmesh.types.BMVert, bmesh.types.BMVert] = {}
    for sv in src.verts:
        p = (rot_m @ sv.co) + loc_v
        vmap[sv] = dst.verts.new(p)
    for sf in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in sf.verts])
            nf.material_index = sf.material_index if mat_idx is None else mat_idx
            nf.smooth = sf.smooth
        except ValueError:
            pass


def create_beveled_box_bm(
    size: tuple[float, float, float],
    bevel: float = 0.004,
    segments: int = 2,
    mat_idx: int = 0,
) -> bmesh.types.BMesh:
    sbm = bmesh.new()
    bmesh.ops.create_cube(sbm, size=1.0)
    sx, sy, sz = size
    for v in sbm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    if bevel > 1e-5:
        bmesh.ops.bevel(
            sbm,
            geom=list(sbm.edges),
            offset=bevel,
            offset_type="OFFSET",
            segments=segments,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
        )
    for f in sbm.faces:
        f.material_index = mat_idx
        f.smooth = True
    return sbm


def create_beveled_cylinder_bm(
    radius: float,
    height: float,
    *,
    segments: int = 48,
    bevel: float = 0.003,
    mat_idx: int = 0,
) -> bmesh.types.BMesh:
    sbm = bmesh.new()
    bmesh.ops.create_cone(
        sbm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=height,
    )
    if bevel > 1e-5:
        cap_edges = [
            e
            for e in sbm.edges
            if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-5
        ]
        bmesh.ops.bevel(
            sbm,
            geom=cap_edges,
            offset=bevel,
            offset_type="OFFSET",
            segments=2,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
        )
    for f in sbm.faces:
        f.material_index = mat_idx
        f.smooth = True
    return sbm


def finalize_object(
    name: str,
    bm: bmesh.types.BMesh,
    materials: list[bpy.types.Material],
    location: tuple[float, float, float],
    *,
    edge_split_deg: float = 34.0,
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
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)

    if edge_split_deg > 0:
        mod = obj.modifiers.new(name="EdgeSplit", type="EDGE_SPLIT")
        mod.use_edge_angle = True
        mod.split_angle = math.radians(edge_split_deg)
        mod.use_edge_sharp = False

    return obj


def build_island_dais(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Island_Act1: Two-tier circular monolithic basalt gallery dais grounded at Z=0.0."""
    mat_list = [mats["basalt"], mats["warm_cove"], mats["champagne_brass"], mats["brushed_ti"]]
    bm = bmesh.new()

    # Outer & upper basalt dais with clean chamfered shadow reveal groove at R = 1.56
    dais_profile = [
        (0.02, 0.000),
        (2.12, 0.000),
        (2.15, 0.008),
        (2.15, 0.058),
        (2.12, 0.068),
        (1.62, 0.068),
        (1.56, 0.068),
        (1.56, 0.078),
        (1.52, 0.078),
        (1.52, 0.132),
        (1.49, 0.140),
        (0.02, 0.140),
    ]
    # Center fill disc edges cleanly closed
    add_revolved_profile(bm, dais_profile, segments=84, closed_profile=True, mat_idx=0)

    # Flush center bottom & top cap disks for center 0.02 radius
    for z_cap, flip in ((0.0, True), (0.140, False)):
        ring_v = [
            bm.verts.new((math.cos(2 * math.pi * s / 84) * 0.02, math.sin(2 * math.pi * s / 84) * 0.02, z_cap))
            for s in range(84)
        ]
        f = bm.faces.new(list(reversed(ring_v)) if flip else ring_v)
        f.material_index = 0
        f.smooth = True

    # Undercut warm amber cove emitter ring inside shadow gap (mat 1 = warm_cove)
    cove_profile = [
        (1.525, 0.069),
        (1.555, 0.069),
        (1.555, 0.076),
        (1.525, 0.076),
    ]
    add_revolved_profile(bm, cove_profile, segments=84, closed_profile=True, mat_idx=1)

    # Flush inlaid champagne-brass precision datum ring on upper deck (mat 2 = champagne_brass)
    brass_ring_profile = [
        (1.425, 0.139),
        (1.448, 0.139),
        (1.448, 0.143),
        (1.425, 0.143),
    ]
    add_revolved_profile(bm, brass_ring_profile, segments=84, closed_profile=True, mat_idx=2)

    # Inner secondary fine brass datum ring
    brass_inner_profile = [
        (0.86, 0.139),
        (0.874, 0.139),
        (0.874, 0.1425),
        (0.86, 0.1425),
    ]
    add_revolved_profile(bm, brass_inner_profile, segments=72, closed_profile=True, mat_idx=2)

    # 12 flush radial champagne-brass precision index ticks between inner & outer rings
    tick_bm = create_beveled_box_bm((0.14, 0.011, 0.005), bevel=0.001, segments=1, mat_idx=2)
    for k in range(12):
        ang = (2.0 * math.pi * k) / 12.0
        r_mid = 1.24
        append_bmesh(
            bm,
            tick_bm,
            location=(math.cos(ang) * r_mid, math.sin(ang) * r_mid, 0.140),
            euler=(0.0, 0.0, ang),
        )
    tick_bm.free()

    # 4 cardinal brushed-titanium perimeter plinth anchors on lower step
    lug_bm = create_beveled_box_bm((0.18, 0.08, 0.022), bevel=0.004, segments=2, mat_idx=3)
    for k in range(4):
        ang = (math.pi / 4.0) + k * (math.pi / 2.0)
        r_lug = 1.84
        append_bmesh(
            bm,
            lug_bm,
            location=(math.cos(ang) * r_lug, math.sin(ang) * r_lug, 0.068),
            euler=(0.0, 0.0, ang),
        )
    lug_bm.free()

    # Horological 24-tick champagne-brass meridian ring & 8 radial data conduit inlays on lower terrace (Z=0.068)
    meridian_profile = [
        (1.668, 0.067),
        (1.688, 0.067),
        (1.688, 0.072),
        (1.668, 0.072),
    ]
    add_revolved_profile(bm, meridian_profile, segments=84, closed_profile=True, mat_idx=2)
    meridian_tick_bm = create_beveled_box_bm((0.065, 0.009, 0.005), bevel=0.001, segments=1, mat_idx=2)
    for k in range(24):
        ang = (2.0 * math.pi * k) / 24.0
        r_t = 1.75
        append_bmesh(
            bm,
            meridian_tick_bm,
            location=(math.cos(ang) * r_t, math.sin(ang) * r_t, 0.069),
            euler=(0.0, 0.0, ang),
        )
    meridian_tick_bm.free()

    conduit_bm = create_beveled_box_bm((0.46, 0.016, 0.006), bevel=0.0015, segments=1, mat_idx=3)
    for k in range(8):
        ang = (2.0 * math.pi * k) / 8.0
        r_c = 1.84
        append_bmesh(
            bm,
            conduit_bm,
            location=(math.cos(ang) * r_c, math.sin(ang) * r_c, 0.069),
            euler=(0.0, 0.0, ang),
        )
    conduit_bm.free()

    # Right-flank cantilevered octagonal basalt & champagne-brass plinth pad seating ExecutiveDossierMonolith
    # Local offset (+1.67, -0.14) maps to avatarRig (+0.60, -1.31, +0.02) flush with upper deck (Z = 0.140m)
    pad_cx, pad_cy = 1.67, -0.14
    pad_bm = bmesh.new()
    add_capped_polygon_prism(
        pad_bm,
        outer_r=0.31,
        height=0.074,
        sides=8,
        z_bottom=0.066,
        chamfer=0.008,
        rot_z=math.pi / 8.0,
        mat_idx=0,
    )
    add_revolved_profile(
        pad_bm,
        [(0.235, 0.136), (0.258, 0.136), (0.258, 0.143), (0.235, 0.143)],
        segments=48,
        closed_profile=True,
        mat_idx=2,
    )
    append_bmesh(bm, pad_bm, location=(pad_cx, pad_cy, 0.0))
    pad_bm.free()

    return finalize_object("SM_Island_Act1", bm, mat_list, (SCULPT_X, SCULPT_Y, 0.0), edge_split_deg=35.0)


def build_atelier_pedestal(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Atelier_Pedestal: Tapered 12-flute dark-titanium stator base with champagne-brass cradle collar."""
    mat_list = [mats["brushed_ti"], mats["natural_ti"], mats["champagne_brass"], mats["warm_cove"], mats["basalt"]]
    bm = bmesh.new()

    # Main tapered architectural base plinth (Z_local 0.0..0.46 => world Z 0.14..0.60)
    # Bottom heavy basalt plinth footpad
    add_capped_polygon_prism(bm, outer_r=0.66, height=0.06, sides=12, z_bottom=0.0, chamfer=0.010, mat_idx=4)
    # Tapered 12-faceted stator column
    col_profile = [
        (0.02, 0.055),
        (0.58, 0.055),
        (0.59, 0.068),
        (0.49, 0.425),
        (0.47, 0.445),
        (0.02, 0.445),
    ]
    add_revolved_profile(bm, col_profile, segments=48, closed_profile=True, mat_idx=0)
    for z_c, flip in ((0.055, True), (0.445, False)):
        rv = [bm.verts.new((math.cos(2 * math.pi * s / 48) * 0.02, math.sin(2 * math.pi * s / 48) * 0.02, z_c)) for s in range(48)]
        f = bm.faces.new(list(reversed(rv)) if flip else rv)
        f.material_index = 0
        f.smooth = True

    # 12 machined natural-titanium vertical structural ribs around the column
    rib_bm = create_beveled_box_bm((0.036, 0.026, 0.36), bevel=0.004, segments=2, mat_idx=1)
    for k in range(12):
        ang = (2.0 * math.pi * k) / 12.0
        r_rib = 0.535
        # Slight inward lean (0.24 rad) matching column taper
        append_bmesh(
            bm,
            rib_bm,
            location=(math.cos(ang) * r_rib, math.sin(ang) * r_rib, 0.25),
            euler=(0.0, -0.23, ang),
        )
    rib_bm.free()

    # 12 champagne-brass base stator accent fins locking column into basalt footpad
    base_fin_bm = create_beveled_box_bm((0.068, 0.018, 0.052), bevel=0.003, segments=1, mat_idx=2)
    for k in range(12):
        ang = (2.0 * math.pi * (k + 0.5)) / 12.0
        r_fin = 0.60
        append_bmesh(
            bm,
            base_fin_bm,
            location=(math.cos(ang) * r_fin, math.sin(ang) * r_fin, 0.075),
            euler=(0.0, 0.0, ang),
        )
    base_fin_bm.free()

    # Upper champagne-brass magnetic cradle collar (Z_local 0.445..0.500 => world Z 0.585..0.640)
    collar_profile = [
        (0.32, 0.442),
        (0.505, 0.442),
        (0.520, 0.458),
        (0.520, 0.488),
        (0.498, 0.500),
        (0.355, 0.500),
        (0.335, 0.482),
        (0.320, 0.458),
    ]
    add_revolved_profile(bm, collar_profile, segments=64, closed_profile=True, mat_idx=2)

    # Inner grooved natural-titanium & champagne-brass vernier bezel ring
    vernier_profile = [
        (0.370, 0.498),
        (0.405, 0.498),
        (0.405, 0.508),
        (0.370, 0.508),
    ]
    add_revolved_profile(bm, vernier_profile, segments=64, closed_profile=True, mat_idx=1)

    # Inner recessed warm levitation stator halo inside cradle bowl
    emitter_profile = [
        (0.24, 0.444),
        (0.335, 0.444),
        (0.335, 0.464),
        (0.24, 0.464),
    ]
    add_revolved_profile(bm, emitter_profile, segments=64, closed_profile=True, mat_idx=3)

    # Center recessed dark stator core mirror dish
    dish_bm = create_beveled_cylinder_bm(0.245, 0.022, segments=48, bevel=0.003, mat_idx=4)
    append_bmesh(bm, dish_bm, location=(0.0, 0.0, 0.450))
    dish_bm.free()

    return finalize_object("SM_Atelier_Pedestal", bm, mat_list, (SCULPT_X, SCULPT_Y, 0.14), edge_split_deg=34.0)


def build_tier3_chassis(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """Prop_Blueprint_Tier3: Enterprise Settlement & Security Chassis (octagonal dark titanium wafer, Z=0.88)."""
    mat_list = [mats["brushed_ti"], mats["champagne_brass"], mats["natural_ti"]]
    bm = bmesh.new()

    # Octagonal annular bevelled chassis frame (local Z -0.044..+0.044)
    add_capped_polygon_prism(
        bm,
        outer_r=0.47,
        height=0.086,
        sides=8,
        z_bottom=-0.043,
        inner_r=0.255,
        chamfer=0.011,
        rot_z=math.pi / 8.0,
        mat_idx=0,
    )

    # Recessed brass inner bore sleeve
    bore_profile = [
        (0.242, -0.036),
        (0.268, -0.036),
        (0.268, 0.036),
        (0.242, 0.036),
    ]
    add_revolved_profile(bm, bore_profile, segments=56, closed_profile=True, mat_idx=1)

    # 4 corner machined champagne-brass clamp lugs
    lug_bm = create_beveled_box_bm((0.088, 0.056, 0.096), bevel=0.006, segments=2, mat_idx=1)
    for k in range(4):
        ang = (math.pi / 4.0) + k * (math.pi / 2.0)
        append_bmesh(
            bm,
            lug_bm,
            location=(math.cos(ang) * 0.425, math.sin(ang) * 0.425, 0.0),
            euler=(0.0, 0.0, ang),
        )
    lug_bm.free()

    # 8 radial underside satin-titanium heat-sink cooling fins
    fin_bm = create_beveled_box_bm((0.15, 0.018, 0.022), bevel=0.0025, segments=1, mat_idx=2)
    for k in range(8):
        ang = (2.0 * math.pi * k) / 8.0
        append_bmesh(
            bm,
            fin_bm,
            location=(math.cos(ang) * 0.35, math.sin(ang) * 0.35, -0.048),
            euler=(0.0, 0.0, ang),
        )
    fin_bm.free()

    return finalize_object("Prop_Blueprint_Tier3", bm, mat_list, (SCULPT_X, SCULPT_Y, 0.88), edge_split_deg=34.0)


def build_tier2_orchestration(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """Prop_Blueprint_Tier2: Multi-Agent Orchestration Stator Ring (satin titanium + brass + optical glass, Z=1.24)."""
    mat_list = [mats["natural_ti"], mats["champagne_brass"], mats["optical_glass"], mats["brushed_ti"]]
    bm = bmesh.new()

    # Main chamfered circular satin-titanium stator ring (R_in=0.315, R_out=0.475)
    ring_profile = [
        (0.320, -0.030),
        (0.460, -0.030),
        (0.475, -0.016),
        (0.475, 0.016),
        (0.460, 0.030),
        (0.320, 0.030),
        (0.310, 0.018),
        (0.310, -0.018),
    ]
    add_revolved_profile(bm, ring_profile, segments=72, closed_profile=True, mat_idx=0)

    # Top & bottom inlaid champagne-brass concentric data tracks
    for z_sign in (-1.0, 1.0):
        track_profile = [
            (0.365, z_sign * 0.027),
            (0.415, z_sign * 0.027),
            (0.415, z_sign * 0.033),
            (0.365, z_sign * 0.033),
        ]
        add_revolved_profile(bm, track_profile, segments=72, closed_profile=True, mat_idx=1)

    # Inner translucent optical glass annular lens (R 0.255..0.315)
    glass_profile = [
        (0.258, -0.012),
        (0.314, -0.012),
        (0.314, 0.012),
        (0.258, 0.012),
    ]
    add_revolved_profile(bm, glass_profile, segments=64, closed_profile=True, mat_idx=2)

    # 8 radial dark-titanium cantilever stator bridges & perimeter pins
    bridge_bm = create_beveled_box_bm((0.085, 0.022, 0.044), bevel=0.003, segments=2, mat_idx=3)
    for k in range(8):
        ang = (2.0 * math.pi * k) / 8.0
        append_bmesh(
            bm,
            bridge_bm,
            location=(math.cos(ang) * 0.295, math.sin(ang) * 0.295, 0.0),
            euler=(0.0, 0.0, ang),
        )
    bridge_bm.free()

    return finalize_object("Prop_Blueprint_Tier2", bm, mat_list, (SCULPT_X, SCULPT_Y, 1.24), edge_split_deg=34.0)


def build_tier1_crown(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """Prop_Blueprint_Tier1: C-Suite Strategic Intelligence Crown (octagonal titanium bezel + sight glass, Z=1.60)."""
    mat_list = [mats["natural_ti"], mats["champagne_brass"], mats["optical_glass"], mats["brushed_ti"]]
    bm = bmesh.new()

    # Main chamfered octagonal crown frame (Z_local -0.038..+0.038)
    add_capped_polygon_prism(
        bm,
        outer_r=0.485,
        height=0.076,
        sides=8,
        z_bottom=-0.038,
        inner_r=0.295,
        chamfer=0.012,
        rot_z=math.pi / 8.0,
        mat_idx=0,
    )

    # Stepped inner champagne-brass circular datum bezel
    bezel_profile = [
        (0.268, -0.026),
        (0.312, -0.026),
        (0.312, 0.032),
        (0.295, 0.042),
        (0.268, 0.042),
        (0.262, 0.028),
        (0.262, -0.018),
    ]
    add_revolved_profile(bm, bezel_profile, segments=64, closed_profile=True, mat_idx=1)

    # Top optical sapphire sight-lens disc inside the crown aperture
    lens_bm = create_beveled_cylinder_bm(0.265, 0.018, segments=56, bevel=0.004, mat_idx=2)
    append_bmesh(bm, lens_bm, location=(0.0, 0.0, 0.014))
    lens_bm.free()

    # 4 corner micro-machined dark-titanium alignment pillars
    pillar_bm = create_beveled_cylinder_bm(0.022, 0.094, segments=20, bevel=0.004, mat_idx=3)
    for k in range(4):
        ang = (math.pi / 4.0) + k * (math.pi / 2.0)
        append_bmesh(bm, pillar_bm, location=(math.cos(ang) * 0.425, math.sin(ang) * 0.425, 0.0))
    pillar_bm.free()

    return finalize_object("Prop_Blueprint_Tier1", bm, mat_list, (SCULPT_X, SCULPT_Y, 1.60), edge_split_deg=34.0)


def build_core_nucleus(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Core_Nucleus: Faceted jewel-cut optical sapphire crystal at Z=1.24."""
    mat_list = [mats["optical_glass"]]
    bm = bmesh.new()

    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.205)
    for v in bm.verts:
        v.co.z *= 1.15
    bmesh.ops.bevel(
        bm,
        geom=list(bm.edges),
        offset=0.006,
        offset_type="OFFSET",
        segments=2,
        profile=0.5,
        affect="EDGES",
        clamp_overlap=True,
    )
    for f in bm.faces:
        f.material_index = 0
        f.smooth = True

    return finalize_object("SM_Core_Nucleus", bm, mat_list, (SCULPT_X, SCULPT_Y, 1.24), edge_split_deg=24.0)


def build_core_filament(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    """SM_Core_Filament: Suspended machined champagne-brass lattice & warm amber filament inside nucleus."""
    mat_list = [mats["warm_cove"], mats["champagne_brass"]]
    bm = bmesh.new()

    # Inner glowing faceted octahedron filament (mat 0 = warm_cove)
    f_bm = bmesh.new()
    bmesh.ops.create_icosphere(f_bm, subdivisions=1, radius=0.072)
    for v in f_bm.verts:
        v.co.z *= 1.22
    for f in f_bm.faces:
        f.material_index = 0
        f.smooth = False
    append_bmesh(bm, f_bm)
    f_bm.free()

    # Twin orthogonal champagne-brass micro gyroscope bands around the filament (mat 1)
    band_profile = [
        (0.112, -0.008),
        (0.125, -0.008),
        (0.125, 0.008),
        (0.112, 0.008),
    ]
    g1_bm = bmesh.new()
    add_revolved_profile(g1_bm, band_profile, segments=48, closed_profile=True, mat_idx=1)
    append_bmesh(bm, g1_bm, euler=(math.radians(38), math.radians(18), 0.0))
    append_bmesh(bm, g1_bm, euler=(math.radians(-52), math.radians(-28), math.radians(90)))
    g1_bm.free()

    return finalize_object("SM_Core_Filament", bm, mat_list, (SCULPT_X, SCULPT_Y, 1.24), edge_split_deg=32.0)


def build_gimbal_ring(
    name: str,
    radius: float,
    thickness_r: float,
    thickness_z: float,
    ring_mat: bpy.types.Material,
    accent_mat: bpy.types.Material,
    trunnion_axis_x: bool = True,
) -> bpy.types.Object:
    """Horological bevelled knife-edge gimbal ring centered at Z=1.24."""
    mat_list = [ring_mat, accent_mat]
    bm = bmesh.new()

    hr = thickness_r * 0.5
    hz = thickness_z * 0.5
    # Chamfered hexagonal cross-section revolved around Z
    sec = [
        (radius - hr, -hz * 0.55),
        (radius, -hz),
        (radius + hr, -hz * 0.55),
        (radius + hr, hz * 0.55),
        (radius, hz),
        (radius - hr, hz * 0.55),
    ]
    add_revolved_profile(bm, sec, segments=96, closed_profile=True, mat_idx=0)

    # Twin horological axle trunnions & 4 cardinal vernier accents
    lug_bm = create_beveled_cylinder_bm(thickness_r * 0.9, thickness_z * 1.45, segments=20, bevel=0.0025, mat_idx=1)
    for sign in (-1.0, 1.0):
        loc = (sign * radius, 0.0, 0.0) if trunnion_axis_x else (0.0, sign * radius, 0.0)
        append_bmesh(bm, lug_bm, location=loc)
    lug_bm.free()

    fin_bm = create_beveled_box_bm((thickness_r * 2.1, thickness_r * 0.45, thickness_z * 1.15), bevel=0.002, segments=1, mat_idx=1)
    for k in range(4):
        ang = (math.pi / 4.0) + k * (math.pi / 2.0)
        append_bmesh(bm, fin_bm, location=(math.cos(ang) * radius, math.sin(ang) * radius, 0.0), euler=(0.0, 0.0, ang))
    fin_bm.free()

    return finalize_object(name, bm, mat_list, (SCULPT_X, SCULPT_Y, 1.24), edge_split_deg=34.0)


def main() -> None:
    clear_scene()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0

    mats = create_material_library()

    objs = [
        build_island_dais(mats),
        build_atelier_pedestal(mats),
        build_tier3_chassis(mats),
        build_tier2_orchestration(mats),
        build_tier1_crown(mats),
        build_core_nucleus(mats),
        build_core_filament(mats),
        build_gimbal_ring(
            "SM_Gyro_Gimbal_Outer",
            radius=0.71,
            thickness_r=0.024,
            thickness_z=0.038,
            ring_mat=mats["brushed_ti"],
            accent_mat=mats["champagne_brass"],
            trunnion_axis_x=True,
        ),
        build_gimbal_ring(
            "SM_Gyro_Gimbal_Inner",
            radius=0.59,
            thickness_r=0.019,
            thickness_z=0.028,
            ring_mat=mats["champagne_brass"],
            accent_mat=mats["natural_ti"],
            trunnion_axis_x=False,
        ),
    ]

    # Ensure world bounds Z_min >= 0.0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objs:
        eo = obj.evaluated_get(depsgraph)
        z_vals = [(obj.matrix_world @ Vector(corner)).z for corner in eo.bound_box]
        print(f"  Node {obj.name:24s} | verts={len(eo.to_mesh().vertices):5d} | Z=[{min(z_vals):.4f}, {max(z_vals):.4f}]")
        eo.to_mesh_clear()

    out_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "public", "models", "props", "act1_studio.glb")
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_materials="EXPORT",
        export_meshopt_compression_enable=True,
        export_meshopt_extension="EXT_meshopt_compression",
    )
    size_bytes = os.path.getsize(out_path)
    print(f"Exported {out_path}: {size_bytes} bytes ({size_bytes / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
