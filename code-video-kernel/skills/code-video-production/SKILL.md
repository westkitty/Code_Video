---
name: code-video-production
description: Use when the user requests creation, continuation, repair, animation, rendering or verification of a genuine rigged 3D puppet film in Code Video, especially articulated characters, full music videos, flight, physical acting, Blender scenes or playable MP4 delivery. Operate the Code Video Production Kernel through an authorized MCP connection or available local scripts. Require verified evaluated bone-relative motion, geometry influence, actual rendered frames (Blender or evidence-bounded VTK mechanical and weighted-mesh acting proofs), full encoded-video checks and visual review. Never treat paper rigs, orbit-only movement, cutouts or synthetic test videos as finished films. Do not trigger for critique-only, text-only prompts, general video questions or static illustrations.
---

# Code Video Production

## Purpose
Produce inspectable, articulated *volumetric* 3D puppet films using evidence-bound tools, honest stage statuses and independent encoded-frame proof. An instruction or JSON receipt alone is not a render.

## Trigger conditions
Use for authorized Code Video film production, continuation, real 3D character animation, verified MP4 delivery, rig repair and existing Code Video project validation. Resume existing shots, cache and reference locks before creating substitutes.

## Non-trigger conditions
Do not run renderers for a request asking only for critique, plans, prompts, explanations, a Skill/plugin audit, or a static picture. Do not route unrelated software animation to this pipeline without a 3D puppet-film objective.

## Required inputs
A film intent or existing scene/project, user constraints, an available runtime and accessible source materials. When the premise is missing, invent an appropriate setup, escalation and payoff. Actual canon assets, lyrics, references and audio must be retrieved and verified, not guessed.

## Optional inputs
A current `.blend`, shot graph, signed proof, audio, immutable reference registry, rig manifest, contact/prop ledger and prior render receipts. Inputs outside a configured workspace require separately authorized staging.

## Default assumptions
Use 1920×1080, 30fps, H.264/yuv420p, AAC for supplied audio, subtitles **OFF**, complete audio coverage and a motivated shot sequence. More than four independent joints are desirable; at least four non-root, geometry-driving, separately timed joints are required. Never select Starsilk unless clearly invoked.

## Feasibility limits
A standalone Skill does not install Blender, create MCP credentials, grant machine access or host a server. `skill.zip` contains workflow instructions, not the kernel binaries. A working kernel is a separate prerequisite for technical execution; its available tools must be discovered live. Blender and real MCP transport remain unverified in the current environment; VTK-EGL mechanical and four-limb weighted-mesh 3D acting demonstration were verified on the isolated build host. This does not prove the user's Mac or ChatGPT connection.

## Workflow
1. **Discover:** Confirm connected MCP tools or local `codevideo` executable; inspect workspace, Blender, FFmpeg, disk, actual references and audio. If unavailable, report a precise `BLOCKED` gate; never produce a 2D substitute.
2. **Lock identity:** For approved recurring characters, inspect current governing records, approved real image pixels and the authorized reference workflow. Preserve protected anatomy, markings, props and exclusion rules; do not register new canon implicitly.
3. **Direct:** Write/validate a complete `codevideo.shotgraph.v1` shot graph. Define purpose, emotion, performances, screen direction, camera, depth, cuts, light and actor/prop continuity. Avoid ornamental camera-only motion.
4. **Model/rig:** Use a real Blender armature and deforming organic skin or intentionally mechanical bone-parented solid meshes. Lock rest/bind pose, topology, bone constraints and relevant controls.
5. **Prove:** Run `inspect_real_rig` / `rig-proof` with >=5 varied frames. Require evaluated relative rotations and geometry-driving joints; reject synchronized, offscreen, cosmetic or root-only channels. Inspect anatomical extremes and silhouettes before full rendering.
6. **Block and act:** Produce timed low-cost playblasts, check anticipation, intention, impact, weight, plant/contact, reach, flight stroke, eye line, expressions and follow-through. No full render until acting and spatial continuity are judged usable.
7. **Sound:** Respect supplied duration and actual lyrics/phonemes. For speech or song, synchronize differentiated mouth/viseme/head/eye motion to verified timings; otherwise record `LIP_SYNC_UNVERIFIED`. Do not introduce synthetic narration or captions without authorization.
8. **Benchmark:** Render genuine entrance/middle/exit samples for each shot, inspect the sample outputs, and report render cost. Missing/stale benchmark = no full render.
9. **Render:** Use `render_verified_shot` in bounded, resumable batches, never trust unsigned cached PNGs. Inspect framing, mesh deformation, clipping and prop positions. Re-render failed frames only, retaining valid evidence.
10. **Encode:** Assemble only if signed full-shot receipts cover every expected frame. Preserve complete authorized source audio; create MP4, probe/count frames, fully decode and inspect audio/subtitle streams.
11. **Review:** Extract actual *encoded* entrance/middle/exit frames plus joint extrema, contacts and cuts. Inspect every shot for identity, independent articulation, weight, silhouette, camera, lips and audio. `ffprobe PASS` never equals artistic PASS.
12. **Deliver:** Expose a real working MP4 link **before** Drive archival, then native `.blend`, code, source hashes, shot graph, diagnostic poses, receipts, QA report and reproducibility instructions. Archive only if authorized and connected.

