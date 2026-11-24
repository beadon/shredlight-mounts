#!/usr/bin/env python3
"""Figures comparing the rear mount's plug in hole A: r6's plug, the V-block nose, and the V-block
nose plus crush ribs (the two test shoes). Every number comes from rear_mount.py.

Writes:
    docs/plug_options.png   top-down view of the three plugs in the hole (gaps exaggerated)
    docs/plug_vblock.png    close-up of the nose end, screw loose and tight: one contact vs two
    out/rear/plug_options.obj (+ .mtl)  the three plugs in hole A at true scale, for Blender

Usage:  .venv/bin/python plug_figures.py
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Polygon  # noqa: E402
from manifold3d import Manifold  # noqa: E402

import rear_mount as rm  # noqa: E402

ROOT = Path(__file__).resolve().parent
B, A_ = rm.HOLE_W / 2, rm.HOLE_L / 2

# The hole's outline, drawn with the nose (hole-local -s) at the top: y here is -s.
t = np.linspace(0, 2 * np.pi, 3600, endpoint=False)
P = np.column_stack([B * np.cos(t), A_ * np.sin(t)])
n = np.column_stack([A_ * np.cos(t), B * np.sin(t)])
n /= np.linalg.norm(n, axis=1)[:, None]                          # outward normals
phi = np.degrees(np.arccos(np.clip(n[:, 1], -1, 1)))             # from the nose (+y here)


def gap(relief):
    """Plug-to-hole gap along each normal: rear_mount.plug_section's rule."""
    g = np.full_like(t, rm.CLR)
    f = phi < rm.NOSE_SPAN
    g[f] += relief * (1 + np.cos(np.radians(phi[f] * 180 / rm.NOSE_SPAN))) / 2
    return g


def seat(g):
    """How far the screw pushes the plug toward the nose before it touches, and the contact points."""
    need = np.where(n[:, 1] > 1e-6, g / np.maximum(n[:, 1], 1e-9), np.inf)
    slide = need.min()
    tip = np.argmax(P[:, 1])
    if need[tip] <= slide + 1e-3:
        return slide, [tip]
    return slide, [int(np.argmin(np.where(np.sign(P[:, 0]) == s, need, np.inf))) for s in (-1, 1)]


def rib_patches(ax, ex):
    for side in (-1, 1):
        for s in rm.RIB_S:
            tt = np.arcsin(-s / A_)                               # hole-local s -> drawn y = -s
            k = np.argmin((P[:, 0] - side * B * np.cos(tt)) ** 2 + (P[:, 1] - A_ * np.sin(tt)) ** 2)
            base = P[k] - ex * rm.CLR * n[k]
            tang = np.array([-n[k][1], n[k][0]])
            u = np.linspace(-1, 1, 30)
            pts = base + np.outer(u * rm.RIB_R, tang) + np.outer(np.sqrt(1 - u ** 2) * rm.RIB_PROUD * ex, n[k])
            ax.add_patch(Polygon(pts, closed=True, fc="#e07b39", ec="#a04a14", lw=1, zorder=4))


