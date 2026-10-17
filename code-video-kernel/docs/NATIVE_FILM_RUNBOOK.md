# Code Video — Native Blender film runbook (0.3.2)

This runs only on a **real Blender-equipped, authorized Mac/Linux host**. It does not install Blender, connect the MCP plugin, assert artistic quality, or send private files to a cloud service. No Docker, no subtitles, no synthetic voice.

## What it creates

After a genuine Blender import and signed seven-pose rig check, the runner renders a 12-second, three-shot Blender film in 96-frame batches. It checks one actual rendered frame per shot before each batch and refuses predicted over-budget shots. It preserves completed, hash-verified shot batches for use on resumption. After all three batches, it encodes H.264/yuv420p MP4, fully decodes it, and creates a signed file-provenance receipt. All results stay inside `CODEVIDEO_WORKSPACE`.

**The finished-film claim still requires human visual inspection of the encoded MP4 and verifying that its download/playback link works.** Technical PASS alone is never artistic PASS.

## Mac quick start

From the extracted plugin directory, with Blender, Python >=3.11 and FFmpeg available:

```bash
bash ./bin/finish-native-on-mac.sh
```

An optional stable run ID permits resuming a previously verified shot while refusing to overwrite incomplete proof:

```bash
bash ./bin/finish-native-on-mac.sh reach_native_001
```

Expected native scene: `CODEVIDEO_WORKSPACE/portable_imports/reach_native_001_native/the_reach_imported_native.blend`.

Expected film after **all** stages complete: `CODEVIDEO_WORKSPACE/native_films/reach_native_001/the_reach_blender.mp4`.

The runner installs Python dependencies into a dedicated `.venv` inside the workspace only. It does not install Blender; confirm its licensing and host compatibility independently.

## CLI control

To invoke one stage independently:

```bash
codevideo native-finish assets/the_reach_skeletal_animated.glb reach_native_001
codevideo native-shot portable_imports/reach_native_001_native/blender_import_proof.json recognition reach_native_001_shot1
codevideo native-assemble reach_native_001 \
  native_shots/reach_native_001_shot1/native_shot_receipt.json \
  native_shots/reach_native_001_shot2/native_shot_receipt.json \
  native_shots/reach_native_001_shot3/native_shot_receipt.json
codevideo native-film-check native_films/reach_native_001/native_film_receipt.json
```

`codevideo native-shot` and `codevideo native-assemble` are recovery/manual alternatives; they must not be called against conflicting run IDs or altered scene bytes.

## Failure states

- `BLOCKED BLENDER_RUNTIME`: no executable Blender; no project created.
- `BLOCKED NATIVE_IMPORT_PROOF`: native import has not demonstrated four deforming meshes/four moving non-root joints and real diagnostic images.
- `PARTIAL BLENDER_BENCHMARK`: no real preview frame; do not attempt full render.
- `PARTIAL RENDER_BUDGET`: the three-frame estimate exceeds the configured cost limit; choose a lower-quality explicit test or a more capable authorized host.
- `PARTIAL BLENDER_RENDER`: a real Blender stage failed; preserve its logs/frames, use a new run ID to repair.
- `BLOCKED SIGNED_BLENDER_SHOTS`: an output was unsigned, mismatched, edited or incomplete.
- `TECHNICAL_PASS_VISUAL_PENDING`: a real encoded 12-second Blender MP4 decoded and checked, but artistic QA and user-accessible link still require direct inspection.

## Production invariants

No orbit-only pseudo-animation, no cutouts/slideshows, no unrelated narration, no subtitles, no unsupported canon claims, no overwriting signed history. Full-length music video production remains **outside** this particular silent 12-second original-character benchmark.