## Optional headless proof-of-reality lane
When Blender is absent but VTK is actually installed and a **noncanonical segmented mechanical proof demonstration** is useful, call `render_mechanical_3d_smoke` or `codevideo vtk-demo NAME`. This is actual parented, volumetric 3D, not a slideshow or still. Require per-joint fixed-camera image changes, >=4 distinct non-root channels, frame/screen-bound checks and a fully decoded MP4. Use `check_articulated_3d_stage` or `vtk-check` to independently confirm the signed local receipt and image hashes. Modify joint curves in the resulting JSON and call `replay_articulated_3d_stage` or `vtk-replay` with a new ID. Never label this demo `FINISHED_VERIFIED`, claim organic skinning or substitute the prebuilt mechanical puppet for a requested canon character. Follow [VTK demonstration contract](references/vtk-demo.md).

## Golden Scene — v0.3.0 actor-quality gate
For an original, noncanonical benchmark character with an available VTK renderer,
prefer the contact-aware **The Reach** experiment over an ornamental turntable.
The VTK actor is a real 3D skinned mesh with normalized weights, numerical IK, planted
feet, parented head motion, and explicit world-to-hand prop transfer, not an image warp.
Run independent shots through `render_golden_actor_shot` (frames 0–95, 96–191, 192–287),
check each receipt with `verify_golden_actor_shot`, assemble via
`assemble_golden_actor_film`, then verify through `verify_assembled_actor_film`.
The CLI equivalents are `actor-batch`, `actor-batch-check`, `actor-assemble`,
`actor-assembly-check`. A signed partial shot is **not** a playable film.
The assembled technical PASS does not certify organic Blender armature rendering,
facial/phoneme acting, human cinematic quality or user-accessible plugin deployment.
Read [Actor Engine lane](references/actor-engine.md) and [Blender gate](references/blender-integration.md).

## Tool/script/reference guidance
- The plugin root contains the executable Python package and Blender scripts. The separate Skill ZIP does not. Discover `preflight`, `inspect_real_rig`, `check_rig_receipt`, `benchmark_real_render`, `render_verified_shot`, `encode_complete_film`, `inspect_encoded_video`, `prepare_visual_review` and `production_verdict`; plus optional VTK `render_mechanical_3d_smoke`, `check_articulated_3d_stage`, `replay_articulated_3d_stage`, `render_golden_actor_shot`, `verify_golden_actor_shot`, `assemble_golden_actor_film`, and `verify_assembled_actor_film`; never assume MCP availability.
- Use [tool contract](references/tool-contract.md) for endpoint, CLI and runtime boundaries; [proof contract](references/proof-contract.md) for gate definitions. These references are bundled inside this standalone Skill.
- Keep writes inside an independently verified dedicated workspace. No arbitrary shell/MCP command execution, public tunnel, unapproved publication or spending. Never treat an untrusted source `.blend` as harmless executable input.

