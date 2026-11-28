#!/usr/bin/env python3
"""Clamp that holds the v7 receiver on a Radium Mach One S truck strut.

The hanger is a 22 mm plate tilted back 30 degrees from vertical (its front face
looks forward and down): measured on the front truck, and Radium's stated truck angle. Above each triangular window, a strut ("rake") rises at 45 degrees in
the plate's plane. The clamp wraps that strut:

  saddle  inverted U dropped over the strut from above; its front arm takes the
          screw, its rear arm ends in a hook pocket, and it carries the platform
  keeper  flat bar slid through the window from the front, under the strut; its
          rear end goes into the saddle's hook, its front end holds the nut
  1x M4 x 20 socket-head cap screw (ISO 4762) with a plain M4 nut (m17; m10-m16: nyloc), in front of the plate, fitted and
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

VERSION = 21

# --- Truck (measured by calipers unless noted) ---
PLATE_T = 21.8       # hanger plate thickness, front to back (21.81 caliper, front truck, 2026-11-13)
STRUT_H = 7.66       # strut, window face to skyward face, in the hanger's plane (caliper across the
                     # angled strut, front truck, 2026-11-13; m1-m7 used ~9 from a ruler photo)
WINDOW_FLAT = 11.0   # flat on the window-side face, front to back, between its chamfers
TOP_CHAMFER = 5.5    # skyward-face chamfers, front to back (~6 measured; modelled smaller)
TOP_CHAMFER_ANGLE = 40.0  # m21: the skyward-face chamfers slope 40 deg from the skyward face, so they cut
                     # TOP_CHAMFER * tan(40) = 4.6 mm into STRUT_H. Found with test strips at 20-40 deg
                     # (chamfer_gauge.py, 2026-11-28): the 40 deg strip is "a perfect fit". m1-m20 used
                     # CHAMFER_DEPTH (~15 deg), which left a wedge gap between the saddle and the strut, so
                     # the front arm bore on the strut's chamfer edge (the line m19's arm sheared along)
CHAMFER_DEPTH = 1.5  # the window-side chamfers' depth into STRUT_H: unmeasured, kept small so they cannot bind
TILT = 30.0          # plate tilted back from vertical: measured on the FRONT truck with a phone
                     # inclinometer (reads 0 against a wall), board on level ground. Matches Radium's
                     # 30 degree truck angle and the m6 test fit (built for 45, aimed ~15 degrees high).
                     # The rear truck is not measured yet.
STRUT_ANGLE = 45.0   # strut angle in the plate's plane (photo estimate; head-on photos of 2026-11-13,
                     # corrected for the 30 degree tilt, give 44-47)

# --- Clamp ---
LINER = 0.25         # gap all round the strut: a snug PLA fit, no liner (m1-m11: 1.0 for a 1 mm rubber liner)
PARTING_GAP = 3.0    # gap between the saddle's front arm and the keeper so the screw can pull
FRONT_ARM_DROP = 2.0 # m18: the front arm reaches this much further down, leaving PARTING_GAP - this
                     # (1 mm) over the keeper: the keeper clamps on the strut and has never closed the
                     # gap, so the arm can stop its front end bending up much sooner (user, 2026-11-22)
LENGTH = 20.0        # keeper length along the strut; it must fit the ~35 mm window side
SADDLE_LENGTH = 30.0 # saddle length along the strut's top face (~55 mm free between beam and block)
SADDLE_T = 5.0       # saddle thickness over the skyward face
KEEPER_T = 5.0       # keeper thickness under the strut, inside the window (m1-m12: 6.0; its slot
                     # in the saddle's hook shrinks with it)
SCREW_D = 4.5        # M4 clearance (m6-m9: M5, 5.5); M4 matches the rest of the board
HEAD_D = 8.0         # M4 socket head (7.0) plus clearance; also the screw's and 3 mm hex key's path through the slot
SCREW_LEN = 20.0
# m17: the m16 keepers (PETG) shattered round the nut on the road; the screw stayed in. The pocket
# was still a 5 mm nyloc's (a plain nut sat under the same 1.2 mm ceiling) with ~1.7 mm of wall
# outboard. Now a plain nut, snug, under a 3 mm ceiling, in a block with NUT_WALL all round it,
# and the keeper prints on its end so the screw's pull runs along the layers, not across them.
NUT_AF = 7.1         # plain M4 nut: the user's measure 6.90 across flats; snug, as rear r6 (m1-m16: 7.3, nyloc)
NUT_H = 3.18 + 0.3   # their nuts are 3.18 thick (m1-m16: 5.0, nyloc)
NUT_CEILING = 3.0    # keeper material above the nut pocket (m1-m16: 1.2); the nut block reaches
                     # below the keeper's underside by whatever doesn't fit (1.48 mm)
NUT_WALL = 3.0       # m17: block wall round the nut pocket, at its corners
SCREW_EXTRA_REACH = NUT_H + 1.0  # m13: the screw must catch the whole nut, +1 mm, while the keeper
                     # still hangs at the bottom of its hook pocket, not only once it's pulled up.
                     # m12 printed: the screw only touched the nut.
PLATFORM_ANCHOR = 13.0  # where the platform's screw path starts, above KEEPER_TOP (m12's head
                     # seat, kept so the light doesn't move when the seat drops)
CHEEK = 8.0          # front arm wall outside the screw (m1-m19: 3.0). m20: m19 right broke when the light's
                     # receiver was pushed nose-first into a post: the front arm sheared off along the line
                     # of the strut's top front chamfer. 8 mm gives that plane ~1.5x the area
KEEPER_CHEEK = 3.0   # keeper wall outside the screw: m17-m19's keeper, unchanged
HOOK_ENGAGE = 5.0    # how far the keeper's rear end reaches into the hook pocket
HOOK_T = 4.0         # hook lip under the keeper's rear end (m1-m15: 3.0; m16 adds 1 mm for the fin's groove)
# m16: the clamp still rattled a little fully seated. The hook pocket's inside corners along its
# floor are chamfered (the keeper's matching edges too), and a V fin under the keeper's rear end
# seats in a V groove in the hook lip: the screw's pull presses the keeper's end down into the V,
# which centres it side to side and takes up the play.
POCKET_CHAMFER = 1.5  # 45 deg chamfers along the pocket floor's deep edge and both end edges
FIN_DEPTH = 1.2      # V groove depth into the hook lip (90 deg included angle)
FIN_CLEAR = 0.1      # fin to groove, normal to the V's faces: a snug sliding fit
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
# m15: the m14 receiver broke where it ran past the pedestal on its 1.6 mm v7 walls alone
# (PLA, after a couple of rides), and its lower rail's rear corner wore against the axle beam.
BACKBONE = True      # solid block behind the whole receiver, rail to rail and end to end
BACKBONE_BRIDGE = 3.0  # backbone material over the channel roof's flat bridge
BACKBONE_ROOT = 6.0  # extra depth where the backbone leaves the pedestal, tapering to 0 at the nose
RAIL_EXTRA = 1.5 + 0.6  # each rail thickened outward by this much, full length, up to the face
                     # (m15-m18: 1.5; m19 adds the racing stripes' depth, so they cut into added material)
# m19: recessed racing stripes, as on the rear mount r6 (user, 2026-11-23): Le Mans twin stripes on the
# rail side that looks up and inboard (nose half, in front of the pedestal), raked slashes on the
# outboard rail side, near the nose. Vertical as printed, so their ceilings slope 45 deg (no supports).
STRIPE_D = 0.6       # recess depth: 3 layers at 0.2 mm
LEMANS_W = 6.0       # Le Mans twin stripes, running nose to tail
LEMANS_GAP = 5.0     # between them
SLASH_W = 3.0        # slash width, measured nose to tail
SLASH_RAKE = 0.5     # each leans this far toward the nose per mm of height
SLASHES = [(18.0, 10.0), (12.0, 13.0), (6.0, 10.0)]   # (mid-height distance behind the nose end, height)
BEAM_CLEAR = 5.0     # minimum gap from the receiver end of the part to the (schematic) axle beam
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
KEEPER_FRONT = SCREW_W + SCREW_D / 2 + KEEPER_CHEEK  # keeper's front end
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
    dt = TOP_CHAMFER * np.tan(np.radians(TOP_CHAMFER_ANGLE))   # m21 (m1-m20: CHAMFER_DEPTH)
    pts = [(0, -HALF_T + cw), (0, HALF_T - cw), (d, HALF_T), (STRUT_H - dt, HALF_T),
           (STRUT_H, HALF_T - ct), (STRUT_H, -HALF_T + ct), (STRUT_H - dt, -HALF_T), (d, -HALF_T)]
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
    # m18: the front arm (in front of the plate only, so the strut's chamfer corners stay open)
    # reaches FRONT_ARM_DROP further down over the keeper's front end.
    s += box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, ARM_BOTTOM - FRONT_ARM_DROP, ARM_BOTTOM, FACE, FRONT_W)
    # Rear arm continues down past the keeper and turns in under it: the hook.
    hook_bottom = KEEPER_BOTTOM - HOOK_CLEAR - HOOK_T
    s += box(-SADDLE_LENGTH / 2, SADDLE_LENGTH / 2, hook_bottom, ARM_BOTTOM, -BACK_W, -FACE)
    # Only HOOK_CLEAR above and below the keeper: the parting gap belongs under the front arm
    # alone (m1-m13 ran the pocket up to the arm's bottom edge too, so the slot was
    # 8.4 mm for a 5 mm keeper and the keeper's rear end could rock 3 mm).
    pocket = chamfered_floor(-LENGTH / 2 - HOOK_CLEAR, LENGTH / 2 + HOOK_CLEAR, KEEPER_BOTTOM - HOOK_CLEAR,
                             KEEPER_TOP + HOOK_CLEAR, -FACE - HOOK_ENGAGE - HOOK_CLEAR, -FACE + 1, POCKET_CHAMFER)
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


def chamfered_floor(u0, u1, v0, v1, w0, w1, c):
    """Box with 45 deg chamfers c along its floor (v = v0) edges at u0, u1 and w0 (the deep end);
    the floor's open end at w1 stays square."""
    return (box(u0, u1, v0 + c, v1, w0, w1) + box(u0 + c, u1 - c, v0, v1, w0 + c, w1)).hull()


