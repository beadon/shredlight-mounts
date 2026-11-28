#!/usr/bin/env python3
"""Fit-test strips for the front strut's skyward-face chamfers (2026-11-27).

The saddle's channel copies the strut's cross-section (truck_mount.strut_profile, grown LINER). Its
two skyward-face chamfers were never measured: m1-m20 model them TOP_CHAMFER (5.5) front to back
but only CHAMFER_DEPTH (1.5) deep, a ~15 deg slope from the skyward face, kept shallow so they
couldn't bind. On the truck that leaves a wedge-shaped gap between the saddle's chamfer and the
strut's (photo, 2026-11-27): the saddle's front arm then bears on the strut's chamfer edge, the
line the m19 arm sheared along.

Each strip is a 5 mm slice of the saddle's channel with the chamfers at one angle (from the skyward
face, over the same TOP_CHAMFER front to back), the angle raised on its face. Push each straight
down onto the strut from the sky side: the right one sits on the skyward flat and both chamfers with
no gap; too shallow rocks on the chamfer corners with a gap over the flat; too steep sits on the flat
with gaps at the chamfers.

Writes out/truck/chamfer_gauge_<angle>.stl and out/truck/chamfer_gauges_all.stl (all on one plate).
They print lying flat, label up, no supports.

Usage:  .venv/bin/python chamfer_gauge.py
"""
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

import shredlight_mount as receiver
import truck_mount as t

ANGLES = (20, 25, 30, 35, 40)   # deg from the skyward face; the m20 model is ~15
THICK = 5.0          # strip length along the strut (the slab's thickness as printed)
WALL = 3.0           # walls round the channel
ARM_TO = 2.5         # the arms reach down to this height above the window face (v), clear of the
                     # window-side chamfers (left at CHAMFER_DEPTH, unchanged)
TAB_H = 7.0          # label tab above the channel's top wall
TEXT_H = 5.0         # label height
TEXT_PROUD = 0.6     # raised label, 3 layers


def profile(angle):
    """The strut's cross-section in (w, v) (w front to back, v up from the window face), with the
    skyward chamfers at `angle`, grown LINER: the saddle's channel."""
    h, ct, d0 = t.HALF_T, t.TOP_CHAMFER, t.CHAMFER_DEPTH
    cw = (t.PLATE_T - t.WINDOW_FLAT) / 2
    d = ct * np.tan(np.radians(angle))
    pts = [(-h + cw, 0), (h - cw, 0), (h, d0), (h, t.STRUT_H - d), (h - ct, t.STRUT_H),
           (-h + ct, t.STRUT_H), (-h, t.STRUT_H - d), (-h, d0)]
    return CrossSection([pts]).offset(t.LINER, join_type=JoinType.Miter), d


def label(text):
    tp = TextPath((0, 0), text, size=10, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    polys = [p for p in tp.to_polygons() if len(p) > 2]
    cs = CrossSection(polys, FillRule.EvenOdd)
    x0, y0, x1, y1 = cs.bounds()
    k = TEXT_H / (y1 - y0)
    return cs.translate([-(x0 + x1) / 2, -(y0 + y1) / 2]).scale([k, k])


def strip(angle):
    chan, d = profile(angle)
    h = t.HALF_T + t.LINER
    top = t.STRUT_H + t.LINER + WALL
    outer = CrossSection.square([2 * (h + WALL), top + TAB_H - ARM_TO]).translate([-h - WALL, ARM_TO])
    body = (outer - chan).extrude(THICK)
    text = label(f"{angle}°").translate([0, top + TAB_H / 2 - 0.3]).extrude(TEXT_PROUD).translate([0, 0, THICK])
    return body + text, d


def main():
    out = Path("out/truck")
    out.mkdir(parents=True, exist_ok=True)
    plate = Manifold()
    for i, a in enumerate(ANGLES):
        m, d = strip(a)
        assert len(m.decompose()) == 1, f"{a}: not one piece"
        t.check_mesh(m, f"chamfer gauge {a}")
        receiver.write_stl(m, out / f"chamfer_gauge_{a}.stl")
        bb = m.bounding_box()
        plate += m.translate([0, i * (bb[4] - bb[1] + 3), 0])
        print(f"{a} deg: chamfer {d:.2f} deep over {t.TOP_CHAMFER} front to back; strip "
              f"{bb[3] - bb[0]:.1f} x {bb[4] - bb[1]:.1f} x {bb[5] - bb[2]:.1f} mm")
    receiver.write_stl(plate, out / "chamfer_gauges_all.stl")


if __name__ == "__main__":
    main()
