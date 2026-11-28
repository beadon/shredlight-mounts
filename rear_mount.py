#!/usr/bin/env python3
"""Rear lights for the Radium Mach One S rear truck (prototype r7; r6 is the last one printed).

The rear truck's motors hide anything mounted on the hanger arms, so two SL-300 lights sit
side by side above the motors, facing the tail. Everything hangs off the oval hole ("hole A")
in the floor of the hanger's pocket, just in front of the charging port.

One printed part (r5; r2-r4 were two, bolted together):

    shoe       a short, solid block standing on a flat foot on the pocket floor, with a plug
               that fills hole A. It takes the rocking loads in compression on the foot.
    light bar  the two v7 receivers (unchanged, see shredlight_mount.py) on plates, joined
               by a solid bridge on top of the shoe.

It prints receiver faces down, with the shoe and its plug pointing up, and no supports.

Holding the shoe in the hole (the user's design): the plug fills the hole and drops straight in.
An M4 x 16 socket-head screw goes in from the nose side, angled down toward the tail at 30 deg
below level (r2, r3: 15), through a captive M4 hex nut in the shoe and out of the plug's rear face, under the
lip at the hole's rear end. The steel shank holds the shoe down; its end presses on the back of
the space under the lip, which pulls the plug tight against the hole's front wall. It can be
reached with the light bar fitted. (r2 also drew a hook-and-wedge version; it was dropped.)

r3: the nut pockets fit the user's plain M4 hex nuts (3.11 mm measured), not 5 mm nylocs.
r4: the shoe's nose end is 3 mm shorter, clear of the Ra button, and the screw is steeper to suit;
it's an M4 x 16, like the bar bolts, with its head hidden in the counterbore. The r4 shoe fit well.
r5: the r4 shoe and light bar as one part; the two bar bolts and their nuts are gone.
r6: the receivers are 56 mm apart (r5: 23), so the charging-port cover lifts straight up between the
lights and both its finger holes are open to the sky; the bridge stops short of the cover's front edge,
and a solid 16 mm 45 deg slope runs along the bar's nose end, under the lights, like the front mounts.
r5's lights sat over the finger holes and left 7.5 mm under the plates for a 12.4 mm thick cover.
r7: a split shoe (see the r7 constants below). Hole A is 7 mm deep, not 9. A lower part slides under the lip
and one M4, square to the surface and reached from above between the lights, pulls it up into a nut; a 45 deg
face pushes the upper part's V-nose forward. The angled screw above (r2-r6) is gone from the part; its code
stays for reference. main() writes the r7 part, the lower part and a test shoe without the light bar.

World frame: x to the rider's right, y toward the nose, z up (sky). Origin: centre of hole A,
on the surface around it. That surface faces the nose, tipped 30 deg up from flat.

Usage:  .venv/bin/python rear_mount.py [outdir]
"""
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, Manifold, OpType

import charge_cover as cc
import shredlight_mount as receiver
import truck_mount as tm

VERSION = 7

# --- Hole A, in the hanger pocket (user's measurements, 2026-11-15) ---
SURFACE_TILT = 30.0  # surface round the hole: tipped 30 deg from flat, facing the nose (inclinometer)
HOLE_W = 16.0        # across the board ("probably 16"; the photo readings were 15.4-16.6)
HOLE_L = 17.0        # along the surface, nose to tail
HOLE_D = 7.0         # deep, square to the surface; solid floor. Measured 7 (2026-11-26); r2-r6 used 9, so their plugs
                     # (8.4 deep) bottomed out 1.4 mm early, the shoe stood proud and rocked on the plug
LIP_T = 1.5          # the plate forming the lip at the hole's rear end (user's estimate 1.5-2; 2.0 looked thicker than
                     # the real metal in the r7 cutaway, so 1.5 from 2026-11-27; r2-r6 used 2.0)
LIP_OVER = 2.0       # r2-r6 only: how far the space under the lip reaches past the lip's edge ("try 2 to start")
# The space under the lip (user, 2026-11-27; r7 first assumed a full-width slot reaching 5.5 mm back, which was
# wrong): seen from above it is the box drawn round the hole's rear half. Side walls flush with the hole's
# sides, back wall LIP_BACK behind the hole's rear apex, square corners, floor level with the hole's floor;
# the front half has no lip. So under the lip there is a ~1 mm strip at the apex (the "apex gap") and two
# near-triangular "corner pockets", back-left and back-right (~4.1 mm from the hole's edge into each
# corner, on the diagonal). Its height is HOLE_D - LIP_T (lip 1.5-2.0, estimated). r7's lower part still
# fits: its outline is the hole moved LOW_SLIDE back, trimmed to this box, so it reaches into both pockets.
LIP_BACK = 1.0
# Only the rear end has a lip; the sides and the front are plain walls.

# --- Behind the hole: the step up to the charging port (user's measurements, 2026-11-15) ---
STEP_Z = 7.5         # the port's surface is 7.5 mm higher than the hole's surface, measured vertically
PORT_Y = -22.0       # port centre behind the hole's centre, measured level (a horizontal projection)
PORT_PLUG_D = 17.5   # charging plug as fitted, 17.5 across (the port itself is 14); it stands vertically
PORT_CLEAR = 2.0
MOTOR_D = 64.0       # motor can diameter (measured); the rest of the surroundings are rough estimates