def fin_groove():
    """m16: V groove in the hook lip's top face, along w, centred on u = 0, open at the pocket's mouth."""
    roof = KEEPER_BOTTOM - HOOK_CLEAR
    d = FIN_DEPTH
    w0 = -FACE - HOOK_ENGAGE - HOOK_CLEAR + POCKET_CHAMFER
    tri = CrossSection([[(-d - 1, roof + 1), (0, roof - d), (d + 1, roof + 1)]])
    # extrude along w: cross-section axes (u, v), extrusion -> w
    return tri.extrude(-FACE + 2 - w0).translate([0, 0, w0])


def fin_ridge():
    """m16: the keeper's V fin, under its rear end: the groove's shape less FIN_CLEAR all round."""
    roof = KEEPER_BOTTOM - HOOK_CLEAR
    apex = roof - FIN_DEPTH + FIN_CLEAR * np.sqrt(2)
    h = KEEPER_BOTTOM - apex + 0.5          # up into the keeper's body, so it joins solidly
    tri = CrossSection([[(-h, apex + h), (0, apex), (h, apex + h)]])
    w0 = -FACE - HOOK_ENGAGE + POCKET_CHAMFER + 0.5
    return tri.extrude(-FACE - w0).translate([0, 0, w0])


def keeper_local():
    # Flat top: presses only the window-side land, so unknown chamfer angles cannot interfere.
    # m16: its bottom edges along the sides and the rear end are chamfered to match the hook
    # pocket's (less HOOK_CLEAR), and it carries the V fin under its rear end.
    ck = POCKET_CHAMFER + HOOK_CLEAR * np.sqrt(2) - 2 * HOOK_CLEAR
    k = chamfered_floor(-LENGTH / 2, LENGTH / 2, KEEPER_BOTTOM, KEEPER_TOP, -FACE - HOOK_ENGAGE, KEEPER_FRONT, ck)
    k += fin_ridge()
    k += nut_block()
    return k - keeper_screw_hole() - nut_pocket()


