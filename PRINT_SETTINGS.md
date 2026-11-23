# Print settings

The parts are printed on an **Original Prusa MK4 (Input Shaper), 0.4 mm nozzle**, in PrusaSlicer,
with the profile below. The support settings matter most: they're tuned so supports break away cleanly.

## Profile

Based on the system profile **0.20mm SPEED @MK4IS 0.4**, saved as a copy, with filament **Generic PLA**.
(PETG or ASA hold up better in the sun and near a hot motor; see the README.)

**Front truck saddles from m15 on (and keepers): PETG.** A PLA m14 saddle cracked from road shock (see the README).
Use the **Generic PETG** filament profile, with **4 perimeters** and **40 % gyroid infill** for the saddle, so the
receiver's rails and backbone are mostly solid wall. Everything else below is unchanged.

| Setting | Value |
|---|---|
| Layer height / first layer | 0.2 mm / 0.2 mm |
| Perimeters | 2 |
| Top / bottom solid layers | 5 / 3 |
| Infill | 15–20 %, grid |
| Seam | aligned |
| Brim, skirt | none |

### Support material (Print Settings → Support material)

| Setting | Value |
|---|---|
| Generate support material | on |
| Auto generated supports | on |
| Overhang threshold | 40° |
| Enforce support for the first | 0 layers |
| Raft layers | 0 |
| Style | **Organic** |
| Top contact Z distance | **0.25 mm** |
| Bottom contact Z distance | same as top |
| Pattern | rectilinear, 2 mm spacing, 0° |
| With sheath around the support | off |
| Top interface layers | 2 |
| Bottom interface layers | 0 (off) |
| Interface pattern | default, **0.3 mm** spacing |
| Interface loops | off |
| Support on build plate only | **on** |
| XY separation between an object and its support | **0.6 mm** |
| Don't support bridges | **on** |
| Organic: max / preferred branch angle | 40° / 25° |
| Organic: branch diameter, angle, double-wall diameter | 2 mm, 5°, 8 mm |
| Organic: tip diameter, branch distance, density | 0.8 mm, 1, 30 % |

The 0.25 mm top contact gap, the 0.6 mm XY gap, the sparse 0.3 mm interface and "don't support
bridges" are what let supports snap off cleanly. "Build plate only" keeps supports out of pockets and
channels that would be hard to clear.

## Per part

All STLs are exported in their print orientation; slice them without rotating.

- **Receivers** (`out/shredlight_mount_*_v7.stl`): lip down. Supports off.
- **Front truck saddles** (`out/truck/truck_mount_*_m18_saddle.stl`): receiver face down, in PETG (above). Designed to
  need little support: the flange channel's roof is chamfered at 45° up to a ~15 mm bridge, which sags
  slightly but doesn't affect the fit (it sits ~6 mm above the flange's path). With the profile above,
  "don't support bridges" leaves it unsupported; for a cleaner roof, block supports in the channel. m15's backbone
  carries that roof along the whole receiver, so any sag runs its full length; it still doesn't touch the flange.
  Auto supports also grow one tree up into the screw-head recess, to the flat ring the head (and its
  spring washer) clamps on: as printed it faces down, tilted ~21°, but it's only 1.75 mm wide. Paint a
  **support blocker** on it: it prints fine unsupported, and a tree there would scar the clamping face.
- **Keepers** (`out/truck/truck_mount_*_m18_keeper.stl`): **standing on the keeper's upper end** (m17), screw
  axis level, so the screw's pull and the keeper's bending run along the layers. m16 printed flat, and both keepers
  split round the nut. Supports off: the nut pocket's roof is a short flat bridge, and the screw hole has a 45° teardrop top.
  It stands 20 mm tall on about 39 × 6.5 mm, so add a **brim**. PETG, with the saddle's perimeters and infill or more.
- **Rear light mount** (`out/rear/rear_mount_r5.stl`): receiver faces down, the shoe and its plug
  pointing up. Supports off: what overhangs is the two chamfered channel-roof bridges, the nut slot's
  ceiling and near-level round holes (the r4 shoe printed this way cleanly).

## Checking supports without the GUI

`slice_check.py` slices STLs with the PrusaSlicer Flatpak's command line, using the support
settings above, and reports where the supports land, in the STL's own coordinates and banded by
height. That's enough to tell which feature a tree is reaching for before opening the slicer.

```sh
.venv/bin/python slice_check.py out/truck/truck_mount_left_m18_saddle.stl out/truck/truck_mount_left_m18_keeper.stl
```

How it works, in case it needs fixing:

- The command is `flatpak run --command=prusa-slicer --filesystem=<dir> com.prusa3d.PrusaSlicer -g
  <support flags> --center 125,105 -o out.gcode part.stl`. `--command=prusa-slicer` is needed;
  the Flatpak's default entry point starts the GUI and exits silently.
- The Flatpak can't see `/tmp`, so files are staged in `~/.cache/shredlight-slice-check/`.
- Loading the saved print profile (`--load "0.20mm SPEED @MK4IS 0.4 - Copy.ini"`) segfaults the
  CLI (PrusaSlicer 2.9.7), so the support settings are passed as flags and everything else is
  PrusaSlicer's default. It's a check of where supports go, not the real print.
- Support moves are read from the G-code's `;TYPE:Support material` sections and shifted back by
  the centring offset into STL coordinates.
