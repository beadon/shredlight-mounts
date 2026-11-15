#!/usr/bin/env python3
"""Clamp that holds the v7 receiver on a Radium Mach One S truck strut.

The hanger is a 22 mm plate tilted back 30 degrees from vertical (its front face
looks forward and down): measured on the front truck, and Radium's stated truck angle. Above each triangular window, a strut ("rake") rises at 45 degrees in
the plate's plane. The clamp wraps that strut:

  saddle  inverted U dropped over the strut from above; its front arm takes the
          screw, its rear arm ends in a hook pocket, and it carries the platform
  keeper  flat bar slid through the window from the front, under the strut; its
          rear end goes into the saddle's hook, its front end holds the nut
  1x M4 x 20 socket-head cap screw (ISO 4762) with an M4 nyloc nut, in front of the plate, fitted and
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
from manifold3d import CrossSection, FillRule, Manifold, OpType

import shredlight_mount as receiver

VERSION = 13

# --- Truck (measured by calipers unless noted) ---
PLATE_T = 21.8       # hanger plate thickness, front to back (21.81 caliper, front truck, 2026-11-13)
STRUT_H = 7.66       # strut, window face to skyward face, in the hanger's plane (caliper across the
                     # angled strut, front truck, 2026-11-13; m1-m7 used ~9 from a ruler photo)
WINDOW_FLAT = 11.0   # flat on the window-side face, front to back, between its chamfers
TOP_CHAMFER = 5.5    # skyward-face chamfers, front to back (~6 measured; modelled smaller)
CHAMFER_DEPTH = 1.5  # how far the chamfers cut into STRUT_H: unmeasured, kept small so they cannot bind
TILT = 30.0          # plate tilted back from vertical: measured on the FRONT truck with a phone
                     # inclinometer (reads 0 against a wall), board on level ground. Matches Radium's
                     # 30 degree truck angle and the m6 test fit (built for 45, aimed ~15 degrees high).
                     # The rear truck is not measured yet.
STRUT_ANGLE = 45.0   # strut angle in the plate's plane (photo estimate; head-on photos of 2026-11-13,
                     # corrected for the 30 degree tilt, give 44-47)

# --- Clamp ---
LINER = 0.25         # gap all round the strut: a snug PLA fit, no liner (m1-m11: 1.0 for a 1 mm rubber liner)
PARTING_GAP = 3.0    # gap between the saddle's front arm and the keeper so the screw can pull
LENGTH = 20.0        # keeper length along the strut; it must fit the ~35 mm window side
SADDLE_LENGTH = 30.0 # saddle length along the strut's top face (~55 mm free between beam and block)
SADDLE_T = 5.0       # saddle thickness over the skyward face
KEEPER_T = 5.0       # keeper thickness under the strut, inside the window (m1-m12: 6.0; its slot
                     # in the saddle's hook shrinks with it)
SCREW_D = 4.5        # M4 clearance (m6-m9: M5, 5.5); M4 matches the rest of the board
HEAD_D = 8.0         # M4 socket head (7.0) plus clearance; also the screw's and 3 mm hex key's path through the slot
SCREW_LEN = 20.0
NUT_AF = 7.3         # M4 nyloc across flats (7.0), plus clearance
NUT_H = 5.0
NUT_CEILING = 1.2    # keeper material left above the nut pocket; the nut stands proud of the
                     # keeper's underside by whatever doesn't fit (1.2 mm with a 5 mm keeper)
SCREW_EXTRA_REACH = NUT_H + 1.0  # m13: the screw must catch the whole nut, +1 mm, while the keeper
                     # still hangs at the bottom of its hook pocket, not only once it's pulled up.
                     # m12 printed: the screw only touched the nut.
PLATFORM_ANCHOR = 13.0  # where the platform's screw path starts, above KEEPER_TOP (m12's head
                     # seat, kept so the light doesn't move when the seat drops)
CHEEK = 3.0          # wall outside the screw
HOOK_ENGAGE = 5.0    # how far the keeper's rear end reaches into the hook pocket
HOOK_T = 3.0         # hook lip under the keeper's rear end
HOOK_WALL = 3.0      # pocket's outer wall
HOOK_CLEAR = 0.4     # sliding clearance around the keeper in the pocket

# --- Receiver platform ---
ROLL = 45.0          # platform rolled outboard about its length
PITCH_DOWN = 0.0     # extra nose-down tip for fine-tuning the aim (m7 was first made with
                     # TILT 45 + PITCH_DOWN 15, which gives the identical part)
SLOT_POINT = 12.0    # where the screw's path crosses the slot, mm from the receiver's centre
                     # toward its open end (the upper, 14.5 mm wide part of the slot)
POD_REAR = 4.0       # how far the side rails run below the pocket, into the pedestal
PEDESTAL_MARGIN = 3.0  # pedestal reaches this far past the saddle top, along the platform
WEB_T = 4.0          # thickness of each web joining a side rail to the saddle (m2-m8, SOLID_PEDESTAL off)
SOLID_PEDESTAL = True  # m9: fill between platform and saddle so the saddle's underside needs no supports
KEEPER_PATH_CLEAR = 0.6  # clearance round the keeper's slide-in path through the pedestal
CHANNEL_CHAMFER = 6.0  # m12: 45 deg chamfers this tall up from each rail into the channel roof, so
                       # the bridge over the flange channel is ~15 mm, not ~27 mm, and sits 6 mm clear of it (7 left a 1.8 mm wall)
# Optional picture engraved on the pedestal's tail-facing wall (the large flat side you see
# from behind the board). Off unless the image exists; it's kept out of the repo (art/ is
# gitignored) and the engraved parts are written as separate, gitignored *_art.stl files.
ART = {"image": "art/source.png", "crop": (200, 20, 1440, 1180), "threshold": 100,
       "stroke": 0.4, "depth": 0.6, "margin": 1.5}
HANGER_CLEAR = 2.0   # minimum gap to the (schematic) hanger in the assembly check

# Light envelope for the assembly preview only (estimated from a photo, not measured)
LIGHT_L, LIGHT_W, LIGHT_H = 78.0, 32.0, 30.0
LIGHT_LENS_PROUD = 5.0  # lens ahead of the platform's front edge

# --- Assembly preview only (schematic hanger; nothing here affects the printed parts) ---
CLAMP_OFFSET = 40.0  # clamp centre from the board centreline, measured across
HANGER_H = 65.0      # hanger laid flat, base of the beam to the apex (measured)
BEAM_H = 12.18       # bar below the windows: thicker section to the window cutout (caliper, 2026-11-13)
BEAM_HALF = 130.0    # axle beam half-length
BLOCK_HALF = 25.0    # pivot block half-width: the recess around the kingpin is 50.05 wide at most

HALF_T = PLATE_T / 2
FACE = HALF_T + LINER                         # clamp faces sit this far from the plate's centre
SCREW_W = FACE + HEAD_D / 2 + 0.5             # screw axis outside the plate's front face, far enough
                                              # that the (now lower) head sits wholly on the front arm (m1-m12: FACE + 1 + SCREW_D / 2)
FRONT_W = SCREW_W + SCREW_D / 2 + CHEEK       # front arm's outer face
BACK_W = FACE + HOOK_ENGAGE + HOOK_CLEAR + HOOK_WALL  # rear arm's outer face
KEEPER_TOP = -LINER  # keeper's upper face, pressing the window-side land
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


def nut_bottom():
    return KEEPER_BOTTOM - max(0.0, NUT_H - (KEEPER_T - NUT_CEILING))


def head_seat():
    # Clamped, the tip is 1 mm + SCREW_EXTRA_REACH past the nut; with the keeper hanging loose
    # at the bottom of the hook pocket it still runs right through the nut.
    return nut_bottom() - 1.0 - SCREW_EXTRA_REACH + SCREW_LEN


def driver_access():
    """The screw head's path: from its seat straight out along the screw axis."""
    return along_v(Manifold.cylinder(200, HEAD_D / 2, circular_segments=32)).translate([0, head_seat(), SCREW_W])