# --- Plug ---
CLR = 0.2            # clearance per side, plug to hole
# V-block nose (test plug, 2026-11-24): r6 wobbles a fraction of a mm side to side, wearing the screw and
# the truck's lip. Its plug is the hole shrunk CLR all round, so the screw's push lands its nose on the
# hole's front wall at ONE point, and it can pivot about it. Shaving the nose's middle back NOSE_RELIEF
# more (fading out NOSE_SPAN deg either side of the centre line) moves the contact to two shoulders,
# ~41 deg either side, which pin it left/right like a rod in a V-block. The user confirmed the hole's
# front end is a smooth oval. Off (0) for r6; the test shoe uses it.
NOSE_RELIEF = 0.35
NOSE_SPAN = 45.0
# Crush ribs (second test shoe, with the V-block nose too, 2026-11-24): another way to stop the wobble. Half-round ribs up the
# plug's sides stand RIB_PROUD off the plug, so they squash RIB_PROUD - CLR into the hole's side walls
# as it goes in; the bottom RIB_LEAD of each tapers to flush, so they start in easily.
RIB_R = 0.6          # 1.2 mm wide
RIB_PROUD = 0.35     # 0.15 mm interference with the hole's wall
RIB_LEAD = 1.5
RIB_S = (-3.5, 3.5)  # along the hole (s, toward the tail) on each side: clear of the nose and the screw's exit
RUNOUT = 4.0         # the screw hole runs on this far past the screw's tip (r2-r6: 1), so its exit from the
                     # plug's rear face is fully open; at 1 mm a thin, tilted skin was left across the bottom of
                     # the exit (seen in the slicer, 2026-11-24). Used by the test shoe; r6 keeps 1.
PLUG_DEPTH = HOLE_D - 0.6  # stops short of the floor

# --- r7: split shoe (2026-11-26) ---
# The plug is split in two. The LOWER part goes into hole A first, on its own, and slides toward the tail
# under the lip. Then the shoe and light bar (the UPPER part, with the V-block nose, which tested better than
# crush ribs) drop in in front of it. One M4 screw, square to the surface, comes down through the upper part
# into a nut lying flat in the lower part. Tightening pulls the lower part up; a 45 deg face between the two
# turns that pull into a push apart, the lower part back under the lip and against the back of the space
# under it, the upper part's V-nose into the hole's front wall. Only plastic touches the lip (r2-r6: the steel
# screw's shank, which wore the lip). The screw is reached from above, between the lights.
LOW_FLOOR = 0.2      # gap under the lower part
TOE_GAP = 0.3        # the lower part's top under the lip, below the lip's underside (as LIP_T: if the lip is
                     # thicker than 1.5 the toe catches it as it slides back; if thinner, the screw pulls it up further)
LOW_REAR = 0.3       # gap behind the lower part's toe, to the back wall of the space under the lip
LOW_TOP = -0.8       # the lower part's top in front of the lip's edge (0.8 under the shoe, room to rise)
LOW_SLIDE = 5.6      # how far it slides toward the tail after it drops in
WEDGE_H = 2.5        # height of the 45 deg face, up to LOW_TOP
WEDGE_FRONT = -1.5   # the lower part's front face (s), below the 45 deg face
WEDGE_CLR = 0.15     # 45 deg face, lower to upper, square to the face
R7_SCREW_S = 4.2     # the screw's axis (s): the nut stays in front of the lip's edge, under 1.9 mm of plastic
R7_NUT_FLOOR = 0.6   # plastic under the nut
R7_SCREW_LEN = 16.0  # M4 x 16 socket head
R7_TIP_GAP = 0.5     # the screw's end above the hole's floor
R7_SLOT = 1.2        # the screw's hole in the upper part is a slot this long toward the tail: the lower part moves
                     # back relative to the upper part as the two push apart

# --- Shoe ---
SHOE_W = 24.0        # across the board: inside the pocket floor's two hex screws (~34 mm apart, estimated)
SHOE_FRONT = 7.5     # nose end (y): r3's 10.5 overhung the Ra button by ~3 mm (test fit, 2026-11-15)
SHOE_REAR = -7.0     # tail end below the step's top (the step's face is 7.36 behind the hole's centre)
SHOE_REAR_TOP = -10.0  # above the step's top the shoe reaches further back, short of the charging plug
STEP_GAP = 1.2       # gap over the step's top

# --- Hardware: M4 socket-head cap screws and plain M4 hex nuts ---
NUT_AF, NUT_T = 7.1, 3.18 + 0.3  # nut pocket: across flats and thickness. The user's plain M4 nuts measure
                                   # 6.90 across flats and 3.18 thick (2026-11-21; r3 used 3.11; r2: 5 mm nylocs)
