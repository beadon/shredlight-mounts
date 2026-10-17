#!/usr/bin/env python3
"""Clamp that holds the v7 receiver on a Radium Mach One S truck strut.

The hanger is a 22 mm plate tilted back 45 degrees (its front face looks forward
and down). Above each triangular window, a strut ("rake") rises at 45 degrees in
the plate's plane. The clamp wraps that strut:

  saddle  inverted U dropped over the strut from above; its front arm takes the
          screw, its rear arm ends in a hook pocket, and it carries the platform
  keeper  flat bar slid through the window from the front, under the strut; its
          rear end goes into the saddle's hook, its front end holds the nut
  1x M5 x 20 socket-head screw with a nyloc nut, in front of the plate, fitted and
          tightened through the receiver's own slot (with the light removed)

The receiver is a platform: v7's lip plate, slot and barbs, face up and level fore
and aft, rolled outboard about its length so it sits low over the clamp. The slot's
open end points at the nose; the light sits on top, lens forward, and slides in from
the front until the barbs catch. The channel under the lip is open at both ends.
The right side is modelled; left is mirrored.

Frames, all in mm:
  world  X = right, Y = forward (toward the nose), Z = up
  strut  u = along the strut, v = across it from the window face (0) to the
         skyward face, w = plate normal (out of the front face)

Usage:  .venv/bin/python truck_mount.py [outdir]
"""
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, Manifold

import shredlight_mount as receiver

VERSION = 6

# --- Truck (measured by calipers unless noted) ---
PLATE_T = 22.0       # hanger plate thickness
STRUT_H = 9.0        # strut, window face to skyward face, in the hanger's plane
WINDOW_FLAT = 11.0   # flat on the window-side face, front to back, between its chamfers
TOP_CHAMFER = 5.5    # skyward-face chamfers, front to back (~6 measured; modelled smaller)
CHAMFER_DEPTH = 1.5  # how far the chamfers cut into the 9 mm: unmeasured, kept small so they cannot bind
TILT = 45.0          # plate tilted back from vertical (user's estimate; to be confirmed by a test fit)
STRUT_ANGLE = 45.0   # strut angle in the plate's plane (photo estimate)

# --- Clamp ---
LINER = 1.0          # gap all round the strut for a 1 mm TPU / rubber liner
PARTING_GAP = 3.0    # gap between the saddle's front arm and the keeper so the screw can pull
LENGTH = 20.0        # keeper length along the strut; it must fit the ~35 mm window side
SADDLE_LENGTH = 30.0 # saddle length along the strut's top face (~55 mm free between beam and block)
SADDLE_T = 5.0       # saddle thickness over the skyward face
KEEPER_T = 6.0       # keeper thickness under the strut, inside the window
SCREW_D = 5.5        # M5 clearance
HEAD_D = 9.0         # M5 socket head (8.5) plus clearance; also the screw's path through the slot
SCREW_LEN = 20.0
NUT_AF = 8.3         # M5 nyloc across flats, plus clearance
NUT_H = 5.0
CHEEK = 3.0          # wall outside the screw
HOOK_ENGAGE = 5.0    # how far the keeper's rear end reaches into the hook pocket
HOOK_T = 3.0         # hook lip under the keeper's rear end
HOOK_WALL = 3.0      # pocket's outer wall
HOOK_CLEAR = 0.4     # sliding clearance around the keeper in the pocket

# --- Receiver platform ---
ROLL = 45.0          # platform rolled outboard about its length (fore-aft stays level)
SLOT_POINT = 12.0    # where the screw's path crosses the slot, mm from the receiver's centre
                     # toward its open end (the upper, 14.5 mm wide part of the slot)
POD_REAR = 4.0       # how far the side rails run below the pocket, into the pedestal
PEDESTAL_MARGIN = 3.0  # pedestal reaches this far past the saddle top, along the platform
WEB_T = 4.0          # thickness of each web joining a side rail to the saddle
HANGER_CLEAR = 2.0   # minimum gap to the (schematic) hanger in the assembly check

# Light envelope for the assembly preview only (estimated from a photo, not measured)
LIGHT_L, LIGHT_W, LIGHT_H = 78.0, 32.0, 30.0
LIGHT_LENS_PROUD = 5.0  # lens ahead of the platform's front edge