def saddle_local():
    top = STRUT_H + SADDLE_T
    s = box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, ARM_BOTTOM, top, -BACK_W, FRONT_W)
    # Rear arm continues down past the keeper and turns in under it: the hook.
    hook_bottom = KEEPER_BOTTOM - HOOK_CLEAR - HOOK_T
    s += box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, hook_bottom, ARM_BOTTOM, -BACK_W, -FACE)
    # Only HOOK_CLEAR above and below the keeper: the parting gap belongs under the front arm
    # alone (m1-m13 first build ran the pocket up to the arm's bottom edge too, so the slot was
    # 8.4 mm for a 5 mm keeper and the keeper's rear end could rock 3 mm).
    pocket = box(-LENGTH / 2 - HOOK_CLEAR, LENGTH / 2 + HOOK_CLEAR, KEEPER_BOTTOM - HOOK_CLEAR,
                 KEEPER_TOP + HOOK_CLEAR, -FACE - HOOK_ENGAGE - HOOK_CLEAR, -FACE + 1)
    # Removing the strut (and everything below its window face) leaves the top and two arms.
    under = box(-SADDLE_LENGTH, SADDLE_LENGTH, -50, 0, -FACE, FACE)
    return (s - along_u(strut_profile(LINER), SADDLE_LENGTH + 2) - under - pocket
            - screw_hole() - driver_access())


