"""Proof-bound, resumable Blender frame production.

An existing PNG is not evidence of a Blender render. Only frames in a locally
attested benchmark/progress/full-shot receipt for the *current cache key* can
be reused. Unknown frames are rendered again, never silently promoted.
"""
from __future__ import annotations
from pathlib import Path
import shutil, subprocess, struct
from .common import inside, load_json, save_json, sha256, stable_hash, result
from .contracts import validate_graph
from .rig_proof import validate_rig_proof, authentic, attest

PNG = b'\x89PNG\r\n\x1a\n'


def valid_png(path:Path, width:int, height:int)->bool:
    try:
        with path.open('rb') as f: h=f.read(24)
        return (len(h)==24 and h[:8]==PNG and h[12:16]==b'IHDR'
                and struct.unpack('>II',h[16:24])==(width,height) and path.stat().st_size>100)
    except (OSError,struct.error):return False


def trusted_frames(root:Path, folder:Path, key:str, scene_hash:str, shot:dict,
                   width:int,height:int)->dict[str,str]:
    """Return only current-frame hashes proven by signed local render receipts."""
    all_names={f'{f:06d}.png' for f in range(shot['start'],shot['end']+1)}
    verified={}
    for label in ('benchmark.json','progress.json','receipt.json'):
        path=folder/label
        if not path.is_file():continue
        try: evidence=load_json(path)
        except (ValueError,OSError):continue
        if not authentic(evidence,root) or evidence.get('cache_key')!=key or evidence.get('shot')!=shot['id']:
            continue
        if (evidence.get('scene_hash') or evidence.get('source_sha256'))!=scene_hash:
            continue
        mapping=evidence.get('sample_hashes') if label=='benchmark.json' else evidence.get('frame_hashes')
        if not isinstance(mapping,dict):continue
        if label=='benchmark.json':
            samples=evidence.get('sample_frames',[])
            if {f'{f:06d}.png' for f in samples if type(f) is int}!=set(mapping):continue
        if label=='receipt.json':
            if (set(mapping)!=all_names or evidence.get('frame_count')!=len(all_names)
                or evidence.get('frame_start')!=shot['start'] or evidence.get('frame_end')!=shot['end']
                or evidence.get('format')!='codevideo.render-receipt.v1'):continue
        if not set(mapping).issubset(all_names):continue
        for name,expected in mapping.items():
            target=folder/name
            if (isinstance(expected,str) and len(expected)==64
                and valid_png(target,width,height) and sha256(target)==expected):
                verified[name]=expected
    return verified


def plan_render(root:Path,graph_path:str,proof_path:str,shot_id:str,*,max_frames:int=180)->dict:
    if type(max_frames) is not int or max_frames<1 or max_frames>1000000:
        return result('BLOCKED',gate='RENDER_BUDGET',error='max_frames must be in 1..1000000')
    graph=load_json(inside(root,graph_path,must_exist=True))
    check=validate_graph(graph,root=root)
    if check['status']!='PASS':return result('BLOCKED',gate='SHOT_GRAPH',issues=check['errors'])
    proof=load_json(inside(root,proof_path,must_exist=True))
    rig=validate_rig_proof(proof,root=root)
    if rig['status']!='PASS':return result('BLOCKED',gate='RIG_PROOF',issues=rig['errors'])
    shot=next((s for s in graph['shots'] if s['id']==shot_id),None)
    if not shot:return result('BLOCKED',gate='SHOT',error='Unknown shot')
    scene=inside(root,graph['scene'],must_exist=True)
    src_hash=sha256(scene)
    if proof.get('scene',{}).get('sha256')!=src_hash or Path(proof.get('scene',{}).get('path','')).resolve()!=scene:
        return result('BLOCKED',gate='SOURCE_MISMATCH',error='Rig proof belongs to a different scene or revision')
    digest=stable_hash({'scene_hash':src_hash,'rig_source_hash':proof['scene']['sha256'],
          'shot':shot,'fps':graph['fps'],'width':graph['width'],'height':graph['height'],
          'driver_hash':sha256(Path(__file__).resolve().parent.parent/'blender'/'render_frames.py')})[:20]
    folder=inside(root,Path('renders')/shot_id/digest)
    known=trusted_frames(root,folder,digest,src_hash,shot,graph['width'],graph['height'])
    missing=[f for f in range(shot['start'],shot['end']+1) if f'{f:06d}.png' not in known]
    return result('PASS',shot=shot_id,camera=shot['camera'],cache_key=digest,
                  output=str(folder),missing=missing[:max_frames],remaining=len(missing),
                  trusted=len(known),expected=shot['end']-shot['start']+1,
                  width=graph['width'],height=graph['height'],fps=graph['fps'],scene=str(scene))


