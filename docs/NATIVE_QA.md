# Code Video: The Reach — Native Blender Technical Proof

Status: **NATIVE TECHNICAL PASS; ARTISTIC/DEPLOYMENT PARTIAL** (17 October 2026)

## Deliverables
- `Native_The_Reach_12s_480p.mp4`: Blender Eevee render, H.264, 480x270, 24 fps, 288 frames, 12.000 s, yuv420p, silent, no subtitle track.
- `Native_The_Reach_Editable.blend`: native Blender 5.2.2 project, 18-bone armature, four continuously weighted limb meshes, camera and lighting setup, keyed gestures and prop constraints.

## Original source and transport integrity
- MP4 SHA-256: `e180b5320636c2d31b411426f526eb27795b5e0e6895230bcf94c133b758e022`
- BLEND SHA-256: `3a778c61eaa53493d1471df54c3ccd1a4d5967e54bc3c575a2b3a9aefae98ceb`
- All 288 source PNGs checked against their Blender frame ledger before encoding on Big Mac.
- Full MP4 decode passed on Big Mac and in this deliverable container.
- Native .blend was independently loaded on MacBook Air Blender 5.2.2; measured motion of all four weighted meshes using evaluated geometry across frames 1, 96, 145, 224, and 288.
- At the reported frame 224, Blender prop constraint contact target error = 0.0m. This is an internal goal comparison, not proof of flawless visual hand-object fit.
- Representative encoded frames visually inspected. Technical 3-shot acting is visible, with deliberately modest character and environment art.

## Limits and open gates
- 480x270 native *technical* film, below project 1920x1080 / 30fps quality default.
- This is a new example humanoid actor scene, not a verified import of the original portable GLB into Blender.
- No supplied audio, lip sync, full multi-character acting, or cinematic feature-film certification.
- Live MCP tool invocation through ChatGPT and arbitrary film-input production remain unverified.
- One short freeze-detection segment (first 0.625 s) should receive artistic consideration but is not a missing-frame error.
- Do not label the general Code Video plugin FINISHED_VERIFIED; the native demonstration itself is encoded and hash-verified.
