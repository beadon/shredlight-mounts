#!/usr/bin/env python3
"""Parametric 3D-printable Shredlights SL-300 slide-in mount (left + mirrored right).

Fit-tested against the SL-300 only; other Shredlights models may use different connectors.

Replicates the powder-coated sheet-metal receiver measured from photos:
a shallow box open at the top, whose front face has a U-shaped slot.
The light's flange slides down behind the front face, its neck through the slot.

Coordinates: X = width, Y = slide direction (light enters from +Y, the top),
Z = out of the back sheet. All parameters are in inches; STL output is in mm.

Each entry in VERSIONS is a fit iteration; its number is engraved on the front lip.

Usage:  .venv/bin/python shredlight_mount.py [outdir]
"""
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

IN = 25.4  # mm per inch

# --- Receiver, measured from the metal part (inches) ---
W = 1.1875           # outer width (~30 mm)
H = 2.25             # outer height (~57 mm)
DEPTH = 0.25         # total depth of the metal part, front lip included
T = 0.0625           # sheet thickness (front face, side and bottom walls)
SLOT_UPPER_W = 0.58  # slot width at the open top
SLOT_LOWER_W = 0.45  # slot width below the 45-degree step
SLOT_UPPER_LEN = 0.46  # top edge down to the start of the step
SLOT_BOTTOM = 0.61   # bottom edge of the part up to the bottom of the slot
SLOT_RADIUS = 0.04   # corner radius at the bottom of the slot

# Optional click-detent notch seen on one edge of the upper slot. Off by default:
# it may just be a paint chip. Enabling it makes the left and right parts differ.
DETENT = False
DETENT_FROM_TOP = 0.22
DETENT_RADIUS = 0.035

# --- Printing ---
FIT = 0.008          # clearance added to the flange gap and each slot edge (~0.2 mm)

# The metal part has no back sheet: its walls sit on the deck, which closes the pocket.
# Set True to close the back in plastic instead (the flange gap stays the same).
BACK_SHEET = False

GAP = DEPTH - T  # space under the front lip for the light's flange (3/16")

# Fit iterations, keyed by the version number engraved on the part. Each gives either
#   narrow: total slot narrowing in mm from the measured slot (split evenly per side), or
#   upper/lower: exact final slot widths in mm (FIT is not added).
VERSIONS = {
    1: {"narrow": 0.0},  # 15.14/11.84 mm, photo-measured: side-to-side play. Obsolete.
    2: {"narrow": 2.0},  # 13.14/9.84 mm: comfortably snug. Current winner.
    3: {"narrow": 4.0},  # 11.14/7.84 mm: too narrow, the light will not insert.
    4: {"upper": 13.0, "lower": 10.0},  # whole-mm candidate, printing.
}

# --- Version label, engraved into the front lip below the slot ---
LABEL_HEIGHT = 0.16  # cap height (~4 mm)
LABEL_DEPTH = 0.02   # engraving depth (~0.5 mm, of the 1.6 mm lip)


def slot_half_widths(narrow=0.0, upper=None, lower=None):
    """Half-widths in inches of the upper and lower slot for one VERSIONS entry (mm)."""
    if upper is not None:
        return upper / IN / 2, lower / IN / 2
    narrow /= IN
    return (SLOT_UPPER_W - narrow) / 2 + FIT, (SLOT_LOWER_W - narrow) / 2 + FIT


def slot_profile(uw, lw):
    """U-slot in the front face; origin at the bottom-centre of the receiver."""
    step_top = H - SLOT_UPPER_LEN
    step_bot = step_top - (uw - lw)  # 45-degree transition
    pts = [(-uw, H + 1), (-uw, step_top), (-lw, step_bot), (-lw, SLOT_BOTTOM),
           (lw, SLOT_BOTTOM), (lw, step_bot), (uw, step_top), (uw, H + 1)]
    slot = CrossSection([pts])
    r = SLOT_RADIUS
    slot = slot.offset(-r, JoinType.Round, circular_segments=32).offset(
        r, JoinType.Round, circular_segments=32)
    if DETENT:
        notch = CrossSection.circle(DETENT_RADIUS, 32).translate(
            [uw, H - DETENT_FROM_TOP])
        slot = slot + notch
    return slot


def label(text):
    """Engraving cutter for text, centred on the solid lip below the slot."""
    path = TextPath((0, 0), text, size=1, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    cs = CrossSection(path.to_polygons(), FillRule.EvenOdd)
    lo, hi = np.array(cs.bounds()).reshape(2, 2)
    cs = cs.translate(list(-(lo + hi) / 2)).scale([LABEL_HEIGHT / (hi[1] - lo[1])] * 2)
    depth = (T if BACK_SHEET else 0) + GAP + FIT + T
    y = -H / 2 + (T + SLOT_BOTTOM) / 2  # midway between the bottom wall and the slot
    return cs.translate([0, y]).extrude(LABEL_DEPTH + 0.5).translate(
        [0, 0, depth - LABEL_DEPTH]).scale([IN, IN, IN])


def left_mount(**version):
    ow = W + 2 * FIT
    gap = GAP + FIT
    back = T if BACK_SHEET else 0
    depth = back + gap + T  # (back sheet), flange pocket, front face

    y0 = -H / 2
    outer = Manifold.cube([ow, H, depth]).translate([-ow / 2, y0, 0])
    # Flange pocket: open at the top, closed by the side walls and bottom wall,
    # and at the back by the deck (or the optional back sheet).
    open_back = 0 if BACK_SHEET else 1
    pocket = Manifold.cube([ow - 2 * T, H, gap + open_back]).translate(
        [-(ow - 2 * T) / 2, y0 + T, back - open_back])
    # Cut from mid-pocket out through the front face only.
    slot = slot_profile(*slot_half_widths(**version)).translate([0, y0]).extrude(gap / 2 + T + 0.5).translate(
        [0, 0, back + gap / 2])

    return (outer - pocket - slot).scale([IN, IN, IN])


def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    f = np.asarray(mesh.tri_verts)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as fh:
        fh.write(b"shredlight mount".ljust(80, b"\0"))
        fh.write(np.uint32(len(f)).tobytes())
        fh.write(rec.tobytes())


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
    out.mkdir(parents=True, exist_ok=True)
    for ver, version in VERSIONS.items():
        left = left_mount(**version)
        uw, lw = slot_half_widths(**version)
        # Engrave after mirroring so the right part's text still reads correctly.
        for side, body in (("left", left), ("right", left.mirror([1, 0, 0]))):
            m = body - label(f"V{ver} {side[0].upper()}")
            name = f"shredlight_mount_{side}_v{ver}"
            write_stl(m, out / f"{name}.stl")
            lo, hi = np.array(m.bounding_box()).reshape(2, 3)
            print(f"{name}.stl  {hi - lo} mm  slot {2 * uw * IN:.2f}/{2 * lw * IN:.2f} mm  volume {m.volume() / 1000:.2f} cm^3")


if __name__ == "__main__":
    main()
