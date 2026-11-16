#!/usr/bin/env python3
"""Rear lights for the Radium Mach One S rear truck (prototype r5).

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

World frame: x to the rider's right, y toward the nose, z up (sky). Origin: centre of hole A,
on the surface around it. That surface faces the nose, tipped 30 deg up from flat.

Usage:  .venv/bin/python rear_mount.py [outdir]
"""
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, Manifold

import shredlight_mount as receiver
import truck_mount as tm

VERSION = 5

# --- Hole A, in the hanger pocket (user's measurements, 2026-11-15) ---
SURFACE_TILT = 30.0  # surface round the hole: tipped 30 deg from flat, facing the nose (inclinometer)
HOLE_W = 16.0        # across the board ("probably 16"; the photo readings were 15.4-16.6)
HOLE_L = 17.0        # along the surface, nose to tail
HOLE_D = 9.0         # deep, square to the surface; solid floor
LIP_T = 2.0          # the plate forming the lip at the hole's rear end is ~2 mm thick
LIP_OVER = 2.0       # how far the space under the lip reaches past the lip's edge ("try 2 to start")
# Only the rear end has a lip; the sides and the front are plain walls.

# --- Behind the hole: the step up to the charging port (user's measurements, 2026-11-15) ---
STEP_Z = 7.5         # the port's surface is 7.5 mm higher than the hole's surface, measured vertically
PORT_Y = -22.0       # port centre behind the hole's centre, measured level (a horizontal projection)
PORT_PLUG_D = 17.5   # charging plug as fitted, 17.5 across (the port itself is 14); it stands vertically
PORT_CLEAR = 2.0
MOTOR_D = 64.0       # motor can diameter (measured); the rest of the surroundings are rough estimates

# --- Plug ---
CLR = 0.2            # clearance per side, plug to hole
PLUG_DEPTH = HOLE_D - 0.6  # stops short of the floor

# --- Shoe ---
SHOE_W = 24.0        # across the board: inside the pocket floor's two hex screws (~34 mm apart, estimated)
SHOE_FRONT = 7.5     # nose end (y): r3's 10.5 overhung the Ra button by ~3 mm (test fit, 2026-11-15)
SHOE_REAR = -7.0     # tail end below the step's top (the step's face is 7.36 behind the hole's centre)
SHOE_REAR_TOP = -10.0  # above the step's top the shoe reaches further back, short of the charging plug
STEP_GAP = 1.2       # gap over the step's top

# --- Hardware: M4 socket-head cap screws and plain M4 hex nuts ---
NUT_AF, NUT_T = 7.0 + 0.3, 3.11 + 0.3  # nut pocket: across flats and thickness (3.11 measured, r3; r2: 5 mm nylocs)
BOLT_HOLE = 4.5      # clearance hole for M4
HEAD_BORE = 8.5      # counterbore for the M4 head (7 mm) and the hex key
# Screw under the lip
B_ANGLE = 60.0       # axis from the surface; in the world it rises 30 deg toward the nose (r3: 45, 15 deg),
                     # so the head sits inside the shortened shoe
B_LEN = 16.0         # M4 x 16 (r2-r4: x 20); tightened, its head sits ~1 mm inside the counterbore
B_RETRACT = 5.0      # backed off this far, its end is inside the plug, so the plug drops straight in
B_NUT_AT = 11.5

# --- Light bar: two v7 receivers, side by side, facing the tail ---
PLUG_GAP = 23.0      # gap between the receivers: the lights overhang them 0.7 mm, leaving 21.6 between the lights
                     # for the 17.5 mm charging plug
CLEAR_Z = 15.0       # receivers' undersides (and the shoe's top) this high above the hole (bar C's top is 12)
PLATE_T = 7.0        # plate under each receiver; the flange channel's roof is cut into it
CHAMFER = 5.0        # 45 deg chamfers up into that roof, so the bridge over the channel is short
FRONT_Y = 10.0       # receivers' nose ends, this far ahead of the hole's centre (the deck is clear: user, 2026-11-15)
BRIDGE_REAR = -10.2  # bridge's tail end, short of the charging plug

T_RAD = np.radians(SURFACE_TILT)
N = np.array([0.0, np.sin(T_RAD), np.cos(T_RAD)])    # out of the surface (up, toward the nose)
A = np.array([0.0, -np.cos(T_RAD), np.sin(T_RAD)])   # along the surface, toward the tail (and up)
HOLE_FRAME = np.column_stack([[-1.0, 0, 0], A, N])   # local (X, s, h) -> world; right-handed


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

def plug_and_screw():
    """Plug and screw cutters, in hole-local coordinates."""
    e = hole_section()
    q = e.offset(-CLR, circular_segments=64)
    plug = q.extrude(PLUG_DEPTH + 1).translate([0, 0, -PLUG_DEPTH])
    a = np.radians(B_ANGLE)
    d = np.array([0.0, -np.cos(a), np.sin(a)])     # out of the hole toward the nose, rising
    edge = HOLE_L / 2                              # the lip's edge (the hole's rear end)
    # The shank's top passes just under the lip's edge; its end (a disc square to the axis)
    # stops 0.1 short of the back of the space under the lip.
    h_edge = -(LIP_T + 0.2 + 2.0 / np.cos(a))      # axis height at the lip's edge
    s_tip = edge + LIP_OVER - 2.0 * np.sin(a) - 0.1
    tip = np.array([0.0, s_tip, h_edge - (s_tip - edge) * np.tan(a)])
    head = B_LEN
    cut = along(rod(head + 1, BOLT_HOLE, -1), tip, d)
    cut += along(rod(60, HEAD_BORE, head - 0.5), tip, d)
    cut += along(nut_pocket(), tip, d, B_NUT_AT)
    screw = {"tip": tip, "d": d, "len": B_LEN, "set": 0.0, "loose": B_RETRACT}
    return plug, cut, screw


