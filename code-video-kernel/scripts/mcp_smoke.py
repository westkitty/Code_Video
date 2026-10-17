"""Optional real MCP v2 in-process protocol test. Does NOT prove ChatGPT remote access.

Run after pip install -e '.[mcp]' on an authorized host with CODEVIDEO_WORKSPACE.
Official SDK v2 expects `Client(build_server(root))` and `client.list_tools()`.
"""
from __future__ import annotations
import asyncio
import json

from codevideo.common import workspace_root
from codevideo.mcp_server import build_server

REQUIRED = {
    'preflight','create_project','check_shot_graph','inspect_real_rig',
    'check_rig_receipt','benchmark_real_render','render_verified_shot',
    'encode_complete_film','inspect_encoded_video','prepare_visual_review',
    'production_verdict','render_mechanical_3d_smoke',
    'replay_articulated_3d_stage','check_articulated_3d_stage',
    'render_golden_reach_actor','check_golden_reach_actor',
    'render_golden_actor_shot','verify_golden_actor_shot','assemble_golden_actor_film','verify_assembled_actor_film',
}

async def smoke():
    try:
        from mcp import Client
    except ImportError as exc:
        raise RuntimeError('Missing official MCP SDK: pip install -e ".[mcp]"') from exc
    root=workspace_root()
    server=build_server(root)
    async with Client(server, raise_exceptions=True) as client:
        listing=await client.list_tools()
        names={tool.name for tool in listing.tools}
        missing=sorted(REQUIRED-names)
        assert not missing, f'MCP tool registration mismatch: {missing}'
        health=await client.call_tool('preflight',{})
        assert not health.is_error, 'MCP preflight reported protocol/tool error'
        payload=health.structured_content or {}
        return {'status':'PASS','protocol_version':client.protocol_version,
                'tool_count':len(names),'server_info':str(client.server_info),
                'preflight_status':payload.get('status','UNPARSED'),
                'note':'In-process client handshake only; ChatGPT remote/HTTP transport remains UNVERIFIED.'}

if __name__=='__main__':
    print(json.dumps(asyncio.run(smoke()),indent=2))
