# Code Video v0.3.2 — Release QA

**Source/package verdict: PASS. Native Blender film verdict: BLOCKED (Blender executable unavailable).**

- 81/81 local regression tests passed.
- Basic Skill validator and strict release certifier passed.
- Both source and Blender worker scripts compile. Wheel build includes `blender/import_portable_rig.py`, `blender/render_native_frames.py`, `codevideo/native_finish.py`.
- Native Mac one-command launcher passes shell syntax and exits 2 without creating a render directory when Blender is unavailable.
- Existing real animated skinned GLB independently verifies four skins, nine animated joints, 289 samples.
- Existing real VTK MP4 independently passes full decode with 288 frames, 12 seconds; this is **not** a Blender film.
- Remote access: DEX//REACH internal error, Desktop Commander device offline; this container has no Blender executable or accessible package network.

## Unverified
- Real Blender glTF import, armature/skin deformation in bpy, saved .blend, diagnostic PNGs, native 12s MP4, artistic QA, actual user-accessible native video link and live ChatGPT MCP host connection.

**Do not call `FINISHED_VERIFIED`.** The only honest finish condition is running the native host path and inspecting the resulting encoded video. Original versions preserved.
