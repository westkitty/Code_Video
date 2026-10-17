"""Source-bound, local-signature-verified 3-shot Golden Scene assembly.

A batch can be rerendered independently under a NEW project name; no unsigned
cached frame is trusted. Staging and MP4 are created only after all 288 hashes
are independently verified against batch receipts and identical source revision.
"""
from __future__ import annotations
import math,shutil,subprocess
from pathlib import Path
from .common import inside, slug,sha256,save_json,load_json,result
from .rig_proof import attest, authentic
from .golden_reach import FORMAT,SHOT_GRAPH,validate_spec
from .verify_mp4 import verify_mp4

FINAL_FORMAT='codevideo.golden-reach-assembled.v1'

def _batch(root:Path,receipt_path:str):
    path=inside(root,receipt_path,must_exist=True)
    r=load_json(path); errors=[]
    if r.get('format')!='codevideo.golden-reach-receipt.v1':errors.append('Wrong batch receipt type')
    if not authentic(r,root):errors.append('Batch receipt unsigned/tampered')
    if r.get('status')!='PARTIAL' or r.get('errors'):errors.append('Batch has errors or is not signed partial stage')
    p=inside(root,r.get('project',''))
    scene=p/'film.json'
    if not scene.is_file() or sha256(scene)!=r.get('model_sha256'):errors.append('Batch scene changed')
    else:
        try:validate_spec(load_json(scene))
        except (ValueError,TypeError,KeyError) as e:errors.append('Invalid film source: '+str(e))
    from . import golden_reach,actor_engine
    if sha256(Path(golden_reach.__file__))!=r.get('source_sha256'):errors.append('Renderer source drift')
    if sha256(Path(actor_engine.__file__))!=r.get('actor_math_sha256'):errors.append('Actor solver source drift')
    start=r.get('frame_start');stop=r.get('frame_stop_exclusive');frame_count=r.get('frame_count')
    if type(start)!=int or type(stop)!=int or type(frame_count)!=int or not (0<=start<stop<=288) or stop-start!=frame_count:
        errors.append('Invalid frame range');start=0;stop=0
    hashes=r.get('frame_hashes',{})
    expected={f'frame_{i:05d}.png' for i in range(start,stop)}
    if not isinstance(hashes,dict) or set(hashes)!=expected:
        errors.append('Missing, extra, or out-of-range frame hashes')
    else:
        for name,expected_hash in hashes.items():
            frame=p/'frames'/name
            if not frame.is_file() or sha256(frame)!=expected_hash:
                errors.append('Frame altered or missing: '+name);break
    proofs=r.get('motion_proof',{})
    for tag in ('hesitation','reach','failure','grasp','reaction'):
        ev=proofs.get(tag,{})
        if not isinstance(ev,dict) or not isinstance(ev.get('changed_pixels'),int) or ev['changed_pixels']<200:
            errors.append('Fixed-camera visual proof absent: '+tag);continue
        diag=p/'diagnostics'/f'{tag}.png'
        if not diag.is_file() or sha256(diag)!=ev.get('sha256'):
            errors.append('Diagnostic changed: '+tag)
    skin=r.get('skinned_meshes',{})
    if set(skin)!= {'right_arm','left_arm','right_leg','left_leg'} or any(
        not x.get('all_weights_normalized') or x.get('max_vertex_deformation_m',0)<.08 for x in skin.values()):
        errors.append('Real normalized, deformed skinning not evidenced')
    if r.get('blender_verified') is not False or r.get('finished_verified') is not False:
        errors.append('Unsupported claim of final/Blender proof')
    if r.get('resolution') not in ([960,540],[640,360],[480,270],[320,180]):
        errors.append('Unsupported demonstration resolution')
    if r.get('fps')!=24:errors.append('FPS contract mismatch')
    if r.get('minimum_critical_landmark_margin_px',-1)<18:errors.append('Camera framing failed')
    return errors,r,p,path


def verify_batch(root:Path,path:str):
    errors,r,p,receipt_path=_batch(root,path)
    return result('PASS' if not errors else 'FAIL',errors=errors,
                  frame_range=[r.get('frame_start'),r.get('frame_stop_exclusive')],
                  receipt=str(receipt_path),scene=str(p/'film.json'))


