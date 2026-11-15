"""Turn a picture into a flat engraving outline (a manifold3d CrossSection, in mm).

Dark ink is kept and everything coloured is dropped. Every line is redrawn at one even
stroke width, so it doesn't get thinner than the nozzle can cut. Areas of solid ink wider
than that stroke stay solid.

The picture itself is not part of this repo: point truck_mount.ART at a local file (art/ is
gitignored). Only use artwork you have the right to use.
"""
import numpy as np
from manifold3d import CrossSection, FillRule
from PIL import Image
from scipy import ndimage as nd


def _disk(k):
    return np.hypot(*np.mgrid[-k:k + 1, -k:k + 1]) <= k


def ink_mask(path, crop=None, threshold=100, stroke=0.4, width_mm=38.0, speck=0.08):
    """Boolean mask of the ink (True = engrave), and the size of one pixel in mm when the
    crop is `width_mm` wide."""
    from skimage.morphology import skeletonize
    im = np.asarray(Image.open(path).convert("RGB")).astype(float)
    if crop:
        x0, y0, x1, y1 = crop
        im = im[y0:y1, x0:x1]
    px = width_mm / im.shape[1]
    ink = (im.max(2) < threshold) & (im[..., 0] - im[..., 2] < 60)   # dark, but not dark red
    lab, n = nd.label(ink)
    sizes = nd.sum(ink, lab, range(1, n + 1))
    ink = np.isin(lab, np.where(sizes * px * px >= speck)[0] + 1)   # drop specks of dust
    k = max(1, int(round(stroke / px / 2)))
    return nd.binary_dilation(skeletonize(ink), _disk(k)) | nd.binary_opening(ink, _disk(k)), px


def mask_outline(mask, px):
    """The mask as a CrossSection: x to the right, y up, centred on the origin, in mm."""
    from skimage.measure import approximate_polygon, find_contours
    padded = np.pad(mask.astype(float), 1)
    polys = []
    for c in find_contours(padded, 0.5):
        c = approximate_polygon(c, 0.4)
        if len(c) >= 4:
            polys.append(np.column_stack([c[:, 1] - 1, -(c[:, 0] - 1)]) * px)
    cs = CrossSection(polys, FillRule.EvenOdd)
    lo, hi = np.array(cs.bounds()).reshape(2, 2)
    return cs.translate(list(-(lo + hi) / 2))
