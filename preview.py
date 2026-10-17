#!/usr/bin/env python3
"""Render 2D preview images of the mount from exact slices of the model.

docs/sections.png  slices through the deck side, the flange pocket and the front lip
docs/versions.png  front lip of every version in VERSIONS, with its engraved label

Usage:  .venv/bin/python preview.py [outdir]
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import shredlight_mount as s

IN = s.IN


def draw(ax, m, z, title):
    for p in m.slice(z).to_polygons():
        p = np.vstack([p, p[:1]])
        ax.fill(p[:, 0], p[:, 1], color="#555", alpha=0.5)
        ax.plot(p[:, 0], p[:, 1], "k", lw=0.8)
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlim(-18, 18)
    ax.set_ylim(-31, 31)
    ax.grid(alpha=0.3)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "docs")
    out.mkdir(parents=True, exist_ok=True)
    back = s.T if s.BACK_SHEET else 0
    gap = s.GAP + s.FIT
    lip_mid = (back + gap + s.T / 2) * IN
    lip_surface = (back + gap + s.T) * IN - 0.2  # inside the engraving

    ver, version = max(s.VERSIONS.items())
    m = s.left_mount(**version) - s.label(f"V{ver} L")
    fig, axs = plt.subplots(1, 3, figsize=(10, 6))
    for ax, (name, z) in zip(axs, (("deck side", 0.1),
                                   ("flange pocket", (back + gap / 2) * IN),
                                   ("front lip", lip_mid))):
        draw(ax, m, z, f"{name} (z={z:.1f} mm)")
    fig.suptitle(f"v{ver} left, slices in mm")
    fig.tight_layout()
    fig.savefig(out / "sections.png", dpi=80)

    fig, axs = plt.subplots(1, len(s.VERSIONS), figsize=(3 * len(s.VERSIONS), 6))
    for ax, (ver, version) in zip(np.atleast_1d(axs), s.VERSIONS.items()):
        uw, lw = s.slot_half_widths(**version)
        m = s.left_mount(**version) - s.label(f"V{ver} L")
        draw(ax, m, lip_surface, f"v{ver}: slot {2 * uw * IN:.2f} / {2 * lw * IN:.2f} mm")
    fig.tight_layout()
    fig.savefig(out / "versions.png", dpi=80)


if __name__ == "__main__":
    main()