# --- Assembly preview only (schematic hanger; nothing here affects the printed parts) ---
CLAMP_OFFSET = 40.0  # clamp centre from the board centreline, measured across
HANGER_H = 65.0      # hanger laid flat, base of the beam to the apex (measured)
BEAM_H = 14.0        # axle beam height below the windows
BEAM_HALF = 130.0    # axle beam half-length
BLOCK_HALF = 18.0    # pivot block half-width

HALF_T = PLATE_T / 2
FACE = HALF_T + LINER                         # clamp faces sit this far from the plate's centre
SCREW_W = FACE + 1.0 + SCREW_D / 2            # screw axis just outside the plate's front face
FRONT_W = SCREW_W + SCREW_D / 2 + CHEEK       # front arm's outer face
BACK_W = FACE + HOOK_ENGAGE + HOOK_CLEAR + HOOK_WALL  # rear arm's outer face
KEEPER_TOP = -LINER  # keeper's upper face, pressing the window-side land through the liner
KEEPER_BOTTOM = KEEPER_TOP - KEEPER_T
ARM_BOTTOM = KEEPER_TOP + PARTING_GAP


def strut_frame():
    """Columns u, v, w of the right strut in world coordinates (a proper rotation)."""
    t, a = np.radians(TILT), np.radians(STRUT_ANGLE)
    w = np.array([0, np.cos(t), -np.sin(t)])  # out of the front face
    p = np.array([0, np.sin(t), np.cos(t)])   # "up" within the plate
    x = np.array([1.0, 0, 0])
    u = -np.cos(a) * x + np.sin(a) * p        # rises toward the truck's centre
    v = np.sin(a) * x + np.cos(a) * p         # toward the skyward face
    m = np.column_stack([u, v, w])
    if np.linalg.det(m) < 0:
        m[:, 0] *= -1  # the clamp is symmetric along u
    return m


def place(part, rot, offset=(0, 0, 0)):
    return part.transform(np.column_stack([rot, offset]))


def along_u(cs, length):
    """Extrude a (v, w) cross-section along u, centred on u = 0."""
    m = cs.extrude(length).translate([0, 0, -length / 2])
    # extrusion axes (a, b, c) -> local (v, w, u), stored as local X = u, Y = v, Z = w
    return place(m, np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float))


def strut_profile(grow=0.0):
    """Strut cross-section in (v, w), grown outward by `grow`."""
    cw = (PLATE_T - WINDOW_FLAT) / 2  # window-side chamfers, front to back
    ct = TOP_CHAMFER
    d = CHAMFER_DEPTH
    pts = [(0, -HALF_T + cw), (0, HALF_T - cw), (d, HALF_T), (STRUT_H - d, HALF_T),
           (STRUT_H, HALF_T - ct), (STRUT_H, -HALF_T + ct), (STRUT_H - d, -HALF_T), (d, -HALF_T)]
    cs = CrossSection([pts], FillRule.EvenOdd)
    return cs.offset(grow) if grow else cs


def box(u0, u1, v0, v1, w0, w1):
    return Manifold.cube([u1 - u0, v1 - v0, w1 - w0]).translate([u0, v0, w0])


def along_v(m):
    """Turn a Z-axis solid so it runs along local v (Y)."""
    return m.rotate([-90, 0, 0])


def screw_hole():
    return along_v(Manifold.cylinder(200, SCREW_D / 2, circular_segments=32)).translate([0, -100, SCREW_W])


def head_seat():
    return KEEPER_BOTTOM - 1.0 + SCREW_LEN  # screw tip 1 mm past the nut


def driver_access():
    """The screw head's path: from its seat straight out along the screw axis."""
    return along_v(Manifold.cylinder(200, HEAD_D / 2, circular_segments=32)).translate([0, head_seat(), SCREW_W])


