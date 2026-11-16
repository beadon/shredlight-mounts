# Print settings

The parts are printed on an **Original Prusa MK4 (Input Shaper), 0.4 mm nozzle**, in PrusaSlicer,
with the profile below. The support settings matter most: they're tuned so supports break away cleanly.

## Profile

Based on the system profile **0.20mm SPEED @MK4IS 0.4**, saved as a copy, with filament **Generic PLA**.
(PETG or ASA hold up better in the sun and near a hot motor; see the README.)

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
- **Front truck saddles** (`out/truck/truck_mount_*_m14_saddle.stl`): receiver face down. Designed to
  need little support: the flange channel's roof is chamfered at 45° up to a ~15 mm bridge, which sags
  slightly but doesn't affect the fit (it sits ~6 mm above the flange's path). With the profile above,
  "don't support bridges" leaves it unsupported; for a cleaner roof, block supports in the channel.
- **Keepers** (`out/truck/truck_mount_*_m14_keeper.stl`): flat, nut pocket on the bed side. Supports off.
- **Rear light mount** (`out/rear/rear_mount_r5.stl`): receiver faces down, the shoe and its plug
  pointing up. Supports off: what overhangs is the two chamfered channel-roof bridges, the nut slot's
  ceiling and near-level round holes (the r4 shoe printed this way cleanly).