# r6: across flats 7.3 -> 7.1, a snug fit. Blue Loctite bonds the screw to the nut, and with 0.3 mm of
# play the nut turned until its corners dug in and rounded out the PLA pocket, so the screw couldn't be
# backed out (the r5 unit had to be pried out of hole A). Snug, it bears on its flats instead.
BOLT_HOLE = 4.5      # clearance hole for M4
HEAD_BORE = 8.5      # counterbore for the M4 head (7 mm) and the hex key
# Screw under the lip
B_ANGLE = 60.0       # axis from the surface; in the world it rises 30 deg toward the nose (r3: 45, 15 deg),
                     # so the head sits inside the shortened shoe
B_LEN = 16.0         # M4 x 16 (r2-r4: x 20); tightened, its head sits ~1 mm inside the counterbore
B_RETRACT = 5.0      # backed off this far, its end is inside the plug, so the plug drops straight in
B_NUT_AT = 11.5

# --- Light bar: two v7 receivers, side by side, facing the tail ---
PLUG_GAP = 56.0      # gap between the receivers: the lights overhang them 0.7 mm, leaving 54.6 between the lights,
                     # so the 51.7 mm charging-port cover lifts out between them (r5: 23, for the plug alone)
CLEAR_Z = 15.0       # receivers' undersides (and the shoe's top) this high above the hole (bar C's top is 12)
PLATE_T = 7.0        # plate under each receiver; the flange channel's roof is cut into it
CHAMFER = 5.0        # 45 deg chamfers up into that roof, so the bridge over the channel is short
FRONT_Y = 10.0       # receivers' nose ends, this far ahead of the hole's centre (the deck is clear: user, 2026-11-15)
CROWN = 16.0         # r6: a solid 45 deg slope ahead of the bar's nose end, under the lights' overhang (the
                     # lights reach ~16 mm past it), to match the front mounts' ~16 mm 45 deg faces. Its top
                     # is flush with the receivers' faces, so it prints on the bed. Each receiver's tunnel runs on through
                     # it, so air still flows nose to tail under the lights.
SIDE_EXTRA = 1.5     # r6: each receiver's outer side thickened (the front mounts' RAIL_EXTRA), so the side
                     # slashes cut into added material: the receiver's own side wall is only ~1.6 mm

# --- Recessed racing stripes (r6) ---
STRIPE_D = 0.6       # recess depth: 3 layers at 0.2 mm
LEMANS_W = 6.0       # Le Mans twin stripes, nose to tail over the top between the lights and down the nose slope
LEMANS_GAP = 5.0     # between them
SLASH_W = 3.0        # three raked slashes on each outer side, measured nose to tail
SLASH_RAKE = 0.5     # each leans this far toward the nose per mm of height (top toward the nose)
SLASHES = [(-8.0, 10.0), (-2.0, 13.0), (4.0, 10.0)]   # (y at mid-height, height): the middle one longest

# --- The charging port's rubber cover (charge_cover.py), which must lift out with the bar fitted ---
COVER_GAP = 5.5      # hole A's rear edge to the cover's front edge (its flat middle), level (user, 2026-11-23)
COVER_CLEAR = 1.0    # the bridge's tail end, this far ahead of the cover's front corners

T_RAD = np.radians(SURFACE_TILT)
N = np.array([0.0, np.sin(T_RAD), np.cos(T_RAD)])    # out of the surface (up, toward the nose)
A = np.array([0.0, -np.cos(T_RAD), np.sin(T_RAD)])   # along the surface, toward the tail (and up)
HOLE_FRAME = np.column_stack([[-1.0, 0, 0], A, N])   # local (X, s, h) -> world; right-handed
HOLE_REAR_Y = (HOLE_L / 2 * A)[1]                    # hole A's rear edge, level from its centre
COVER_Y = HOLE_REAR_Y - COVER_GAP + cc.FRONT_DIP     # the cover's front corners (its local y = 0)
BRIDGE_REAR = round(COVER_Y + cc.outline().bounds()[3] + COVER_CLEAR, 2)   # r5: -10.2


def hole_section():
    return CrossSection.circle(HOLE_W / 2, 96).scale([1, HOLE_L / HOLE_W])


def at_hole(m):
    return tm.place(m, HOLE_FRAME)


def along(m, tip, d, t0=0.0):
    """A z-axis primitive moved so it starts t0 along the axis from `tip` and runs along d.
    Its local x stays perpendicular to d's plane (the hole's X, i.e. across the board)."""
    z = np.array([0, 0, 1.0])
    k = np.cross(z, d)
    s, c = np.linalg.norm(k), z @ d
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    r = np.eye(3) + K + K @ K * ((1 - c) / s ** 2) if s > 1e-9 else np.eye(3)
    return tm.place(m, r, np.asarray(tip) + t0 * np.asarray(d))


def nut_pocket(slot=30.0):
    """Hex nut pocket, axis z, centred; its corners point along +x, and a slot of the nut's
    width runs out along +x so the nut slides in from that side."""
    r = NUT_AF / np.sqrt(3)
    hexa = CrossSection.circle(r, 6)
    p = (hexa + hexa.translate([slot, 0])).hull()
    return p.extrude(NUT_T).translate([0, 0, -NUT_T / 2])


def rod(length, d, start=0.0, seg=24):
    return Manifold.cylinder(length, d / 2, circular_segments=seg).translate([0, 0, start])


# ---------------------------------------------------------------- parts

