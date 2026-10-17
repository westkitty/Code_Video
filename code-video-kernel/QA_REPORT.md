# Code Video v0.3.2 — Native Film Runner QA

Verdict: **LOCAL CODE PASS / NATIVE BLENDER EXECUTION BLOCKED**. Do not mark film FINISHED_VERIFIED.

## Verified here
- **81/81** total local Python regression tests PASS; the original v0.3.1 tests continue to pass.
- Python source/Blender workers compile; Mac shell launcher and local MCP launcher pass shell syntax checks.
- Previous v0.3.0 VTK demo MP4 re-probed, fully decoded, and confirmed 288 frames/12 seconds; it is **not** native Blender proof.
- Native GLB re-verified: four skinned meshes, nine animated joints, 289 timestamps.
- Skill passes strict release certification and full Python wheel builds containing both Blender workers.
- New negative controls test no-Blender no-mutation behavior, receipt forgery rejection, missing shot rejection, invalid PNG rejection, three-shot coverage and Mac command syntax.
- Blender worker scripts compile but cannot be imported as `bpy` is absent.
- One-command Mac launcher returns an explicit `BLOCKED` without creating a workspace when no Blender executable is found.
- Existing valid animated `.glb` and previous VTK film preserved; no native `.blend` or Blender MP4 has been fabricated.

## Native Blender proof pending
- Real GLB import into Blender and native scene save.
- Seven multi-pose images and actual evaluated deform meshes/independent parent-relative rotations.
- Three independent 96-frame Blender rendered batches and full H.264 assemble/decode.
- Visual review, shadow/contact/camera continuity, finished-film status and real ChatGPT MCP connection.

## How to reproduce
See `docs/NATIVE_FILM_RUNBOOK.md`; run `bash ./bin/finish-native-on-mac.sh` on a supported Mac with Blender, FFmpeg, Python >=3.11. Technical `PASS` alone is insufficient: inspect final encoded film and user-accessible path.
