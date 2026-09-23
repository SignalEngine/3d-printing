#!/usr/bin/env python3
"""MODEL CARD: measure an uploaded 3MF/STL/OBJ before anything is planned around it.

Usage: python3 model_card.py model.3mf --json card.json [--sheet sheet.png] [--timeout 60]

Card = per part (unique mesh; `instances` says how many copies sit on the plate): name, bbox, volume,
watertight, body count, its 3 biggest FLAT faces (where a name/label can go), gear teeth when it is one;
pairs of parts closer than 3 mm (smallest gap, touching); 3MF metadata (title, designer, licence,
description); `limits` = anything that timed out, failed or was measured on a decimated copy.
The whole run finishes inside --timeout seconds: a phase that would overrun is skipped and named in `limits`.
"""
import argparse, html, json, os, re, shutil, signal, subprocess, sys, tempfile, time, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).parent))
import measure_mechanism as mm

HEAVY_FACES = 200_000     # total faces above which everything is measured on a decimated copy
DECIMATE_TOL_MM = 0.02    # manifold simplify tolerance: keeps flats flat, changes gaps by <= this
MAX_SHEET_PARTS = 12
FLAT_FACES = 3
MAX_MESH_BYTES = 60_000_000   # uncompressed mesh XML; the 97 MB planetary spinner needed >10 GB to parse
MEM_CAP_BYTES = 4 * 1024 ** 3


class Deadline(Exception):
    pass


def _alarm(signum, frame):
    raise Deadline()


def clean_text(s, n=300):
    for _ in range(3):
        s = html.unescape(s)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()[:n]


def read_meta(path):
    """Title/Designer/License/Description from a 3MF's root <metadata>; {} for anything else."""
    if Path(path).suffix.lower() != ".3mf":
        return {}
    try:
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("3D/3dmodel.model"))
    except Exception:
        return {}
    found = {}
    for el in root:
        if el.tag.endswith("metadata") and el.get("name") in ("Title", "Designer", "License", "Description") and el.text:
            found[el.get("name")] = el.text
    out = {k: clean_text(v, 300 if k == "Description" else 200) for k, v in found.items()}
    return {k: v for k, v in out.items() if v}


def bambu_part_names(path):
    """part id -> name from a Bambu/Orca 3MF's Metadata/model_settings.config."""
    try:
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("Metadata/model_settings.config"))
    except Exception:
        return {}
    names = {}
    for part in root.iter("part"):
        for md in part.findall("metadata"):
            if md.get("key") == "name" and md.get("value"):
                names[part.get("id")] = md.get("value")
    return names


def load_parts(path):
    """[(name, canonical mesh, [placed mesh per instance])], one entry per unique geometry."""
    loaded = trimesh.load(path)
    if not isinstance(loaded, trimesh.Scene):
        return [("part-1", loaded, [loaded])]
    names = bambu_part_names(path)
    by_geom = {}
    for node in loaded.graph.nodes_geometry:
        transform, gname = loaded.graph[node]
        g = loaded.geometry[gname]
        if isinstance(g, trimesh.Trimesh):
            by_geom.setdefault(gname, []).append(g.copy().apply_transform(transform))
    out, used = [], {}
    for n, (gname, placed) in enumerate(by_geom.items(), 1):
        m = re.match(r"\d+", gname)
        name = names.get(m.group(0) if m else "", f"part-{n}")
        name = re.sub(r"\.(stl|step|stp|obj|3mf)$", "", name, flags=re.I)
        used[name] = used.get(name, 0) + 1
        if used[name] > 1:
            name = f"{name} {used[name]}"
        out.append((name, loaded.geometry[gname], placed))
    return out


def decimate(mesh):
    import manifold3d
    man = manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.array(mesh.vertices, dtype=np.float32),
                                              tri_verts=np.array(mesh.faces, dtype=np.uint32)))
    small = man.simplify(DECIMATE_TOL_MM).to_mesh()
    return trimesh.Trimesh(np.array(small.vert_properties)[:, :3], np.array(small.tri_verts), process=False)


