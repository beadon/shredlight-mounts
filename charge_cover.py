#!/usr/bin/env python3
"""Dummy of the Radium Mach One S charging-port cover, for fitting the rear light bar around it.

The real cover is a rubber plug that fills the recess around the charging port, behind hole A.
Seen from above, its front (nose-side) edge is the long one, curved in slightly (a flat middle and
a curve up to each corner); its sides bow outward and narrow to a short flat back edge. Two finger
recesses in its top, near the front edge, are how it's pulled out, and the r5 light bar covers
them. This dummy is printed to check the fit in the recess, and placed in rear_mount.py's assembly
to plan a way out from under the light bar.

Measured with calipers (photos, 2026-11-21): see the constants. It sits flush with the surface
around it; the port hole underneath is blind, under a 4.00 mm top skin. The real cover's two front
curves differ slightly (likely a moulding quirk); the dummy makes them mirror images.

Frame: x across the board, y along the board, z up; the cover's top face at z = 0, its front
corners on y = 0, and the cover running back toward -y. rear_mount.py places it.

Usage:  .venv/bin/python charge_cover.py [outdir]
"""
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, Manifold, OpType

import shredlight_mount as receiver

VERSION = 4

# Width across the cover at distances back from its front corners (calipers, 2026-11-21)
WIDTHS = [(0.0, 51.70), (10.0, 47.83), (20.0, 43.6), (25.0, 37.0), (30.0, 22.0)]
BACK_FLAT = 14.0     # flat back edge (user, ~14)
DEPTH = 31.65        # front corners to the back edge (calipers)
FRONT_DIP = 3.2      # the front edge's flat middle sits this far behind its corners (user)
FRONT_FLAT = 24.0    # width of that flat middle (ESTIMATE from photos)
CORNER_R = 2.0       # outer corner rounding (user: 3 looked too chunky, 2026-11-21)
THICK = 12.4         # thickness at the front (calipers, read from the photo as ~12.4)
TAIL_THICK = 9.0     # thickness at the back: the top curves down toward it (user, approximate)
SKIN = 4.0           # the top skin, and the finger holes' floors (user)
# Underside: a "butterfly" stands down to the bottom, set well in from the outside edge (a moat
# round it, hollow up to the top skin, no rim): the outline inset by MOAT_SIDE at the sides and
# MOAT_END at the front and back, corners rounded, with a notch at the back between the two wings,
# NOTCH_W across where they meet the ring round the port hole. The wings are thin shells: below the
# top skin each finger hole widens out to within WING_WALL of the butterfly's edge, the notch and
# the port hole (the user, 2026-11-22: thick inner walls were what made v3-v4 look like a blob).
# (photos and calipers, 2026-11-22. v1-v2: separate oval wings and a free-standing ring, 13.08
# apart where the real one measures 11.23; v3 filled the underside to 2.5 from the edge and v4's
# first try grew the wings out from the finger holes: both "a blob", the wings lost.)
MOAT_SIDE = 6.0      # outside edge to the butterfly, sides (ESTIMATE from photos: ~35 across)
MOAT_END = 3.5       # outside edge to the butterfly, front and back (ESTIMATE: ~21.5 long)
WING_CORNER_R = 3.0  # the wings' rounded outer corners, seen from below (ESTIMATE)
WING_WALL = 1.5      # the wings' shell (ESTIMATE)
NOTCH_W = 11.23      # between the wings, where they meet the ring (calipers)
NOTCH_R = 2.0        # the notch's rounded inside corners (ESTIMATE)
RING_T = 1.5         # wall round the port hole, seen where the notch exposes it (calipers, 2026-11-22)
EDGE_R = 1.0         # the top face's outside edge is rounded (ESTIMATE)