def shoe():
    plug, cut, screw = plug_and_screw()
    above = at_hole(Manifold.cube([200, 200, 100]).translate([-100, -100, 0]))
    w = SHOE_W / 2
    top = CLEAR_Z + 0.5                        # reaches 0.5 into the light bar's bridge: no coplanar seam
    body = Manifold.cube([SHOE_W, SHOE_FRONT - SHOE_REAR, top + 40]).translate([-w, SHOE_REAR, -40]) ^ above
    z0 = STEP_Z + STEP_GAP
    body += Manifold.cube([SHOE_W, SHOE_REAR - SHOE_REAR_TOP + 1, top - z0]).translate([-w, SHOE_REAR_TOP, z0])
    return body + at_hole(plug), screw, at_hole(cut)


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
    top = zr + rail_bottom                      # plate tops
    face = zr + hi[2]                           # receivers' faces (the bed, as printed)
    L = FRONT_Y - BRIDGE_REAR
    # The bridge runs up to the receivers' faces, so it doesn't hang across the gap as printed;
    # above the plates it stays between the rails, under where the lights sit.
    bridge = (Manifold.cube([PLUG_GAP + 2, L, top - CLEAR_Z]).translate([-PLUG_GAP / 2 - 1, BRIDGE_REAR, CLEAR_Z])
              + Manifold.cube([PLUG_GAP + 0.4, L, face - top + 0.5]).translate([-PLUG_GAP / 2 - 0.2, BRIDGE_REAR, top - 0.5]))
    return recv + bridge, rot, offs, face


def mount():
    """The whole printed part: shoe and light bar in one, minus the angled screw's hole, nut
    pocket, counterbore and the hex key's path. Also returns the screw and the light bar."""
    sh, screw, cut = shoe()
    bar, rot, offs, face = light_bar()
    return sh + bar - cut, screw, cut, bar, rot, offs


def port_column():
    return Manifold.cylinder(200, PORT_PLUG_D / 2 + PORT_CLEAR, circular_segments=48).translate([0, PORT_Y, STEP_Z])


def hanger_schematic():
    """Schematic surroundings (ESTIMATES from photos, except the hole, the step, the port and bar C's height)."""
    floor = Manifold.cube([50, 52, 20]).translate([-25, -38, -20])
    hole = hole_section().extrude(HOLE_D + 1).translate([0, 0, -HOLE_D])
    under_lip = hole_section().translate([0, LIP_OVER]).extrude(HOLE_D - LIP_T).translate([0, 0, -HOLE_D])
    floor = at_hole(floor - hole - under_lip)
    rear_edge = (HOLE_L / 2 * A)[1]
    step = Manifold.cube([50, 40, STEP_Z + 20]).translate([-25, rear_edge - 40, -20]) - at_hole(hole + under_lip)
    port_stub = Manifold.cylinder(6, 9, circular_segments=32).translate([0, PORT_Y, STEP_Z])
    housing = floor + step + port_stub
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
    part, screw, cut, _, _, _ = mount()
    report("rear mount", part)
    assert all((lb ^ part).is_empty() for lb in lights), "the part runs into a light"
    set_ = screw_solid(screw, 0.0)
    loose = screw_solid(screw, screw["loose"])
    assert (set_ ^ sch["housing"]).is_empty(), "the screw, set, runs into the truck"
    # Drops straight in along the hole's axis with the screw backed off; can't lift once it's set.
    assert all(((part + loose).translate(list(dd * N)) ^ sch["housing"]).volume() < 0.01 for dd in (0, 2, 5, 10, 20))
    assert ((part + set_).translate(list(0.5 * N)) ^ sch["housing"]).volume() > 0.01
    print("  fits in with the screw backed off, and can't lift once it's set")
    # Receiver faces down, the shoe and its plug pointing up (as the r4 shoe printed, top face down).
    receiver.write_stl(tm.face_down(part, [0, 0, 1.0]), out / f"rear_mount_r{VERSION}.stl")
    scene = {"rear_hanger_schematic": (sch["housing"] + sch["motor_plates"], "hanger_schematic"),
             "motors_schematic": (sch["motors"], "hanger_schematic"),
             "bar_c_schematic": (sch["bar_c"], "hanger_schematic"),
             "wheels_schematic": (sch["wheels"], "hanger_schematic"),
             "rear_mount": (part, "saddle"),
             "screw": (set_, "hanger_schematic"),
             "charging_plug_column": (port ^ Manifold.cube([60, 60, 60]).translate([-30, -50, 0]), "light_placeholder")}
    for i, lb in enumerate(lights):
        scene[f"light_placeholder_{i}"] = (lb, "light_placeholder")
    tm.write_obj(scene, out / f"rear_assembly_r{VERSION}.obj")

if __name__ == "__main__":
    main()