def flat_faces(mesh, top=FLAT_FACES):
    """The biggest coplanar face groups: area, normal, centroid, 2D extent (length x width)."""
    if len(mesh.facets) == 0:
        return []
    order = np.argsort(-mesh.facets_area)[:top]
    out = []
    for i in order:
        idx = mesh.facets[i]
        area = float(mesh.facets_area[i])
        normal = mesh.facets_normal[i]
        w = mesh.area_faces[idx]
        centroid = (mesh.triangles_center[idx] * w[:, None]).sum(axis=0) / w.sum()
        pts = np.unique(mesh.vertices[mesh.faces[idx]].reshape(-1, 3), axis=0)
        p2 = trimesh.transform_points(pts, trimesh.geometry.plane_transform(centroid, normal))[:, :2]
        ext = sorted(float(e) for e in trimesh.bounds.oriented_bounds_2D(p2)[1])
        out.append({"area_mm2": round(area, 1), "normal": [round(float(x), 3) for x in normal],
                    "centroid_mm": [round(float(x), 2) for x in centroid],
                    "length_mm": round(ext[1], 2), "width_mm": round(ext[0], 2)})
    return out


def build_sheet(parts, out_png, deadline, limits):
    from PIL import Image, ImageDraw
    tmp = Path(tempfile.mkdtemp(prefix="model-card-"))
    tiles = []
    try:
        for name, canon, placed in parts[:MAX_SHEET_PARTS]:
            left = deadline - time.monotonic()
            if left < 4:
                limits.append(f"sheet: stopped after {len(tiles)} of {len(parts)} parts (time)")
                break
            stl, png = tmp / "p.stl", tmp / f"{len(tiles)}.png"
            canon.export(stl)
            try:
                subprocess.run(["xvfb-run", "-a", "f3d", str(stl), f"--output={png}", "--resolution=480,360",
                                "--up=+Z", "--camera-direction=-1,1,-1.2"], capture_output=True, timeout=min(20, left))
            except subprocess.TimeoutExpired:
                limits.append(f"sheet: render of '{name}' timed out")
                continue
            if png.exists():
                tiles.append((name, len(placed), Image.open(png).convert("RGB")))
            else:
                limits.append(f"sheet: no render for '{name}'")
        if len(parts) > MAX_SHEET_PARTS:
            limits.append(f"sheet: shows the first {MAX_SHEET_PARTS} of {len(parts)} parts")
        if not tiles:
            return
        w, h, cols = 480, 360, min(4, len(tiles))
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (w * cols, (h + 40) * rows), (255, 255, 255))
        draw = ImageDraw.Draw(sheet)
        for i, (name, count, img) in enumerate(tiles):
            x, y = (i % cols) * w, (i // cols) * (h + 40)
            img.thumbnail((w, h))
            sheet.paste(img, (x + (w - img.width) // 2, y + 40 + (h - img.height) // 2))
            draw.text((x + 12, y + 12), f"{name}" + (f" (x{count})" if count > 1 else ""), fill=(0, 0, 0))
        sheet.save(out_png)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_card(card, path, sheet_png, timeout):
    t0 = time.monotonic()
    limits = card["limits"]
    parts = load_parts(path)
    if not parts:
        limits.append("no solid parts found")
        return
    total = sum(len(c.faces) for _, c, _ in parts)
    if total > HEAVY_FACES:
        try:
            parts = [(n, decimate(c), [decimate(p) for p in placed]) for n, c, placed in parts]
            limits.append(f"heavy mesh ({total} faces): measured on a decimated copy (tolerance {DECIMATE_TOL_MM} mm)")
        except Exception as e:
            limits.append(f"decimation failed ({type(e).__name__}); measured at full size")
    labelled = []   # (label, placed mesh) per instance, for the pair scan
    for name, canon, placed in parts:
        row = {"name": name, "instances": len(placed), "bbox_mm": [round(float(x), 2) for x in placed[0].extents],
               "position_mm": [round(float(x), 1) for x in placed[0].bounds.mean(axis=0)],
               "volume_cm3": round(abs(float(canon.volume)) / 1000, 2), "watertight": bool(canon.is_watertight)}
        for key, fn in (("bodies", lambda: int(canon.body_count)), ("flat_faces", lambda: flat_faces(placed[0])),
                        ("gear", lambda: (lambda g: {"teeth": g[0], "module_mm": round(g[2], 2)} if g else None)(mm.gear_teeth(canon)))):
            try:
                row[key] = fn()
            except Deadline:
                raise
            except Exception as e:
                row[key] = None
                limits.append(f"{key} for '{name}' failed: {type(e).__name__}")
        card["parts"].append(row)
        for k, p in enumerate(placed, 1):
            labelled.append((name if len(placed) == 1 else f"{name} #{k}", p))
    try:
        for i in range(len(labelled)):
            for j in range(i + 1, len(labelled)):
                a, b = labelled[i][1], labelled[j][1]
                if float(np.max(np.maximum(a.bounds[0], b.bounds[0]) - np.minimum(a.bounds[1], b.bounds[1]))) > mm.CLOSE_MM:
                    continue
                gap = mm.min_gap(a, b, mm.GAP_SAMPLES_MAX)
                if gap <= mm.CLOSE_MM:
                    card["pairs"].append({"a": labelled[i][0], "b": labelled[j][0], "gap_mm": round(gap, 3),
                                          "touching": gap < 0.05})
    except Deadline:
        limits.append(f"pairs skipped: timed out after {timeout} s")
    if sheet_png:
        try:
            build_sheet(parts, sheet_png, t0 + timeout - 3, limits)
        except Deadline:
            limits.append("sheet skipped: timed out")
        except Exception as e:
            limits.append(f"sheet failed: {type(e).__name__}: {e}"[:200])


def too_big(path):
    """Mesh data (uncompressed) beyond what trimesh can parse inside the budget: it needs ~100x the XML size in RAM."""
    try:
        if Path(path).suffix.lower() == ".3mf":
            with zipfile.ZipFile(path) as z:
                size = sum(i.file_size for i in z.infolist() if i.filename.endswith(".model"))
        else:
            size = os.path.getsize(path)
    except Exception:
        return 0
    return size if size > MAX_MESH_BYTES else 0


def run_worker(a):
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (MEM_CAP_BYTES, MEM_CAP_BYTES))
    # the alarm interrupts a Python-level phase; make_card records it in `limits` and moves on
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(max(5, a.timeout - 12))
    card = {"file": os.path.basename(a.path), "parts": [], "pairs": [], "meta": read_meta(a.path), "limits": []}
    big = too_big(a.path)
    try:
        if big:
            card["limits"].append(f"geometry skipped: {big // 1_000_000} MB of mesh data is too big to measure in {a.timeout} s")
        else:
            make_card(card, a.path, a.sheet, a.timeout - 12)
    except Deadline:
        card["limits"].append(f"card incomplete: timed out after {a.timeout} s")
    except MemoryError:
        card["limits"].append("card incomplete: model too big for memory")
    signal.alarm(0)
    Path(a.json).write_text(json.dumps(card, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", required=True)
    ap.add_argument("--sheet")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--worker", action="store_true")
    a = ap.parse_args()
    if a.worker:
        return run_worker(a)
    # supervise: a C-level parse that never returns to Python cannot be interrupted by the alarm, so the
    # measuring runs in a child that is killed at the hard limit
    cmd = [sys.executable, __file__, a.path, "--json", a.json, "--timeout", str(a.timeout), "--worker"] + (["--sheet", a.sheet] if a.sheet else [])
    try:
        r = subprocess.run(cmd, timeout=a.timeout, stderr=subprocess.PIPE, text=True)
        err = "" if r.returncode == 0 else f"measuring crashed ({r.returncode}): {r.stderr.strip()[-160:]}"
    except subprocess.TimeoutExpired:
        err = f"card incomplete: killed after {a.timeout} s"
    if err:
        print(err, file=sys.stderr)
        Path(a.json).write_text(json.dumps({"file": os.path.basename(a.path), "parts": [], "pairs": [], "meta": read_meta(a.path), "limits": [err]}, indent=1))
    card = json.loads(Path(a.json).read_text())
    print(f"{card['file']}: {len(card['parts'])} parts, {len(card['pairs'])} close pairs, limits: {card['limits'] or 'none'}")


if __name__ == "__main__":
    main()