# Finger recesses, mirror images, one each side. The outer wall follows the side FINGER_EDGE in
# from the cover's edge, the front wall follows the front edge FINGER_FROM in, and the inner walls
# run straight along the board, FINGER_GAP apart (user). Flat floors SKIN above the bottom (user),
# so they're ~8 deep at the front and shallower toward the back, following the top's curve.
FINGER_EDGE = 4.0    # outer wall in from the cover's side (user, 2026-11-21)
FINGER_FROM = 3.33   # front wall in from the front edge: the thinnest wall there (calipers, 2026-11-21)
FINGER_GAP = 17.0    # between the two recesses' inner walls (user, 2026-11-21)
FINGER_L = 18.12     # front to back (calipers, 2026-11-21; its rounded corners make it approximate)
FINGER_CORNER_R = 1.5  # rounded corners of the recess, seen from above (v1-v2's 3.0 made them
                       # slots; the real one's front end is 11.77 across, user 2026-11-22)

# Hole in the underside that the charging port fits into, on the centreline (calipers, 2026-11-21):
# 13.18 across, its centre 12.00 behind the front edge (taken as the edge's flat middle, straight
# in front of it). It is blind: the top skin over it is 4.00 thick. The rubber stretches over the
# port; the rigid print at 13.18 didn't go over it (v1, 2026-11-22), so the dummy's hole is opened
# up by CUP_CLEAR. The dummy is located by its outline, so a loose fit on the port is fine.
CUP_D_MEASURED = 13.18
CUP_CLEAR = 1.8
CUP_D = CUP_D_MEASURED + CUP_CLEAR
CUP_Y = FRONT_DIP + 12.0   # centre, behind the front corners


def half_width(d, front_extra=0.0):
    """Half the cover's width at d mm behind its front corners. The sides are straight edges
    through every measured width (front corner to the 20 mm width is all but one straight line),
    then to the flat back edge, BACK_FLAT wide, at DEPTH. front_extra widens the sharp front corner
    so that, rounded, it still measures WIDTHS[0] across."""
    pts = [(0.0, WIDTHS[0][1] + front_extra)] + WIDTHS[1:] + [(DEPTH, BACK_FLAT)]
    return np.interp(np.asarray(d, float), [p[0] for p in pts], [p[1] / 2 for p in pts])


def front_edge(x):
    """How far the front edge is behind the corners' line at x: FRONT_DIP across the flat middle,
    easing up to 0 at the corners along a half-cosine."""
    w, f = WIDTHS[0][1] / 2 + 0.5, FRONT_FLAT / 2
    t = np.clip((np.abs(x) - f) / (w - f), 0, 1)
    return FRONT_DIP * (1 + np.cos(np.pi * t)) / 2


def outline():
    """Top-view outline, corners rounded; the front is drawn wider until the rounded outline
    measures WIDTHS[0] across, as the calipers did."""
    extra = 0.0
    for _ in range(12):
        cs = sharp_outline(extra)
        lo, hi = np.array(cs.bounds()).reshape(2, 2)
        extra += WIDTHS[0][1] - (hi[0] - lo[0])
    return cs.simplify(0.01)          # drops the near-duplicate points rounding leaves (slivers in the mesh)


def sharp_outline(extra):
    ds = np.linspace(0, DEPTH, 60)
    right = [(float(half_width(d, extra)), -d) for d in ds]
    w = (WIDTHS[0][1] + extra) / 2
    xs = np.linspace(w, -w, 61)[1:-1]
    front = [(float(x), -float(front_edge(x))) for x in xs]
    # walk: front-right corner -> down the right side -> back edge -> up the left side -> front edge
    pts = right + [(-x, y) for x, y in right[::-1]] + front[::-1]
    p = np.array(pts)
    signed = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) / 2
    cs = CrossSection([pts if signed > 0 else pts[::-1]])
    return cs.offset(-CORNER_R, circular_segments=32).offset(CORNER_R, circular_segments=32)


def top_drop(y):
    """How far the top face is below its long-edge height at y (y = 0 to -DEPTH): a convex curve,
    flat at the long edge and falling to TAIL_THICK at the short edge."""
    return (THICK - TAIL_THICK) * (-y / DEPTH) ** 2


def above_top():
    """Everything above the curved top face, across the whole cover."""
    ys = np.linspace(1, -DEPTH - 1, 60)
    pts = [(y, -top_drop(min(0.0, max(y, -DEPTH - 1)))) for y in ys] + [(-DEPTH - 1, 5.0), (1, 5.0)]
    p = np.array(pts)
    signed = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) / 2
    prof = CrossSection([pts if signed > 0 else pts[::-1]])   # counter-clockwise, or it's empty
    # profile axes (y, z), extruded along x
    m = prof.extrude(100).transform(np.array([[0, 0, 1.0, -50], [1, 0, 0, 0], [0, 1, 0, 0]]))
    return m