def saddle_local():
    top = STRUT_H + SADDLE_T
    s = box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, ARM_BOTTOM, top, -BACK_W, FRONT_W)
    # Rear arm continues down past the keeper and turns in under it: the hook.
    hook_bottom = KEEPER_BOTTOM - HOOK_CLEAR - HOOK_T
    s += box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, hook_bottom, ARM_BOTTOM, -BACK_W, -FACE)
    pocket = box(-LENGTH / 2 - HOOK_CLEAR, LENGTH / 2 + HOOK_CLEAR, KEEPER_BOTTOM - HOOK_CLEAR,
                 KEEPER_TOP + PARTING_GAP, -FACE - HOOK_ENGAGE - HOOK_CLEAR, -FACE + 1)
    # Removing the strut (and everything below its window face) leaves the top and two arms.
    under = box(-SADDLE_LENGTH, SADDLE_LENGTH, -50, 0, -FACE, FACE)
    return (s - along_u(strut_profile(LINER), SADDLE_LENGTH + 2) - under - pocket
            - screw_hole() - driver_access())


def keeper_local():
    # Flat top: presses only the window-side land, so unknown chamfer angles cannot interfere.
    k = box(-LENGTH / 2, LENGTH / 2, KEEPER_BOTTOM, KEEPER_TOP, -FACE - HOOK_ENGAGE, FRONT_W)
    nut = along_v(CrossSection.circle(NUT_AF / np.sqrt(3), 6).extrude(NUT_H)).translate([0, KEEPER_BOTTOM, SCREW_W])
    return k - screw_hole() - nut


def receiver_rot(roll=None):
    """Receiver face up, slot's open end (Y) toward the nose, rolled outboard about Y."""
    r = np.radians(ROLL if roll is None else roll)
    return np.array([[np.cos(r), 0, np.sin(r)], [0, 1, 0], [-np.sin(r), 0, np.cos(r)]])


def receiver_dims():
    """Bounds of the v7 receiver, its inner half-width and the flange gap behind the lip."""
    body = receiver.left_mount(**receiver.VERSIONS[7])
    lo, hi = np.array(body.bounding_box()).reshape(2, 3)
    inner = (hi[0] - lo[0]) / 2 - receiver.T * receiver.IN
    gap = (receiver.GAP + receiver.FIT) * receiver.IN
    return body, lo, hi, inner, gap


def receiver_body():
    """v7 lip and side rails only: the bottom wall is cut away and the rails run back."""
    body, lo, hi, inner, gap = receiver_dims()
    body -= Manifold.cube([2 * inner, receiver.T * receiver.IN + 2, gap + 1]).translate([-inner, lo[1] - 1, -1])
    for x0 in (lo[0], inner):
        body += Manifold.cube([receiver.T * receiver.IN, hi[1] - lo[1], POD_REAR]).translate([x0, lo[1], -POD_REAR])
    return body, lo, hi


def saddle_top(rot):
    """The saddle's top slab (over the strut's skyward face), in world coordinates."""
    top = STRUT_H + SADDLE_T
    return place(box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, top - 1, top, -BACK_W, FRONT_W), rot)


def pocket_local():
    """Where the light's flange runs: under the lip, between the rails, full length."""
    _, lo, hi, inner, gap = receiver_dims()
    return Manifold.cube([2 * inner, hi[1] - lo[1], gap]).translate([-inner, lo[1], 0])


def screw_head(rot):
    return place(along_v(Manifold.cylinder(5.0, HEAD_D / 2, circular_segments=32)).translate(
        [0, head_seat(), SCREW_W]), rot)


def pod_placement(rot, rrot):
    """Slide the platform out along the screw's path, keeping the path through the slot at
    SLOT_POINT, until the flange channel clears the clamp and the screw head."""
    _, lo, hi, inner, gap = receiver_dims()
    axis = rot[:, 1]                                    # screw axis (local v) in world
    seat = rot @ np.array([0, head_seat(), SCREW_W])
    target = np.array([0, SLOT_POINT, gap + receiver.T * receiver.IN / 2])  # mid-lip, on the slot
    blockers = place(saddle_local(), rot) + screw_head(rot)
    pocket = pocket_local()
    for s in np.arange(0, 120, 0.25):
        off = seat + s * axis - rrot @ target
        if (place(pocket, rrot, off) ^ blockers).volume() < 1e-3:
            return off
    raise RuntimeError("no platform position clears the clamp")


