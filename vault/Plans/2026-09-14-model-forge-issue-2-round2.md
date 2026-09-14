# model-forge issue #2, round 2: jury findings (brain-triaged)

Worktree: /root/wt-mf-issue2 (branch fix/model-forge-issue-2, HEAD 5139192). Python: /root/3d-printing/.venv/bin/python.
Rules: each new gate case RED on current code first, then GREEN; `skills/model-forge/tests/run_gates.sh all` ends ALL_GATES_OK; commit on the branch; no push, no merge, no self-review. Minimum code. This is the LAST round: fix exactly these and stop.

## R1 (confirmed by brain repro, blocking) verify_model.py: island check ignores the self-support allowance
Repro: build123d Cylinder(10,20) with a 2 mm chamfer on the bottom edge, exported to STL. verify_model.py WARNs "needs supports — largest mid-air island 25mm^2 at z=2.0". A plain cylinder gives no WARN. A 45° bottom chamfer is self-supporting, and SKILL.md's design rules tell the agent to add one to nearly every part.
Cause (from GLM, confirm in code): islands are computed as poly.difference(prev_poly.buffer(1e-6)) instead of the same buffer(reach) (dz·tan 50°) the unsupported-area check uses.
Fix: island = new area outside prev_poly.buffer(reach).
Gates: the chamfered cylinder has NO needs-supports line. The closed-top tube and the real holder (/root/3d-printing/models/poop-bag-holder/holder_v3.3mf --bodies 5) still WARN on the ~1543 mm² roof at z≈65.

## R2 slice_gate.py: the supports gate can false-PASS
gate_slice_supports only greps the script's own "supports: tree" line. It never checks that the G-code contains supports.
Fix: count support feature blocks in the G-code (`^; FEATURE: Support` / `^;TYPE:Support`) and print `support feature blocks: N`. Gate asserts N > 0 with --supports tree, and N == 0 with --supports none on the closed-top tube.

## R3 small output and gate fixes
- slice_gate.py: the filament delta sign is hardcoded "+", so a negative delta prints "+-2.3g". Use `{delta:+.1f}`.
- verify_model.py summary line: say "N smaller island(s) 20–X mm² (islands under 20 mm² ignored: bridges/threads)" so the dropped count isn't hidden.
- run_gates.sh open-tube no-WARN case: also FAIL if the output contains "skipped", so a crashed check can't pass as "no warning".
