#!/usr/bin/env python3
"""Silhouette tracer: any picture -> one solid black-on-white shape + the outline polygon a fabric sheet can fill.

Usage: silhouette.py IMAGE --width 120 [--pitch 10] [--mask-out mask.png] [--method alpha|threshold|rembg]
Prints one JSON line {"ok","outline":[[x,y]...] (mm, y up, bbox at the origin, overall width = --width),"mask_png","method",
"tiles","islands","width_mm","height_mm","detail"} and exits 0 if ok else 1 (detail = a plain reason the customer can read).

How the shape is found (first that applies):
  alpha      a PNG/WebP with real transparency: the alpha channel IS the shape.
  threshold  a plain background (logo, drawing, scan): Otsu on brightness; the side of the threshold that does NOT touch
             the picture's border is the shape.
  rembg      a photo (busy background): a small neural cut-out model (onnxruntime, CPU) on this machine, no per-use cost.
             Needs the `rembg` + `onnxruntime` packages (the 3d-printing venv only; the print-job image never runs this).
Clean-up: largest connected blob only, every hole filled (a silhouette is solid), a light smooth, then Douglas-Peucker
(0.5 % of the width). Refuses in plain words when the result would not hold tiles together at the pitch (under 3 tiles, or
split into separate pieces) or is taller than the bed.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image, ImageOps

MAX_PX = 1024            # longest side traced; larger pictures are shrunk first
MASK_PX = 512            # longest side of the mask PNG handed back to the page
BED = 250.0              # largest side in mm (fabric.py's bed is 256; whole 10 mm tiles)
MIN_TILES = 3
MAX_POINTS = 400         # the outline stays this small (TweakMyPart stores and re-checks it)
NOISE_GRADIENT = 45.0    # mean neighbour-pixel brightness step (0-255): static is ~85, photos and drawings are well under 25
DEFAULT_MODEL = "u2net"


class Refused(ValueError):
    """The picture cannot become a fabric; the message is what the customer is told."""


MAX_DECODE_PX = 40_000_000   # refuse BEFORE decoding: a tiny file can claim 50000 x 50000 pixels (review P3: decompression bomb)


def _load(path):
    img = Image.open(path)              # lazy: reads the header only
    if img.width * img.height > MAX_DECODE_PX:
        raise Refused("that picture is too large; please send one under 40 megapixels")
    img.load()
    img = ImageOps.exif_transpose(img)
    if max(img.size) > MAX_PX:
        k = MAX_PX / max(img.size)
        img = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    return img


def _has_alpha(img):
    if img.mode in ("RGBA", "LA"):
        a = np.asarray(img.getchannel("A"))
    elif img.mode == "P" and "transparency" in img.info:
        a = np.asarray(img.convert("RGBA").getchannel("A"))
    else:
        return None
    return a if (a < 250).mean() > 0.01 else None      # an opaque "alpha" channel says nothing about the shape


def _otsu(gray):
    hist = np.bincount(gray.ravel(), minlength=256).astype(float)
    tot = hist.sum()
    w0 = np.cumsum(hist)
    m = np.cumsum(hist * np.arange(256))
    w1 = tot - w0
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (m[-1] * w0 - tot * m) ** 2 / (w0 * w1)     # proportional to the between-class variance
    return int(np.nanargmax(np.nan_to_num(between, nan=-1.0)))


def _border(a, frac=0.02):
    n = max(1, int(min(a.shape[:2]) * frac))
    return np.concatenate([a[:n].reshape(-1, *a.shape[2:]), a[-n:].reshape(-1, *a.shape[2:]),
                           a[:, :n].reshape(-1, *a.shape[2:]), a[:, -n:].reshape(-1, *a.shape[2:])])


def _plain_background(rgb):
    return float(_border(rgb.astype(float)).std(axis=0).max()) <= 24.0


def _noise(gray):
    g = gray.astype(float)
    return (np.abs(np.diff(g, axis=0)).mean() + np.abs(np.diff(g, axis=1)).mean()) / 2 > NOISE_GRADIENT


def _threshold_mask(gray):
    t = _otsu(gray)
    dark, light = gray <= t, gray > t
    # the shape is the side that does not touch the picture's border (a black logo on white, or a white cut-out on black)
    return dark if _border(dark).mean() <= _border(light).mean() else light


def _rembg_mask(img, model):
    try:
        from rembg import new_session, remove
    except ImportError as e:
        raise Refused("photo cut-out is not available on this machine") from e
    try:
        out = remove(img.convert("RGB"), session=new_session(model), only_mask=True)
    except Exception as e:                               # model missing/offline: say so plainly, never crash
        raise Refused("photo cut-out could not run on this machine") from e
    return np.asarray(out.convert("L")) > 127


def _clean(mask):
    """Largest blob only, every hole filled, lightly smoothed. Returns a bool mask."""
    from scipy import ndimage as ndi
    lab, n = ndi.label(mask)
    if n == 0:
        raise Refused("we couldn't find a solid shape in that picture")
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    mask = lab == (1 + int(np.argmax(sizes)))
    mask = ndi.binary_fill_holes(mask)
    sigma = max(1.0, 0.006 * max(mask.shape))
    mask = ndi.gaussian_filter(mask.astype(float), sigma) > 0.5
    lab, n = ndi.label(mask)                             # smoothing can drop a thin shape entirely, or split it
    if n == 0:
        raise Refused("that shape is too thin: it is only a line or a thin scribble, so it can't hold tiles together")
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


def _outline(mask, width_mm):
    from shapely.geometry import Polygon
    from skimage.measure import find_contours
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    k = width_mm / (x1 - x0)
    pad = np.pad(mask[y0:y1, x0:x1].astype(float), 1)
    contours = find_contours(pad, 0.5)
    if not contours:
        raise Refused("no clear shape found in that picture")
    contour = max(contours, key=len)      # (row, col), sub-pixel
    poly = Polygon([((c - 1) * k, (y1 - y0 - (r - 1)) * k) for r, c in contour])   # image rows grow down, mm grow up
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.geom_type != "Polygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    tol = 0.005 * width_mm
    poly = poly.simplify(tol)
    while len(poly.exterior.coords) - 1 > MAX_POINTS:
        tol *= 1.5
        poly = poly.simplify(tol)
    minx, miny, maxx, maxy = poly.bounds
    from shapely import affinity
    poly = affinity.translate(poly, -minx, -miny)
    return poly, maxx - minx, maxy - miny


def _write_mask(mask, path):
    ys, xs = np.nonzero(mask)
    crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    img = Image.fromarray(np.where(crop, 0, 255).astype(np.uint8))
    k = MASK_PX / max(img.size)
    if k < 1:
        img = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    img.save(path)


def trace(path, width_mm, pitch=10.0, method=None, model=DEFAULT_MODEL, mask_out=None):
    """The JSON-able result described in the module docstring. Never raises for a bad picture: ok=false + a plain detail."""
    res = {"ok": False, "outline": [], "mask_png": None, "method": None, "tiles": 0, "islands": 0,
           "width_mm": width_mm, "height_mm": None, "detail": ""}
    try:
        if not (isinstance(width_mm, (int, float)) and 0 < width_mm <= BED):
            raise Refused(f"the width must be between 1 and {BED:.0f} mm")
        try:
            img = _load(path)
        except Refused:
            raise                                # _load's own plain reason (e.g. too many pixels) reaches the customer
        except Exception as e:
            raise Refused("that file is not a picture we can read") from e
        gray = np.asarray(img.convert("L"))
        if _noise(gray):
            raise Refused("that picture is too noisy to find one shape in")
        alpha = _has_alpha(img) if method in (None, "alpha") else None
        if method == "alpha" and alpha is None:
            raise Refused("that picture has no transparency to trace")
        rgb = np.asarray(img.convert("RGB"))
        if alpha is not None:
            res["method"], mask = "alpha", alpha > 127
        elif method == "threshold" or (method is None and _plain_background(rgb)):
            res["method"], mask = "threshold", _threshold_mask(gray)
        else:
            res["method"], mask = "rembg", _rembg_mask(img, model)
        mask = _clean(mask)
        poly, w, h = _outline(mask, width_mm)
        if max(w, h) > BED:
            raise Refused(f"at {width_mm:g} mm wide this shape is {h:.0f} mm tall, bigger than the bed: use a smaller width")
        import fabric
        o = fabric.Outline("poly:" + " ".join(f"{x:.2f},{y:.2f}" for x, y in poly.exterior.coords[:-1]))
        cells, dropped = fabric.fill(o, pitch)
        res.update(tiles=len(cells), islands=dropped, height_mm=round(h, 2))
        if len(cells) < MIN_TILES:
            raise Refused(f"that shape is too thin or too small: at {width_mm:g} mm wide it fills only {len(cells)} tile(s), so it can't hold together")
        if dropped:
            raise Refused(f"at {width_mm:g} mm wide the shape splits into {dropped + 1} separate pieces: try a larger width or a chunkier picture")
        res["outline"] = [[round(x, 2), round(y, 2)] for x, y in poly.exterior.coords[:-1]]
        if mask_out:
            _write_mask(mask, mask_out)
            res["mask_png"] = mask_out
        res["ok"] = True
        res["detail"] = f"traced by {res['method']}: {len(cells)} tiles at {width_mm:g} mm wide"
    except Refused as e:
        res["detail"] = str(e)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("image")
    ap.add_argument("--width", type=float, required=True, help="overall width of the shape in mm")
    ap.add_argument("--pitch", type=float, default=10.0)
    ap.add_argument("--method", choices=["alpha", "threshold", "rembg"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--mask-out")
    a = ap.parse_args(argv)
    res = trace(a.image, a.width, a.pitch, a.method, a.model, a.mask_out)
    print(json.dumps(res))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