def saddle_outer_local():
    """The saddle's outer envelope (body plus hook), before anything is cut out of it."""
    top = STRUT_H + SADDLE_T
    hook_bottom = KEEPER_BOTTOM - HOOK_CLEAR - HOOK_T
    return (box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, ARM_BOTTOM, top, -BACK_W, FRONT_W)
            + box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, hook_bottom, ARM_BOTTOM, -BACK_W, -FACE))


def pedestal_voids_local():
    """What the solid pedestal must leave open, in the strut frame."""
    c = KEEPER_PATH_CLEAR
    # Everything below the arms' bottom edge, from the plate's rear face forward, along the whole
    # saddle: the plate and window, the strut's window-side chamfers, the keeper and nut, and the
    # space in front. (m9/m10 stopped this at the window face, leaving thin tabs in the chamfer
    # corners beyond the keeper's ends.)
    front = box(-200, 200, -200, ARM_BOTTOM, -FACE, 200)
    # The keeper's slot behind the plate, into the hook pocket (it slides in along -w).
    path = box(-LENGTH / 2 - c, LENGTH / 2 + c, KEEPER_BOTTOM - c, KEEPER_TOP + c,
               -FACE - HOOK_ENGAGE - HOOK_CLEAR, 200)
    return front + path


def keeper_local():
    # Flat top: presses only the window-side land, so unknown chamfer angles cannot interfere.
    k = box(-LENGTH / 2, LENGTH / 2, KEEPER_BOTTOM, KEEPER_TOP, -FACE - HOOK_ENGAGE, FRONT_W)
    nut = along_v(CrossSection.circle(NUT_AF / np.sqrt(3), 6).extrude(NUT_H)).translate([0, nut_bottom(), SCREW_W])
    return k - screw_hole() - nut


