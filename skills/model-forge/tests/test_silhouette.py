"""silhouette.py + fabric.py --outline image:. Every test builds its own picture (no downloaded photos).
Run: /root/3d-printing/.venv/bin/python -m pytest -q skills/model-forge/tests/test_silhouette.py"""
import json, os, subprocess, sys, tempfile, unittest
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
sys.path.insert(0, SCRIPTS)
import fabric  # noqa: E402
import silhouette  # noqa: E402

TMP = tempfile.mkdtemp()
PY = sys.executable


def save(img, name):
    p = os.path.join(TMP, name)
    img.save(p)
    return p


def circle_png(name="circle.png", size=400, r=150, fg=0, bg=255):
    img = Image.new("L", (size, size), bg)
    ImageDraw.Draw(img).ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r], fill=fg)
    return save(img, name)


def pet_photo(seed, size=384):
    """A rendered 'pet' (shaded body, head, ears, legs, tail) on a busy synthetic background. Returns (RGB image, truth mask)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size] / size
    bg = np.stack([120 + 90 * np.sin(6 * xx + seed), 110 + 80 * np.cos(5 * yy + 2 * seed), 100 + 90 * np.sin(4 * (xx + yy))], -1)
    bg = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(bg)
    for _ in range(40):
        x, y, r = rng.integers(0, size), rng.integers(0, size), rng.integers(10, 50)
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v) for v in rng.integers(30, 230, 3)))
    truth = Image.new("L", (size, size), 0)
    t = ImageDraw.Draw(truth)
    for kind, g in [("e", (0.22, 0.42, 0.72, 0.78)), ("e", (0.60, 0.22, 0.86, 0.50)),
                    ("p", [(0.62, 0.26), (0.66, 0.10), (0.72, 0.24)]), ("p", [(0.74, 0.24), (0.80, 0.10), (0.83, 0.28)]),
                    ("r", (0.27, 0.72, 0.34, 0.92)), ("r", (0.58, 0.72, 0.65, 0.92)), ("p", [(0.22, 0.50), (0.08, 0.36), (0.14, 0.62)])]:
        if kind == "e":
            t.ellipse([v * size for v in g], fill=255)
        elif kind == "r":
            t.rectangle([v * size for v in g], fill=255)
        else:
            t.polygon([(x * size, y * size) for x, y in g], fill=255)
    m = np.asarray(truth) > 127
    fur = np.stack([150 + 40 * np.sin(30 * xx * yy + seed) + rng.normal(0, 12, (size, size)), 105 + 30 * yy + rng.normal(0, 12, (size, size)),
                    70 + 20 * xx + rng.normal(0, 12, (size, size))], -1)
    out = np.asarray(bg).astype(float)
    out[m] = fur[m]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), m


def tiles_of(spec):
    cells, _ = fabric.fill(fabric.Outline(spec), 10.0)
    return len(cells)


class Trace(unittest.TestCase):
    def test_black_circle_traces_to_a_circle_with_the_same_tile_count(self):
        r = silhouette.trace(circle_png(), 100, mask_out=os.path.join(TMP, "m.png"))
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["method"], "threshold")
        want = tiles_of("circle:100")
        self.assertLessEqual(abs(r["tiles"] - want), 0.10 * want, (r["tiles"], want))
        xs, ys = zip(*r["outline"])
        self.assertAlmostEqual(max(xs) - min(xs), 100, delta=0.5)
        self.assertAlmostEqual(max(ys) - min(ys), 100, delta=1.5)
        self.assertEqual((min(xs), min(ys)), (0.0, 0.0))
        self.assertLess(len(r["outline"]), 200)                        # simplified, not one point per pixel
        mask = np.asarray(Image.open(r["mask_png"]))
        self.assertEqual(set(np.unique(mask)), {0, 255})               # black shape on white
        self.assertLess(mask[mask.shape[0] // 2, mask.shape[1] // 2], 5)

    def test_a_white_shape_on_a_black_background_is_still_the_shape(self):
        r = silhouette.trace(circle_png("inv.png", fg=255, bg=0), 100)
        self.assertTrue(r["ok"], r["detail"])
        want = tiles_of("circle:100")
        self.assertLessEqual(abs(r["tiles"] - want), 0.10 * want)

    def test_a_transparent_png_uses_the_alpha_channel(self):
        img = Image.new("RGBA", (400, 400), (255, 255, 255, 0))
        ImageDraw.Draw(img).ellipse([50, 50, 350, 350], fill=(200, 30, 30, 255))
        r = silhouette.trace(save(img, "alpha.png"), 100)
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["method"], "alpha")

    def test_the_alpha_wins_over_a_background_that_would_fool_a_threshold(self):
        img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))              # the transparent pixels are black (a common export)
        ImageDraw.Draw(img).ellipse([50, 50, 350, 350], fill=(20, 20, 20, 255))
        r = silhouette.trace(save(img, "alpha_dark.png"), 100)
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["method"], "alpha")
        want = tiles_of("circle:100")
        self.assertLessEqual(abs(r["tiles"] - want), 0.10 * want)

    def test_a_white_background_logo_uses_threshold(self):
        img = Image.new("RGB", (500, 300), (250, 250, 250))
        d = ImageDraw.Draw(img)
        d.rectangle([60, 60, 440, 240], fill=(30, 60, 160))
        d.ellipse([80, 80, 200, 200], fill=(250, 250, 250))            # a hole: a silhouette is solid, so it is filled
        r = silhouette.trace(save(img, "logo.jpg", ), 120)
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["method"], "threshold")
        self.assertAlmostEqual(r["height_mm"], 120 * 180 / 380, delta=2)
        self.assertLessEqual(abs(r["tiles"] - tiles_of("rect:120,56.8")), 3)   # hole filled: about the full rectangle

    def test_a_photo_is_handed_to_the_cutout_model_not_the_threshold(self):
        img, _ = pet_photo(1)
        calls = []
        real = silhouette._rembg_mask
        try:
            silhouette._rembg_mask = lambda im, model: calls.append(model) or np.asarray(pet_photo(1)[1])
            r = silhouette.trace(save(img, "pet_fake.png"), 120)
        finally:
            silhouette._rembg_mask = real
        self.assertEqual(calls, [silhouette.DEFAULT_MODEL])
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["method"], "rembg")

    def test_a_busy_photo_cut_out_by_the_real_model(self):
        try:
            from rembg import new_session
            new_session(silhouette.DEFAULT_MODEL)
        except Exception as e:
            self.skipTest(f"rembg model unavailable here: {type(e).__name__}")
        img, truth = pet_photo(2)
        r = silhouette.trace(save(img, "pet.png"), 120)
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["method"], "rembg")
        ys, xs = np.nonzero(truth)
        truth_w = xs.max() - xs.min() + 1
        want = tiles_of("poly:" + " ".join(f"{(x - xs.min()) * 120 / truth_w:.2f},{(ys.max() - y) * 120 / truth_w:.2f}"
                                          for x, y in _hull(truth)))
        self.assertGreater(r["tiles"], 0.6 * want, (r["tiles"], want))
        self.assertLess(r["tiles"], 1.5 * want, (r["tiles"], want))

    def test_static_is_refused(self):
        noise = np.random.default_rng(0).integers(0, 256, (300, 300, 3), dtype=np.uint8)
        r = silhouette.trace(save(Image.fromarray(noise), "noise.png"), 100)
        self.assertFalse(r["ok"])
        self.assertIn("noisy", r["detail"])

    def test_a_one_pixel_line_is_refused(self):
        img = Image.new("L", (400, 400), 255)
        ImageDraw.Draw(img).line([20, 200, 380, 200], fill=0, width=1)
        r = silhouette.trace(save(img, "line.png"), 100)
        self.assertFalse(r["ok"])
        self.assertIn("thin", r["detail"])

    def test_a_shape_that_splits_into_islands_at_tile_size_is_refused(self):
        img = Image.new("L", (600, 200), 255)
        d = ImageDraw.Draw(img)
        d.ellipse([10, 20, 190, 180], fill=0)
        d.ellipse([410, 20, 590, 180], fill=0)
        d.rectangle([180, 96, 420, 104], fill=0)                        # a neck 8 px = ~1.3 mm at 100 mm wide: under half a tile
        r = silhouette.trace(save(img, "dumbbell.png"), 100)
        self.assertFalse(r["ok"])
        self.assertIn("separate pieces", r["detail"])
        self.assertGreater(r["islands"], 0)

    def test_a_shape_too_tall_for_the_bed_is_refused(self):
        img = Image.new("L", (100, 600), 255)
        ImageDraw.Draw(img).rectangle([10, 10, 90, 590], fill=0)
        r = silhouette.trace(save(img, "tall.png"), 100)
        self.assertFalse(r["ok"])
        self.assertIn("bigger than the bed", r["detail"])

    def test_a_very_wiggly_shape_still_gives_a_bounded_outline(self):
        img = Image.new("L", (1000, 1000), 255)
        d = ImageDraw.Draw(img)
        pts = [(500 + (380 + 60 * np.sin(40 * t)) * np.cos(t), 500 + (380 + 60 * np.sin(40 * t)) * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 2000)]
        d.polygon(pts, fill=0)
        r = silhouette.trace(save(img, "wiggle.png"), 150)
        self.assertTrue(r["ok"], r["detail"])
        self.assertLessEqual(len(r["outline"]), silhouette.MAX_POINTS)

    def test_a_file_that_is_not_a_picture_is_refused_not_a_crash(self):
        p = os.path.join(TMP, "x.png")
        open(p, "w").write("not an image")
        r = silhouette.trace(p, 100)
        self.assertFalse(r["ok"])
        self.assertIn("not a picture", r["detail"])

    def test_a_silly_width_is_refused(self):
        for w in (0, -5, 400, float("nan")):
            self.assertFalse(silhouette.trace(circle_png(), w)["ok"], w)

    def test_exif_orientation_is_applied(self):
        img = Image.new("L", (400, 200), 255)
        ImageDraw.Draw(img).rectangle([20, 20, 380, 180], fill=0)
        exif = Image.Exif()
        exif[0x0112] = 6                                                # stored sideways: displayed rotated 90 degrees
        p = os.path.join(TMP, "rot.jpg")
        img.save(p, exif=exif)
        r = silhouette.trace(p, 100)
        self.assertTrue(r["ok"], r["detail"])
        self.assertGreater(r["height_mm"], 100)                         # a tall shape once the rotation is applied


def _hull(mask):
    """Pixel points around a mask (its boundary): enough for a polygon tile count against the model's cut-out."""
    from shapely.geometry import MultiPoint
    ys, xs = np.nonzero(mask)
    return list(MultiPoint(list(zip(xs.tolist(), ys.tolist()))).convex_hull.exterior.coords)[:-1]


