"""Encode shot frames with FFmpeg and assemble loss-aware full-timeline MP4."""
from __future__ import annotations
from pathlib import Path
import shutil, subprocess
from .common import inside, load_json, save_json, sha256, stable_hash, result
from .contracts import validate_graph
from .render_shots import plan_render, valid_png
from .preflight import probe_media

def _run(args:list[str],timeout:int=1800):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {'status':'FAIL','error':str(exc)}
    if p.returncode:return {'status':'FAIL','error':'FFmpeg exited '+str(p.returncode),'stderr':p.stderr[-2800:]}
    return {'status':'PASS'}

def _quote_concat(p:Path):
    return "file '"+str(p).replace("'", "'\\''")+"'\n"

def assemble(root:Path,graph_path:str,proof_path:str,*,timeout:int=1800)->dict:
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:return result('BLOCKED',error='FFmpeg missing')
    graph=load_json(inside(root,graph_path,must_exist=True))
    contract=validate_graph(graph,root=root)
    if contract['status']!='PASS':return result('BLOCKED',gate='SHOT_GRAPH',issues=contract['errors'])
    plans=[]; frame_digest=[]
    for s in graph['shots']:
        p=plan_render(root,graph_path,proof_path,s['id'],max_frames=1000000)
        if p['status']!='PASS' or p['missing']:
            return result('BLOCKED',gate='FRAME_COMPLETENESS',shot=s['id'],missing=p.get('missing'),details=p)
        receipt=Path(p['output'])/'receipt.json'
        if not receipt.exists():return result('BLOCKED',gate='FRAME_RECEIPT',shot=s['id'])
        r=load_json(receipt)
        from .rig_proof import authentic
        if not authentic(r,root):return result('BLOCKED',gate='FRAME_RECEIPT',shot=s['id'],error='Missing signed Blender render receipt')
        expected_names={f'{frame:06d}.png' for frame in range(s['start'],s['end']+1)}
        hashes=r.get('frame_hashes')
        if (r.get('format')!='codevideo.render-receipt.v1'
            or r.get('cache_key')!=p['cache_key'] or r.get('shot')!=s['id']
            or r.get('frame_count')!=p['expected'] or r.get('scene_hash')!=sha256(Path(p['scene']))
            or r.get('frame_start')!=s['start'] or r.get('frame_end')!=s['end']
            or not isinstance(hashes,dict) or set(hashes)!=expected_names):
            return result('BLOCKED',gate='FRAME_RECEIPT',shot=s['id'],error='Incomplete or stale signed render receipt')
        for frame,expected_hash in hashes.items():
            candidate=Path(p['output'])/frame
            if not candidate.exists() or sha256(candidate)!=expected_hash:
                return result('BLOCKED',gate='FRAME_INTEGRITY',shot=s['id'],file=frame)
        frame_digest.append(stable_hash(hashes))
        plans.append(p)
    audio=graph.get('audio')
    media=None
    if audio:
        apath=inside(root,audio,must_exist=True)
        media=probe_media(apath)
        if media['status']!='PASS' or not any(s['type']=='audio' for s in media['streams']):
            return result('BLOCKED',gate='AUDIO',details=media)
        if abs(media['duration_s']-contract['duration_s'])>max(0.12,2/graph['fps']):
            return result('BLOCKED',gate='FULL_AUDIO',error='Timeline must cover the complete source audio',
                          audio_s=media['duration_s'],timeline_s=contract['duration_s'])
    fingerprint=stable_hash({'graph':graph,'frame_caches':[p['cache_key'] for p in plans],
                             'exact_frame_hashes':frame_digest,
                             'codec':'libx264/crf18/preset-medium/yuv420p',
                             'audio_hash':sha256(apath) if audio else None})[:20]
    delivery=inside(root,Path('deliveries')/f'{fingerprint}.mp4')
    if delivery.exists():
        from .verify_mp4 import verify_mp4
        receipt=delivery.with_suffix('.receipt.json')
        if not receipt.is_file():
            return result('BLOCKED',gate='DELIVERY_RECEIPT',error='Cached delivery has no provenance; preserving existing file')
        old=load_json(receipt)
        if old.get('sha256')!=sha256(delivery) or old.get('fingerprint')!=fingerprint:
            return result('BLOCKED',gate='DELIVERY_RECEIPT',error='Cached delivery hash/provenance changed; preserving file')
        checked=verify_mp4(root,str(delivery),graph_path,deep=True)
        return result('TECHNICAL_PASS_VISUAL_PENDING' if checked['status']=='PASS' else 'ENCODED_UNVERIFIED',
                      video=str(delivery),cached=True,check=checked)
    staging=inside(root,Path('staging')/fingerprint)
    staging.mkdir(parents=True,exist_ok=True)
    segments=[]
    for s,p in zip(graph['shots'],plans):
        target=staging/(s['id']+'.mp4')
        if target.exists():
            prior=target.with_suffix('.receipt.json')
            if not prior.is_file() or load_json(prior).get('sha256')!=sha256(target):
                return result('BLOCKED',gate='STAGE_INTEGRITY',shot=s['id'],error='Existing segment is untrusted; preserving it')
        else:
            command=[ffmpeg,'-hide_banner','-nostdin','-y','-v','error',
                     '-framerate',str(graph['fps']),'-start_number',str(s['start']),
                     '-i',str(Path(p['output'])/'%06d.png'),'-frames:v',str(p['expected']),
                     '-an','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',
                     '-r',str(graph['fps']),'-movflags','+faststart',str(target)]
            run=_run(command,timeout)
            if run['status']!='PASS':return result('PARTIAL',stage='segment',shot=s['id'],details=run)
            save_json(target.with_suffix('.receipt.json'),{'sha256':sha256(target),'frame_digest':frame_digest[len(segments)]})
        segment_receipt=load_json(target.with_suffix('.receipt.json'))
        if segment_receipt.get('frame_digest')!=frame_digest[len(segments)]:
            return result('BLOCKED',gate='STAGE_INTEGRITY',shot=s['id'],error='Cached segment belongs to different frames')
        segments.append(target)
    concatfile=staging/'segments.txt'
    concatfile.write_text(''.join(_quote_concat(p) for p in segments),encoding='utf-8')
    silent=staging/'silent.mp4'
    if silent.exists():
        old=staging/'silent.receipt.json'
        if not old.is_file() or load_json(old).get('sha256')!=sha256(silent):
            return result('BLOCKED',gate='STAGE_INTEGRITY',error='Existing concat output untrusted; preserving it')
    else:
        cmd=[ffmpeg,'-hide_banner','-nostdin','-y','-v','error','-f','concat','-safe','0',
             '-i',str(concatfile),'-map','0:v:0','-c','copy','-movflags','+faststart',str(silent)]
        run=_run(cmd,timeout)
        if run['status']!='PASS':return result('PARTIAL',stage='concat',details=run)
        save_json(staging/'silent.receipt.json',{'sha256':sha256(silent)})
    delivery.parent.mkdir(parents=True,exist_ok=True)
    pending=delivery.with_suffix('.partial.mp4')
    cmd=[ffmpeg,'-hide_banner','-nostdin','-y','-v','error','-i',str(silent)]
    if audio:
        cmd+=['-i',str(apath),'-map','0:v:0','-map','1:a:0','-c:v','copy',
              '-c:a','aac','-b:a','192k','-t',str(contract['duration_s'])]
    else:
        cmd+=['-map','0:v:0','-c:v','copy','-an']
    cmd+=['-sn','-movflags','+faststart',str(pending)]
    run=_run(cmd,timeout)
    if run['status']!='PASS':return result('PARTIAL',stage='mux',details=run)
    from .verify_mp4 import verify_mp4
    check=verify_mp4(root,str(pending),graph_path,deep=True)
    if check['status']!='PASS':
        return result('ENCODED_UNVERIFIED',file=str(pending),details=check)
    pending.rename(delivery)
    receipt={'format':'codevideo.delivery.v1','mp4':str(delivery),'sha256':sha256(delivery),
             'fingerprint':fingerprint,'frames':contract['total_frames'],'duration_s':contract['duration_s'],
             'audio_source_sha256':sha256(apath) if audio else None,'qa':'TECHNICAL_PASS_VISUAL_PENDING',
             'ffprobe':check.get('video')}
    save_json(delivery.with_suffix('.receipt.json'),receipt)
    return result('TECHNICAL_PASS_VISUAL_PENDING',video=str(delivery),receipt=str(delivery.with_suffix('.receipt.json')),
                  check=check)
