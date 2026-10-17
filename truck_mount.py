#!/usr/bin/env python3
"""Two-part clamp that holds the v7 receiver on a Radium Mach One S truck strut.

The hanger is a 22 mm plate tilted back 45 degrees (its front face looks forward
and down). Above each triangular window, a strut ("rake") rises at 45 degrees in
the plate's plane. The clamp wraps that strut:

  saddle  inverted U dropped over the strut from above; its arms run down both faces
          of the plate and it carries the wedge and the receiver pod
  keeper  flat bar slid through the window under the strut; its ends stick out past
          both plate faces, under the saddle's arms, and hold the nuts
  2x M4 x 40 socket-head screws with nyloc nuts, one in front of the plate, one behind

The pod holds the receiver with its slot vertical and its face pointing straight
forward, so the light shines level. The right side is modelled; left is mirrored.

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

VERSION = 1

# --- Truck (measured by calipers unless noted) ---
PLATE_T = 22.0       # hanger plate thickness
STRUT_H = 32.0       # strut, window face to skyward face
WINDOW_FLAT = 11.0   # flat land on the window-side face, between its chamfers
TOP_CHAMFER = 5.5    # skyward-face chamfers (~6 measured; modelled smaller so they cannot bind)
TILT = 45.0          # plate tilted back from vertical (assumed; check level on the print)
STRUT_ANGLE = 45.0   # strut angle in the plate's plane (photo estimate)

# --- Clamp ---
LINER = 1.0          # gap all round the strut for a 1 mm TPU / rubber liner
PARTING_GAP = 3.0    # gap between the saddle's arms and the keeper so the screws can pull
LENGTH = 20.0        # along the strut; the keeper must fit the ~35 mm window side
SADDLE_T = 5.0       # saddle thickness over the skyward face
KEEPER_T = 6.0       # keeper thickness under the strut, inside the window
SCREW_D = 4.4        # M4 clearance
HEAD_D = 8.0         # M4 socket head counterbore (also the driver access)
SCREW_LEN = 40.0
NUT_AF = 7.3         # M4 nyloc across flats, plus clearance
NUT_H = 5.0
CHEEK = 3.0          # wall outside each screw

# --- Receiver pod ---
POD_PAD = 3.0        # back sheet behind the receiver's open pocket
POD_CLEAR = 2.0      # minimum gap from the pod to the plate's front face
POD_TOP = 0.0        # pod top relative to the strut's skyward face (+ = higher)

HALF_T = PLATE_T / 2
SCREW_W = HALF_T + LINER + 1.0 + SCREW_D / 2  # screw axes sit just outside the plate faces
HALF_W = SCREW_W + SCREW_D / 2 + CHEEK
KEEPER_TOP = -LINER  # keeper's upper face, pressing the window-side land through the liner
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
    cw = (PLATE_T - WINDOW_FLAT) / 2  # 45-degree window-side chamfers
    ct = TOP_CHAMFER
    pts = [(0, -WINDOW_FLAT / 2), (0, WINDOW_FLAT / 2), (cw, HALF_T), (STRUT_H - ct, HALF_T),
           (STRUT_H, HALF_T - ct), (STRUT_H, -HALF_T + ct), (STRUT_H - ct, -HALF_T), (cw, -HALF_T)]
    cs = CrossSection([pts], FillRule.EvenOdd)
    return cs.offset(grow) if grow else cs


def box(u0, u1, v0, v1, w0, w1):
    return Manifold.cube([u1 - u0, v1 - v0, w1 - w0]).translate([u0, v0, w0])


def along_v(m):
    """Turn a Z-axis solid so it runs along local v (Y)."""
    return m.rotate([-90, 0, 0])


def screw_holes():
    holes = Manifold()
    for w in (-SCREW_W, SCREW_W):
        holes += along_v(Manifold.cylinder(200, SCREW_D / 2, circular_segments=32)).translate([0, -100, w])
    return holes


def head_seat():
    return KEEPER_TOP - KEEPER_T - 1.0 + SCREW_LEN  # screw tip 1 mm past the nut


def driver_access():
    acc = Manifold()
    for w in (-SCREW_W, SCREW_W):
        acc += along_v(Manifold.cylinder(200, HEAD_D / 2, circular_segments=32)).translate([0, head_seat(), w])
    return acc


def saddle_local():
    top = STRUT_H + SADDLE_T
    s = box(-LENGTH / 2, LENGTH / 2, ARM_BOTTOM, top, -HALF_W, HALF_W)
    # Removing the strut (and everything below its window face) leaves the top and two arms.
    under = box(-LENGTH, LENGTH, -50, 0, -HALF_T - LINER, HALF_T + LINER)
    return s - along_u(strut_profile(LINER), LENGTH + 2) - under - screw_holes() - driver_access()


def keeper_local():
    # Flat top: presses only the 9 mm land, so unknown chamfer angles cannot interfere.
    k = box(-LENGTH / 2, LENGTH / 2, KEEPER_TOP - KEEPER_T, KEEPER_TOP, -HALF_W, HALF_W)
    nuts = Manifold()
    for w in (-SCREW_W, SCREW_W):
        nut = CrossSection.circle(NUT_AF / np.sqrt(3), 6).extrude(NUT_H)
        nuts += along_v(nut).translate([0, KEEPER_TOP - KEEPER_T, w])
    return k - screw_holes() - nuts


def receiver_rot():
    """Receiver X -> world -X, slot (Y) -> up, face normal (Z) -> forward."""
    return np.array([[-1.0, 0, 0], [0, 0, 1], [0, 1, 0]])


def receiver_body():
    body = receiver.left_mount(**receiver.VERSIONS[7])
    lo, hi = np.array(body.bounding_box()).reshape(2, 3)
    pad = Manifold.cube([hi[0] - lo[0], hi[1] - lo[1], POD_PAD]).translate([lo[0], lo[1], -POD_PAD])
    return body + pad, lo, hi


def pod_placement(rot):
    """World offset of the receiver's local origin, keeping POD_CLEAR off the plate face."""
    _, lo, hi = receiver_body()
    half_h = (hi[1] - lo[1]) / 2
    cheek = rot @ np.array([0, (ARM_BOTTOM + STRUT_H + SADDLE_T) / 2, HALF_W])
    z_top = (rot @ np.array([0, STRUT_H, 0]))[2] + POD_TOP
    zc = z_top - half_h
    t = np.radians(TILT)
    # Plate front face: cos(t) y - sin(t) z = HALF_T; the pod's highest back corner is worst.
    y_back = (HALF_T + POD_CLEAR + np.sin(t) * z_top) / np.cos(t)
    return np.array([cheek[0], y_back + POD_PAD, zc])