def plug_section(relief=0.0):
    """The plug's outline in hole-local (X, s) (s toward the tail): the hole shrunk CLR all round,
    with `relief` more taken off the middle of its nose (the V-block nose, see NOSE_RELIEF)."""
    if relief <= 0:
        return hole_section().offset(-CLR, circular_segments=64)
    b, a = HOLE_W / 2, HOLE_L / 2
    t = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    p = np.column_stack([b * np.cos(t), a * np.sin(t)])
    n = np.column_stack([a * np.cos(t), b * np.sin(t)])
    n /= np.linalg.norm(n, axis=1)[:, None]                      # outward normals
    phi = np.degrees(np.arccos(np.clip(-n[:, 1], -1, 1)))        # from the nose (-s)
    g = np.full_like(t, CLR)
    f = phi < NOSE_SPAN
    g[f] += relief * (1 + np.cos(np.radians(phi[f] * 180 / NOSE_SPAN))) / 2
    return CrossSection([p - g[:, None] * n])


def nose_contact(relief):
    """How far the screw pushes the plug toward the nose before it touches, and where (deg from the
    centre line), for a plug outline from plug_section."""
    b, a = HOLE_W / 2, HOLE_L / 2
    t = np.linspace(np.pi, 2 * np.pi, 3601)                      # the nose half (s < 0)
    n = np.column_stack([a * np.cos(t), b * np.sin(t)])
    n /= np.linalg.norm(n, axis=1)[:, None]
    phi = np.degrees(np.arccos(np.clip(-n[:, 1], -1, 1)))
    g = np.full_like(t, CLR)
    f = phi < NOSE_SPAN
    g[f] += relief * (1 + np.cos(np.radians(phi[f] * 180 / NOSE_SPAN))) / 2
    need = g / np.maximum(-n[:, 1], 1e-9)
    k = np.argmin(need)
    return need[k], phi[k]


def crush_ribs():
    """The crush ribs, in hole-local coordinates (see RIB_R)."""
    b, a = HOLE_W / 2, HOLE_L / 2
    ribs = Manifold()
    for side in (-1, 1):
        for s in RIB_S:
            t = np.arcsin(s / a)
            p = np.array([side * b * np.cos(t), a * np.sin(t)])
            n = np.array([side * a * np.cos(t), b * np.sin(t)]); n /= np.linalg.norm(n)
            c = p - (CLR + RIB_R - RIB_PROUD) * n                  # rib axis: its side stands RIB_PROUD off the plug
            inner = RIB_R - RIB_PROUD - 0.05                        # just inside the plug at the bottom (flush
                                                                    # faces leave the mesh with open edges)
            z0 = -PLUG_DEPTH + 0.05
            rib = Manifold.cylinder(PLUG_DEPTH - RIB_LEAD + 0.4, RIB_R, circular_segments=24).translate([0, 0, z0 + RIB_LEAD - 0.05])
            rib += Manifold.cylinder(RIB_LEAD, inner, RIB_R, circular_segments=24).translate([0, 0, z0])
            ribs += rib.translate([c[0], c[1], 0])
    return ribs


def plug_and_screw(relief=0.0, runout=1.0, ribs=False):
    """Plug and screw cutters, in hole-local coordinates."""
    q = plug_section(relief)
    plug = q.extrude(PLUG_DEPTH + 1).translate([0, 0, -PLUG_DEPTH])
    if ribs:
        plug += crush_ribs()
    a = np.radians(B_ANGLE)
    d = np.array([0.0, -np.cos(a), np.sin(a)])     # out of the hole toward the nose, rising
    edge = HOLE_L / 2                              # the lip's edge (the hole's rear end)
    # The shank's top passes just under the lip's edge; its end (a disc square to the axis)
    # stops 0.1 short of the back of the space under the lip.
    h_edge = -(2.0 + 0.2 + 2.0 / np.cos(a))        # axis height at the lip's edge (r2-r6 took the lip as 2.0 thick)
    s_tip = edge + LIP_OVER - 2.0 * np.sin(a) - 0.1
    tip = np.array([0.0, s_tip, h_edge - (s_tip - edge) * np.tan(a)])
    head = B_LEN
    cut = along(rod(head + runout, BOLT_HOLE, -runout), tip, d)
    cut += along(rod(60, HEAD_BORE, head - 0.5), tip, d)
    cut += along(nut_pocket(), tip, d, B_NUT_AT)
    screw = {"tip": tip, "d": d, "len": B_LEN, "set": 0.0, "loose": B_RETRACT}
    return plug, cut, screw


def shoe(relief=0.0, runout=1.0, ribs=False):
    plug, cut, screw = plug_and_screw(relief, runout, ribs)
    above = at_hole(Manifold.cube([200, 200, 100]).translate([-100, -100, 0]))
    w = SHOE_W / 2
    top = CLEAR_Z + 0.5                        # reaches 0.5 into the light bar's bridge: no coplanar seam
    body = Manifold.cube([SHOE_W, SHOE_FRONT - SHOE_REAR, top + 40]).translate([-w, SHOE_REAR, -40]) ^ above
    z0 = STEP_Z + STEP_GAP
    body += Manifold.cube([SHOE_W, SHOE_REAR - SHOE_REAR_TOP + 1, top - z0]).translate([-w, SHOE_REAR_TOP, z0])
    return body + at_hole(plug), screw, at_hole(cut)