def keeper_screw_hole():
    """m17: the screw hole with a 45 deg peak toward -u (up as the keeper prints, on its end), so
    its roof needs no support."""
    r = SCREW_D / 2
    tear = (CrossSection.circle(r, 32) + CrossSection.square([0.01, 0.01], center=True).translate([-r * np.sqrt(2), 0])).hull()
    return along_v(tear.extrude(200)).translate([0, -100, SCREW_W])


def nut_hex():
    """The nut pocket's outline in (u, w) about the screw axis, corners along w: printed on its end
    (u up), its roof is then a short flat bridge, not two shallow slopes."""
    return CrossSection.circle(NUT_AF / np.sqrt(3), 6).rotate(30)


def nut_pocket():
    return along_v(nut_hex().extrude(NUT_H)).translate([0, nut_bottom(), SCREW_W])


def nut_block():
    """m17: solid round the nut, NUT_WALL past its corners across the keeper (w) and its flats
    along it (u), from the nut's open end up to the keeper's top. Toward the keeper's lower end
    (-u, nearer the axle beam) it stops there; toward the upper end it runs to the end, which
    prints on the bed, so nothing overhangs."""
    r = NUT_AF / np.sqrt(3) + NUT_WALL
    return box(-NUT_AF / 2 - NUT_WALL, LENGTH / 2, nut_bottom(), KEEPER_TOP, SCREW_W - r, SCREW_W + r)


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


