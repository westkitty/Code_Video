# Code Video Production Kernel 0.3.2

**Portable Agent Plugins v1 package, MCP server adapter, Python 3D-puppet production kernel, Blender scripts and separately installable ChatGPT Skill.** No Docker. Source-first, provenance-gated, conservatively verified. This bundle is **not automatically installed in ChatGPT**, is **not a remote service**, and has **not passed a live Blender/MCP transport test** in the current environment.

## v0.3.1 — Portable Animated Rig / Blender Import Proof Gate (preserved)

**Local verified:** An actual self-contained glTF 2.0 `.glb` was generated from the same 12-second Cinder actor performance. It includes four continuous skinned limb meshes, true JOINTS_0/WEIGHTS_0 attributes, four two-bone parented skins, inverse bind matrices, nine animated rotation joints, and 289 keyed time samples across 17 transform channels. Head/jaw, sphere contact and world-space foot motion are retained. The GLB is an editable rigged animated interchange asset, **not** a rendered film or a `.blend` file. The default 12-second VTK MP4 from v0.3.0 is preserved separately.

Independent verification evaluates the downloaded GLB's matrices/weights through all 289 timestamps, reproduces the trusted actor deformation with sub-millimetre tolerances, refuses modified joint/mesh/weight/contact data and checks SHA-256 against a receipt. Trimesh also successfully opens the actual asset as multiple 3D meshes. This proves portable glTF structure and local skinning math, **not Blender import compatibility**.

The plugin now includes `blender/import_portable_rig.py` and the `portable-rig-import` command. This requires an actually installed Blender executable and refuses to self-certify without a native import, evaluated armature/deformed-mesh checks, seven fixed-camera diagnostic PNGs, and a saved `.blend`. The native worker was syntax-checked only on this isolated build host; it has **not** run in Blender. A locally signed receipt is required before `portable-import-check` reports PASS.

From the extracted plugin source, run on a machine with NumPy (Blender is not needed for the export):

```bash
python3 -m pip install -e '.[portable-rig]'
mkdir -p "$HOME/CodeVideoWorkspace"
export CODEVIDEO_WORKSPACE="$HOME/CodeVideoWorkspace"
codevideo portable-rig-export TheReach_Animated_GLB
codevideo portable-rig-check portable_rigs/TheReach_Animated_GLB/portable_rig_receipt.json
```

Then on the same authorized machine **with verified Blender installed**, continue:

```bash
codevideo preflight
codevideo portable-rig-import portable_rigs/TheReach_Animated_GLB/the_reach_skeletal_animated.glb blender_import_001
codevideo portable-import-check portable_imports/blender_import_001/blender_import_proof.json
```

A `BLOCKED` result for the native import is the expected correct behavior without Blender. Even after a Blender import passes, actual Blender 3-shot performance rendering, full MP4 decode, artistic review and ChatGPT MCP connection are separate required gates.

## What is actually built

- A typed 28-tool MCP adapter using the **MCP Python SDK v2** interface, plus a CLI invoking the same core logic.
- A local workspace sandbox and conservative runtime preflight.
- A Blender rig inspector measuring evaluated parent-relative bone transforms and geometry influence at multiple frames.
- A signed local rig proof (HMAC) bound to the saved `.blend` SHA-256. **Local receipts establish provenance within the trusted workspace, not protection against a malicious local user who can run/edit Python and access the signing key.**
- A chronological shot-graph validator (integer FPS, complete contiguous frames, camera IDs, purposes, acting and visibility constraints).
- Actual Blender three-frame benchmark requirement per shot (where Blender is installed).
- A resumable Blender render cache that reuses **only** frames independently covered by signed matching benchmark/progress/full-shot receipts. Correct-looking untrusted PNGs are re-rendered.
- An FFmpeg encoder checking every expected signed frame hash and binding staging cache identity to actual frame content, source scene, shot graph, audio hash and encoding profile.
- H.264/yuv420p MP4 output, AAC when source audio exists, full `ffprobe`/decode and source-audio duration checks, subtitles **OFF**.
- One-pass shot-review frame extraction, per-shot review packet, and honest G0–G8 status. Machine tests do **not** certify emotional performance, anatomy, canon, actual lip sync or user-accessible delivery.
- An optional original **mechanical/segmented** 3D demo puppet generator for Blender. Its actual execution remains unverified here.
- **NEW verified VTK-EGL 3D stage:** runnable, volumetric mechanical puppet using actual parented VTK assemblies and meshes (16 bones; 14 animated non-root joints). Fixed-camera, individually isolated joint poses prove eight independent body components actually change rendered pixels. It renders real frames, encodes and fully decodes an H.264 MP4, checks image bounds, signs source/scene/frame/diagnostic/video hashes and supports non-destructive replays of edited joint keyframes. This is not 2D, a sprite, an image warp or a Blender/organic-skinning certificate.