def receiver_rot(roll=None, pitch_down=None):
    """Receiver face up, slot's open end (Y) toward the nose, rolled outboard about Y, then
    tipped nose-down about X so the beam aims below level."""
    r = np.radians(ROLL if roll is None else roll)
    p = -np.radians(PITCH_DOWN if pitch_down is None else pitch_down)
    rx = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]])
    return rx @ np.array([[np.cos(r), 0, np.sin(r)], [0, 1, 0], [-np.sin(r), 0, np.cos(r)]])


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
    seat = rot @ np.array([0, KEEPER_TOP + PLATFORM_ANCHOR, SCREW_W])
    target = np.array([0, SLOT_POINT, gap + receiver.T * receiver.IN / 2])  # mid-lip, on the slot
    blockers = place(saddle_local(), rot) + screw_head(rot)
    # Everything open inside the receiver's outline (flange pocket, slot, the space between
    # the barbs) must stay clear, not just the pocket: m12's tighter fit first put the
    # saddle into the slot.
    body, blo, bhi = receiver_body()
    zone = Manifold.cube([bhi[0] - blo[0], bhi[1] - blo[1], bhi[2] + 0.001]).translate([blo[0], blo[1], 0])
    pocket = pocket_local() + (zone - body)
    for s in np.arange(0, 120, 0.25):
        off = seat + s * axis - rrot @ target
        if (place(pocket, rrot, off) ^ blockers).is_empty():
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

    if SOLID_PEDESTAL:
        # One solid block from the platform's back up to the saddle, instead of two webs, so
        # nothing on the saddle's underside overhangs. Everything that must stay open is cut
        # back out: the plate and window, the keeper's slot and its path in from the front.
        # Sweep the saddle straight toward the platform (straight down as printed), so the
        # block's sides are vertical on the bed. Over the flange channel (cut out below) it
        # leaves a flat roof spanning rail to rail: a bridge, not an overhang.
        outer = place(saddle_outer_local(), rot)
        down = rrot[:, 2]                                   # toward the platform's face
        sweep = (outer + outer.translate(list(150 * down))).hull()
        # Where the saddle overhangs the platform's outline, the block runs on down to the bed
        # (the platform's face plane), staying out of the space the light sits in.
        below_face = place(Manifold.cube([400, 400, 400]).translate([-200, -200, hi[2] - 400]), rrot, roff)
        webs = (sweep ^ below_face) - place(pedestal_voids_local(), rot)

    # Channel under the lip, between the rails, open at both ends: the light's flange
    # slides through it, and grit can leave from the front or the rear.
    channel = place(Manifold.cube([2 * inner, hi[1] - lo[1] + 80, gap + POD_REAR]).translate(
        [-inner, lo[1] - 40, -POD_REAR]), rrot, roff)

    strut = place(along_u(strut_profile(LINER), 400), rot)
    access = place(screw_hole() + driver_access(), rot)
    if SOLID_PEDESTAL:
        # Under the saddle the channel stops where the saddle's top slab begins, so its roof is
        # one flat bridge rather than the slab's sloping face (supports in there would be hard
        # to clear, and the flange slides through it). It still clears the flange gap.
        under_lip = place(Manifold.cube([2 * inner, hi[1] - lo[1], gap + POD_REAR]).translate(
            [-inner, lo[1], -POD_REAR]), rrot, roff)
        dip = saddle ^ under_lip   # only along the platform; past its ends there is no flange
        roof = -POD_REAR
        if not dip.is_empty():
            roof = float(((np.asarray(dip.to_mesh().vert_properties)[:, :3] - roff) @ rrot[:, 2]).max())
        assert roof < gap, "saddle reaches into the flange gap"
        channel = place(Manifold.cube([2 * inner, hi[1] - lo[1] + 80, gap - roof]).translate(
            [-inner, lo[1] - 40, roof]), rrot, roff)
        # Roof raised as a flat-topped gable: 45 deg chamfers up from each rail, then a short
        # bridge. As printed (face down) the chamfers are 45 deg walls that need no support.
        c = CHANNEL_CHAMFER
        span = hi[1] - lo[1] + 80
        gable = (Manifold.cube([2 * inner, span, 0.01]).translate([-inner, lo[1] - 40, roof])
                 + Manifold.cube([2 * (inner - c), span, 0.01]).translate([-inner + c, lo[1] - 40, roof - c])).hull()
        channel += place(gable, rrot, roff)
        # Inside the platform's outline the pedestal stops at the channel roof: the lip, slot,
        # barbs and rails come from v7 alone, unchanged.
        webs -= place(Manifold.cube([hi[0] - lo[0], hi[1] - lo[1], hi[2] + 1 - roof]).translate(
            [lo[0], lo[1], roof]), rrot, roff)
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


def art_wall_normal(rot, rrot):
    """Outward normal of the pedestal's tail-facing wall: the rear arm's outer face, swept
    toward the platform, so it lies square to the sweep direction."""
    down = rrot[:, 2]
    n = -rot[:, 2] - (-rot[:, 2] @ down) * down
    return n / np.linalg.norm(n)


