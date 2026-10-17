# Tool and runtime contract

The **separate** Code Video Production Kernel plugin provides the MCP server and CLI. A standalone Skill installation does not provide the renderer or connection. Never claim the Skill alone generates videos.

Discover actual MCP tool availability live. Typical tools: `preflight`, `create_project`, `check_shot_graph`, `inspect_real_rig`, `check_rig_receipt`, `benchmark_real_render`, `render_verified_shot`, `encode_complete_film`, `inspect_encoded_video`, `prepare_visual_review`, `production_verdict`. Remote MCP must be intentionally connected through a secure authenticated endpoint/tunnel; localhost HTTP cannot be reached from ChatGPT web directly.

For local CLI hosts with authorized filesystem access: install Python >=3.11, FFmpeg and Blender; configure `CODEVIDEO_WORKSPACE` to a dedicated directory; `codevideo preflight`, `codevideo init PROJECT`, `codevideo rig-proof SCENE --frames 0,8,17,24,32`, `codevideo benchmark GRAPH PROOF SHOT`, `codevideo render GRAPH PROOF SHOT`, `codevideo encode GRAPH PROOF`, `codevideo verify VIDEO --graph GRAPH`.

Use only verified actual paths. Never use a fabricated `proof/puppet-REPLACE...` path as a working argument. Tool subprocesses invoke known Blender/FFmpeg scripts, never arbitrary user shell. Check tools and permissions before mutations; do not expose unauthenticated HTTP listeners.
