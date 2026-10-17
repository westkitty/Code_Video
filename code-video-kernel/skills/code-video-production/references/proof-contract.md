# Code Video 0.2.0 — Evidence contract

## Gate chain and proof types

- **G0**: `preflight` checks Python, Blender, FFmpeg/FFprobe, source media and disk; absence is `PARTIAL/BLOCKED`, never a render PASS.
- **G1**: Canon and recurring identities are checked by external approved reference workflows. This kernel cannot certify character approval.
- **G2/G3**: Run *actual Blender* probe on a saved, current SHA-256-bound `.blend`; validate >=5 matching sample frames, bone ancestry, >=4 separately timed non-root joints driving real mesh geometry. Segmented bodies need bone-parented volumetric pieces; organic bodies need weight-skinned changing mesh vertices. **Blender path still certifies one armature per scene only**; multi-armature scenes fail closed pending per-puppet proofs.
- **G4**: Real acting, contact, weight, facial performance, wing anatomy and readable silhouette require shot-level artistic inspection. Skeleton math alone cannot certify these.
- **G5**: Shot ranges start at 0, are contiguous and inclusive, FPS integer 1–120, all camera/acting fields present and source audio timeline complete. Actual scene camera existence is tested when Blender renders.
- **G6**: Each per-shot frame is provably among signed matching benchmark/progress/full-shot receipts; final shot receipt covers **all exact frames**. FFmpeg segments and completed delivery are cache-bound to SHA-256 of frame contents and audio; final MP4 must pass FFprobe plus full decode, audio/subtitle checks and required stream/frame counts.
- **G7**: From the actual encoded MP4, inspect every shot's entrance/mid/exit, extrema, joints, clipping, contact and continuity. Review extraction is a single FFmpeg pass. The kernel generates review evidence but never approves its own artistry.
- **G8**: Verify that the user can access and play the delivered file. Local existence is not enough. Present outputs before any requested archive write.

## Receipt trust boundary

Local receipts carry an HMAC bound to the dedicated workspace's `.codevideo/proof-key`. This detects routine tampering and accidental mixing of separate scenes. It is **not a hostile-local-actor attestation**: anyone with access to the signing key and code can generate new receipts. Synthetic test fixtures explicitly exercise this local trust boundary; they are never proof that Blender ran.

A PNG with matching signature/dimensions is *not* trusted as a render. `benchmark.json`, `progress.json`, or `receipt.json` must be authentic for the active shot/scene/hash, and cached hashes must match. Unknown cached PNGs are rerendered, preserving valid already signed outputs. Rendered pixels must also decode at MP4 assembly time; CRC/header heuristics alone are not full image or cinematic validation.

The render fingerprint covers scene file SHA-256 and relevant shot metadata/renderer script hash. **External dependencies referenced by a `.blend` are not automatically hashed**, so production scenes must stage/lock images, caches and other linked assets; changing an external dependency without changing the `.blend` may invalidate the reuse assumption. The code does not yet provide authoritative external-asset dependency provenance.

## Deployment, authentication and limits

- A separate hosted/secure tunneled MCP server is required for ChatGPT web. The plugin ships no secrets, live endpoint, tunnel or authentication infrastructure. The stdio Agent Plugin declaration is intended for compatible local hosts.
- Blender processes run with `--disable-autoexec`, but this is not a full security sandbox for untrusted `.blend` files. Do not use untrusted linked assets without explicit examination.
- This kernel does not ensure actual physical dynamics, multi-character rig certification, lip-sync accuracy, asset rights, canon fidelity, cinematic judgment or playback reachability.
- `FINISHED_VERIFIED` requires external G7 and G8 proof. `TECHNICAL_PASS_VISUAL_PENDING` remains incomplete until then.

## Independent VTK segmented-puppet proof lane (v0.2.0)

This **does not replace G2/G3 Blender organic skinning** and never changes the Blender proof acceptance path. It provides a real alternative-engine, *mechanical-only* diagnostic under `codevideo vtk-demo`: actual volumetric VTK source meshes, an explicit parent-child `vtkAssembly` rig (not whole-model motion), 14 non-root keyed joint channels, and individually changed geometry with the camera/root held fixed. It saves raw diagnostic PNGs, per-joint changed-pixel counts, actual per-frame PNG hashes, an H.264 MP4 with `ffprobe`/full decode, and a signed local output receipt. It also checks per-frame subject image boundaries; camera clipping fails closed.

A replay from edited `rig_scene.json` produces an entirely new output directory; the camera, material and mesh topology live in editable Python source. The diagnostic source is noncanonical and cannot establish identity, physical contact realism, organic deformation, lip sync, subjective acting, or delivery access. Video status remains `TECHNICAL_PASS_VISUAL_PENDING`. Dependencies: `vtk`, `numpy`, `Pillow`, `ffmpeg`, `ffprobe`; the VTK runtime is an *optional* separate extra. Signatures prove continuity within this workspace, not hostile-local-runner security.
