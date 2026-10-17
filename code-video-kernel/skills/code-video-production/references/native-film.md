# Native 3D film contract (0.3.2)

Use this only when real Blender and signed portable import proof are available.

- Required input: exact workspace-contained skinned GLB, source hash, and an original run ID. No Starsilk without explicit canon verification.
- Entry: `codevideo native-finish assets/the_reach_skeletal_animated.glb reach_native_001` (Blender required). Output is a new native `.blend`, 7 diagnostic images, 3 signed 96-frame batches, a 288-frame 24fps 12-second H.264 MP4 and local receipts; subtitles/audio remain OFF for this original benchmark.
- Mac convenience: `bash ./bin/finish-native-on-mac.sh` from full plugin source. Requires verified Python >=3.11, Blender 4.5+, FFmpeg; can explicitly set `CODEVIDEO_BLENDER=/Applications/Blender.app/Contents/MacOS/Blender`. Python packages are scoped to a dedicated workspace venv.
- Host preflight must fail before creating any project when Blender is missing. Do not fabricate a substitute `.blend` or claim a native render from a glTF file alone.
- `codevideo native-shot IMPORT_RECEIPT recognition|struggle|resolution NEW_ID` may rerender an affected shot; completed signed shot receipts can be reused. `codevideo native-assemble FILM_ID SHOT1 SHOT2 SHOT3` requires exact film coverage. `codevideo native-film-check RECEIPT` rechecks source/frames/MP4.
- A benchmark checks one real Blender-rendered frame for each shot. If it predicts runtime beyond the configured budget, stop before full shot rendering and report `RENDER_BUDGET`.
- Every output file must match a signed, source-locked receipt and scene hash; a corrected source requires a new ID. A tampered source or missing frame must fail closed.
- After encoded structural/decode PASS, inspect face, weight shifts, actual grip, moving deformed skin, frame margins, shadows, cuts and contacts. Only human/video-artifact inspection can promote artistic acceptance, and a host-tested user-accessible link is mandatory for FINISHED_VERIFIED.
- The original 0.3.2 build sandbox has no Blender, so the native path cannot be honestly marked executed there. Remote tools must be selected and authorized live; do not silently trigger unapproved cost or machine changes.
