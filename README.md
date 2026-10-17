# Shredlight Mounts

3D-printable left and right receivers for [Shredlights](https://shredlights.com) **SL-300**
skateboard lights. The lights are the male side of the connection: their mounting tongue slides
down into the receiver from the open top and hugs the underside of the front lip.

> **Scope:** designed and fit-tested for the SL-300 only. Other Shredlights models may use
> different connectors, and supporting them is out of scope for this project.

The geometry is a copy of the stock powder-coated sheet-metal bracket, measured from
photos against a ruler and then refined by test prints. The reference photos are
[front with ruler](docs/reference/front-with-ruler.jpg) and [side, showing depth](docs/reference/side-depth.jpg).

![Front lip of each fit version](docs/versions.png)

## Shape

Approximately 30 × 57 × 6.6 mm (1-3/16 × 2-1/4 × 1/4"):

- **Front lip** (1/16"), with a U-slot that has a wide upper section, a 45° step and a narrower lower section
- **Side walls and bottom wall** (1/16"), which form a 3/16" pocket under the lip for the light's flange
- **Open back.** The board closes the pocket, just as it does on the metal part. Set `BACK_SHEET = True` to close it in plastic.

![Slices through the part](docs/sections.png)

## Fit versions

Each version is engraved on the front lip (e.g. `V2 L`), so a printed part can be traced back to its STL.

| Version | Slot upper / lower | Result |
|---|---|---|
| v1 | 15.14 / 11.84 mm | Photo-measured. Side-to-side play. Obsolete. |
| v2 | 13.14 / 9.84 mm | Snug, but the upper slot spreads about 1 mm when the light goes in. Stresses the part. |
| v3 | 11.14 / 7.84 mm | Too narrow. The light will not insert. |
| v4 | 13.00 / 10.00 mm | Works, but the upper slot is even tighter than v2's. |
| v5 | 14.50 / 10.00 mm | Upper widened by the measured spread plus clearance. **Being tested.** |

The STLs are in [`out/`](out), in millimetres.

## Printing

- Print lip-down. The open back faces up, so nothing needs to bridge.
- PETG or ASA is recommended. The 1/16" lip carries the load, and PLA creeps when left in the sun.

## Building

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python shredlight_mount.py out   # STLs for every version in VERSIONS
.venv/bin/python preview.py docs           # preview images
```

All dimensions are named constants, in inches, at the top of `shredlight_mount.py`. To add a fit
version, add an entry to `VERSIONS`: either `{"narrow": mm}` from the measured slot, or
`{"upper": mm, "lower": mm}` for exact widths.

## Roadmap

- [ ] Confirm v5 slides in without spreading, then pick the final slot
- [ ] Design what the mount attaches to on the board

## License

[GPL-3.0](LICENSE). Shredlights is a trademark of its owner. This project is not affiliated with or endorsed by them.
