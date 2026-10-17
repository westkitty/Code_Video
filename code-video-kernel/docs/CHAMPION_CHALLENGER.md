# Code Video Champion vs Challenger — 0.1.1 vs 0.2.0

**Same runtime:** isolated Linux container with Python, FFmpeg/FFprobe, VTK-EGL and Pillow, without Blender, the official MCP SDK or internet package downloads. Audited 2026-10-16/17.

| Acceptance dimension | 0.1.1 champion | 0.2.0 challenger | Evidence |
|---|---|---|---|
| Real volumetric 3D puppet can render HERE | BLOCKED: Blender not installed | **PASS for noncanonical segmented mechanical demo** | `144` actual 960x540 VTK-EGL frames, MP4 full decode |
| Joint independence | Signed Blender probe exists but cannot run here | VTK demo has **14** independently timed non-root channels | actual per-bone keyed rotations and distinct temporal envelopes |
| Joint geometry really changes | Blender fixture tests; no actual GPU render | **8** individually isolated joints change rendered pixels with fixed root/camera | neutral and isolated diagnostic renders, signed hashes |
| Camera clipping | General guidance only | Subject boundary check measured on every demo frame; camera crop found and repaired | Minimum silhouette distance **58 pixels** from image edge |
| Editable motion | Blender Python source after installing Blender | Replay actual edited `rig_scene.json` joint curves into NEW separate MP4 | real changed-video-hash regression |
| Frame provenance | Signed Blender receipts and audio-safe encoder | Original functionality preserved + local signed VTK source/scene/frame/diagnostic/video hashes | actual `vtk-check` PASS |
| Synthetic MP4 QA | FFmpeg real decode | Preserved | regression suite |
| Automated unit/integration tests | **37 passing** | **46 passing** | independently rerun same host |
| MCP adapter tools | 11 registered in mock | **14 registered in mock** | tests; live MCP SDK still unavailable |
| Real Blender organic skinning | UNVERIFIED | UNVERIFIED | Blender missing; no false pass |
| ChatGPT-connected plugin | NOT CONNECTED | NOT CONNECTED | requires official SDK + authenticated endpoint |
| Render quality & anatomy | Not assessed | Basic proof-grade mechanical cartoon only; **not cinematic feature-film quality** | inspected review frames; human emotional acting not certified |

## Champion's preserved strengths

The revised release **does not replace** the proven Blender rig inspector, source/shot/frame cache signatures, full-shot receipts, MP4 encoder, or visual-review status barriers. Rendering for the user's real organically deforming character still uses Blender by default. No image-based character cutouts are introduced.

## Challenger's genuinely different mechanism

The new VTK backend can create a proof-of-reality stage without Blender: actual `vtkAssembly` hierarchical transformations parent real 3D mesh volumes. A fixed camera and stationary root isolate one non-root joint at a time, and changed pixels are counted from actual rendered geometry. It exports editable animation curves, creates an independently reproducible new version on replays, rejects static-track manipulations before rendering, checks frame-by-frame subject bounds, and binds artifacts to hashes.

**Evidence:** Demo source `11c71832232e54b83d8315490ebc02d632f6c19e5b2c4a833515bc4a0f99974a` (SHA-256), MP4 `8209d747cc7ba35792c5ed6d617e658f198ac2841b2d8483fc6c8a1c726e4d21` (SHA-256), 144 frames at 24fps, 960x540, render wall time 17.535 seconds on this runtime. This is a single observed run, not a render-speed benchmark against Blender.

## Costs & counterevidence

VTK is an optional substantial dependency that may not be available or fast on the user's Mac architecture; installation is **not** presumed. It provides intentionally segmented geometry only, not Blender armature skinning, facial speech controls, flight physics, real foot IK, approved visual canon, or full user audio. It is a production-health demonstration, not automatic film production. Animated orthographic/3D depth, camera work and actual mesh movement do not alone certify high artistic quality.

## Verdict: SURPASSES as a verifiable developer proof system; COMPETES/UNVERIFIED as a complete film studio

0.2.0 preserves 0.1.1's prior passing tests and adds an important actual-rendering fallback and stronger framed-scene evidence. It does **not** pass the all-gates finished-film acceptance test; live Blender/organic animation and real ChatGPT MCP connections remain unresolved.
