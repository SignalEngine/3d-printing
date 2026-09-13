# 3D modelling stack for the agent (2026-09-13)

Goal: text request → verified, print-ready 3MF/STEP for the Bambu A1, on a headless VPS with no GPU.

## Installed and proven on this VPS
| Tool | Role | Where | Proof |
|---|---|---|---|
| model-forge skill (James's) | Workflow: interrogate → model → verify → deliver | `~/.claude/skills/model-forge` | smoke part built + passed |
| build123d 0.11.1 | Parametric BREP CAD (OpenCASCADE) | `/root/3d-printing/.venv` | `models/smoke/` |
| trimesh 5.1 + manifold3d | Mesh checks, repair, robust booleans | venv (also needs networkx + lxml to load .3mf) | the checker FAILs a mesh with deleted faces |
| f3d 2.2.1 | Real headless render | apt; run it under `xvfb-run -a` | correct iso render of the smoke plate |

Gotchas found:
- trimesh can't load .3mf without `networkx` and `lxml`, so the checker crashed until those were added.
- f3d with no display core-dumps. The `osmesa` and `egl` backends exit 0 but write no PNG. `xvfb-run` works.
- `--edges` in f3d, and edge lines in the matplotlib renderer, draw build123d's long sliver triangles as dark bars that look like real geometry. Edges are now off in both.

## Researched, not installed (GitHub API data, 2026-09-13)
- **CadQuery** (5.7k★): the older sibling of build123d. Fallback only.
- **OpenSCAD** (10.2k★) + **BOSL2** (2.4k★): CSG scripting. BOSL2 has threads, gears, and attachments. Worth adding if a part needs BOSL2's gears or threads.
- **OrcaSlicer CLI** (15.7k★): a real slice as the final printability check. Best next addition.
- MCP servers (OpenSCAD, FreeCAD, blender-mcp): not needed, because Claude Code already drives Python directly. Star counts not checked.
- Text-to-CAD: Text2CAD is a research repo. zoo.dev Text-to-CAD is a paid hosted API that returns STEP.
- Organic shapes (image/text → mesh): TRELLIS 13.6k★, Hunyuan3D-2 14.8k★ (no commits since Oct 2025), TripoSR 6.9k★. All need a CUDA GPU, which this VPS doesn't have. The workable route is a hosted API (Tripo/Meshy, not checked), then trimesh repair, then the same checks.

## Next
- Add an OrcaSlicer CLI slice step with a Bambu A1 profile, once a real part needs it.