def backbone_local(roof, root_y):
    """m15, in the receiver's frame: a block behind the receiver from end to end, deep enough to
    cover the channel roof's bridge, tapering from BACKBONE_ROOT deeper at the pedestal's front
    face to nothing at the nose (no sharp step for a crack to start at), plus each rail
    thickened outward. Inside the receiver's outline the caller trims it back to the roof."""
    _, lo, hi, _, _ = receiver_dims()
    x0, x1 = lo[0] - RAIL_EXTRA, hi[0] + RAIL_EXTRA
    z0 = roof - CHANNEL_CHAMFER - BACKBONE_BRIDGE
    slab = Manifold.cube([x1 - x0, hi[1] - lo[1], hi[2] - z0]).translate([x0, lo[1], z0])
    root = Manifold.cube([x1 - x0, 1.0, hi[2] - z0 + BACKBONE_ROOT]).translate(
        [x0, root_y - 1.0, z0 - BACKBONE_ROOT])
    nose = Manifold.cube([x1 - x0, 1.0, hi[2] - z0]).translate([x0, hi[1] - 1.0, z0])
    return slab + (root + nose).hull()


def beam_keepout(rot, rrot, roff):
    """m15: the axle beam grown by BEAM_CLEAR, only where it meets the receiver end of the part
    (local z above the clamp), so the rails can't reach the beam when the light shakes."""
    t0 = clamp_offset()
    c = BEAM_CLEAR
    grown = place(box(-BEAM_HALF, BEAM_HALF, -BEAM_H - c, c, -HALF_T - c, HALF_T + c),
                  plate_frame()).translate(list(-t0))
    near_face = place(Manifold.cube([400, 400, 400]).translate([-200, -200, -10]), rrot, roff)
    return grown ^ near_face


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
        if BACKBONE:
            webs += place(backbone_local(roof, ys.max() + PEDESTAL_MARGIN), rrot, roff) \
                - place(pedestal_voids_local(), rot)
        webs -= place(Manifold.cube([hi[0] - lo[0], hi[1] - lo[1], hi[2] + 1 - roof]).translate(
            [lo[0], lo[1], roof]), rrot, roff)
    webs -= channel
    saddle = (saddle + webs) + pod - strut - access - place(fin_groove(), rot)
    if BACKBONE:
        saddle -= beam_keepout(rot, rrot, roff)
    inv = np.column_stack([rrot.T, -rrot.T @ roff])
    saddle -= place(stripes_local(saddle.transform(inv)), rrot, roff)
    return {"saddle": saddle, "keeper": keeper, "webs": webs, "pod": pod}, rot, rrot, roff