def finger_recess(sign):
    """The recess on the +x side (sign 1) or the -x side (-1)."""
    if sign < 0:
        return finger_recess(1).mirror([1, 0, 0])    # an exact mirror image
    o = outline()
    # Within FINGER_EDGE of the sides is solid; within FINGER_FROM of the front edge is solid.
    near_front = CrossSection([list(map(tuple, np.array(
        [(float(x), -float(front_edge(x)) - FINGER_EDGE - 0.5) for x in np.linspace(40, -40, 161)]
        + [(-40.0, 10.0), (40.0, 10.0)])))])
    if near_front.area() == 0:
        near_front = CrossSection([[(float(x), -float(front_edge(x)) - FINGER_EDGE - 0.5) for x in np.linspace(-40, 40, 161)]
                                   + [(40.0, 10.0), (-40.0, 10.0)]])
    side_band = (o - o.offset(-FINGER_EDGE, circular_segments=48)) - near_front
    inside = o.offset(-FINGER_FROM, circular_segments=48) - side_band
    # the front wall follows the front edge FINGER_FROM in (thinner than the sides' FINGER_EDGE)
    xs = np.linspace(-40, 40, 161)
    front = [(float(x), -float(front_edge(x)) - FINGER_FROM) for x in xs]
    p = np.array(front + [(40.0, -60.0), (-40.0, -60.0)])
    signed = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) / 2
    behind = CrossSection([list(map(tuple, p)) if signed > 0 else list(map(tuple, p[::-1]))])
    x0 = FINGER_GAP / 2
    back = -(front_edge(x0) + FINGER_FROM + FINGER_L)     # FINGER_L measured along the inner wall
    rows = CrossSection.square([60, -back]).translate([x0, back])
    c = FINGER_CORNER_R
    shape = ((inside ^ behind) ^ rows).offset(-c, circular_segments=32).offset(c, circular_segments=32).simplify(0.01)
    if sign < 0:
        shape = shape.mirror([1, 0])
    # Below the skin the hole fills its wing, leaving WING_WALL to the butterfly's edge and the port
    # hole, and NOTCH_W / 2 + WING_WALL from the centreline. Through the top skin it morphs from the
    # opening to that, in steps of STEP: the parts of the opening outside the wing retreat while the
    # wing's interior grows in.
    inner = NOTCH_W / 2 + WING_WALL
    side = CrossSection.square([40, 60]).translate([inner, -50])
    if sign < 0:
        side = side.mirror([1, 0])
    wing = (body().offset(-WING_WALL, circular_segments=32) ^ side) \
        - CrossSection.circle(CUP_D / 2 + WING_WALL, 64).translate([0, -CUP_Y])
    floor, step, grow = -THICK + SKIN, 0.4, 8.0
    zs = list(np.arange(0.0, -SKIN, -step)) + [-SKIN]
    layers = [wing.simplify(0.01).extrude(-SKIN - floor).translate([0, 0, floor])]
    for k in range(len(zs) - 1):
        z_top, z_bot = zs[k], zs[k + 1]
        t = -z_top / SKIN                       # 0 at the top face, toward 1 at the skin's underside
        sec = (shape ^ wing.offset(grow * (1 - t), circular_segments=32)) + \
            (wing ^ shape.offset(grow * t, circular_segments=32))
        top = 1.0 if k == 0 else z_top
        sec = sec.offset(0.05).offset(-0.05)    # merge pieces that only touch (pinched mesh edges)
        layers.append(sec.simplify(0.01).extrude(top - z_bot).translate([0, 0, z_bot]))
    return Manifold.batch_boolean(layers, OpType.Add)