def lower_pieces(grow=0.0):
    """r7: the lower part's two convex pieces, in hole-local coordinates (X, s, h), in place under the lip:
    the tall piece in front of the lip's edge (up to LOW_TOP, its front a 45 deg face) and the toe that runs
    under the lip. `grow` enlarges both, for the clearance the upper part keeps from them. Its outline seen
    from above is the plug's, moved LOW_SLIDE toward the tail, so it drops into the hole that far forward
    and slides back."""
    plan = plug_section().translate([0, LOW_SLIDE])
    oval = plug_section()                                   # in front of the lip's edge (CLR inside it)
    rear = HOLE_L / 2 + LIP_BACK - LOW_REAR
    toe_rect = CrossSection.square([HOLE_W - 2 * CLR, rear + 20]).translate([-HOLE_W / 2 + CLR, -20])
    bottom, toe_top = -HOLE_D + LOW_FLOOR, -LIP_T - TOE_GAP
    f, w = WEDGE_FRONT, WEDGE_H
    side = CrossSection([[(f, bottom), (40, bottom), (40, LOW_TOP), (f + w, LOW_TOP), (f, LOW_TOP - w)]])
    if grow:
        side = side.offset(grow, circular_segments=16)
    side = side.extrude(40).translate([0, 0, -20]).transform(
        np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))     # (s, h) sketch, extruded along X
    tall = (plan ^ oval).offset(grow, circular_segments=64).extrude(LOW_TOP - bottom + 2 * grow).translate([0, 0, bottom - grow]) ^ side
    toe = (plan ^ toe_rect).offset(grow, circular_segments=64).extrude(toe_top - bottom + 2 * grow).translate([0, 0, bottom - grow]) ^ side
    return [tall, toe]


def r7_screw():
    """The M4's axis (square to the surface) and its ends, hole-local."""
    tip = -HOLE_D + R7_TIP_GAP
    return {"s": R7_SCREW_S, "tip": tip, "seat": tip + R7_SCREW_LEN}


def lower_part():
    """r7: the lower part, with the nut pocket (slot out of its side, +X) and the screw's hole."""
    sc = r7_screw()
    low = Manifold.batch_boolean(lower_pieces(), OpType.Add)
    nb = -HOLE_D + LOW_FLOOR + R7_NUT_FLOOR
    nut = nut_pocket(slot=20.0).translate([0, sc["s"], nb + NUT_T / 2])
    hole = rod(40, BOLT_HOLE, -20).translate([0, sc["s"], 0])
    return low - nut - hole


def upper_plug():
    """r7: the upper part's plug, V-block nose, PLUG_DEPTH deep, clear of the lower part wherever it can
    move as the two push apart (it slides up and back along the 45 deg face)."""
    plug = plug_section(NOSE_RELIEF).extrude(PLUG_DEPTH + 1).translate([0, 0, -PLUG_DEPTH])
    keep = Manifold()
    for p in lower_pieces(WEDGE_CLR):
        keep += Manifold.hull(p + p.translate([0, 1.0, 1.0]))
    return plug - keep


def r7_cuts():
    """r7: the screw's slot through the upper part and the counterbore above it, out through the bar."""
    sc = r7_screw()
    def slot(d, h0, h1):
        c = rod(h1 - h0, d, h0, seg=32)
        return Manifold.hull(c.translate([0, sc["s"], 0]) + c.translate([0, sc["s"] + R7_SLOT, 0]))
    return slot(BOLT_HOLE, -10, sc["seat"]) + slot(HEAD_BORE, sc["seat"], 80)


def shoe_r7():
    above = at_hole(Manifold.cube([200, 200, 100]).translate([-100, -100, 0]))
    w = SHOE_W / 2
    top = CLEAR_Z + 0.5
    body = Manifold.cube([SHOE_W, SHOE_FRONT - SHOE_REAR, top + 40]).translate([-w, SHOE_REAR, -40]) ^ above
    z0 = STEP_Z + STEP_GAP
    body += Manifold.cube([SHOE_W, SHOE_REAR - SHOE_REAR_TOP + 1, top - z0]).translate([-w, SHOE_REAR_TOP, z0])
    return body + at_hole(upper_plug())


def rear_rot():
    """Receiver local -> world: slot's open end (+Y, the lens) toward the tail, face up."""
    return np.column_stack([[-1.0, 0, 0], [0, -1.0, 0], [0, 0, 1.0]])


