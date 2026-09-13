# model-forge v2: merge plan

**Goal:** keep James's model-forge as the base and graft in the proven parts of the other agent CAD tools. The result stays a skill with scripts, not an MCP server.

**Why not switch to one of the others:** none of them is better overall.
- brs077/3dp-mcp-server: 11★, no commits since March, and its licence (CC BY-NC-ND) forbids copying code. Its advertised multi-colour split is a stub that just copies the whole model.
- pzfreo/build123d-mcp: 86★, Apache-2.0. Good checks, but it's built as a sandboxed server for untrusted code, which is overhead we don't need.
- robertcoop/openscad-mcp: 137★, MIT. Good measuring tools, but it runs on OpenSCAD, not our CAD library (build123d).

Star counts and licences come from the research agent's `gh api` reads on 2026-09-13.

## Build: in priority order

| # | Change | Source (licence) | Why |
|---|---|---|---|
| 1 | Fix `tempfile.mktemp` (deprecated, race-prone) in both scripts | model-forge bug | cheapest fix |
| 2 | Fix the checker's "on the bed" test (0.1 mm vs 0.05 mm, with and without a normal check). Weight the thin-wall sample by face area, not triangle index | model-forge bug | overhang, bed-contact and thin-wall numbers are skewed today |
| 3 | `render.sh`: f3d under Xvfb, iso/top/front/section PNGs; matplotlib grid kept as fallback | already proven this session | real depth render instead of the painter's-algorithm grid |
| 4 | `features.py`: list holes (diameter, depth, axis, which face) from the CAD geometry, then compare to the intended sizes | idea from openscad-mcp (MIT); written natively in build123d | catches "hole on the wrong face" or "M3 not M4" as numbers before looking at a picture |
| 5 | `fit.py`: clearance, interference volume and contact area between named parts | idea from openscad-mcp geom.py (MIT), rewritten on trimesh | model-forge checks single bodies only today; lids, clips and mating parts need this |
| 6 | Slice gate: OrcaSlicer CLI with a Bambu A1 profile. Pass means a real slice succeeds; log print time and filament | new | "watertight" is not the same as "slices clean" |
| 7 | Docs: bd_warehouse threads, fasteners and gears patterns in `build123d-patterns.md` | concept from brs077 (no code copied) | stops the agent hand-rolling threads |

## Skipped, with reasons
- **Parameter sensitivity audit** (pzfreo): useful, but add it when a real part breaks under a dimension change.
- **Plate bin-packing / shrinkage compensation** (brs077): Bambu Studio's auto-arrange and filament shrinkage setting already do this.
- **MCP server wrapper:** Claude Code already runs the venv Python directly.
- **Organic/sculpt generation:** needs a GPU or a paid API. Separate decision.

## Gates (each must fail RED first)
- Checker: a mesh with deleted faces → FAIL (already proven); a plate with a 0.5 mm wall → thin-wall WARN.
- `features.py`: move a hole to the wrong face → the hole-position check fails.
- `fit.py`: lid 0.2 mm clearance passes; lid 0.2 mm oversize → reports interference volume > 0.
- Slice gate: smoke plate slices; a non-manifold mesh is refused or flagged.
- End-to-end: one real part (James picks) → .3mf opens in Bambu Studio. **James's eyes only.**

## Where it lives
- Skill: `~/.claude/skills/model-forge/` (live copy).
- Optional: a versioned copy in `SignalEngine/3d-printing` under `skills/model-forge/`. That makes it public, so it's James's call.

## Cost
Built by a Sonnet builder pane from this plan, then the brain runs verify + /jury + review-gate. Estimate 2–3 hours in one session. OrcaSlicer's A1 profile setup is the unknown.