## v0.3.0 — The Actor Engine / Golden Scene (preserved)

**Executed evidence:** The same 288 absolute-time poses are rendered as three distinct
96-frame, source-hash-locked **VTK 3D** shot batches. The puppet has four real continuous
triangulated limb meshes with normalized two-bone **linear-blend vertex skinning** (not
rigid cutouts), separate moving head assembly, physical two-link IK, two world-locked feet,
and a sphere owner/contact transition at t=9.3s. The complete **12.000s**, **960x540**,
**24fps** H.264 video was fully decoded after signed batch assembly. Art style is an
original noncanonical technical puppet. Cinematic/character polish remains unfinished.

**Blender armature lane added but still unverified:**
`blender/create_organic_reach.py` authors a reusable armature and four continuously
weighted meshes, with the same actor timing and three linked cameras. The actual builder
execution, .blend output, skin stress poses, and native rendering require a working Blender
host; no such host was accessible in this build. An authored Python script is **not a
Blender rig certificate**. Do not substitute VTK evidence for Blender armature proof.

### Render source-verified independent shots (no Docker)

Requires VTK, NumPy, Pillow, FFmpeg and enough time/disk. Start with a dedicated *empty*
workspace. Never reuse altered or unsigned frames. Source paths are inside the configured
`CODEVIDEO_WORKSPACE` and output project IDs are immutable:

```bash
export CODEVIDEO_WORKSPACE="$HOME/CodeVideoWorkspace"
codevideo actor-batch reach_shot01 0 96
codevideo actor-batch reach_shot02 96 96
codevideo actor-batch reach_shot03 192 96
codevideo actor-batch-check projects/reach_shot01/actor_receipt.json
codevideo actor-batch-check projects/reach_shot02/actor_receipt.json
codevideo actor-batch-check projects/reach_shot03/actor_receipt.json
codevideo actor-assemble the_reach_final \
  projects/reach_shot01/actor_receipt.json \
  projects/reach_shot02/actor_receipt.json \
  projects/reach_shot03/actor_receipt.json
codevideo actor-assembly-check projects/the_reach_final/assembly_receipt.json
```

A batch legitimately returns `PARTIAL` (CLI exit code 2) until all three exist; the
`actor-batch-check` is the expected positive acceptance gate for each segment. The final
assembly fails closed on missing/altered frames, overlaps, mixed source revisions, missing
real vertex deformation, and unsigned receipts. Re-render a failed shot under a new ID.

The actor film is editable through the versioned `film.json` performance tracks. Stage that
same JSON as an input to all three batches using `--spec`, preserving a new source hash.
Changing shot length/contact event requires a new validated contract rather than changing
these protected benchmark values without new tests.

### Create the Blender-native actor scene on a verified Blender-equipped machine

```bash
blender -b --factory-startup --disable-autoexec \
  --python blender/create_organic_reach.py -- \
  --out "$HOME/CodeVideoWorkspace/reach_v030.blend"
```

After successful creation, **still run real evaluated-bone/mesh proof, extreme-pose tests,
three-shot benchmark and actual Blender render**. This code path was syntax-checked but not
runtime-executed in the build environment. Verify the rig's rest/pose mapping before
claiming accurate anatomical IK or organic deformation.

### Version boundaries

The verified VTK actor is a real deformable weighted 3D puppet; it is **not** a Blender
armature, not a general model-import pipeline, not a certified realistic character, and
not a deployed ChatGPT MCP server. Standalone Skill workflow is packaged separately.

## Package layout

```text
code-video-kernel/
  plugin.json, mcp.json, bin/codevideo-mcp   Portable plugin + stdio launcher
  pyproject.toml, codevideo/                CLI, validators, MCP tools
  blender/                                  Real Blender rig, render and demo scripts
  codevideo/vtk_stage.py                     Optional real 3D segmented-puppet stage with fixed-camera articulation evidence
  schema/shot_graph.schema.json             Source-level shot contract
  skills/code-video-production/             Releasable ChatGPT Skill + references/tests
  tests/                                    Positive and adversarial regression tests
  docs/                                     Proof contract, QA and performance evidence
  OPERATIONAL_STATE.md, QA_REPORT.md        Latest verified state and limits
```

## Install on a verified Blender-equipped Mac (no Docker)

Full Blender pipeline requires **Python 3.11+**, actual Blender and FFmpeg/FFprobe. The optional VTK demonstration can instead run where headless VTK/EGL is available. Choose the machine and writable directory explicitly; no MacBook/Big Mac target is assumed. Do **not** expose this server to the internet without authenticated access controls.

