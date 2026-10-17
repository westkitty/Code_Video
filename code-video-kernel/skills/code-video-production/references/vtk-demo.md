# VTK Real 3D Mechanical Demonstration Contract

This is an optional, original, noncanonical mechanical proof-of-reality path. It is not Blender, not organic skinning, not a complete film production pipeline.

**Trigger:** Only when the user authorizes an actual segmented mechanical 3D demonstration, asks to test the Code Video production kernel, or when Blender is unavailable and a small truthful engine-specific rig proof would materially help. Never replace requested real characters with the demo.

**Runtime:** `pip install -e ".[vtk-demo]"` must succeed on the authorized host; requires VTK with a functioning offscreen/EGL/OpenGL renderer plus FFmpeg/FFprobe. Do not assume wheel/driver support on macOS or Android. No Docker dependency.

**CLI:** `codevideo vtk-demo DEMO_ID`, `codevideo vtk-check projects/DEMO_ID/stage_receipt.json`. Motion editing: modify `projects/DEMO_ID/rig_scene.json` joint_tracks; `codevideo vtk-replay projects/DEMO_ID/rig_scene.json NEW_DEMO_ID` creates a new immutable output directory. Existing source is preserved.

**MCP:** `render_mechanical_3d_smoke`, `replay_articulated_3d_stage`, `check_articulated_3d_stage`. Discover tools live. Heavy renders require explicit user authorization for target/runtime costs; use only dedicated workspace paths.

**Pass evidence:** Source program and per-frame models, parented VTK vtkAssembly hierarchy, independently animated bone angles, >=4 visible fixed-camera isolated joint image effects, no bounding-box edge cutoffs, `ffprobe` actual 144 frames at 24fps 960x540 by default, full MP4 decode, signed receipt over scene/render/script/diagnostics/video. No subtitles/audio. Synthetic source assets are not substituted for user-provided characters.

**Limits:** HMAC is local provenance not tamper-proof proof against a privileged hostile local user; the source JSON exposes motion and hierarchy, while mesh topology and camera editing require Python source. Shader/physical-light quality, foot locks, organic skinning, canon, lips, audio and performance artistry are not certified. Return `TECHNICAL_PASS_VISUAL_PENDING` until independent human/vision review plus accessible delivery are evidenced. Never upgrade it to `FINISHED_VERIFIED` by JSON alone.
