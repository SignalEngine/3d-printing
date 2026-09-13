"""Acceptance gate for the holder edit. Compares an edited mesh against original.stl in the upright frame.

usage: gate.py <edited.stl> [--source-frame]   (--source-frame: file is still in the tilted source frame)
Exit 0 only if every check passes. Must FAIL on holder_v2.stl (the broken first attempt).
"""
import sys, numpy as np, trimesh
from edit import F, TH, ZS, MAP, SLOT_KEEP, CLIP_BASE, FILL_Z, LOOP_THETA, LOOP_T, ang_in

path = sys.argv[1]
m = trimesh.load(path, force="mesh"); m.merge_vertices()
body = sorted(m.split(only_watertight=False), key=lambda b: -b.volume)[0]
if "--source-frame" in sys.argv:
    body.apply_transform(F)

T, Z = np.meshgrid(np.radians(TH), ZS)
O = np.c_[45 * np.cos(T.ravel()), 45 * np.sin(T.ravel()), Z.ravel()]
D = np.c_[-np.cos(T.ravel()), -np.sin(T.ravel()), np.zeros(T.size)]
loc, ri, _ = body.ray.intersects_location(O, D, multiple_hits=False)
rad = np.full(T.size, np.nan); rad[ri] = np.hypot(loc[:, 0], loc[:, 1]); NEW = rad.reshape(T.shape)

zone = (ZS[:, None] > FILL_Z[0] + 1) & (ZS[:, None] < FILL_Z[1] - 1)
slot = np.array([ang_in(t, *SLOT_KEEP) for t in TH])[None, :]
clip = np.array([ang_in(t, CLIP_BASE[0], CLIP_BASE[1]) for t in TH])[None, :] & (ZS[:, None] > CLIP_BASE[2] - 2) & (ZS[:, None] < CLIP_BASE[3] + 2)
loopw = np.array([abs(((t - LOOP_THETA + 180) % 360) - 180) < 8 for t in TH])[None, :] & (ZS[:, None] > 40)
free = zone & ~slot & ~clip & ~loopw

panel_before = ((MAP > 24.6) & (MAP < 25.4) & free).sum()
panel_after = ((NEW > 24.6) & (NEW < 25.4) & free).sum()
holes_after = ((NEW < 23.3) & free).sum()
# open slot = ray reaches the bore OR passes clean through (a back-wall bone lined up with the slot); both mean "open"
open_before = (MAP < 23.3) | np.isnan(MAP); open_after = (NEW < 23.3) | np.isnan(NEW)
slot_before = open_before & zone & slot; slot_after = open_after & zone & slot
iou = (slot_before & slot_after).sum() / max((slot_before | slot_after).sum(), 1)
thread = np.nanmax(np.abs(NEW[ZS < 10] - MAP[ZS < 10]))
lid = np.nanmax(np.abs(NEW[(ZS > 66.5)] - MAP[(ZS > 66.5)]))
loop_px = ((NEW > 27.0) & np.array([abs(((t - LOOP_THETA + 180) % 360) - 180) < 6 for t in TH])[None, :] & (ZS[:, None] > 42)).sum()

checks = [
    ("hex panels gone (px left vs before)", panel_after <= 0.02 * panel_before, f"{panel_after} vs {panel_before}"),
    ("bone holes cut through the wall", holes_after > 100, f"{holes_after} px see the bore"),
    ("bag slot unchanged (IoU)", iou > 0.97, f"{iou:.3f}"),
    ("thread unchanged (max dr mm)", thread < 0.05, f"{thread:.3f}"),
    ("lid unchanged (max dr mm)", lid < 0.05, f"{lid:.3f}"),
    ("hook loop present", loop_px > 20, f"{loop_px} px"),
    ("body watertight", body.is_watertight, str(body.is_watertight)),
]
for name, ok, val in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {val}")
sys.exit(0 if all(ok for _, ok, _ in checks) else 1)
