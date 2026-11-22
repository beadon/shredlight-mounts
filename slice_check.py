#!/usr/bin/env python3
"""Slice STLs with PrusaSlicer's command line and report where it puts supports.

Uses the PrusaSlicer Flatpak (com.prusa3d.PrusaSlicer) with the support settings from
PRINT_SETTINGS.md passed as flags, so it answers "does this part need supports, and where
do they touch it?" without opening the GUI. It is a check, not the real print: everything
except the support options is PrusaSlicer's default (the saved print profile segfaults the
CLI when loaded with --load, so it isn't used).

Support positions are reported in the STL's own coordinates (the part is centred on the bed
for slicing and shifted back), banded by height, so they can be matched to the model.

Usage:  .venv/bin/python slice_check.py out/truck/truck_mount_left_m16_saddle.stl [more.stl ...]
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

# The Flatpak sandbox can't see /tmp, so the files are staged under the home directory.
WORK = Path.home() / ".cache" / "shredlight-slice-check"
CENTRE = (125.0, 105.0)
SUPPORT_FLAGS = [
    "--support-material", "--support-material-auto",
    "--support-material-style", "organic",
    "--support-material-threshold", "40",
    "--dont-support-bridges",
    "--support-material-buildplate-only",
    "--support-material-contact-distance", "0.25",
]


def slice_stl(stl):
    WORK.mkdir(parents=True, exist_ok=True)
    src = WORK / stl.name
    shutil.copy(stl, src)
    gcode = src.with_suffix(".gcode")
    gcode.unlink(missing_ok=True)
    cmd = ["flatpak", "run", "--command=prusa-slicer", f"--filesystem={WORK}", "com.prusa3d.PrusaSlicer",
           "-g", *SUPPORT_FLAGS, "--center", f"{CENTRE[0]},{CENTRE[1]}", "-o", str(gcode), str(src)]
    subprocess.run(cmd, check=True, capture_output=True, timeout=600)
    if not gcode.exists():
        raise RuntimeError(f"PrusaSlicer wrote no G-code for {stl}")
    return gcode


def support_points(gcode, shift):
    """(x, y, z) of every support extrusion move, shifted into STL coordinates."""
    z, typ, x, y, out = 0.0, None, 0.0, 0.0, []
    for line in open(gcode):
        if line.startswith(";Z:"):
            z = float(line[3:])
        elif line.startswith(";TYPE:"):
            typ = line[6:].strip()
        elif line.startswith("G1"):
            mx, my = re.search(r"X([-\d.]+)", line), re.search(r"Y([-\d.]+)", line)
            if mx: x = float(mx.group(1))
            if my: y = float(my.group(1))
            if typ and "Support" in typ and "E" in line and (mx or my):
                out.append((x - shift[0], y - shift[1], z))
    return np.array(out).reshape(-1, 3)


def stl_bounds(stl):
    """Bounds of a binary STL (as this repo writes them)."""
    data = Path(stl).read_bytes()
    n = int.from_bytes(data[80:84], "little")
    rec = np.frombuffer(data[84:84 + 50 * n], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    v = rec["v"].reshape(-1, 3)
    return v.min(0), v.max(0)


def report(stl):
    lo, hi = stl_bounds(stl)
    shift = (CENTRE[0] - (hi[0] - lo[0]) / 2 - lo[0], CENTRE[1] - (hi[1] - lo[1]) / 2 - lo[1])
    pts = support_points(slice_stl(stl), shift)
    print(f"== {stl}  (part {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm)")
    if not len(pts):
        print("  no support")
        return
    print(f"  {len(pts)} support moves, up to z {pts[:, 2].max():.2f}")
    top = pts[pts[:, 2] >= pts[:, 2].max() - 1.0]
    print(f"  highest support (top 1 mm) touches x {top[:, 0].min():.1f}..{top[:, 0].max():.1f}, "
          f"y {top[:, 1].min():.1f}..{top[:, 1].max():.1f}")
    for y0 in np.arange(np.floor(pts[:, 1].min() / 5) * 5, pts[:, 1].max(), 5):
        b = pts[(pts[:, 1] >= y0) & (pts[:, 1] < y0 + 5)]
        if len(b):
            print(f"  y {y0:5.0f}..{y0 + 5:<4.0f} x {b[:, 0].min():5.1f}..{b[:, 0].max():<5.1f} "
                  f"z up to {b[:, 2].max():5.2f}  ({len(b)} moves)")


if __name__ == "__main__":
    for arg in sys.argv[1:] or ["out/truck/truck_mount_left_m16_saddle.stl"]:
        report(Path(arg))