def stripes_local(saddle):
    """m19, in the receiver's frame (`saddle` given in that frame): the racing stripes' cutter.
    Each design is clipped to its rail side's exposed flat face, 1 mm in from its edges."""
    _, lo, hi, _, _ = receiver_dims()
    d = STRIPE_D
    sk = saddle.transform(np.array([[0, 1.0, 0, 0], [0, 0, 1.0, 0], [1.0, 0, 0, 0]]))  # (y, z, x): slice at x

    def face(xf, out):
        """The flat face at x = xf, facing +-x (out), as a (y, z) region with a 1 mm margin."""
        return (sk.slice(xf - out * 0.05) - sk.slice(xf + out * 0.05)).offset(-1.0)

    def cutter(cs, xf, out):
        """(y, z) sketch cut d deep into the face at x = xf. As printed (receiver face down, so local
        -z is up) each groove's upper side would be a flat ceiling; it slopes 45 deg instead."""
        straight = cs.extrude(d + 1)                                  # t: 0 at the floor, d at the face
        deeper = cs.extrude(d + 1.02).translate([0, 0, -0.01])
        shear = np.array([[1.0, 0, 0, 0], [0, 1.0, -1.0, d], [0, 0, 1.0, 0]])   # deeper -> toward the bed (+z)
        m = straight ^ deeper.transform(shear)
        return m.transform(np.array([[0, 0, out, xf - out * d], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))

    def band(cs_region):
        lo_, hi_ = np.array(cs_region.bounds()).reshape(2, 2)
        return lo_, hi_

    # Slashes on the outboard rail side, near the nose (local +y).
    xo, nose = hi[0] + RAIL_EXTRA, hi[1]
    r_out = face(xo, 1)
    near = r_out ^ CrossSection.square([30, 60]).translate([nose - 30, -30])
    zlo, zhi = band(near)[0][1], band(near)[1][1]
    zc = (zlo + zhi) / 2
    sl = CrossSection()
    for back, h in SLASHES:
        yc = nose - back
        a, b = (yc - SLASH_RAKE * h / 2, zc - h / 2), (yc + SLASH_RAKE * h / 2, zc + h / 2)
        sl += CrossSection([[(a[0] - SLASH_W / 2, a[1]), (a[0] + SLASH_W / 2, a[1]),
                             (b[0] + SLASH_W / 2, b[1]), (b[0] - SLASH_W / 2, b[1])]])
    cut = cutter(sl ^ r_out, xo, 1)
    # Le Mans twins on the inboard rail side (it looks up and inboard), nose to tail. That face is
    # only ~14 mm tall clear of the pedestal, so the pair is scaled down to fit it, 1 mm in from its edges.
    xi = lo[0] - RAIL_EXTRA
    r_in = face(xi, -1)
    (ylo, _), (yhi, _) = band(r_in)
    ends = [band(r_in ^ CrossSection.square([1, 60]).translate([y, -30])) for y in (ylo, yhi - 1)]
    zlo, zhi = max(e[0][1] for e in ends), min(e[1][1] for e in ends)   # clear of the face's notches
    k = min(1.0, (zhi - zlo - 0.6) / (2 * LEMANS_W + LEMANS_GAP))
    w, g, zc = LEMANS_W * k, LEMANS_GAP * k, (zlo + zhi) / 2
    lm = CrossSection()
    for sg in (-1, 1):
        lm += CrossSection.square([yhi - ylo + 2, w]).translate([ylo - 1, zc + sg * (g + w) / 2 - w / 2])
    stripes_local.lemans = (w, g)
    cut += cutter(lm ^ r_in, xi, -1)
    return cut


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
        # Print orientations: saddle receiver-face down, keeper on its end.
        receiver.write_stl(face_down(saddle, srot[:, 2]), out / f"{tag}_saddle.stl")
        kl = keeper_local() if side == "right" else keeper_local().mirror([1, 0, 0])
        # m17: on its upper end (where the nut block runs out), screw axis level, so the screw's pull
        # and the keeper's bending run along the layers (m16 printed flat and split across them).
        receiver.write_stl(to_bed(kl, [0, 90 if side == "right" else -90, 0]), out / f"{tag}_keeper.stl")
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
