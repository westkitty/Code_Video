"""Require real, signed, reproducible Blender samples before full-shot rendering."""
from __future__ import annotations
import shutil,subprocess,time
from pathlib import Path
from .common import inside,load_json,save_json,sha256,result
from .render_shots import plan_render,valid_png,trusted_frames
from .rig_proof import attest,authentic

def benchmark(root:Path,graph_path:str,proof_path:str,shot_id:str,*,timeout:int=240)->dict:
    plan=plan_render(root,graph_path,proof_path,shot_id,max_frames=1000000)
    if plan['status']!='PASS':return plan
    blender=shutil.which('blender')
    if not blender:return result('BLOCKED',gate='BLENDER',error='Blender unavailable: cannot benchmark real 3D frames')
    graph=load_json(inside(root,graph_path,must_exist=True))
    shot=next(s for s in graph['shots'] if s['id']==shot_id)
    frames=sorted(set([shot['start'],(shot['start']+shot['end'])//2,shot['end']]))
    folder=Path(plan['output']);folder.mkdir(parents=True,exist_ok=True)
    receipt_file=folder/'benchmark.json'
    scene_hash=sha256(Path(plan['scene']))
    trusted=trusted_frames(root,folder,plan['cache_key'],scene_hash,shot,graph['width'],graph['height'])
    if receipt_file.exists():
        try:receipt=load_json(receipt_file)
        except (ValueError,OSError):receipt={}
        if (authentic(receipt,root) and receipt.get('cache_key')==plan['cache_key']
            and receipt.get('source_sha256')==scene_hash
            and receipt.get('sample_frames')==frames
            and set(receipt.get('sample_hashes',{}))=={f'{f:06d}.png' for f in frames}
            and all(f'{f:06d}.png' in trusted for f in frames)):
            return result('PASS',receipt=str(receipt_file),estimate_s=receipt.get('estimated_total_seconds'),
                          samples=frames,rendered_new_samples=0,cached=True)
    # Never certify unknown cached PNGs. Blender rerenders all samples itself.
    recipe={'output':str(folder),'camera':shot['camera'],'frames':frames,
            'width':graph['width'],'height':graph['height'],'fps':graph['fps']}
    recipe_path=folder/'benchmark-recipe.json';save_json(recipe_path,recipe)
    script=Path(__file__).resolve().parents[1]/'blender'/'render_frames.py'
    start=time.monotonic()
    try:
        p=subprocess.run([blender,'--background','--disable-autoexec',plan['scene'],'--python',str(script),
                          '--','--recipe',str(recipe_path)],capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as exc:return result('BLOCKED',gate='BENCHMARK',error=str(exc))
    elapsed=time.monotonic()-start
    if p.returncode:return result('BLOCKED',gate='BENCHMARK',error='Blender benchmark failed',stderr=p.stderr[-1400:])
    if not all(valid_png(folder/f'{f:06d}.png',graph['width'],graph['height']) for f in frames):
        return result('BLOCKED',gate='BENCHMARK',error='One or more sampled frames invalid')
    per_frame=elapsed/len(frames)
    receipt={'format':'codevideo.benchmark.v1','cache_key':plan['cache_key'],'shot':shot_id,
             'source_sha256':scene_hash,'sample_frames':frames,
             'sample_hashes':{f'{f:06d}.png':sha256(folder/f'{f:06d}.png') for f in frames},
             'elapsed_seconds':round(elapsed,3),'newly_rendered_samples':len(frames),
             'seconds_per_sample_frame':round(per_frame,3),
             'estimated_total_seconds':round(per_frame*plan['expected'],1),
             'disclaimer':'Sample-only estimate; simulation and shader costs may vary.'}
    save_json(receipt_file,attest(receipt,root))
    return result('PASS',receipt=str(receipt_file),estimate_s=receipt['estimated_total_seconds'],
                  samples=frames,rendered_new_samples=len(frames))