def right_parts():
    rot = strut_frame()
    saddle = place(saddle_local(), rot)
    keeper = place(keeper_local(), rot)

    body, lo, hi = receiver_body()
    rrot = receiver_rot()
    roff = pod_placement(rot, rrot)
    pod = place(body, rrot, roff)

    # Webs: one per side rail, each a WEB_T thick hull from the rail's lower edge down to the
    # strip of the saddle's top directly beneath it. Only the part of the platform over the
    # clamp is joined; its ends overhang on its own lip and rails.
    _, _, _, inner, gap = receiver_dims()
    top = saddle_top(rot)
    corners = np.asarray(top.to_mesh().vert_properties)[:, :3]
    ys = (corners - roff) @ rrot[:, 1]                  # saddle top, along the platform's length
    y0, y1 = max(lo[1], ys.min() - PEDESTAL_MARGIN), min(hi[1], ys.max() + PEDESTAL_MARGIN)
    webs = Manifold()
    rail = receiver.T * receiver.IN
    for xc in (lo[0] + rail / 2, hi[0] - rail / 2):
        x0 = xc - WEB_T / 2
        band = place(Manifold.cube([WEB_T, 400, 400]).translate([x0, -200, -200]), rrot, roff)
        foot = top ^ band
        if foot.is_empty():
            continue
        strip = Manifold.cube([WEB_T, y1 - y0, 1]).translate([x0, y0, -POD_REAR])
        webs += (foot + place(strip, rrot, roff)).hull()

    # Channel under the lip, between the rails, open at both ends: the light's flange
    # slides through it, and grit can leave from the front or the rear.
    channel = place(Manifold.cube([2 * inner, hi[1] - lo[1] + 80, gap + POD_REAR]).translate(
        [-inner, lo[1] - 40, -POD_REAR]), rrot, roff)

    strut = place(along_u(strut_profile(LINER), 400), rot)
    access = place(screw_hole() + driver_access(), rot)
    webs -= channel
    saddle = (saddle + webs) + pod - strut - access
    return {"saddle": saddle, "keeper": keeper, "webs": webs, "pod": pod}, rot, rrot, roff


def light_envelope(rrot, roff):
    """Placeholder box where the SL-300 sits on the platform (estimated size)."""
    _, lo, hi = receiver_body()
    front = hi[1] + LIGHT_LENS_PROUD
    box_ = Manifold.cube([LIGHT_W, LIGHT_L, LIGHT_H]).translate([-LIGHT_W / 2, front - LIGHT_L, hi[2]])
    return place(box_, rrot, roff)


def label_cut(rrot, roff, text):
    return place(receiver.label(text), rrot, roff)


def face_down(m, normal):
    """Rotate so `normal` points at the bed, then sit the part on z = 0."""
    n = np.asarray(normal, float) / np.linalg.norm(normal)
    target = np.array([0, 0, -1.0])
    c = n @ target
    if c < -0.999999:
        r = np.diag([1.0, -1, -1])
    else:
        k = np.cross(n, target); K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        r = np.eye(3) + K + K @ K / (1 + c)
    m = place(m, r)
    lo = np.array(m.bounding_box())[:3]
    return m.translate([-lo[0], -lo[1], -lo[2]])


def to_bed(m, rot_deg):
    m = m.rotate(rot_deg)
    lo = np.array(m.bounding_box())[:3]
    return m.translate([-lo[0], -lo[1], -lo[2]])


def plate_frame():
    """Columns: across the board, up within the tilted plate, and the plate normal."""
    t = np.radians(TILT)
    return np.column_stack([[1.0, 0, 0], [0, np.sin(t), np.cos(t)], [0, -np.cos(t), np.sin(t)]])


def clamp_offset():
    """Where the right strut frame's origin sits in the schematic hanger, in world mm."""
    a = np.radians(STRUT_ANGLE)
    q0 = LENGTH / 2 * np.sin(a) + 8  # window face a little above the beam at the clamp
    return plate_frame() @ np.array([CLAMP_OFFSET, q0, 0])