def render_shot(root:Path,graph_path:str,proof_path:str,shot_id:str,*,max_frames:int=180,timeout:int=900)->dict:
    plan=plan_render(root,graph_path,proof_path,shot_id,max_frames=max_frames)
    if plan['status']!='PASS':return plan
    blender=shutil.which('blender')
    if not blender:return result('BLOCKED',gate='BLENDER',error='Blender missing; no frames rendered',plan=plan)
    folder=Path(plan['output']);folder.mkdir(parents=True,exist_ok=True)
    graph=load_json(inside(root,graph_path,must_exist=True))
    shot=next(s for s in graph['shots'] if s['id']==shot_id)
    source_hash=sha256(Path(plan['scene']))
    trusted=trusted_frames(root,folder,plan['cache_key'],source_hash,shot,graph['width'],graph['height'])
    benchmark_file=folder/'benchmark.json'
    if not benchmark_file.is_file():
        return result('BLOCKED',gate='BENCHMARK',error='Run actual three-frame benchmark before rendering')
    measured=load_json(benchmark_file)
    sample_keys={f'{f:06d}.png' for f in measured.get('sample_frames',[]) if type(f) is int}
    if (not authentic(measured,root) or measured.get('cache_key')!=plan['cache_key']
        or measured.get('source_sha256')!=source_hash or not sample_keys
        or sample_keys!=set(measured.get('sample_hashes',{})) or not sample_keys.issubset(trusted)):
        return result('BLOCKED',gate='BENCHMARK',error='Benchmark absent, stale, incomplete or tampered')
    failure=None
    if plan['missing']:
        recipe={'output':str(folder),'camera':plan['camera'],'frames':plan['missing'],
                'width':plan['width'],'height':plan['height'],'fps':plan['fps']}
        recipe_path=folder/'recipe.json';save_json(recipe_path,recipe)
        script=Path(__file__).resolve().parent.parent/'blender'/'render_frames.py'
        try:
            p=subprocess.run([blender,'--background','--disable-autoexec',plan['scene'],'--python',str(script),
                              '--','--recipe',str(recipe_path)],text=True,capture_output=True,
                              timeout=min(max(timeout,1),3600))
            if p.returncode:failure={'error':'Blender exited nonzero','stderr':p.stderr[-1800:]}
        except (subprocess.TimeoutExpired,OSError) as exc:failure={'error':str(exc)}
    # Preserve verified progress after each batch, including completed frames before a crash.
    for frame in plan['missing']:
        name=f'{frame:06d}.png'; file=folder/name
        if valid_png(file,plan['width'],plan['height']):trusted[name]=sha256(file)
    progress={'format':'codevideo.render-progress.v1','shot':shot_id,'cache_key':plan['cache_key'],
              'scene_hash':source_hash,'frame_hashes':trusted}
    save_json(folder/'progress.json',attest(progress,root))
    if failure:return result('PARTIAL',output=str(folder),progress=str(folder/'progress.json'),**failure)
    after=plan_render(root,graph_path,proof_path,shot_id,max_frames=1000000)
    if after['status']!='PASS':return after
    if after['remaining']:
        return result('PARTIAL',output=str(folder),progress=str(folder/'progress.json'),
                      remaining=after['remaining'],rendered_batch=len(plan['missing']))
    frame_hashes={f'{f:06d}.png':sha256(folder/f'{f:06d}.png') for f in range(shot['start'],shot['end']+1)}
    receipt={'format':'codevideo.render-receipt.v1','shot':shot_id,'cache_key':plan['cache_key'],
             'frame_start':shot['start'],'frame_end':shot['end'],'frame_count':len(frame_hashes),
             'frame_hashes':frame_hashes,'scene_hash':source_hash}
    save_json(folder/'receipt.json',attest(receipt,root))
    return result('PASS',receipt=str(folder/'receipt.json'),output=str(folder),frames=len(frame_hashes))
