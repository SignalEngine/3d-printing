# Gates: model-forge v2 merge

OWNS: skills/model-forge/**

Scope: fix mktemp/checker bugs, add real render/features/fit/slice scripts, add bd_warehouse docs — per vault/Plans/2026-09-13-model-forge-v2.md.

- [x] G1: no deprecated tempfile.mktemp remains in shipped scripts
  CHECK: bash -c '! grep -rn "tempfile.mktemp" skills/model-forge/scripts/*.py && echo NO_MKTEMP_OK'
  EXPECT: NO_MKTEMP_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=bd8fe6fa21b0952c13a8d4c242fe76f63f5b1f8c80432db77d61cbb58b663d2a; exit=0; EXPECT=matched; output-sha256=af1dc462f8f34f96e5b71636360944944b435b66f3b977e0026b90ab9e073efb; output-bytes=13; shell=/bin/sh; cwd=/root/wt-model-forge-v2; path=6e0b5bc8a1e5/19 entries

- [x] G2: checker gates on sabotaged mesh (RED) and passes a good plate with a thin wall as WARN not FAIL
  CHECK: bash skills/model-forge/tests/run_gates.sh checker
  EXPECT: CHECKER_GATE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=4282df68d7344f2556cfa922b18da25d5ad4458589414e6193256fcf009f948f; exit=0; EXPECT=matched; output-sha256=bea652b04a25eaab813da62d088ccbaa3364e13e777bcc1f53083a64c3564336; output-bytes=191; shell=/bin/sh; cwd=/root/wt-model-forge-v2; path=6e0b5bc8a1e5/19 entries

- [x] G3: render.sh produces real f3d depth-rendered PNGs (iso/top/front/section)
  CHECK: bash skills/model-forge/tests/run_gates.sh render
  EXPECT: RENDER_GATE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=a94c3136b4dc1e25a2be2d6ef9ded20cd2ee5956f8f9d26bbd5466aedd2aa58d; exit=0; EXPECT=matched; output-sha256=8ae9e5671c9f4117e6603b773e82833194041b11edaf62adb3fb99717025f33a; output-bytes=70; shell=/bin/sh; cwd=/root/wt-model-forge-v2; path=6e0b5bc8a1e5/19 entries

- [x] G4: features.py flags a hole moved to the wrong face
  CHECK: bash skills/model-forge/tests/run_gates.sh features
  EXPECT: FEATURES_GATE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=60a31af804f908e888bfa4d63eb94e74b4e9eac696cae52f93f3e70945a8515a; exit=0; EXPECT=matched; output-sha256=6dabd6ed4dc0dd92dc2005883ad6e406bf824004bb8d424fda4d027975921184; output-bytes=154; shell=/bin/sh; cwd=/root/wt-model-forge-v2; path=6e0b5bc8a1e5/19 entries

- [x] G5: fit.py reports interference volume > 0 for an oversized lid, 0 for a cleared one
  CHECK: bash skills/model-forge/tests/run_gates.sh fit
  EXPECT: FIT_GATE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=576f6d27b3d21ead11b8ab8f14e933088eb24b2b91746b7c3fbc6f3af488bfb9; exit=0; EXPECT=matched; output-sha256=9cd1bd26cf573cf34ecea41c3a4a8728556e7a908035d3255075a37b27e4ca98; output-bytes=93; shell=/bin/sh; cwd=/root/wt-model-forge-v2; path=6e0b5bc8a1e5/19 entries

- [x] G6: slice_gate.py slices a good plate on the Bambu A1 profile and refuses a non-manifold mesh
  CHECK: bash skills/model-forge/tests/run_gates.sh slice
  EXPECT: SLICE_GATE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=e01fa854bd7cd108f0632fe6cf2500633f10325c79ec18763b1d23bbabea154d; exit=0; EXPECT=matched; output-sha256=8bb197e63753acca51df02a62dbaa2e96b490598689eb8f4443a5725c27a0716; output-bytes=148; shell=/bin/sh; cwd=/root/wt-model-forge-v2; path=6e0b5bc8a1e5/19 entries

- [x] G7: build123d-patterns.md documents bd_warehouse threads/fasteners/gears, and importing all three works in the venv
  CHECK: bash skills/model-forge/tests/run_gates.sh docs
  EXPECT: DOCS_GATE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=68761d082bf85186591b0a991dbdd763fd86eeb5f9f05553fb32f356220e838a; exit=0; EXPECT=matched; output-sha256=762b546419ccd8b22eb24284a0ac3f2fcb3cc3e082b684560b270d9f275439a9; output-bytes=122; shell=/bin/sh; cwd=/root/wt-model-forge-v2; path=6e0b5bc8a1e5/19 entries

- [x] G8: full gate runner is a single non-zero-on-failure entrypoint
  CHECK: bash skills/model-forge/tests/run_gates.sh all
  EXPECT: ALL_GATES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=7ff261eb43d904d97a757ebabe715602175aed2a25b72ed6f0c5271a983ed54b; exit=0; EXPECT=matched; output-sha256=eafd34a90df3a8ed4a22ec413abf9858901a4d3854c8bd3d67acee9ee6a10c6b; output-bytes=791; shell=/bin/sh; cwd=/root/wt-model-forge-v2; path=6e0b5bc8a1e5/19 entries