def light_bar():
    _, lo, hi, inner, gap = tm.receiver_dims()
    body, lo, hi = tm.receiver_body()
    rail_bottom = -tm.POD_REAR
    plate = Manifold.cube([hi[0] - lo[0], hi[1] - lo[1], PLATE_T]).translate([lo[0], lo[1], rail_bottom - PLATE_T])
    roof = Manifold.hull(Manifold.cube([2 * inner, hi[1] - lo[1] + 2, 0.01]).translate([-inner, lo[1] - 1, rail_bottom])
                         + Manifold.cube([2 * (inner - CHAMFER), hi[1] - lo[1] + 2, 0.01]).translate(
                             [-inner + CHAMFER, lo[1] - 1, rail_bottom - CHAMFER]))
    one = body + plate - roof
    zr = CLEAR_Z - rail_bottom + PLATE_T       # receiver origin height so the plate's underside is at CLEAR_Z
    xc = PLUG_GAP / 2 + (hi[0] - lo[0]) / 2
    y0 = FRONT_Y + lo[1]                        # local -Y end (nose end) at FRONT_Y
    rot = rear_rot()
    offs = [np.array([s * xc, y0, zr]) for s in (1, -1)]
    recv = Manifold()
    for off in offs:
        recv += tm.place(one, rot, off)
    hw, rl = (hi[0] - lo[0]) / 2, hi[1] - lo[1]
    for sg in (1, -1):                          # the thickened outer sides (into the receiver by 0.5: no seam)
        recv += Manifold.cube([SIDE_EXTRA + 0.5, rl + 0.5, zr + hi[2] - CLEAR_Z]).translate(
            [xc + hw - 0.5 if sg > 0 else -xc - hw - SIDE_EXTRA, FRONT_Y - rl, CLEAR_Z])
    top = zr + rail_bottom                      # plate tops
    face = zr + hi[2]                           # receivers' faces (the bed, as printed)
    L = FRONT_Y - BRIDGE_REAR
    # The bridge runs up to the receivers' faces, so it doesn't hang across the gap as printed;
    # above the plates it stays between the rails, under where the lights sit.
    bridge = (Manifold.cube([PLUG_GAP + 2, L, top - CLEAR_Z]).translate([-PLUG_GAP / 2 - 1, BRIDGE_REAR, CLEAR_Z])
              + Manifold.cube([PLUG_GAP + 0.4, L, face - top + 0.5]).translate([-PLUG_GAP / 2 - 0.2, BRIDGE_REAR, top - 0.5]))
    # Over the shoe the bridge reaches back to the shoe's rear face, so the two meet flush: r6's first
    # cut left the shoe's top 1 mm past the bridge, a ledge the slicer supported. The cover's front
    # edge dips back to -12.9 across this width, so the cover still clears it.
    sb = min(SHOE_REAR_TOP, BRIDGE_REAR)
    bridge += Manifold.cube([SHOE_W, BRIDGE_REAR - sb + 0.5, face - CLEAR_Z]).translate([-SHOE_W / 2, sb, CLEAR_Z])
    c, f, w = CROWN, FRONT_Y, xc + hw + SIDE_EXTRA
    slope = CrossSection([[(f - 0.5, face - c - 0.5), (f + c, face), (f - 0.5, face)]]).extrude(2 * w)
    bridge += slope.transform(np.array([[0, 0, 1.0, -w], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
    # Keep each receiver's tunnel (the space under its lip and the channel roof below it) open nose
    # to tail through the slope, so air and water still pass under the lights.
    n = hi[1] - lo[1] + c + 4                  # through the whole receiver, so no end face sits inside its tunnel
    vent = Manifold.cube([2 * inner, n, gap - rail_bottom]).translate([-inner, lo[1] - c - 2, rail_bottom])
    y_ = lo[1] - c - 2
    vent += Manifold.hull(Manifold.cube([2 * inner, n, 0.01]).translate([-inner, y_, rail_bottom])
                          + Manifold.cube([2 * (inner - CHAMFER), n, 0.01]).translate([-inner + CHAMFER, y_, rail_bottom - CHAMFER]))
    vents = Manifold()
    for off in offs:
        vents += tm.place(vent, rot, off)
    return recv + bridge - vents - stripes(face, w), rot, offs, face


def stripes(face, w):
    """The recessed racing stripes: Le Mans twins over the top between the lights and on down the
    nose slope, and three raked slashes on each outer side (x = +-w)."""
    d, f, c = STRIPE_D, FRONT_Y, CROWN
    yz_to_x = np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])   # (y, z) sketch, extruded along +x
    k = 1 / np.sqrt(2)
    # slope sketch (x, s): s runs down the slope from its top edge; the third axis points into the part
    on_slope = np.array([[1.0, 0, 0, 0], [0, -k, -k, f + c], [0, k, -k, face]])
    cut = Manifold()
    for sg in (-1, 1):
        x0 = sg * (LEMANS_GAP + LEMANS_W) / 2 - LEMANS_W / 2
        y0 = min(SHOE_REAR_TOP, BRIDGE_REAR) - 1         # off the tail end of the bridge (and its part over the shoe)
        cut += Manifold.cube([LEMANS_W, f + c - y0 + 1, d + 1]).translate([x0, y0, face - d])
        cut += Manifold.cube([LEMANS_W, c * np.sqrt(2) + 1, d + 1]).translate([x0, -0.5, -1]).transform(on_slope)
    zc = CLEAR_Z + (face - CLEAR_Z) / 2
    side = CrossSection()
    for yc, h in SLASHES:
        lo, hi = (yc - SLASH_RAKE * h / 2, zc - h / 2), (yc + SLASH_RAKE * h / 2, zc + h / 2)
        side += CrossSection([[(lo[0] - SLASH_W / 2, lo[1]), (lo[0] + SLASH_W / 2, lo[1]),
                               (hi[0] + SLASH_W / 2, hi[1]), (hi[0] - SLASH_W / 2, hi[1])]])
    slab = side.extrude(d + 1).transform(yz_to_x)
    cut += slab.translate([w - d, 0, 0]) + slab.mirror([1, 0, 0]).translate([-w + d, 0, 0])
    return cut


def mount():
    """The whole printed part: shoe and light bar in one, minus the angled screw's hole, nut
    pocket, counterbore and the hex key's path. Also returns the screw and the light bar."""
    sh, screw, cut = shoe()
    bar, rot, offs, face = light_bar()
    # simplify: the hex key's path through the nose slope and the stripes leave slivers (zero-area triangles)
    return (sh + bar - cut).simplify(0.005), screw, cut, bar, rot, offs


def cover_placed():
    """The dummy charging-port cover in its recess, flush with the port's surface."""
    return cc.cover().translate([0, COVER_Y, STEP_Z])


def cover_lift_path():
    """Everything the cover passes through, lifted straight up out of its recess."""
    return cc.outline().extrude(150).translate([0, COVER_Y, STEP_Z - cc.THICK - 0.5])


def port_column():
    return Manifold.cylinder(200, PORT_PLUG_D / 2 + PORT_CLEAR, circular_segments=48).translate([0, PORT_Y, STEP_Z])


def hanger_schematic():
    """Schematic surroundings (ESTIMATES from photos, except the hole, the step, the port and bar C's height)."""
    floor = Manifold.cube([50, 52, 20]).translate([-25, -38, -20])
    hole = hole_section().extrude(HOLE_D + 1).translate([0, 0, -HOLE_D])
    # the space under the lip: the box round the hole's rear half (see LIP_BACK)
    under_lip = Manifold.cube([HOLE_W, HOLE_L / 2 + LIP_BACK, HOLE_D - LIP_T]).translate([-HOLE_W / 2, 0, -HOLE_D])
    floor = at_hole(floor - hole - under_lip)
    rear_edge = (HOLE_L / 2 * A)[1]
    step = Manifold.cube([50, 40, STEP_Z + 20]).translate([-25, rear_edge - 40, -20]) - at_hole(hole + under_lip)
    port_stub = Manifold.cylinder(6, 9, circular_segments=32).translate([0, PORT_Y, STEP_Z])
    recess = cc.outline().extrude(cc.THICK).translate([0, COVER_Y, STEP_Z - cc.THICK])   # the cover's recess
    housing = floor + step - recess + port_stub
    motors = Manifold()
    for s in (1, -1):
        motors += Manifold.cylinder(72, MOTOR_D / 2, circular_segments=48).rotate([0, 90, 0]).translate(
            [s * 38 - 36, -70, 8 - MOTOR_D / 2])
    bar = Manifold.cylinder(170, 10, circular_segments=32).rotate([0, 90, 0]).translate([-85, -105, 2])
    for s in (1, -1):
        bar += Manifold.cylinder(60, 10, circular_segments=32).rotate([90, 0, 0]).translate([s * 85, -45, 2])
    plates = Manifold()
    for s in (1, -1):
        plates += Manifold.cube([6, 100, 60]).translate([s * 81 - 3, -110, -50])
    wheels = Manifold()
    for s in (1, -1):
        wheels += Manifold.cylinder(55, 55, circular_segments=64).rotate([0, 90, 0]).translate([s * 125 - 27.5, -10, -20])
    return {"housing": housing, "motors": motors, "bar_c": bar, "motor_plates": plates, "wheels": wheels}


def light_boxes(rot, offs):
    _, lo, hi = tm.receiver_body()
    return [tm.place(Manifold.cube([tm.LIGHT_W, tm.LIGHT_L, tm.LIGHT_H]).translate(
        [-tm.LIGHT_W / 2, hi[1] + tm.LIGHT_LENS_PROUD - tm.LIGHT_L, hi[2]]), rot, off) for off in offs]


def screw_solid(screw, travel):
    """The screw itself (shank and head), `travel` back from its set position, in world coordinates."""
    t0 = screw["set"] + travel
    m = along(rod(screw["len"], 4.0, 0) + rod(4.0, 7.0, screw["len"]), screw["tip"], screw["d"], t0)
    return at_hole(m)


def mount_r7():
    """r7: the upper part (shoe, plug and light bar in one, with the screw's slot and counterbore)."""
    bar, rot, offs, face = light_bar()
    return (shoe_r7() + bar - at_hole(r7_cuts())).simplify(0.005), bar, rot, offs


def r7_screw_solid():
    sc = r7_screw()
    m = rod(sc["seat"] - sc["tip"], 4.0, sc["tip"]) + rod(4.0, 7.0, sc["seat"])
    return at_hole(m.translate([0, sc["s"], 0]))


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out") / "rear"
    out.mkdir(parents=True, exist_ok=True)
    sch = hanger_schematic()
    port = port_column()
    _, rot, offs, _ = light_bar()
    lights = light_boxes(rot, offs)
    world = list(sch.values())

    def report(name, m):
        assert len(m.decompose()) == 1, f"{name} is not one piece"
        hits = {k: (m ^ v).volume() for k, v in sch.items()}
        hits["charging plug"] = (m ^ port).volume()
        bad = {k: round(v, 2) for k, v in hits.items() if v > 0.01}
        print(f"{name}: {m.volume() / 1000:.1f} cm^3, overlaps: {bad or 'none'}")
        tm.check_mesh(m, name)

    for i, lb in enumerate(lights):
        print(f"  light {i}: bottom {lb.bounding_box()[2]:.1f} above the hole; "
              f"overlaps schematic {sum((lb ^ m).volume() for m in world):.1f}, plug column {(lb ^ port).volume():.1f}")
    part, _, _, _ = mount_r7()
    lower = at_hole(lower_part())
    report("rear mount (upper part)", part)
    report("lower part", lower)
    assert all((lb ^ part).is_empty() for lb in lights), "the part runs into a light"
    assert all((lb ^ at_hole(r7_cuts())).is_empty() for lb in lights), "the screw's counterbore runs into a light"
    # The lower part drops in LOW_SLIDE toward the nose, then slides back under the lip.
    A_ = A
    for dd in (0, 2, 5, 10, 20):
        assert (lower.translate(list(-LOW_SLIDE * A_ + dd * N)) ^ sch["housing"]).volume() < 0.01, "lower part can't drop in"
    for t in np.linspace(0, LOW_SLIDE, 23):
        assert (lower.translate(list(-t * A_)) ^ sch["housing"]).volume() < 0.01, "lower part can't slide under the lip"
    assert (lower.translate(list(1.0 * N)) ^ sch["housing"]).volume() > 0.01, "lower part isn't under the lip"
    print(f"  the lower part drops in {LOW_SLIDE} mm forward and slides back under the lip, which then holds it down")
    # Then the upper part drops straight in, in front of and over it.
    for dd in (0, 2, 5, 10, 20):
        assert (part.translate(list(dd * N)) ^ (sch["housing"] + lower)).volume() < 0.01, "upper part can't drop in"
    print("  the upper part drops straight in over it")
    screw = r7_screw_solid()
    assert (screw ^ sch["housing"]).is_empty() and (screw ^ part).volume() < 0.01 and (screw ^ lower).volume() < 0.01
    sc = r7_screw()
    nb = -HOLE_D + LOW_FLOOR + R7_NUT_FLOOR
    nut = at_hole(Manifold.cylinder(NUT_T - 0.3, 6.9 / np.sqrt(3), circular_segments=6).translate([0, sc["s"], nb]))
    lo_env = at_hole(Manifold.batch_boolean(lower_pieces(), OpType.Add))
    assert (nut - lo_env).volume() < 0.01, "the nut pokes out of the lower part"
    ceiling = LOW_TOP - (nb + NUT_T)
    print(f"  M4 x {R7_SCREW_LEN:.0f} square to the surface, end {R7_TIP_GAP} mm above the floor; nut under {ceiling:.1f} mm of plastic")
    exit_ = at_hole(r7_cuts()) ^ part.hull()
    print(f"  counterbore top reaches z {exit_.bounding_box()[5]:.1f}, between the lights (x 0)")
    path = cover_lift_path()
    assert (part ^ path).is_empty() and all((lb ^ path).is_empty() for lb in lights), "the cover can't lift out"
    receiver.write_stl(tm.face_down(part, [0, 0, 1.0]), out / f"rear_mount_r{VERSION}.stl")
    # Test shoe: the r7 upper part without the light bar, to try the split shoe in hole A before the whole
    # part. Prints like the r4 and test shoes: top face down, plug up.
    test = (shoe_r7() - at_hole(r7_cuts())).simplify(0.005)
    report("test shoe r7 (upper part, no light bar)", test)
    for dd in (0, 2, 5, 10, 20):
        assert (test.translate(list(dd * N)) ^ (sch["housing"] + lower)).volume() < 0.01
    assert (screw ^ test).volume() < 0.01
    receiver.write_stl(tm.face_down(test, [0, 0, 1.0]), out / f"rear_shoe_test_r{VERSION}.stl")
    # The lower part prints on its bottom face.
    receiver.write_stl(tm.face_down(lower, list(-N)), out / f"rear_lower_r{VERSION}.stl")
    scene = {"rear_hanger_schematic": (sch["housing"] + sch["motor_plates"], "hanger_schematic"),
             "motors_schematic": (sch["motors"], "hanger_schematic"),
             "bar_c_schematic": (sch["bar_c"], "hanger_schematic"),
             "wheels_schematic": (sch["wheels"], "hanger_schematic"),
             "rear_mount": (part, "saddle"),
             "lower_part": (lower, "keeper"),
             "screw": (screw, "hanger_schematic"),
             "charge_cover": (cover_placed(), "light_placeholder"),
             "charging_plug_column": (port ^ Manifold.cube([60, 60, 60]).translate([-30, -50, 0]), "light_placeholder")}
    for i, lb in enumerate(lights):
        scene[f"light_placeholder_{i}"] = (lb, "light_placeholder")
    tm.write_obj(scene, out / f"rear_assembly_r{VERSION}.obj")


if __name__ == "__main__":
    main()
