# Protected regression fixtures

- Blender absent -> BLOCKED; never claim rig or rendered MP4.
- Fake manifest lists four bones with root-only motion -> reject as non-articulated.
- Existing unsigned PNG with correct dimensions -> DO NOT trust or sign as Blender-rendered.
- Signed receipt lists 1/30 frames -> reject complete encode.
- Two or more joints duplicate normalized timing -> do not count as independent.
- Arbitrary H.264 MP4 matches frame count but has no rig/source receipt -> do not claim Code Video technical completion.
- Valid MP4 but encoded character clips camera and wings -> visual QA FAIL; do not report FINISHED_VERIFIED.
- Source song exists, timeline truncates 20 seconds -> block full-audio export.
- External reference path named APPROVED but no verified registry/pixels -> stop before canonical character model.

## VTK 0.2.0 regressions
- On a Blender-free host with verified VTK, a mechanical smoke test may generate real volumetric stage frames; report them as a mechanical demo, not a Blender-certified production.
- Change only the root or camera while all joint orientations remain fixed: the validator must not accept it as articulated performance.
- Keep camera/root fixed and rotate a detached bone without bound geometry: the proof must not count it as visible articulation.
- Change JSON head keyframes and replay to a new ID: actual final MP4 must differ, and the old source/video must survive.
- Tamper with a diagnostic PNG, a source frame, the source JSON or the MP4: the signed stage checker must fail.
- Clip a character against any image boundary: screen safety must report failure and prevent release.
- Ask for Shard-God: never replace with the synthetic mechanical demo instead of retrieving canonical approved images and actual anatomy.

## v0.3 actor regressions

- Positive: user asks for a 3D benchmark reaching scene with actual weighted meshes,
  planted feet, and an encoded MP4 => choose actor pipeline when runtime permits.
- Negative: user asks for text-only changes to instructions => do NOT render.
- Missing Blender: actual VTK CPU-skinned scene may render as a limited proof, but do
  NOT call it a native Blender armature or finished feature film.
- Interrupted full render: refuse unsigned previously-rendered PNGs; use three new
  source-verified shot batches instead of silent reuse.
- Missing or overlapping shot range: `actor-assemble` MUST BLOCK.
- Scene edited between batches: mixed scene-hash final assembly MUST BLOCK.
- Bent joint with unconstrained IK or non-normalized skin weights: MUST BLOCK.
- A user asks to verify music lip-sync with no source transcript: `LIP_SYNC_UNVERIFIED`.

## Portable rig v0.3.1 regressions
- Valid GLB contains four skin objects, true joint/weight attributes, 289 animation samples and source-bound hashes; `portable-rig-check` passes after a fresh export.
- Tamper bone quaternion, mesh rest vertices, weight buffer, parent hierarchy or sphere ownership samples: local geometric proof fails.
- Supply a fake Blender receipt with plausible meshes/joints and fake `.blend`: native check refuses unsigned provenance.
- Run native import without Blender executable: `BLOCKED` with no fake native output directory.
- Run duplicate export ID: refuse overwrite. Do not promote portable asset proof into a Blender or MP4 completion claim.

## Native film v0.3.2 regressions
- Blender absent: native-finish BLOCKED before any output directory is created.
- Unsigned fake shot/movie JSON: FAIL.
- Existing incomplete import or stage ID: do not overwrite; require new ID or signed receipt reuse.
- Missing one of 288 PNGs, mismatched widths/heights, reused unsigned frames, altered .blend or revision drift: reject assembly.
- Real Blender benchmark over time budget: refuse full shot, preserve source.
- Full MP4 metadata/decode must match 288 frames at 24fps, 12 seconds, yuv420p and no audio/subtitles.
- Native Blender host not connected: do not claim a .blend or Blender MP4; preserve GLB and previous VTK film.