def options_figure(path, ex=6.0):
    fig, axs = plt.subplots(1, 3, figsize=(15, 6.2))
    cases = [("r6 plug", 0.0, False, "#7aa6d8"),
             ("V-block nose  (rear_shoe_test_vnose)", rm.NOSE_RELIEF, False, "#6fbf73"),
             ("V-block nose + crush ribs  (…_vnose_ribs)", rm.NOSE_RELIEF, True, "#6fbf73")]
    for ax, (title, relief, ribs, colour) in zip(axs, cases):
        g = gap(relief)
        ax.add_patch(Polygon(P, closed=True, fc="#d9d9d9", ec="#555", lw=2.5, zorder=1))
        ax.add_patch(Polygon(P - (ex * g)[:, None] * n, closed=True, fc=colour, ec="#1d3f6e", lw=1.5, zorder=3))
        if ribs:
            rib_patches(ax, ex)
        lip = P[P[:, 1] < -5.5]
        lip = lip[np.argsort(lip[:, 0])]
        ax.plot(lip[:, 0], lip[:, 1], color="#222", lw=6, solid_capstyle="round", zorder=5)
        ax.text(0, -A_ - 1.3, "lip (rear end)", ha="center", va="top", fontsize=9)
        ax.text(0, A_ + 1.0, "NOSE ↑", ha="center", va="bottom", fontsize=10, weight="bold")
        ax.add_patch(FancyArrowPatch((0, -3.0), (0, 1.2), arrowstyle="-|>", mutation_scale=16,
                                     color="#1f4e9c", lw=2.2, zorder=6))
        ax.text(0.5, -2.6, "screw pushes\nplug to nose", fontsize=8, color="#1f4e9c", zorder=6)
        ax.plot([0], [-A_ + 1.0], marker="o", ms=7, mfc="#333", mec="white", zorder=6)
        slide, ks = seat(g)
        for k in ks:
            ax.plot(*P[k], marker="*", ms=15, color="#d00" if len(ks) == 1 else "#0a0", zorder=7)
        ax.set_title(title, fontsize=11, weight="bold", pad=22)
        ax.set_xlim(-12, 12); ax.set_ylim(-12.5, 12); ax.set_aspect("equal"); ax.axis("off")
    axs[0].text(0, 10.6, "one contact, at the tip:\nthe plug can pivot about it", ha="center", fontsize=8.5, color="#b00")
    a = seat(gap(rm.NOSE_RELIEF))
    axs[1].text(0, 10.6, f"two contacts, ~{phi[a[1][0]]:.0f}° either side:\npinned left and right",
                ha="center", fontsize=8.5, color="#060")
    axs[2].text(0, 10.6, f"4 ribs, {2 * rm.RIB_R:.1f} mm wide, squash\n{rm.RIB_PROUD - rm.CLR:.2f} mm into the hole's sides",
                ha="center", fontsize=8.5, color="#a04a14")
    fig.text(0.5, 0.03, "Looking straight down into hole A (square to its tipped surface), nose at the top. Grey = hole, "
             "coloured = plug, ● = where the screw leaves the plug, under the lip, ★ = where the plug touches the hole "
             f"with the screw tight. Gaps drawn {ex:.0f}× real size.", ha="center", fontsize=9.5, wrap=True)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def vblock_figure(path, ex=4.0):
    fig, axs = plt.subplots(2, 2, figsize=(12, 8.2))
    for row, (name, relief, colour) in enumerate([("r6 plug", 0.0, "#7aa6d8"), ("V-block nose", rm.NOSE_RELIEF, "#6fbf73")]):
        g = gap(relief)
        slide, ks = seat(g)
        for col, tight in enumerate((False, True)):
            ax = axs[row, col]
            gg = g - (slide * n[:, 1] if tight else 0.0)
            plug = P - (ex * gg)[:, None] * n
            ax.fill(P[:, 0], P[:, 1], color="#d9d9d9", zorder=1)
            ax.plot(P[:, 0], P[:, 1], color="#444", lw=2.5, zorder=3)
            ax.fill(plug[:, 0], plug[:, 1], color=colour, alpha=0.9, zorder=2)
            ax.plot(plug[:, 0], plug[:, 1], color="#1d3f6e", lw=1.2, zorder=3)
            if tight:
                for k in ks:
                    ax.plot(*P[k], marker="*", ms=18, color="#d00" if len(ks) == 1 else "#0a0", zorder=5)
            ax.set_title(f"{name}, screw {'tight' if tight else 'loose'}", fontsize=11, weight="bold")
            ax.text(0, 9.55, "NOSE ↑   (hole's front wall)", ha="center", va="top", fontsize=9)
            ax.set_xlim(-8.6, 8.6); ax.set_ylim(-0.5, 9.6); ax.set_aspect("equal"); ax.axis("off")
    s0 = seat(gap(0.0))[0]
    s1, k1 = seat(gap(rm.NOSE_RELIEF))
    axs[0, 1].text(0, 2.2, f"pushed {s0:.2f} mm, the tip touches the wall at ONE point (red ★):\n"
                   "the plug can still swing left and right about it", ha="center", fontsize=9.5, color="#b00")
    axs[1, 0].text(0, 2.2, f"the same plug with the middle of its nose shaved back\n"
                   f"{rm.NOSE_RELIEF:.2f} mm more ({rm.CLR + rm.NOSE_RELIEF:.2f} mm at the tip)", ha="center", fontsize=9.5)
    axs[1, 1].text(0, 2.2, f"pushed {s1:.2f} mm, the two shoulders touch, ~{phi[k1[0]]:.0f}° either side (green ★★):\n"
                   "like a rod in a V-block, it's pinned left and right", ha="center", fontsize=9.5, color="#060")
    fig.text(0.5, 0.02, "Front half of hole A seen from above, square to its surface. Grey = hole, coloured = plug. "
             f"Gaps drawn {ex:.0f}× real size.", ha="center", fontsize=9.5)
    fig.savefig(path, dpi=105, bbox_inches="tight")
    plt.close(fig)


