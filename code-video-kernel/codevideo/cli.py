"""CLI entry point; MCP delegates to the identical audited core functions."""
from __future__ import annotations
import argparse,json,os,sys
from .common import workspace_root,inside,GateError

def main(argv=None)->int:
    parser=argparse.ArgumentParser(description='Code Video: rigorously gated articulated 3D film production')
    parser.add_argument('--workspace',help='Dedicated workspace path (also CODEVIDEO_WORKSPACE)')
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('preflight');p.add_argument('--media')
    p=commands.add_parser('job-preflight');p.add_argument('spec')
    p=commands.add_parser('job-build');p.add_argument('spec')
    p=commands.add_parser('job-render');p.add_argument('spec');p.add_argument('--max-frames',type=int,default=48)
    p=commands.add_parser('job-encode');p.add_argument('spec')
    p=commands.add_parser('job-produce');p.add_argument('spec');p.add_argument('--max-seconds',type=int,default=7200)
    p=commands.add_parser('init');p.add_argument('name')
    p=commands.add_parser('demo');p.add_argument('name')
    p=commands.add_parser('vtk-demo');p.add_argument('name');p.add_argument('--width',type=int,default=960);p.add_argument('--height',type=int,default=540);p.add_argument('--fps',type=int,default=24);p.add_argument('--seconds',type=float,default=6)
    p=commands.add_parser('vtk-replay');p.add_argument('scene');p.add_argument('name');p.add_argument('--width',type=int,default=960);p.add_argument('--height',type=int,default=540);p.add_argument('--fps',type=int,default=24);p.add_argument('--seconds',type=float,default=6)
    p=commands.add_parser('vtk-check');p.add_argument('receipt')
    p=commands.add_parser('portable-rig-export');p.add_argument('name');p.add_argument('--spec')
    p=commands.add_parser('portable-rig-check');p.add_argument('receipt')
    p=commands.add_parser('portable-rig-import');p.add_argument('glb');p.add_argument('name')
    p=commands.add_parser('portable-import-check');p.add_argument('receipt')
    p=commands.add_parser('native-finish');p.add_argument('glb');p.add_argument('name');p.add_argument('--width',type=int,default=960);p.add_argument('--height',type=int,default=540);p.add_argument('--samples',type=int,default=12);p.add_argument('--max-seconds',type=int,default=7200)
    p=commands.add_parser('native-shot');p.add_argument('import_receipt');p.add_argument('shot',choices=['recognition','struggle','resolution']);p.add_argument('name');p.add_argument('--width',type=int,default=960);p.add_argument('--height',type=int,default=540);p.add_argument('--samples',type=int,default=12)
    p=commands.add_parser('native-assemble');p.add_argument('name');p.add_argument('receipts',nargs=3)
    p=commands.add_parser('native-film-check');p.add_argument('receipt')
    p=commands.add_parser('actor-reach');p.add_argument('name');p.add_argument('--width',type=int,default=960);p.add_argument('--height',type=int,default=540);p.add_argument('--spec')
    p=commands.add_parser('actor-check');p.add_argument('receipt')
    p=commands.add_parser('actor-batch');p.add_argument('name');p.add_argument('start_frame',type=int);p.add_argument('frame_count',type=int);p.add_argument('--width',type=int,default=960);p.add_argument('--height',type=int,default=540);p.add_argument('--spec')
    p=commands.add_parser('actor-batch-check');p.add_argument('receipt')
    p=commands.add_parser('actor-assemble');p.add_argument('name');p.add_argument('receipts',nargs=3)
    p=commands.add_parser('actor-assembly-check');p.add_argument('receipt')
    p=commands.add_parser('shots');p.add_argument('graph')
    p=commands.add_parser('rig-proof');p.add_argument('scene');p.add_argument('--frames',required=True,help='comma-separated frame numbers');p.add_argument('--anatomy',choices=['organic','segmented'],default='organic')
    p=commands.add_parser('rig-check');p.add_argument('proof')
    p=commands.add_parser('benchmark');p.add_argument('graph');p.add_argument('proof');p.add_argument('shot')
    p=commands.add_parser('render');p.add_argument('graph');p.add_argument('proof');p.add_argument('shot');p.add_argument('--max-frames',type=int,default=180)
    p=commands.add_parser('encode');p.add_argument('graph');p.add_argument('proof')
    p=commands.add_parser('verify');p.add_argument('video');p.add_argument('--graph')
    p=commands.add_parser('review-frames');p.add_argument('video');p.add_argument('graph')
    p=commands.add_parser('status');p.add_argument('graph');p.add_argument('--proof');p.add_argument('--video')
    p=commands.add_parser('serve');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8787);p.add_argument('--stdio',action='store_true')
    args=parser.parse_args(argv)
    if args.workspace:os.environ['CODEVIDEO_WORKSPACE']=args.workspace
    try:
        root=workspace_root()
        if args.command=='preflight':
            from .preflight import preflight
            out=preflight(root,args.media)
        elif args.command.startswith('job-'):
            from . import production_job
            if args.command=='job-preflight':out=production_job.preflight(root,args.spec)
            elif args.command=='job-build':out=production_job.build(root,args.spec)
            elif args.command=='job-render':out=production_job.render(root,args.spec,max_frames=args.max_frames)
            elif args.command=='job-encode':out=production_job.encode(root,args.spec)
            elif args.command=='job-produce':out=production_job.produce(root,args.spec,max_render_seconds=args.max_seconds)
        elif args.command=='init':
            from .project import create_project
            out=create_project(root,args.name)
        elif args.command=='demo':
            from .project import create_demo_project
            out=create_demo_project(root,args.name)
        elif args.command=='vtk-demo':
            from .vtk_stage import run_stage
            out=run_stage(root,args.name,width=args.width,height=args.height,fps=args.fps,seconds=args.seconds)
        elif args.command=='vtk-replay':
            from .vtk_stage import replay_stage
            out=replay_stage(root,args.scene,args.name,width=args.width,height=args.height,fps=args.fps,seconds=args.seconds)
        elif args.command=='vtk-check':
            from .vtk_stage import check_stage
            out=check_stage(root,args.receipt)
        elif args.command=='portable-rig-export':
            from .portable_rig import export_reach
            out=export_reach(root,args.name,args.spec)
        elif args.command=='portable-rig-check':
            from .portable_rig import check_export
            out=check_export(root,args.receipt)
        elif args.command=='portable-rig-import':
            from .blender_bridge import import_rig
            out=import_rig(root,args.glb,args.name)
        elif args.command=='portable-import-check':
            from .blender_bridge import check_import
            out=check_import(root,args.receipt)
        elif args.command=='native-finish':
            from .native_finish import finish_native
            out=finish_native(root,args.glb,args.name,width=args.width,height=args.height,samples=args.samples,max_estimated_seconds=args.max_seconds)
        elif args.command=='native-shot':
            from .native_finish import native_shot
            out=native_shot(root,args.import_receipt,args.shot,args.name,width=args.width,height=args.height,samples=args.samples)
        elif args.command=='native-assemble':
            from .native_finish import assemble_native
            out=assemble_native(root,args.name,args.receipts)
        elif args.command=='native-film-check':
            from .native_finish import check_native_film
            out=check_native_film(root,args.receipt)
        elif args.command=='actor-reach':
            from .golden_reach import render
            out=render(root,args.name,width=args.width,height=args.height,spec_path=args.spec)
        elif args.command=='actor-check':
            from .golden_reach import check
            out=check(root,args.receipt)
        elif args.command=='actor-batch':
            from .golden_reach import render
            out=render(root,args.name,width=args.width,height=args.height,spec_path=args.spec,
                       frames_limit=args.frame_count,start_frame=args.start_frame)
        elif args.command=='actor-batch-check':
            from .actor_batches import verify_batch
            out=verify_batch(root,args.receipt)
        elif args.command=='actor-assemble':
            from .actor_batches import assemble
            out=assemble(root,args.name,args.receipts)
        elif args.command=='actor-assembly-check':
            from .actor_batches import check_assembly
            out=check_assembly(root,args.receipt)
        elif args.command=='shots':
            from .contracts import inspect_graph
            out=inspect_graph(inside(root,args.graph,must_exist=True),root)
        elif args.command=='rig-proof':
            from .rig_proof import probe_blend
            out=probe_blend(root,args.scene,[int(v) for v in args.frames.split(',')],args.anatomy)
        elif args.command=='rig-check':
            from .rig_proof import validate_rig_proof
            from .common import load_json
            out=validate_rig_proof(load_json(inside(root,args.proof,must_exist=True)),root=root)
        elif args.command=='benchmark':
            from .benchmark import benchmark
            out=benchmark(root,args.graph,args.proof,args.shot)
        elif args.command=='render':
            from .render_shots import render_shot
            out=render_shot(root,args.graph,args.proof,args.shot,max_frames=min(180,max(1,args.max_frames)))
        elif args.command=='encode':
            from .assemble import assemble
            out=assemble(root,args.graph,args.proof)
        elif args.command=='verify':
            from .verify_mp4 import verify_mp4
            out=verify_mp4(root,args.video,args.graph,deep=True)
        elif args.command=='review-frames':
            from .verify_mp4 import extract_review_frames
            out=extract_review_frames(root,args.video,args.graph)
        elif args.command=='status':
            from .project import production_status
            out=production_status(root,args.graph,args.proof,args.video)
        elif args.command=='serve':
            from .mcp_server import serve
            serve(root,host=args.host,port=args.port,stdio=args.stdio)
            return 0
        else:raise GateError('Unknown command')
    except (GateError,OSError,ValueError,KeyError,RuntimeError,json.JSONDecodeError) as exc:
        out={'status':'BLOCKED','error':str(exc)}
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out['status'] not in ('BLOCKED','FAIL','PARTIAL','ENCODED_UNVERIFIED') else 2

if __name__=='__main__':sys.exit(main())
