"""Shaded renders of the truck mount assembly, for checking it by eye.

A small z-buffer rasteriser (numpy + Pillow), so no 3D viewer is needed. Writes
docs/truck_render.png: the whole truck from the nose and from the rider's right, and
a close-up of the right mount with the screw's path through the receiver slot.

Usage:  .venv/bin/python render_views.py [output.png]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

import truck_mount as t


def tris(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    return v[np.asarray(mesh.tri_verts)]


def view_matrix(az, el):
    az, el = np.radians(az), np.radians(el)
    d = np.array([np.cos(el) * np.sin(az), -np.cos(el) * np.cos(az), np.sin(el)])  # camera direction (toward viewer)
    right = np.cross([0, 0, 1], d); right /= np.linalg.norm(right); up = np.cross(d, right)
    return np.array([right, up, d])


def render(objs, outline, az, el, title, W=900, H=700, scale=None, centre=None):
    R = view_matrix(az, el)
    allv = np.vstack([tris(m).reshape(-1, 3) for m, _ in objs + outline])
    P = allv @ R.T
    if centre is None: centre = (P.min(0) + P.max(0)) / 2
    if scale is None: scale = 0.85 * min(W / np.ptp(P[:, 0]), H / np.ptp(P[:, 1]))
    zbuf = np.full((H, W), -1e9); img = np.full((H, W, 3), 245.0)
    light = np.array([0.3, 0.5, 0.8]); light /= np.linalg.norm(light)
    for m, col in objs:
        T = tris(m) @ R.T
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        shade = 0.35 + 0.65 * np.clip(np.abs(n @ light), 0, 1)
        S = np.empty_like(T); S[..., 0] = (T[..., 0] - centre[0]) * scale + W / 2; S[..., 1] = H / 2 - (T[..., 1] - centre[1]) * scale; S[..., 2] = T[..., 2]
        for k in range(len(S)):
            a, b, c = S[k]
            x0, x1 = int(max(0, np.floor(min(a[0], b[0], c[0])))), int(min(W - 1, np.ceil(max(a[0], b[0], c[0]))))
            y0, y1 = int(max(0, np.floor(min(a[1], b[1], c[1])))), int(min(H - 1, np.ceil(max(a[1], b[1], c[1]))))
            if x1 < x0 or y1 < y0: continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-9: continue
            l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
            l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
            l3 = 1 - l1 - l2
            inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
            z = l1 * a[2] + l2 * b[2] + l3 * c[2]
            zb = zbuf[y0:y1 + 1, x0:x1 + 1]
            upd = inside & (z > zb)
            zb[upd] = z[upd]
            img[y0:y1 + 1, x0:x1 + 1][upd] = np.array(col) * shade[k]
    im = Image.fromarray(img.astype(np.uint8)); d = ImageDraw.Draw(im)
    for m, col in outline:   # wireframe boxes drawn on top (e.g. the light placeholder)
        T = tris(m) @ R.T
        for tri in T:
            pts = [((p[0] - centre[0]) * scale + W / 2, H / 2 - (p[1] - centre[1]) * scale) for p in tri]
            d.line(pts + [pts[0]], fill=col, width=1)
    d.text((10, 8), title, fill=(0, 0, 0))
    return im


def assembly_views(path):
    from manifold3d import Manifold
    parts, rot, rrot, roff = t.right_parts()
    t0, flip = t.clamp_offset(), np.diag([-1.0, 1, 1])
    hanger = t.schematic_hanger(rot)
    rs, rk = parts["saddle"].translate(list(t0)), parts["keeper"].translate(list(t0))
    ls = parts["saddle"].mirror([1, 0, 0]).translate(list(flip @ t0))
    lk = parts["keeper"].mirror([1, 0, 0]).translate(list(flip @ t0))
    lights = [(t.light_envelope(rrot, roff).translate(list(t0)), (40, 80, 220)),
              (t.light_envelope(flip @ rrot @ flip, flip @ roff).translate(list(flip @ t0)), (40, 80, 220))]
    path_ = t.place(t.along_v(Manifold.cylinder(70, 1.0, circular_segments=8)).translate(
        [0, t.head_seat(), t.SCREW_W]), rot).translate(list(t0))
    # Beam: a thin rod from the lens along the light's axis, and a level one for comparison.
    _, lo, hi = t.receiver_body()
    lens = t.place(Manifold.cube([1, 1, 1]).translate([-0.5, hi[1] + t.LIGHT_LENS_PROUD, hi[2] + t.LIGHT_H / 2]),
                   rrot, roff).translate(list(t0))
    tip = np.mean(np.array(lens.bounding_box()).reshape(2, 3), axis=0)
    rod = lambda d: Manifold.cylinder(60, 0.8, circular_segments=8).transform(np.column_stack([
        np.column_stack([np.cross(d, [1, 0, 0]), [1, 0, 0], d]), tip]))
    beam, level = rod(rrot[:, 1]), rod(np.array([0, 1.0, 0]))
    grey, red, green = (150, 150, 155), (200, 50, 40), (40, 150, 90)
    everything = [(hanger, grey), (rs, red), (ls, red), (rk, green), (lk, green)]
    a = render(everything, lights, 180, 5,
               "1. From the nose (the rider's right mount is on the LEFT). Blue = light, estimated size.", W=760, H=520)
    b = render(everything + [(beam, (255, 140, 0)), (level, (120, 120, 120))], lights, 90, 5,
               f"2. From the rider's right side. Nose to the RIGHT. Orange = beam, grey = level ({t.PITCH_DOWN:.0f} deg apart).",
               W=760, H=520)
    c = render([(hanger, grey), (rs, red), (rk, green), (path_, (255, 140, 0))], [], 135, 35,
               "3. Right mount from front-right, above. Orange = the M5 screw's path, through the slot.", W=760, H=560)
    big = Image.new("RGB", (1520, 1080), (255, 255, 255))
    big.paste(a, (0, 0)); big.paste(b, (760, 0)); big.paste(c, (380, 520))
    big.save(path)


if __name__ == "__main__":
    assembly_views(sys.argv[1] if len(sys.argv) > 1 else "docs/truck_render.png")
