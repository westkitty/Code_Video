# Code Video — Operational State

Project: Code Video Production Kernel
Current source revision: v0.3.2 native Blender film execution path (local QA complete, host Blender execution unavailable)
Preserved baseline: v0.3.1 exact exported animated GLB and v0.3.0 12-second VTK MP4; no originals overwritten.

## Locally verified
- Baseline v0.3.1: 68/68 tests pass; actual portable 360,360-byte skeletal GLB and independent skinning math are intact.
- v0.3.2: Python native production coordinator, Mac Bash handoff, native Blender shot worker, camera setups and exact 3x96 shot graph implemented; 81/81 local regression tests PASS, including 13 new/native-lane checks.
- Native-film preflight refuses missing Blender *before* writing render directories, proving the fail-closed blocker on this host.
- Signed shot/final-receipt guard code verifies source revision, 288 exact frame hashes, proper PNG headers and dimensions, three source-matched shot receipts, H.264 metadata and a full decode. This path is **code-tested but not Blender-executed**.
- Previous v0.3.1 validator, exporter, VTK film, Blender source, and no-subtitle preference preserved.

## Not verified / blocked
- No Blender binary, `bpy`, or online authorized Mac workstation in this isolated runtime; package DNS failed. No native `.blend` or Blender-rendered MP4 was made.
- Script has not demonstrated actual glTF import, Blender rendered skinning, animated contact, cinematography or human visual acceptability in Blender.
- MCP protocol handshake / ChatGPT plugin installation unverified; no cloud tunnel or account mutation.
- This is a **native-runner-ready** release only, not finished Blender film proof.

## Resume contract
1. On an authorized Mac with Blender 4.5+ and FFmpeg, extract plugin ZIP and run `bash ./bin/finish-native-on-mac.sh` in its root; optional run ID to resume verified shot receipts.
2. Observe native import proof PASS (four deform meshes, >=4 moving non-root joints, seven real PNGs, saved `.blend`).
3. Verify all 3 native shot receipts; encoder must produce 288 frames at 24fps/12s, yuv420p H.264, full decode.
4. Visually inspect encoded entrance/middle/exit and contact/cuts; ensure native film is actually accessible to user.
5. Only then promote native Blender gate, deploy MCP with user consent and archive verified artifacts AFTER showing them to user.

## Protected
Original GLB/MP4, no subtitles, no unapproved voices, no still/slideshow substitutes, no invented Blender results, no default publication, no overwrite or force-push.
