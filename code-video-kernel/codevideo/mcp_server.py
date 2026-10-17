"""Official MCP SDK v2 adapter. All paths sandboxed within CODEVIDEO_WORKSPACE."""
from __future__ import annotations
from pathlib import Path
from .common import workspace_root

def build_server(root:Path):
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise RuntimeError('Install optional MCP SDK v2: python -m pip install -e ".[mcp]"') from exc
    app=MCPServer('Code Video - Puppet Production Kernel')

    @app.tool()
    def preflight(media: str = '') -> dict:
        """Read-only: check actual Blender/FFmpeg availability, disk and optional media metadata."""
        from .preflight import preflight as run
        return run(root,media or None)

    @app.tool()
    def create_project(project_id: str) -> dict:
        """Create a new version-safe local 3D film template. Not a render or finished film."""
        from .project import create_project
        return create_project(root,project_id)

    @app.tool()
    def render_mechanical_3d_smoke(project_id: str) -> dict:
        """Heavy optional VTK-EGL test: create new, noncanonical 3D segmented puppet, actually animate 14 independent joints, render verified MP4 and fixed-camera per-joint diagnostic images. NOT a Blender or organic-skinning certification."""
        from .vtk_stage import run_stage
        return run_stage(root, project_id)

    @app.tool()
    def replay_articulated_3d_stage(scene_path: str, new_project_id: str) -> dict:
        """Heavy optional VTK-EGL test: create a NEW project from edited motion tracks in a previously built mechanical 3D rig scene, without overwriting source."""
        from .vtk_stage import replay_stage
        return replay_stage(root,scene_path,new_project_id)

    @app.tool()
    def check_articulated_3d_stage(receipt_path: str) -> dict:
        """Read-only: verify signed actual-VTK-render proof, per-joint pixel evidence, source and playable full-decoded MP4 hash; cannot approve artistic QA."""
        from .vtk_stage import check_stage
        return check_stage(root,receipt_path)

    @app.tool()
    def render_golden_reach_actor(project_id: str) -> dict:
        """Heavy optional real VTK + NumPy LBS performance: produce an original 12-second 3-shot puppet film with arm/leg skinning, two-bone IK, planted feet, and actual prop grasp. Blender organic rig remains UNVERIFIED. Creates new project only."""
        from .golden_reach import render
        return render(root,project_id)

    @app.tool()
    def check_golden_reach_actor(receipt_path: str) -> dict:
        """Read-only: verify local signature and all 288 source frames plus full H.264 decode of golden actor film. Does not approve cinematic quality or Blender armature."""
        from .golden_reach import check
        return check(root,receipt_path)

    @app.tool()
    def render_golden_actor_shot(project_id: str, start_frame: int, frame_count: int) -> dict:
        """Heavy, bounded source-verifiable VTK actor shot (96 frames preferred). New project only; no Blender claim."""
        from .golden_reach import render
        return render(root,project_id,start_frame=start_frame,frames_limit=frame_count)

    @app.tool()
    def verify_golden_actor_shot(receipt_path: str) -> dict:
        """Verify local shot receipt, skinning proof, hashes and frame-range coverage; read-only."""
        from .actor_batches import verify_batch
        return verify_batch(root,receipt_path)

    @app.tool()
    def assemble_golden_actor_film(project_id: str, shot_receipts: list[str]) -> dict:
        """Assemble ONLY three separately signed shot batches covering 288 unique frames, same source revision; full-decode output."""
        from .actor_batches import assemble
        return assemble(root,project_id,shot_receipts)

    @app.tool()
    def verify_assembled_actor_film(receipt_path: str) -> dict:
        """Read-only verify all shot hashes, final MP4 and scene revision; never conflate with artistic approval."""
        from .actor_batches import check_assembly
        return check_assembly(root,receipt_path)

    @app.tool()
    def export_portable_animated_rig(asset_id: str) -> dict:
        """Export a new original 3D glTF/GLB skinned puppet with joints, weights, 12s keyed action. Offline arithmetic proof only; Blender import and production film UNVERIFIED."""
        from .portable_rig import export_reach
        return export_reach(root,asset_id)

    @app.tool()
    def verify_portable_animated_rig(receipt_path: str) -> dict:
        """Verify GLB integrity and animated skinning versus the actor math; does NOT certify Blender execution or theatrical quality."""
        from .portable_rig import check_export
        return check_export(root,receipt_path)

    @app.tool()
    def import_portable_rig_in_blender(glb_path: str, asset_id: str) -> dict:
        """Heavy host-side Blender gate: import verified animated GLB, inspect real armatures and deformed meshes, save diagnostic PNGs and native .blend; BLOCKED without actual Blender."""
        from .blender_bridge import import_rig
        return import_rig(root,glb_path,asset_id)

    @app.tool()
    def verify_native_import_receipt(receipt_path: str) -> dict:
        """Read-only: check locally signed Blender import report, source and scene hashes, and actual diagnostic renders; no artistic-film certification."""
        from .blender_bridge import check_import
        return check_import(root,receipt_path)

    @app.tool()
    def finish_native_blender_actor_film(glb_path: str, run_id: str) -> dict:
        """Blender-only 12s rigged film. Benchmarks and renders 3 source-verified shots, encodes MP4, fully decodes; may be long-running. BLOCKED if Blender is absent. No arbitrary shell or publication."""
        from .native_finish import finish_native
        return finish_native(root, glb_path, run_id)

    @app.tool()
    def render_native_blender_shot(import_receipt: str, shot: str, run_id: str) -> dict:
        """Long-running, resumable-in-shots native Blender 3D film stage. Requires a locally signed real import proof."""
        from .native_finish import native_shot
        return native_shot(root, import_receipt, shot, run_id)

    @app.tool()
    def assemble_native_blender_film(film_id: str, shot_receipts: list[str]) -> dict:
        """Hash-check all 288 actual Blender PNGs and 3 signed shot receipts before H264 encoding; requires visual review."""
        from .native_finish import assemble_native
        return assemble_native(root, film_id, shot_receipts)

    @app.tool()
    def check_native_blender_film(receipt_path: str) -> dict:
        """Recheck every source frame, signed native Blender receipt, 12s H264 full decode without changing files."""
        from .native_finish import check_native_film
        return check_native_film(root, receipt_path)

    @app.tool()
    def check_shot_graph(graph_path: str) -> dict:
        """Read-only: validate shot chronology, camera names, dramatic direction and audio constraints."""
        from .contracts import inspect_graph
        from .common import inside
        return inspect_graph(inside(root,graph_path,must_exist=True),root)

    @app.tool()
    def inspect_real_rig(blend_path: str, frames: list[int], anatomy: str = 'organic') -> dict:
        """Executes trusted Blender probe on a WORKSPACE .blend; measures true joints, skinned vertices, and animation. No manifest-only acceptance."""
        from .rig_proof import probe_blend
        return probe_blend(root,blend_path,frames,anatomy)

    @app.tool()
    def check_rig_receipt(proof_path: str) -> dict:
        """Read-only: validate Blender evaluation receipt against current scene hash. Does not substitute for inspecting Blender directly."""
        from .rig_proof import validate_rig_proof
        from .common import load_json,inside
        return validate_rig_proof(load_json(inside(root,proof_path,must_exist=True)),root=root)

    @app.tool()
    def benchmark_real_render(graph_path: str, proof_path: str, shot_id: str) -> dict:
        """Heavy bounded operation: render 3 real Blender diagnostic frames, measure elapsed cost, and gate full shot rendering."""
        from .benchmark import benchmark
        return benchmark(root,graph_path,proof_path,shot_id)

    @app.tool()
    def render_verified_shot(graph_path: str, proof_path: str, shot_id: str, max_frames: int = 90) -> dict:
        """Heavy local operation: render up to 90 missing Blender frames, only after graph/rig pass. Explicit caller approval advised."""
        from .render_shots import render_shot
        return render_shot(root,graph_path,proof_path,shot_id,max_frames=min(max(max_frames,1),90))

    @app.tool()
    def encode_complete_film(graph_path: str, proof_path: str) -> dict:
        """Heavy local operation: assemble receipt-verified shot frames, preserve full soundtrack, encode H264 MP4, decode and probe."""
        from .assemble import assemble
        return assemble(root,graph_path,proof_path)

    @app.tool()
    def inspect_encoded_video(video_path: str, graph_path: str = '') -> dict:
        """Read-only: full ffprobe/decode, audio/subtitle/timeline tests and black/frozen/silent anomaly candidates. Visual acting unverified."""
        from .verify_mp4 import verify_mp4
        return verify_mp4(root,video_path,graph_path or None)

    @app.tool()
    def prepare_visual_review(video_path: str, graph_path: str) -> dict:
        """Extract individual frame evidence for every shot's entrance/middle/exit; does not auto-approve visual quality."""
        from .verify_mp4 import extract_review_frames
        return extract_review_frames(root,video_path,graph_path)

    @app.tool()
    def production_verdict(graph_path: str, proof_path: str = '', video_path: str = '') -> dict:
        """Read-only G0-G8 proof ledger with honest PARTIAL / TECHNICAL_PASS_VISUAL_PENDING statuses."""
        from .project import production_status
        return production_status(root,graph_path,proof_path or None,video_path or None)

    return app

def serve(root:Path,host:str='127.0.0.1',port:int=8787,stdio:bool=False):
    if host not in ('127.0.0.1','localhost','::1'):
        raise ValueError('Non-loopback HTTP binding forbidden; use an authenticated Secure MCP Tunnel')
    if type(port) is not int or not 1<=port<=65535:raise ValueError('Bad port')
    app=build_server(root)
    if stdio:app.run(transport='stdio')
    else:app.run(transport='streamable-http',host=host,port=port,json_response=True,stateless_http=True)

if __name__=='__main__':serve(workspace_root(),stdio=True)