class FabricImage(unittest.TestCase):
    def test_fabric_outline_image_fills_the_traced_shape(self):
        p = circle_png("fab.png")
        o = fabric.Outline(f"image:{p}@100")
        cells, dropped = fabric.fill(o, 10.0)
        self.assertEqual(dropped, 0)
        want = tiles_of("circle:100")
        self.assertLessEqual(abs(len(cells) - want), 0.10 * want)

    def test_fabric_cli_builds_a_sheet_from_a_picture(self):
        p = circle_png("cli.png")
        out = os.path.join(TMP, "cli.3mf")
        r = subprocess.run([PY, os.path.join(SCRIPTS, "fabric.py"), "--outline", f"image:{p}@60", "--out", out], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        info = json.load(open(out + ".json"))
        self.assertLessEqual(abs(info["tiles"] - tiles_of("circle:60")), 0.10 * tiles_of("circle:60") + 1)

    def test_fabric_cli_refuses_a_bad_picture_in_plain_words(self):
        p = os.path.join(TMP, "bad.png")
        open(p, "w").write("nope")
        r = subprocess.run([PY, os.path.join(SCRIPTS, "fabric.py"), "--outline", f"image:{p}@60", "--out", os.path.join(TMP, "bad.3mf")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("REFUSED: that file is not a picture", r.stderr)

    def test_default_width_is_100(self):
        o = fabric.Outline(f"image:{circle_png('def.png')}")
        self.assertAlmostEqual(o.w, 100, delta=0.5)

    def test_the_silhouette_cli_prints_one_json_line(self):
        p = circle_png("cli2.png")
        r = subprocess.run([PY, os.path.join(SCRIPTS, "silhouette.py"), p, "--width", "80", "--mask-out", os.path.join(TMP, "cli2-mask.png")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertTrue(d["ok"] and d["method"] == "threshold" and os.path.exists(d["mask_png"]))


if __name__ == "__main__":
    unittest.main()


class ReviewFixes(unittest.TestCase):
    def test_the_sheet_pitch_reaches_the_trace(self):
        # review P2: image outlines were judged at pitch 10 whatever tile the sheet used
        seen = {}
        real = silhouette.trace
        def spy(path, width_mm, pitch=10.0, **kw):
            seen["pitch"] = pitch
            return real(path, width_mm, pitch=pitch, **kw)
        silhouette.trace = spy
        try:
            png = os.path.join(tempfile.mkdtemp(), "c.png")
            img = Image.new("L", (400, 400), 255); ImageDraw.Draw(img).ellipse((20, 20, 380, 380), fill=0); img.save(png)
            fabric.build_sheet(f"image:{png}@90", 8.0, None, 0.4, tile="drape")
        finally:
            silhouette.trace = real
        self.assertEqual(seen["pitch"], 8.0)

    def test_a_huge_picture_is_refused_before_it_is_decoded(self):
        png = os.path.join(tempfile.mkdtemp(), "big.png")
        Image.new("1", (6400, 6400), 1).save(png)          # 41 MP, a tiny file
        r = silhouette.trace(png, 100)
        self.assertFalse(r["ok"]); self.assertIn("too large", r["detail"])

    def test_a_non_numeric_width_is_a_clean_refusal(self):
        with self.assertRaises(ValueError) as e:
            fabric.Outline("image:/tmp/x.png@abc")
        self.assertIn("number of mm", str(e.exception))