def assemble(root:Path,project_id:str,receipt_paths:list[str]):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):return result('BLOCKED',error='Missing FFmpeg binaries')
    if not isinstance(receipt_paths,list) or len(receipt_paths)!=3:return result('BLOCKED',error='Exactly three independently signed shot batches required')
    batches=[];issues=[]
    for path in receipt_paths:
        try:errors,r,p,receipt_path=_batch(root,path)
        except (KeyError,ValueError,OSError) as ex:return result('BLOCKED',error='Unreadable batch proof: '+str(ex))
        issues.extend(errors);batches.append((r,p,receipt_path))
    if issues:return result('BLOCKED',gate='SIGNED_FRAME_COVERAGE',errors=issues)
    batches.sort(key=lambda e:e[0]['frame_start'])
    expected=[(x['frame_start'],x['frame_end']+1) for x in SHOT_GRAPH]
    covered=[(r['frame_start'],r['frame_stop_exclusive']) for r,_,_ in batches]
    if covered!=expected:return result('BLOCKED',gate='SHOT_COVERAGE',error='Gap, overlap or wrong shot range',actual=covered,expected=expected)
    baseline=batches[0][0]
    if any(r['model_sha256']!=baseline['model_sha256'] or r['resolution']!=baseline['resolution'] or
           r['source_sha256']!=baseline['source_sha256'] or r['actor_math_sha256']!=baseline['actor_math_sha256']
           for r,_,_ in batches):
        return result('BLOCKED',gate='SOURCE_CONTINUITY',error='Batch sources, dimensions or renderer revisions do not match')
    target=inside(root,Path('projects')/slug(project_id))
    if target.exists():return result('BLOCKED',error='Output project exists; cannot overwrite')
    # Everything upstream passed; commit a new immutable assembly project.
    target.mkdir(parents=True);dst=target/'frames';dst.mkdir()
    shutil.copy2(batches[0][1]/'film.json',target/'film.json')
    for r,p,_ in batches:
        for name,digest in r['frame_hashes'].items():
            source=p/'frames'/name; destination=dst/name
            shutil.copy2(source,destination)
            if sha256(destination)!=digest:raise RuntimeError('Frame copy failed hash readback: '+name)
    output=target/'the_reach.mp4'
    width,height=baseline['resolution'];cmd=['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y',
        '-framerate','24','-start_number','0','-i',str(dst/'frame_%05d.png'),'-frames:v','288','-an',
        '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    proc=subprocess.run(cmd,text=True,capture_output=True,timeout=240)
    if proc.returncode:return result('PARTIAL',stage='encode',error=proc.stderr[-1200:],project=str(target))
    video=verify_mp4(root,str(output),deep=True);data=video.get('video',{})
    fail=[]
    if video.get('status')!='PASS':fail.append('Full decode not PASS')
    if data.get('frames')!=288:fail.append('Frame count not 288')
    if abs(float(data.get('fps',0))-24)>.005:fail.append('FPS does not match 24')
    if abs(float(data.get('duration_s',0))-12)>.08:fail.append('Video duration differs from 12 seconds')
    evidence={'format':FINAL_FORMAT,'production_status':'TECHNICAL_PASS_VISUAL_PENDING' if not fail else 'ENCODED_UNVERIFIED',
              'source_sha256':baseline['model_sha256'],'renderer_sha256':baseline['source_sha256'],
              'solver_sha256':baseline['actor_math_sha256'],'shots':SHOT_GRAPH,
              'batches':[{'receipt_path':str(path),'receipt_sha256':sha256(path),'frames':r['frame_count'],
                          'range':[r['frame_start'],r['frame_stop_exclusive']]} for r,_,path in batches],
              'film_path':str(output),'film_sha256':sha256(output),'decoded_video':data,
              'frame_hashes':{f.name:sha256(f) for f in sorted(dst.glob('*.png'))},
              'camera_bounds_passed':True,'blender_armature_verified':False,'subtitles':'OFF','audio':'NONE',
              'human_artistic_review':'PENDING','finished_verified':False,'errors':fail}
    save_json(target/'assembly_receipt.json',attest(evidence,root))
    return result(evidence['production_status'],video=str(output),scene=str(target/'film.json'),
        receipt=str(target/'assembly_receipt.json'),shots=3,frames=288,errors=fail)


def check_assembly(root:Path,path:str):
    receipt_path=inside(root,path,must_exist=True);r=load_json(receipt_path);issues=[]
    if r.get('format')!=FINAL_FORMAT:issues.append('Bad receipt type')
    if not authentic(r,root):issues.append('Bad attestation')
    if r.get('finished_verified') is not False or r.get('blender_armature_verified') is not False:issues.append('Overclaim')
    video=inside(root,r.get('film_path',''));project=video.parent
    if not video.is_file() or sha256(video)!=r.get('film_sha256'):issues.append('MP4 altered or missing')
    if not (project/'film.json').is_file() or sha256(project/'film.json')!=r.get('source_sha256'):issues.append('Scene altered')
    hashes=r.get('frame_hashes',{})
    if set(hashes)!={f'frame_{i:05d}.png' for i in range(288)}:issues.append('Missing encoded source frames')
    else:
        for name,h in hashes.items():
            if not (project/'frames'/name).exists() or sha256(project/'frames'/name)!=h:issues.append('Source frame altered: '+name);break
    for batch in r.get('batches',[]):
        try:
            path=inside(root,batch['receipt_path'],must_exist=True)
            if sha256(path)!=batch['receipt_sha256'] or verify_batch(root,str(path))['status']!='PASS':issues.append('Batch proof invalid')
        except (OSError,KeyError,ValueError):issues.append('Batch receipt unavailable')
    if not issues and verify_mp4(root,str(video),deep=True).get('status')!='PASS':issues.append('Encoded video failed full decode')
    return result('PASS' if not issues else 'FAIL',errors=issues,
                  production_status='TECHNICAL_PASS_VISUAL_PENDING',video=str(video))
