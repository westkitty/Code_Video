# Code Video — Independent New Film Job Lane (experimental)

This v0.4 development lane adds an original Blender film job through the existing public CLI and MCP adapter. It is NOT a general arbitrary prompt-to-film generator.

## Supported profile

- Exactly one original, NONCANONICAL humanoid with an 18-bone native Blender armature, two-weight continuous limb meshes, IK-planted feet, independent arm/neck/head/spine animation.
- Preset action: uncover_sprout — block push, reveal a luminous sprout, and final reaction.
- Exactly three motivated cameras in a continuous shot timeline; source-bound diagnostics and source hashes.
- Silent 12–20-second film, 24 or 30 fps, 16:9 resolutions 640/960/1280/1920 pixels wide.
- No subtitles. No synthetic voice. No image-cutout or 2D replacement.

Unsupported: arbitrary prompts, multiple characters, quadrupeds, winged flyers, canonical Starsilk characters, user audio, lip sync, freeform performance generation. The engine must reject these and never misrepresent coverage.

## New film source contract

See examples/weight_of_light/job.json for the 1920×1080, 30fps, 360-frame original film fixture The Weight of Light. Every shot declares its purpose, emotion, physical performance, continuity and exact frame range.

## How to run

Create a dedicated workspace outside the repo and copy examples/weight_of_light/job.json into it. Ensure Python >=3.11, Blender 5.2.2 and FFmpeg/ffprobe on PATH. Inside code-video-kernel/:

    export CODEVIDEO_WORKSPACE="$HOME/CodeVideoJobs"
    mkdir -p "$CODEVIDEO_WORKSPACE"
    cp examples/weight_of_light/job.json "$CODEVIDEO_WORKSPACE/weight_of_light_hd.json"
    python3.13 -m codevideo.cli job-preflight weight_of_light_hd.json
    python3.13 -m codevideo.cli job-build weight_of_light_hd.json
    python3.13 -m codevideo.cli job-render weight_of_light_hd.json --max-frames 48
    python3.13 -m codevideo.cli job-produce weight_of_light_hd.json --max-seconds 7200

Set CODEVIDEO_BLENDER to an absolute executable when Blender is installed outside PATH.

## Files

jobs/<job_id>/job.normalized.json: deterministic normalized job and hash.
jobs/<job_id>/scene.blend: native editable Blender scene.
jobs/<job_id>/rig_manifest.json: evaluated parent-relative joint and weighted-mesh proof.
jobs/<job_id>/diagnostics/: rendered pose evidence.
jobs/<job_id>/frames/frame_manifest.json: hashes of real, verified Blender PNG frames.
jobs/<job_id>/film.mp4: only exists after all required frames successfully encode.
jobs/<job_id>/film_receipt.json: FFprobe and full-decode result plus 9 encoded-shot review images.

Jobs are non-overwriting and resumable: every prior PNG is checked against the job, scene and content hash before reuse. Rendering first performs an actual full-resolution per-camera benchmark. A budget breach leaves genuine partial frames and an explicit PARTIAL status, never an impostor full-HD film.

The best possible automated status is TECHNICAL_PASS_VISUAL_PENDING. G7 and G8 require real encoded-frame visual inspection plus a verified accessible published MP4; no unit test alone can certify artistic completeness.

GitHub Pages remains a static showcase and release-download surface; it is not a cloud Blender renderer.
