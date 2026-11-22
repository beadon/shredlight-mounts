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

VERSION = 1

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
# The underside is hollow up to the top skin, leaving thin walls standing down to the bottom: the
# outer rim, the finger holes' walls (the "butterfly" wings seen from below) and a ring round the
# port hole (photo, 2026-11-21; thicknesses ESTIMATES)
RIM_T = 1.5          # outer rim
FINGER_WALL_T = 1.5  # round each finger hole
RING_T = 2.0         # round the port hole

# Finger recesses, mirror images, one each side. The outer wall follows the side FINGER_EDGE in
# from the cover's edge, the front wall follows the front edge FINGER_FROM in, and the inner walls
# run straight along the board, FINGER_GAP apart (user). Flat floors SKIN above the bottom (user),
# so they're ~8 deep at the front and shallower toward the back, following the top's curve.
FINGER_EDGE = 4.0    # outer wall in from the cover's side (user, 2026-11-21)
FINGER_FROM = 3.33   # front wall in from the front edge: the thinnest wall there (calipers, 2026-11-21)
FINGER_GAP = 17.0    # between the two recesses' inner walls (user, 2026-11-21)
FINGER_L = 18.12     # front to back (calipers, 2026-11-21; its rounded corners make it approximate)
FINGER_CORNER_R = 3.0  # rounded corners of the recess, seen from above (ESTIMATE)

# Hole in the underside that the charging port fits into, on the centreline (calipers, 2026-11-21):
# 13.18 across, its centre 12.00 behind the front edge (taken as the edge's flat middle, straight
# in front of it). It is blind: the top skin over it is 4.00 thick.
CUP_D = 13.18
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
    return cs


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
    shape = ((inside ^ behind) ^ rows).offset(-c, circular_segments=32).offset(c, circular_segments=32)
    if sign < 0:
        shape = shape.mirror([1, 0])
    floor = -THICK + SKIN
    return shape.extrude(1 - floor).translate([0, 0, floor])


def underside_cavity():
    """The hollow underside: inside the outer rim, outside the finger holes' walls (the "butterfly"
    wings seen from below) and the ring round the port hole, up to SKIN under the curved top."""
    o = outline()
    fingers = Manifold.batch_boolean([finger_recess(s) for s in (1, -1)], OpType.Add).project()
    region = (o.offset(-RIM_T, circular_segments=48) - fingers.offset(FINGER_WALL_T, circular_segments=48)
              - CrossSection.circle(CUP_D / 2 + RING_T, 64).translate([0, -CUP_Y]))
    tall = region.extrude(THICK + 2).translate([0, 0, -THICK - 1])
    return tall - above_top().translate([0, 0, -SKIN])


def cover():
    c = outline().extrude(THICK).translate([0, 0, -THICK]) - above_top()
    for s in (1, -1):
        c -= finger_recess(s)
    c -= underside_cavity()
    cup_deep = THICK - top_drop(-CUP_Y) - SKIN       # leaves the measured top skin over the port
    c -= Manifold.cylinder(cup_deep + 1, CUP_D / 2, circular_segments=48).translate([0, -CUP_Y, -THICK - 1])
    return c


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out") / "rear"
    out.mkdir(parents=True, exist_ok=True)
    c = cover()
    # Prints on its flat bottom; the port hole's roof is a short (13 mm) bridge.
    receiver.write_stl(c.translate([0, 0, THICK]), out / f"dummy_charge_cover_v{VERSION}.stl")
    lo, hi = np.array(c.bounding_box()).reshape(2, 3)
    print(f"dummy cover v{VERSION}: {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm, "
          f"{c.volume() / 1000:.1f} cm^3")


if __name__ == "__main__":
    main()
