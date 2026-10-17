#!/bin/bash
# Safe one-command Mac handoff for a verified original Code Video rig.
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source_glb="$repo/examples/portable_actor/the_reach_skeletal_animated.glb"
if [[ ! -f "$source_glb" ]]; then
  printf 'Missing bundled source rig: %s\n' "$source_glb" >&2
  exit 1
fi
if [[ -n "${CODEVIDEO_BLENDER:-}" ]]; then
  blender="$CODEVIDEO_BLENDER"
elif command -v blender >/dev/null 2>&1; then
  blender="$(command -v blender)"
elif [[ -x /Applications/Blender.app/Contents/MacOS/Blender ]]; then
  blender=/Applications/Blender.app/Contents/MacOS/Blender
else
  printf 'BLOCKED: Native Blender is not installed. Install Blender 4.5 LTS or later, then rerun.\n' >&2
  exit 2
fi
if [[ ! -x "$blender" ]]; then
  printf 'BLOCKED: Blender path not executable: %s\n' "$blender" >&2
  exit 2
fi
for program in python3 ffmpeg ffprobe; do
  if ! command -v "$program" >/dev/null 2>&1; then
    printf 'BLOCKED: Missing %s; install it before rendering.\n' "$program" >&2
    exit 2
  fi
done
# Demand Python 3.11+ and explicit Python package preflight before creating files.
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' || {
  printf 'BLOCKED: Python >=3.11 required.\n' >&2; exit 2;
}
# Never infer another machine or privileged directory. This stays in the user's home.
workspace="${CODEVIDEO_WORKSPACE:-$HOME/Documents/CodeVideoNativeWorkspace}"
case "$workspace" in
  /*) ;;
  *) printf 'BLOCKED: CODEVIDEO_WORKSPACE must be absolute.\n' >&2; exit 2 ;;
esac
if [[ "$workspace" == / || "$workspace" == "$HOME" ]]; then
  printf 'BLOCKED: Refusing a broad workspace root.\n' >&2; exit 2
fi
mkdir -p "$workspace/assets"
if [[ ! -f "$workspace/assets/the_reach_skeletal_animated.glb" ]]; then
  cp "$source_glb" "$workspace/assets/the_reach_skeletal_animated.glb"
fi
python3 - "$source_glb" "$workspace/assets/the_reach_skeletal_animated.glb" <<'PY'
import hashlib,sys
p,q=sys.argv[1:]
H=lambda name:hashlib.sha256(open(name,'rb').read()).hexdigest()
if H(p)!=H(q):raise SystemExit('BLOCKED: Existing workspace GLB differs from source; do not overwrite.')
PY
# Dependencies are installed only into the workspace's own venv; never system Python.
venv="$workspace/.venv"
if [[ ! -x "$venv/bin/python" ]]; then python3 -m venv "$venv"; fi
if ! "$venv/bin/python" -c 'import numpy' 2>/dev/null; then
  "$venv/bin/python" -m pip install --disable-pip-version-check 'numpy>=1.24'
fi
if ! "$venv/bin/python" -c 'import codevideo' 2>/dev/null; then
  "$venv/bin/python" -m pip install --disable-pip-version-check -e "$repo"
fi
run="${1:-reach_native_$(date -u +%Y%m%dT%H%M%SZ)}"
case "$run" in
  *[!a-zA-Z0-9_-]*|"") printf 'BLOCKED: Run ID must be ASCII alphanumeric, underscore or dash.\n' >&2; exit 2 ;;
esac
export CODEVIDEO_BLENDER="$blender" CODEVIDEO_WORKSPACE="$workspace" PYTHONPATH="$repo"
printf 'Blender: %s\nWorkspace: %s\nRun: %s\n' "$blender" "$workspace" "$run"
"$venv/bin/python" -m codevideo.cli --workspace "$workspace" native-finish \
  assets/the_reach_skeletal_animated.glb "$run" --width 960 --height 540 --samples 12 --max-seconds 7200