```bash
cd /PATH/TO/code-video-kernel
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp,dev]'
mkdir -p "$HOME/CodeVideoWorkspace"
export CODEVIDEO_WORKSPACE="$HOME/CodeVideoWorkspace"
.venv/bin/codevideo preflight
.venv/bin/python -m pytest -q
```

`.[mcp,dev]` pins the locally tested *API shape* to `mcp>=2.2,<2.3` and installs pytest. **SDK installation and protocol handshake were not runnable in the build environment** (no network access). A successful `pip install` is a prerequisite, not evidence of transport success.

### Actual 3D segmented-puppet demonstration (independent of Blender)

Install the optional heavy 3D runtime into the virtualenv on an authorized machine (VTK wheels vary by OS/architecture):

```bash
.venv/bin/python -m pip install -e '.[vtk-demo,dev]'
mkdir -p "$HOME/CodeVideoWorkspace"
export CODEVIDEO_WORKSPACE="$HOME/CodeVideoWorkspace"
.venv/bin/codevideo vtk-demo mechanical_broadway
```

This creates `projects/mechanical_broadway/stage.mp4` and editable `rig_scene.json`, a complete PNG frame sequence, individual neutral/joint-extreme diagnostic images and a **locally signed** `stage_receipt.json`. Check the actual output:

```bash
.venv/bin/codevideo vtk-check projects/mechanical_broadway/stage_receipt.json
```

Edit the JSON `joint_tracks` in the source project (but not its structural pivots), then rerender non-destructively under a NEW project ID:

```bash
.venv/bin/codevideo vtk-replay projects/mechanical_broadway/rig_scene.json mechanical_broadway_take2
```

Do not copy an old local receipt or proof secret as a trusted attestation onto another machine. The JSON keyframes are editable, while mesh topology and pivots require editing `codevideo/vtk_stage.py`. Output is `TECHNICAL_PASS_VISUAL_PENDING`, never `FINISHED_VERIFIED`; it does not certify Blender, organic skinning, multi-character scenes, lip sync, or performance quality. **No captions or audio are added to this proof clip.**

### Real puppet smoke test on that machine

```bash
.venv/bin/codevideo demo mechanical_test
.venv/bin/codevideo rig-proof projects/mechanical_test/scenes/puppet.blend --anatomy segmented --frames 0,8,17,24,32,46,59
.venv/bin/codevideo shots projects/mechanical_test/film.json
```

Read the **actual `proof_file`** path returned by `rig-proof` before continuing. Use it in place of `ACTUAL_PROOF_PATH` below; do not guess an SHA-based filename.

```bash
.venv/bin/codevideo benchmark projects/mechanical_test/film.json ACTUAL_PROOF_PATH setup
.venv/bin/codevideo render projects/mechanical_test/film.json ACTUAL_PROOF_PATH setup
.venv/bin/codevideo benchmark projects/mechanical_test/film.json ACTUAL_PROOF_PATH payoff
.venv/bin/codevideo render projects/mechanical_test/film.json ACTUAL_PROOF_PATH payoff
.venv/bin/codevideo encode projects/mechanical_test/film.json ACTUAL_PROOF_PATH
```

The demo is a **2-second segmented proof scene**, not a certified feature film. Inspect Blender's actual rig and encoded video. `render` may return `PARTIAL` for long shots; repeat the exact command to resume after the bounded frame batch.

For a new production, run `.venv/bin/codevideo init PROJECT_ID`, place a real rigged `.blend` under its scene directory, edit `film.json`, verify its cameras and music, and follow the same proof/benchmark/render/encode gates. Sources must be staged in the dedicated workspace; canonical references require separate authoritative checks.

## Plugin vs. Skill installation

**Portable Agent Plugins host:** `plugin.json` follows the published Agent Plugins 1.0 schema and `mcp.json` declares a `stdio` server (`./bin/codevideo-mcp`, workspace in `${PLUGIN_DATA}/workspace`). The host must support this format, create writable `PLUGIN_DATA`, install Python dependencies and start the server. This manifest **does not itself create a ChatGPT connection**.

**ChatGPT web/Android:** ChatGPT cannot directly connect to your machine's `127.0.0.1` service. Start the local HTTP MCP adapter only when desired:

```bash
.venv/bin/codevideo serve --host 127.0.0.1 --port 8787
```