def schematic_hanger(rot):
    """Both struts at their modelled cross-section, plus a box beam and pivot block."""
    pf = plate_frame()
    t0 = clamp_offset()
    right = place(along_u(strut_profile(), 400), rot).translate(list(t0))
    # The struts run from the beam's underside up to the apex, where the pivot block caps them.
    apex = HANGER_H - BEAM_H
    keep = place(box(0, 300, -BEAM_H, apex, -HALF_T, HALF_T), pf)
    right = right ^ keep
    struts = right + right.mirror([1, 0, 0])
    beam = place(box(-BEAM_HALF, BEAM_HALF, -BEAM_H, 0, -HALF_T, HALF_T), pf)
    block = place(box(-BLOCK_HALF, BLOCK_HALF, 0, apex, -HALF_T, HALF_T), pf)
    return struts + beam + block


# Blender-friendly colours for the assembly OBJ.
COLOURS = {"hanger_schematic": (0.55, 0.55, 0.58), "saddle": (0.80, 0.15, 0.12), "keeper": (0.15, 0.60, 0.35),
           "light_placeholder": (0.25, 0.45, 0.85)}


def write_obj(objects, path):
    """One OBJ with a named, coloured object per part (plus its .mtl)."""
    mtl = path.with_suffix(".mtl")
    with open(mtl, "w") as fh:
        for name, rgb in COLOURS.items():
            fh.write(f"newmtl {name}\nKd {rgb[0]} {rgb[1]} {rgb[2]}\n\n")
    with open(path, "w") as fh:
        fh.write(f"mtllib {mtl.name}\n")
        base = 1
        for name, (m, material) in objects.items():
            mesh = m.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3]
            f = np.asarray(mesh.tri_verts) + base
            fh.write(f"o {name}\nusemtl {material}\n")
            fh.writelines(f"v {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in v)
            fh.writelines(f"f {a} {b} {c}\n" for a, b, c in f)
            base += len(v)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out") / "truck"
    out.mkdir(parents=True, exist_ok=True)
    parts, rot, rrot, roff = right_parts()
    flip = np.diag([-1.0, 1, 1])
    t0 = clamp_offset()
    scene = {"hanger_schematic": (schematic_hanger(rot), "hanger_schematic")}
    for side in ("right", "left"):
        if side == "right":
            saddle, keeper, off, srot = parts["saddle"], parts["keeper"], roff, rrot
        else:
            saddle, keeper = parts["saddle"].mirror([1, 0, 0]), parts["keeper"].mirror([1, 0, 0])
            off, srot = flip @ roff, flip @ rrot @ flip  # mirrored roll, still a rotation
        # Engrave with each side's own (proper) rotation so the text reads correctly.
        saddle -= label_cut(srot, off, f"M{VERSION} {side[0].upper()}")
        tag = f"truck_mount_{side}_m{VERSION}"
        # Assembly: both sides on one schematic hanger; the left is the mirror image of the
        # right across the board centreline (x = 0).
        shift = t0 if side == "right" else flip @ t0
        receiver.write_stl(saddle.translate(list(shift)), out / f"assembly_m{VERSION}_{side}_saddle.stl")
        receiver.write_stl(keeper.translate(list(shift)), out / f"assembly_m{VERSION}_{side}_keeper.stl")
        scene[f"{side}_saddle"] = (saddle.translate(list(shift)), "saddle")
        scene[f"{side}_keeper"] = (keeper.translate(list(shift)), "keeper")
        scene[f"{side}_light_placeholder"] = (light_envelope(srot, off).translate(list(shift)), "light_placeholder")
        # Print orientations: saddle receiver-face down, keeper flat side down.
        receiver.write_stl(face_down(saddle, srot[:, 2]), out / f"{tag}_saddle.stl")
        kl = keeper_local() if side == "right" else keeper_local().mirror([1, 0, 0])
        receiver.write_stl(to_bed(kl, [90, 0, 0]), out / f"{tag}_keeper.stl")
        print(f"{tag}: saddle {saddle.volume() / 1000:.1f} cm^3, keeper {keeper.volume() / 1000:.1f} cm^3")
    receiver.write_stl(scene["hanger_schematic"][0], out / f"assembly_m{VERSION}_hanger_schematic.stl")
    write_obj(scene, out / f"assembly_m{VERSION}.obj")


if __name__ == "__main__":
    main()