## Output format
Show MP4 first when genuinely available. Classify every stage as `PASS`, `FAIL`, `BLOCKED` or `UNVERIFIED`, and the production as `PARTIAL`, `RIGGED_UNRENDERED`, `TECHNICAL_PASS_VISUAL_PENDING`, `ENCODED_UNVERIFIED` or `FINISHED_VERIFIED`. Include exact evidence paths/hashes only when observed; distinguish human artistic review from machine checks.

## Error handling
If a dependency, actual source reference, external host, consent or render fails, stop only that branch and preserve previous verified outputs. Log exact frame/shot, error and next recoverable action. Retry a corrected source or frame once evidence changes; do not blindly loop. Failed camera/framing or lip-sync review remains `UNVERIFIED` even when encoding succeeds.

## Final quality checklist
- [ ] Actual renderer host and source bytes verified; no assumed install. VTK mechanical or weighted-mesh film never substitutes for a separately evaluated organic Blender armature proof.
- [ ] Canon/identity proof passed when relevant; original media protected.
- [ ] Genuine volumetric rig and >=4 meaningful non-root geometry-driving channels measured.
- [ ] Blocking, contacts, silhouette and animated shot bounds visually inspected.
- [ ] All shots have coherent spatial/prop continuity and motivated camera moves.
- [ ] Full requested audio covered; no unwanted narration/subtitles; lipsync evidence honest.
- [ ] Every frame provenance-verified; encoded MP4 fully probed and decoded.
- [ ] Every encoded shot reviewed; playback link accessed; final status justified.

## Portable animated skeleton bridge (v0.3.1)
When Blender is unavailable but the authorized goal is native skeletal character handoff, prefer actual skinned **glTF/GLB interchange** to a mock `.blend`. Use `export_portable_animated_rig` or `codevideo portable-rig-export NAME` in a dedicated workspace with NumPy. Verify using `verify_portable_animated_rig` / `portable-rig-check`; it inspects actual JOINTS_0, WEIGHTS_0, inverse bind matrices, bone hierarchy and 289 animation samples, including prop attachment. This creates an editable animated 3D rig, **not a playable new film or native Blender proof**.

On a verified Blender host, execute `import_portable_rig_in_blender` / `portable-rig-import GLB NEW_ID`, then `verify_native_import_receipt` / `portable-import-check RECEIPT`. Require imported Blender ARMATURE modifiers, >=4 independently animated non-root joints, >=4 evaluated deform meshes, a saved native scene, seven diagnostic images and a locally signed receipt. Missing host, import, skinning, renders, or signed receipt means `BLENDER_ARMATURE_UNVERIFIED`; never report it as finished. See [Portable rig gate](references/portable-rig.md).

## Blender-native Golden Scene completion lane (v0.3.2)
When asked to finish the native Blender 3D actor pipeline, verify the **actual** host and source. Use `codevideo native-finish GLB NEW_RUN_ID` on an authorized machine with Blender 4.5+, Python and FFmpeg, or `finish_native_blender_actor_film` only if the connected MCP host has demonstrated authenticated connectivity and adequate job lifetime. On Mac, the bundled complete-plugin source offers `bash ./bin/finish-native-on-mac.sh` to stage the original, noncanonical `The Reach` GLB in a dedicated workspace. The script cannot install Blender itself.

The native import must prove real armature modifiers, four evaluated deforming meshes, four nonroot independently animated joints and seven fixed-camera diagnostic renders. The new film producer performs a **real Blender frame benchmark** then renders three separately signed 96-frame shots with automatically fitted director cameras. It assembles only exactly 288 verified source-matched frames, full-decodes a 24fps H.264 MP4 and enforces subtitles OFF. Reuse only signed revision-matching receipts; never trust copied PNGs. Even with code and encode PASS, classify `TECHNICAL_PASS_VISUAL_PENDING` until shot-by-shot artistic and playback inspection succeeds. Read [Native Blender run contract](references/native-film.md) and [Blender integration](references/blender-integration.md).

If Blender or remote host is unavailable, return `BLOCKED BLENDER_RUNTIME` and preserve the verified v0.3.1 GLB and v0.3.0 VTK film. Do not invent a `.blend`, claim organic native rendering, or substitute VTK film. A syntax-only Blender worker test is *not* a native rig/film PASS. An unconnected MCP server is not an installed plugin.