Connect ChatGPT using a **host-managed Secure MCP Tunnel** or a publicly reachable authenticated HTTPS MCP endpoint. An authenticated tunnel must have real access controls; a publicly forwarded unauthenticated `/mcp` route is unsafe. In ChatGPT, go to Plugins → + → Add custom MCP server. For Business workspaces, owner/admin permissions apply. A setup is considered connected only after ChatGPT discovers and successfully invokes the tools. See the [official connection guide](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt).

**Standalone Skill:** Install the separately provided `skill.zip` through the host's Skills UI. That ZIP contains instructions and self-contained references/tests; it **does not include** `codevideo/`, Blender or MCP binaries. The Skill teaches the workflow and recognizes when the actual runtime is missing.

## Tool surface

`preflight`, `create_project`, `render_mechanical_3d_smoke`, `replay_articulated_3d_stage`, `check_articulated_3d_stage`, `check_shot_graph`, `inspect_real_rig`, `check_rig_receipt`, `benchmark_real_render`, `render_verified_shot`, `encode_complete_film`, `inspect_encoded_video`, `prepare_visual_review`, `production_verdict`.

Tools take only workspace-contained paths and invoke fixed Blender/FFmpeg entrypoints. There is no general-purpose remote shell, deletion, automatic publishing or narration function. A `.blend` can nevertheless contain linked references, drivers or assets: treat untrusted scene files as untrusted inputs and audit or quarantine before opening. `--disable-autoexec` is helpful but not a general filesystem sandbox.

## Verified and unverified boundaries

See [QA_REPORT.md](QA_REPORT.md), [docs/PROOF_CONTRACT.md](docs/PROOF_CONTRACT.md) and [docs/RELEASE_AUDIT.md](docs/RELEASE_AUDIT.md). Local verification covers code tests, synthetic FFmpeg decoding, an **actually rendered 6-second VTK-EGL mechanical puppet film**, package structure and performance measurements—not a live Blender organically skinned film or installed ChatGPT plugin. The production status remains `TECHNICAL_PASS_VISUAL_PENDING` until independent shot-level review and accessible delivery are actually proven.

### Actual MCP protocol smoke test (next deployment gate)

After installing the optional official `mcp>=2.2,<2.3` SDK, run:

```bash
export CODEVIDEO_WORKSPACE="$HOME/CodeVideoWorkspace"
.venv/bin/python scripts/mcp_smoke.py
```

This verifies the **real MCP SDK protocol path in memory**, tool discovery (14 tools), and the read-only `preflight` call on that host; the original build's fake server mock is not an MCP handshake. It was authored against the current official [MCP Python SDK v2 testing guide](https://py.sdk.modelcontextprotocol.io/get-started/testing/) but **could not be executed on this isolated build host** because the SDK package is unavailable and DNS resolution is blocked. A successful in-process test is also not proof that ChatGPT can reach a separately authenticated HTTP endpoint.

## v0.3.2 — Native Blender film execution (new, **host test pending**)

The previous version exported an actual skinned GLB and introduced a native import
probe. This revision adds the missing **Blender-native final-film** stages:

- `blender/import_portable_rig.py` now generates three source-space, automatically
  framed cameras and a stage while proving evaluated mesh deformation and saving
  a native `.blend`. It keeps the original seven fixed-camera stress renders.
- `blender/render_native_frames.py` renders one genuine 3D shot at a time using
  Blender Cycles CPU; no still-image substitutes, synthetic audio or captions.
- `codevideo native-shot` checks a real single-frame cost benchmark, renders
  96 frames, checks PNG byte signatures/dimensions/hashes and signs a source-bound
  local receipt. It reuses *only* verified matching shot receipts.
- `codevideo native-assemble` refuses gaps, overlaps or mixed source revisions,
  copies exactly 288 verified native frames, encodes H.264/yuv420p, probes and
  fully decodes 12 seconds, and records that artistic review is still pending.
- `codevideo native-finish` orchestrates Blender import + the three shot stages +
  assembly while preserving prior versions. `codevideo native-film-check`
  rechecks the native source, receipts, encoded video and frame integrity.

**Native rendering and import are not verified in this isolated container.** The
actual blocker is no Blender executable or reachable authorized Mac. Source
syntax and negative-control tests do not certify `bpy` functionality. Never
report a Blender-native MP4 or `.blend` unless the Mac runner genuinely created
and validated those files.

For Mac handoff, see [the full runbook](docs/NATIVE_FILM_RUNBOOK.md). A bounded
entrypoint is included, requiring Python >=3.11, Blender 4.5+ and FFmpeg:

```bash
bash ./bin/finish-native-on-mac.sh
```

No automatic Blender download, no Docker, no public tunnel, no user-facing
subtitles or unapproved narration. The repo root is never used as the output
workspace; new IDs preserve existing original/revision files.
