# Portable Rig Contract (v0.3.1)

Use the official glTF 2.0 skin contract: mesh `POSITION`, `NORMAL`, `JOINTS_0` and normalized `WEIGHTS_0`; `skin.joints` order must match the per-joint inverse bind matrices. Animated nodes use absolute timestamps and translation/quaternion channels; non-root joints must independently affect evaluated geometry. Cinder's 4 actual skin groups use 2 joint influences per vertex and moving appendage end-effectors, with rigid torso/head/face supports and an independently animated orb.

This workflow has two **different** evidence classes:
1. **Local portable rig PASS:** Exact GLB bytes are parsed, all 289 sampled frames reproduce the Cinder actor's CPU weighted-mesh deformation, an independent 3D mesh loader accepts the asset, a source SHA-256 receipt exists. This is an *asset-level* proof. The GLB does not contain the final MP4 or Blender `.blend`.
2. **Actual Blender import PASS:** A real Blender executable imports that exact GLB, constructs real Armatures and ARMATURE modifiers, proves independently changing non-root joints and evaluated vertex deformation, saves an actual `.blend` and seven fixed-camera diagnostic PNGs, and produces a locally signed receipt. This gate is unavailable in the original build container. Final film delivery requires a separately rendered, fully decoded and visually examined Blender MP4.

Local commands: `codevideo portable-rig-export NAME`, `codevideo portable-rig-check portable_rigs/NAME/portable_rig_receipt.json`.
Blender host commands: `codevideo portable-rig-import portable_rigs/NAME/the_reach_skeletal_animated.glb NEW_ID`, `codevideo portable-import-check portable_imports/NEW_ID/blender_import_proof.json`.

Never guess `.blend` paths, construct fake proof JSON, reinterpret VTK or glTF math as native Blender evidence, silently install Blender, or overwrite an existing output ID. Do not claim ChatGPT MCP deployment until the actual connection handshakes successfully.
