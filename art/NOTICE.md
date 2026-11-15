# Artwork notice

`source.png` and every file derived from it in this folder (`variants/`) are
**Calvin and Hobbes © Bill Watterson** (distributed by Andrews McMeel Syndication).
They are **not** covered by this repository's GPL-3.0 licence. They're kept here only
as personal reference for engraving the owner's own skateboard parts.

## Variants

Black-and-white ink masks, black = engraved. Each is 38 mm wide at its stored DPI. Made with
`artwork.ink_mask(path, crop=(200, 20, 1440, 1180), threshold, stroke)`, which keeps dark
ink only (colour dropped), removes specks under 0.08 mm², and redraws every line at an
even `stroke` width so it can print with a 0.4 mm nozzle.

| File | threshold | stroke | Notes |
|---|---|---|---|
| `ink_t100_s0p4_38mm.png` | 100 | 0.4 mm | Current pick: both faces, stripes, tail and wheels all readable |
| `ink_t100_s0p45_38mm.png` | 100 | 0.45 mm | Slightly bolder; a bit more fill-in around the wagon |
| `ink_t80_s0p4_38mm.png` | 80 | 0.4 mm | Lighter: fewer of the faint lines |
| `ink_t100_s0p6_38mm.png` | 100 | 0.6 mm | Boldest; the wagon and Calvin's shirt start to merge |