def body():
    """The butterfly seen from below: the outline inset by the moat, its corners rounded, minus the
    notch between the wings behind the port ring (rounded where it meets the ring)."""
    o = outline()
    ds = np.linspace(-10, DEPTH + 10, 90)
    right = [(float(half_width(np.clip(d, 0, DEPTH))) - MOAT_SIDE, -float(d)) for d in ds]
    sides = CrossSection([right + [(-x, y) for x, y in right[::-1]]])
    if sides.area() == 0:
        sides = CrossSection([(right + [(-x, y) for x, y in right[::-1]])[::-1]])
    b = o.offset(-MOAT_END, circular_segments=48) ^ sides
    ring = CrossSection.circle(CUP_D / 2 + RING_T, 64).translate([0, -CUP_Y])
    notch = CrossSection.square([NOTCH_W, DEPTH]).translate([-NOTCH_W / 2, -CUP_Y - DEPTH])
    b = b - (notch - ring)
    r = WING_CORNER_R
    b = b.offset(-r, circular_segments=32).offset(r, circular_segments=32)       # round the corners
    b = b.offset(NOTCH_R, circular_segments=32).offset(-NOTCH_R, circular_segments=32)  # and inside ones
    return b.simplify(0.01)


def underside_cavity():
    """The hollow underside: everything round the body, out past the outside edge, up to SKIN under
    the top (flat here; cover() bends it down with the top)."""
    region = outline().offset(1.0, circular_segments=48) - body()
    return region.simplify(0.01).extrude(THICK + 1 - SKIN).translate([0, 0, -THICK - 1])


def top_plate():
    """The cover as a flat-topped prism with the top face's outside edge rounded by EDGE_R (in
    steps, each inset by the round at its height)."""
    o = outline()
    parts = [o.extrude(THICK - EDGE_R).translate([0, 0, -THICK])]
    n = 6
    for i in range(n):
        z0, z1 = -EDGE_R + EDGE_R * i / n, -EDGE_R + EDGE_R * (i + 1) / n
        dz = z1 + EDGE_R              # height above the start of the round, 0..EDGE_R
        inset = EDGE_R - np.sqrt(EDGE_R ** 2 - dz ** 2)
        parts.append(o.offset(-inset, circular_segments=32).simplify(0.01).extrude(z1 - z0 + 0.001).translate([0, 0, z0]))
    return Manifold.batch_boolean(parts, OpType.Add)


def bend_top(xyz):
    """Warp: bring the flat-topped cover's top face, and the top skin under it, down by top_drop(y),
    so the top curves toward the back. The finger holes' floors (and everything below them) stay
    flat; between the floors and the skin the drop eases in."""
    xyz = np.array(xyz, dtype=float)
    floor, skin = -THICK + SKIN, -SKIN
    w = np.clip((xyz[:, 2] - floor) / (skin - floor), 0.0, 1.0)
    xyz[:, 2] -= top_drop(np.clip(xyz[:, 1], -DEPTH, 0.0)) * w
    return xyz


def cover():
    """Built flat-topped, refined, then bent (a boolean cut with a curved surface left slivers that
    slicers had to repair)."""
    c = top_plate()
    for s in (1, -1):
        c -= finger_recess(s)
    c -= underside_cavity()
    c -= Manifold.cylinder(THICK - SKIN + 1, CUP_D / 2, circular_segments=48).translate([0, -CUP_Y, -THICK - 1])
    return c.simplify(0.01).refine_to_length(1.0).warp_batch(bend_top).simplify(0.001)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out") / "rear"
    out.mkdir(parents=True, exist_ok=True)
    c = cover()
    # Prints top face down. Bottom down, the top skin overhangs the feet all round and needs
    # support under nearly all of it; top down, the hollow opens upward and only the back of the
    # curved top (up to ~3.4 mm off the bed) needs a little (slice_check.py, 2026-11-21).
    top_down = c.mirror([0, 0, 1])
    lo = np.array(top_down.bounding_box())[:3]
    receiver.write_stl(top_down.translate(list(-lo)), out / f"dummy_charge_cover_v{VERSION}.stl")
    lo, hi = np.array(c.bounding_box()).reshape(2, 3)
    print(f"dummy cover v{VERSION}: {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm, "
          f"{c.volume() / 1000:.1f} cm^3")


if __name__ == "__main__":
    main()