def right_parts():
    rot = strut_frame()
    saddle = place(saddle_local(), rot)
    keeper = place(keeper_local(), rot)

    body, lo, hi = receiver_body()
    rrot, roff = receiver_rot(), pod_placement(rot)
    pod = place(body, rrot, roff)

    # Wedge: hull of the saddle's front cheek face and the pod's back sheet.
    cheek = place(box(-LENGTH / 2, LENGTH / 2, ARM_BOTTOM, STRUT_H + SADDLE_T,
                      HALF_W - 1, HALF_W), rot)
    back = place(Manifold.cube([hi[0] - lo[0], hi[1] - lo[1], 1]).translate([lo[0], lo[1], -POD_PAD]),
                 rrot, roff)
    wedge = (cheek + back).hull()

    strut = place(along_u(strut_profile(LINER), 400), rot)
    saddle = saddle + wedge + pod - strut - place(screw_holes() + driver_access(), rot)
    return {"saddle": saddle, "keeper": keeper}, rot, rrot, roff


def label_cut(rrot, roff, text):
    return place(receiver.label(text), rrot, roff)


def to_bed(m, rot_deg):
    m = m.rotate(rot_deg)
    lo = np.array(m.bounding_box())[:3]
    return m.translate([-lo[0], -lo[1], -lo[2]])


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out") / "truck"
    out.mkdir(parents=True, exist_ok=True)
    parts, rot, rrot, roff = right_parts()
    flip = np.diag([-1.0, 1, 1])
    for side in ("right", "left"):
        if side == "right":
            saddle, keeper, off = parts["saddle"], parts["keeper"], roff
        else:
            saddle, keeper = parts["saddle"].mirror([1, 0, 0]), parts["keeper"].mirror([1, 0, 0])
            off = flip @ roff
        # Same receiver orientation on both sides, so the text reads correctly on each.
        saddle -= label_cut(rrot, off, f"M{VERSION} {side[0].upper()}")
        tag = f"truck_mount_{side}_m{VERSION}"
        receiver.write_stl(saddle, out / f"{tag}_assembly_saddle.stl")
        receiver.write_stl(keeper, out / f"{tag}_assembly_keeper.stl")
        # Print orientations: saddle receiver-face down (forward -> bed), keeper flat side down.
        receiver.write_stl(to_bed(saddle, [-90, 0, 0]), out / f"{tag}_saddle.stl")
        kl = keeper_local() if side == "right" else keeper_local().mirror([1, 0, 0])
        receiver.write_stl(to_bed(kl, [90, 0, 0]), out / f"{tag}_keeper.stl")
        print(f"{tag}: saddle {saddle.volume() / 1000:.1f} cm^3, keeper {keeper.volume() / 1000:.1f} cm^3")
    strut = place(along_u(strut_profile(), 80), rot)
    receiver.write_stl(strut, out / "reference_strut_right.stl")


if __name__ == "__main__":
    main()
