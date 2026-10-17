# The Weight of Light — Native Film QA, 2026-10-17

## Scope and classification

**TECHNICAL_PASS / VISUAL_ARTISTIC_PARTIAL** for a 12-second, 360-frame, original noncanonical humanoid-action fixture. This is a new scene generated from the public job contract, not a rerender of The Reach. **Not** a claim of a finished arbitrary-input autonomous studio, canonical identity, audio or universal anatomy support.

## Source-bound production

- Contract: `code-video-kernel/examples/weight_of_light/job.json` (`job_id: weight_of_light_release`), 1920×1080, 30 fps, 360-frame continuous three-shot timeline.
- Big Mac Blender 5.2.2 Eevee and FFmpeg (actual execution).
- Actual native Blender scene: `assets/weight-of-light-editable.blend`; original, no private material.
- Actual armature: 18 bones; 11 moving nonroot channels; 4 continuous deforming weighted limb meshes (proof manifest: `docs/weight-of-light-rig-proof.json`).
- Camera/pose preflight: 13 different diagnostic Blender frames inspected before HD production. Shot 3 camera originally clipped the head; camera position/focal length corrected **before** this release scene was built.
- Evaluated bounding-volume contact witness: 5 samples (frames 176/200/220/235/260), maximum hand-to-obstacle clearance 0.00819 metres. Bounding boxes are not a surface-interpenetration solver; residual contact realism is not fully certified.
- The rig worker, helper, scene, job, frame manifest, individual PNG frames and encoded MP4 were hash-bound; all **360/360** PNG frames checked before encoding.

## Encoded media verification

| Requirement | Verified value |
|---|---|
| MP4 | `assets/weight-of-light-native-blender.mp4` |
| Codec | H.264 |
| Pixel format | yuv420p |
| Dimensions | 1920×1080 |
| FPS | 30/1 |
| Duration | 12.000000 seconds |
| Video frames | 360 |
| Audio | Intentionally none |
| Subtitle track | None |
| Full decode | PASS on Big Mac AND independently on MacBook |
| Receipt | `docs/weight-of-light-film-receipt.json` |
| MP4 SHA-256 | `f21002579adca91151e63122f0902a5e4406288a2b236127f15e08d14325f7bf` |
| Blender SHA-256 | `4b9553371f83cf4a0703692d756a5e982e833d0ef12e331f57824a0a85e0c2e2` |

FFmpeg blackdetect found no black intervals. Automated freezedetect at the -50 dB, 0.6-second threshold flagged holds beginning approximately 0.0–1.73, 1.73–2.93 and 11.27 seconds to the end. These are considered **artistic caution**, not a claim that frames were missing; the original scene deliberately includes quiet holds. Do not wave them away as necessarily cinematic.

## Real encoded-frame visual inspection

Independently extracted from the final encoded MP4 and visually inspected at about 0.2, 2.0, 3.8, 4.5, 6.0, 7.8, 8.5, 10.5, and 11.7 seconds. The separate automatic encoded shot-review packet includes each shot entrance/middle/exit.

- **Shot 1, 0–4 s:** true character volume, lights, ground plane, growing preparatory pose. Camera contains the character. Subtle/near-static first two seconds.
- **Shot 2, 4–8 s:** intentionally tight hand/obstacle insert (head is out of frame by design). Skinned arm changes its relative orientation; physical contact against the block is present. Prop displacement is relatively small and may not read strongly to an unbriefed viewer.
- **Shot 3, 8–12 s:** whole actor reappears, sprout becomes visible and blooms, puppet adjusts head, torso and arms in reaction. Final frame is in bounds, no former head clipping.
- **Remaining artistic defects/risks:** restrained action and incomplete anticipation/follow-through readability; nearly static holds; low-complexity visual language; subtle prop movement; possible mechanical/stiff motion; limited testing of penetrations between all geometry. More directorial and performance work is required before claiming exceptional quality.

**Verdict:** G0–G6 pass for this bounded noncanonical film, G7 **PARTIAL** artistically, G8 applies only after public URLs and downloadable native artifacts pass live verification. G9 remains **PARTIAL** (one supported production template, not arbitrary projects). G10 must have fresh successful CI and HTTPS release checks. G11 official MCP in-process handshake passed 33 tools; remote ChatGPT installation unverified.

The 2026-10-17 The Reach release is preserved unchanged.
