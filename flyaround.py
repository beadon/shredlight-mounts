#!/usr/bin/env python3
"""Fly-around GIFs of the assemblies, plus one combined STL each for GitHub's 3D viewer.

Renders the Blender assemblies (out/truck/assembly_m*.obj, out/rear/rear_assembly_r*.obj) with
Blender's Workbench engine, turning the camera once round each, and joins the frames into
docs/flyaround_front.gif and docs/flyaround_rear.gif. It also writes out/truck/assembly_m*_view.stl
and out/rear/rear_assembly_r*_view.stl: everything in one mesh, which GitHub shows as a 3D model
you can turn in the browser (it doesn't display OBJ files).

Needs Blender on the PATH (tested with 5.2). Run truck_mount.py and rear_mount.py first.

Usage:  .venv/bin/python flyaround.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRAMES = 36          # 10 degrees per frame
SIZE = (640, 480)
FRAME_MS = 90

# (OBJ, GIF, STL, title); per-object colours override the OBJ's materials for a clearer picture.
JOBS = [
    ("out/truck/assembly_m19.obj", "docs/flyaround_front.gif", "out/truck/assembly_m19_view.stl", "front truck, m19"),
    ("out/rear/rear_assembly_r6.obj", "docs/flyaround_rear.gif", "out/rear/rear_assembly_r6_view.stl", "rear truck, r6"),
]
COLOURS = {   # name prefix -> RGB
    "hanger_schematic": (0.60, 0.60, 0.63), "rear_hanger_schematic": (0.60, 0.60, 0.63),
    "motors_schematic": (0.22, 0.22, 0.24), "wheels_schematic": (0.16, 0.16, 0.17), "bar_c_schematic": (0.45, 0.45, 0.48),
    "right_saddle": (0.80, 0.15, 0.12), "left_saddle": (0.80, 0.15, 0.12), "rear_mount": (0.80, 0.15, 0.12),
    "right_keeper": (0.15, 0.60, 0.35), "left_keeper": (0.15, 0.60, 0.35), "screw": (0.10, 0.10, 0.10),
    "right_light": (0.25, 0.45, 0.85), "left_light": (0.25, 0.45, 0.85), "light_placeholder": (0.25, 0.45, 0.85),
}
SKIP = ("charging_plug_column",)   # a clearance volume, not a part

BLENDER_SCRIPT = r'''
import bpy, json, math, sys
from mathutils import Vector
job = json.loads(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=job["obj"], forward_axis="Y", up_axis="Z")
for o in list(bpy.data.objects):
    if any(o.name.startswith(p) for p in job["skip"]):
        bpy.data.objects.remove(o)
for o in bpy.data.objects:
    for prefix, rgb in sorted(job["colours"].items(), key=lambda kv: -len(kv[0])):
        if o.name.startswith(prefix):
            o.color = (*rgb, 1.0)
            break
# One combined STL for GitHub's viewer.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.wm.stl_export(filepath=job["stl"], export_selected_objects=True, forward_axis="Y", up_axis="Z")
# Scene: Workbench, object colours, soft shadows and cavity for depth.
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light, sh.color_type = "STUDIO", "OBJECT"
sh.show_shadows, sh.show_cavity, sh.show_object_outline = True, True, True
sc.display.shadow_focus = 0.6
sc.render.resolution_x, sc.render.resolution_y = job["size"]
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.96, 0.96, 0.96)
sh.background_type = "WORLD"
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
# Frame everything: orbit the bounding box's centre.
pts = [o.matrix_world @ Vector(c) for o in bpy.data.objects for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
centre, radius = (lo + hi) / 2, (hi - lo).length / 2
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
dist = radius / math.tan(min(cam.data.angle_x, cam.data.angle_y) / 2) * 0.78
el = math.radians(job["elevation"])
for i in range(job["frames"]):
    az = math.radians(job["start"] + 360 * i / job["frames"])
    cam.location = centre + Vector((dist * math.cos(el) * math.sin(az), -dist * math.cos(el) * math.cos(az), dist * math.sin(el)))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{job['frames_dir']}/f{i:03d}.png"
    bpy.ops.render.render(write_still=True)
'''


def main():
    from PIL import Image, ImageDraw
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "render.py"
        script.write_text(BLENDER_SCRIPT)
        for obj, gif, stl, title in JOBS:
            frames = Path(tmp) / Path(gif).stem
            frames.mkdir()
            job = {"obj": str(ROOT / obj), "stl": str(ROOT / stl), "frames_dir": str(frames), "frames": FRAMES,
                   "size": SIZE, "elevation": 25, "start": -30, "colours": COLOURS, "skip": SKIP}
            subprocess.run(["blender", "-b", "--factory-startup", "--python", str(script), "--", json.dumps(job)],
                           check=True, capture_output=True)
            ims = []
            for f in sorted(frames.glob("f*.png")):
                im = Image.open(f).convert("RGB")
                ImageDraw.Draw(im).text((10, 8), f"Shredlight mounts: {title} (schematic truck)", fill=(40, 40, 40))
                ims.append(im.quantize(colors=96, method=Image.Quantize.MEDIANCUT))
            ims[0].save(ROOT / gif, save_all=True, append_images=ims[1:], duration=FRAME_MS, loop=0, optimize=True)
            print(f"{gif}: {len(ims)} frames, {(ROOT / gif).stat().st_size / 1e6:.1f} MB; {stl}")


if __name__ == "__main__":
    sys.exit(main())