def blender_scene(path):
    """The three plugs, each with a stub of the shoe and the set screw, in a block cut with hole A and
    the space under its lip. Hole-local coordinates with the surface laid flat: z out of the surface,
    -y toward the nose. True scale."""
    hole = rm.hole_section().extrude(rm.HOLE_D + 1).translate([0, 0, -rm.HOLE_D])
    under_lip = rm.hole_section().translate([0, rm.LIP_OVER]).extrude(rm.HOLE_D - rm.LIP_T).translate([0, 0, -rm.HOLE_D])
    block = Manifold.cube([30, 32, 14]).translate([-15, -16, -14]) - hole - under_lip
    foot = Manifold.cube([rm.SHOE_W, 15, 3]).translate([-rm.SHOE_W / 2, -7.5, 0])
    objs = {}
    for i, (label, relief, runout, ribs) in enumerate([("r6_plug", 0.0, 1.0, False),
                                                       ("vblock_nose", rm.NOSE_RELIEF, rm.RUNOUT, False),
                                                       ("vblock_nose_ribs", rm.NOSE_RELIEF, rm.RUNOUT, True)]):
        plug, cut, screw = rm.plug_and_screw(relief, runout, ribs)
        part = max(((plug + foot) - cut).decompose(), key=lambda m: m.volume())
        shank = rm.along(rm.rod(screw["len"], 4.0), screw["tip"], screw["d"])
        dx = (i - 1) * 40.0
        objs[f"{i + 1}_{label}_hanger"] = (block.translate([dx, 0, 0]), "hanger")
        objs[f"{i + 1}_{label}"] = (part.translate([dx, 0, 0]), "plug_r6" if i == 0 else "plug_vblock")
        objs[f"{i + 1}_{label}_screw"] = (shank.translate([dx, 0, 0]), "screw")
        if ribs:
            objs[f"{i + 1}_{label}_ribs_highlight"] = ((rm.crush_ribs() - cut).translate([dx, 0, 0]), "rib")
    mats = {"hanger": (0.6, 0.6, 0.63, 0.35), "plug_r6": (0.48, 0.65, 0.85, 1.0),
            "plug_vblock": (0.3, 0.7, 0.35, 1.0), "rib": (0.88, 0.48, 0.22, 1.0), "screw": (0.1, 0.1, 0.1, 1.0)}
    mtl = path.with_suffix(".mtl")
    with open(mtl, "w") as fh:
        for k, (r, g, b, a) in mats.items():
            fh.write(f"newmtl {k}\nKd {r} {g} {b}\nd {a}\n\n")
    with open(path, "w") as fh:
        fh.write(f"mtllib {mtl.name}\n")
        base = 1
        for name, (m, mat) in objs.items():
            mesh = m.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3]
            tri = np.asarray(mesh.tri_verts) + base
            fh.write(f"o {name}\nusemtl {mat}\n")
            fh.writelines(f"v {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in v)
            fh.writelines(f"f {a} {b} {c}\n" for a, b, c in tri)
            base += len(v)


def main():
    options_figure(ROOT / "docs/plug_options.png")
    vblock_figure(ROOT / "docs/plug_vblock.png")
    (ROOT / "out/rear").mkdir(parents=True, exist_ok=True)
    blender_scene(ROOT / "out/rear/plug_options.obj")
    print("docs/plug_options.png, docs/plug_vblock.png, out/rear/plug_options.obj")


if __name__ == "__main__":
    main()