def art_cut(saddle, n, mirror=False, print_up=None, nudge=0.0):
    """Cutter for the ART picture on the saddle's flat wall facing about `n`, upright as seen
    when mounted (world z is up), fitted inside the wall with ART["margin"] all round.
    `mirror` flips the picture left to right (the left mount's wall is the right's mirror image).
    `nudge` shifts the picture by that much (mm) on the wall, to step off an exact
    coincidence with an edge of the part, which leaves a pinched vertex in the mesh.
    `print_up` (world vector pointing away from the bed as printed): the wall prints vertical, so
    each groove's upper side would be a flat little ceiling that slicers support. Instead each
    groove's ceiling slopes down at 45 deg going into the wall, so it prints unsupported."""
    import artwork
    # The wall's exact normal: the largest flat area among the triangles facing within 5 deg of n.
    mesh = saddle.to_mesh()
    tri = np.asarray(mesh.vert_properties)[:, :3][np.asarray(mesh.tri_verts)]
    cr = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    area = np.linalg.norm(cr, axis=1) / 2
    nrm = cr / (2 * area[:, None] + 1e-12)
    near = (nrm @ n > np.cos(np.radians(5))) & (area > 1e-9)
    key = np.round(np.column_stack([nrm[near], np.einsum("ij,ij->i", nrm[near], tri[near, 0])]), 3)
    groups, inv = np.unique(key, axis=0, return_inverse=True)
    best = np.argmax(np.bincount(inv.ravel(), weights=area[near]))
    n = groups[best, :3] / np.linalg.norm(groups[best, :3])
    up = np.array([0, 0, 1.0]) - n[2] * n
    up /= np.linalg.norm(up)
    right = np.cross(up, n)                       # the viewer's right, looking at the wall
    frame = np.column_stack([right, up, n])
    local = saddle.transform(np.column_stack([frame.T, [0, 0, 0]]))
    plane = groups[best, 3]                       # the wall's own height, not the part's
    wall = local.slice(plane - 0.01).offset(-ART["margin"])
    # The wall is a square tipped about 45 deg as seen mounted, so try turning the picture
    # too and keep the angle that fits it largest. Fit on the ink itself (a drawing on a
    # diagonal leaves its bounding box mostly empty), then redraw the ink at the final size so the stroke stays
    # ART["stroke"] wide.
    nominal = 38.0
    mask, px = artwork.ink_mask(ART["image"], ART["crop"], ART["threshold"], ART["stroke"], width_mm=nominal)
    mask = mask[:, ::-1] if mirror else mask
    hull = artwork.mask_outline(mask, px).offset(0.3).simplify(0.1)   # the ink itself, slightly fattened
    lo, hi = np.array(wall.bounds()).reshape(2, 2)
    centre = (lo + hi) / 2
    best = (0, 0, centre)
    for ang in range(-60, 61, 10):
        h = hull.rotate(ang)
        for c in [centre + np.array([dx, dy]) for dx in (-3, 0, 3) for dy in (-3, 0, 3)]:
            fits = lambda k: (h.scale([k, k]).translate(list(c)) - wall).area() < 1e-6
            k_lo, k_hi = 0.1, 2.0
            for _ in range(12):
                k = (k_lo + k_hi) / 2
                k_lo, k_hi = (k, k_hi) if fits(k) else (k_lo, k)
            if k_lo > best[0]:
                best = (k_lo, ang, c)
    k, ang, c = best
    for _ in range(20):   # the redrawn ink is a hair bolder than the scaled-down one: shrink to fit
        mask, px = artwork.ink_mask(ART["image"], ART["crop"], ART["threshold"], ART["stroke"], width_mm=nominal * k)
        mask = mask[:, ::-1] if mirror else mask
        pic = artwork.mask_outline(mask, px).rotate(ang).translate(list(c + nudge))
        if (pic - wall).area() < 1e-6:
            break
        k *= 0.98
    else:
        raise RuntimeError("artwork does not fit the wall")
    print(f"  artwork turned {ang} deg,", end="")
    print(f" {nominal * k:.1f} mm wide before turning, {ART['depth']} mm deep")
    art_cut.last = (wall.offset(ART["margin"]), pic)   # for previews: the wall and the picture, flat
    straight = pic.extrude(ART["depth"] + 1).translate([0, 0, plane - ART["depth"]])
    cutter = straight
    if print_up is not None:
        # 45 deg ceilings: intersect the straight cut with a copy sheared toward the bed by
        # one mm per mm of depth. One clean boolean, a true slope, and no coincident walls (m13's
        # first try stacked thin slabs: the STL came out full of slivers and non-manifold edges).
        up2 = np.array([print_up @ right, print_up @ up])
        up2 /= np.linalg.norm(up2)
        shear = np.array([[1.0, 0, up2[0], -up2[0] * plane], [0, 1, up2[1], -up2[1] * plane], [0, 0, 1, 0]])
        deeper = pic.extrude(ART["depth"] + 1.02).translate([0, 0, plane - ART["depth"] - 0.01])
        cutter = straight ^ deeper.transform(shear)
    return cutter.transform(np.column_stack([frame, [0, 0, 0]]))


def check_mesh(m, name):
    """No pinched (non-manifold, once vertices are welded by position) edges and no zero-area
    triangles: what a slicer would otherwise 'repair'."""
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    f = np.asarray(mesh.tri_verts)
    tri = v[f].astype(np.float64)
    zero = int((np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) < 2e-10).sum())
    _, inv = np.unique(v, axis=0, return_inverse=True)
    fw = inv.ravel()[f]
    e = np.sort(np.concatenate([fw[:, [0, 1]], fw[:, [1, 2]], fw[:, [2, 0]]]), axis=1)
    _, count = np.unique(e, axis=0, return_counts=True)
    bad = int((count != 2).sum())
    print(f"  {name}: {len(f)} triangles, {zero} zero-area, {bad} non-manifold/open edges")
    return zero, bad


def check_receiver_unchanged(saddle, rrot, roff):
    """The receiver (lip, slot, barbs, rails, flange gap) must be exactly v7's: nothing added
    for the clamp may reach into it. m9's first build filled the slot this way."""
    body, lo, hi = receiver_body()
    local = saddle.translate(list(-roff)).transform(np.column_stack([np.linalg.inv(rrot), [0, 0, 0]]))
    zone = Manifold.cube([hi[0] - lo[0], hi[1] - lo[1], hi[2] + 0.001]).translate([lo[0], lo[1], 0])
    diff = ((local ^ zone) - body).volume() + ((body ^ zone) - local).volume()
    if diff > 0.01:
        raise RuntimeError(f"receiver differs from v7 by {diff:.2f} mm^3")


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out") / "truck"
    out.mkdir(parents=True, exist_ok=True)
    parts, rot, rrot, roff = right_parts()
    check_receiver_unchanged(parts["saddle"], rrot, roff)
    flip = np.diag([-1.0, 1, 1])
    t0 = clamp_offset()
    scene = {"hanger_schematic": (schematic_hanger(rot), "hanger_schematic")}
    scene_art = {}
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
        if Path(ART["image"]).exists():
            n = art_wall_normal(rot, rrot) * (np.array([-1.0, 1, 1]) if side == "left" else 1)
            for nudge in (0.0, 0.003, -0.003, 0.007, -0.007):
                cut = art_cut(saddle, n, mirror=side == "left", print_up=-srot[:, 2], nudge=nudge)
                art = saddle - cut
                # Keep only the solid itself: a sealed void (where the slope closes over a gap
                # between two close strokes) comes back as its own negative-volume shell;
                # dropping it fills it.
                art = Manifold.batch_boolean([p for p in art.decompose() if p.volume() > 1.0], OpType.Add) \
                    if len(art.decompose()) > 1 else art
                removed = saddle.volume() - art.volume()
                inside = (cut ^ saddle).volume()
                # Everything removed lies inside the cutter (less any sealed bubbles, filled
                # back in), the part is one piece, and its mesh is clean enough that slicers
                # needn't repair it (a nudge of a few microns steps off an exact coincidence).
                assert removed <= inside + 1e-2 and len(art.decompose()) == 1
                if check_mesh(art, f"{tag} artwork, nudged {nudge} mm") == (0, 0):
                    break
            else:
                raise RuntimeError("artwork mesh still has defects")
            receiver.write_stl(face_down(art, srot[:, 2]), out / f"{tag}_saddle_art.stl")
            scene_art[f"{side}_saddle"] = (art.translate(list(shift)), "saddle")
    receiver.write_stl(scene["hanger_schematic"][0], out / f"assembly_m{VERSION}_hanger_schematic.stl")
    write_obj(scene, out / f"assembly_m{VERSION}.obj")
    if Path(ART["image"]).exists():
        write_obj({**scene, **scene_art}, out / f"assembly_m{VERSION}_art.obj")


if __name__ == "__main__":
    main()
