"""Inspect actual encoded bytes; success is NOT a substitute for visual QA."""
from __future__ import annotations
from pathlib import Path
import json,re,shutil,subprocess,math,uuid
from .common import inside, load_json, sha256, result
from .contracts import validate_graph

def run_checked(args:list[str],timeout:int=600):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        return p.returncode,p.stdout,p.stderr
    except (OSError,subprocess.TimeoutExpired) as exc:
        return -1,'',str(exc)

def _fps(s):
    try:
        a,b=map(float,s.split('/'))
        return a/b if b else 0
    except (AttributeError,ValueError):return 0

def verify_mp4(root:Path,video:str,graph_path:str|None=None,*,deep:bool=True)->dict:
    try:src=inside(root,video,must_exist=True)
    except (OSError,ValueError) as exc:return result('BLOCKED',error=str(exc))
    if src.suffix.lower()!='.mp4':return result('FAIL',error='Expected MP4')
    ffmpeg=shutil.which('ffmpeg'); ffprobe=shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:return result('BLOCKED',error='ffmpeg and ffprobe required')
    rc,stdout,stderr=run_checked([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(src)])
    if rc:return result('FAIL',error='ffprobe failed',stderr=stderr[-1200:])
    try:meta=json.loads(stdout)
    except json.JSONDecodeError:return result('FAIL',error='ffprobe returned invalid JSON')
    streams=meta.get('streams',[])
    videos=[s for s in streams if s.get('codec_type')=='video']
    audios=[s for s in streams if s.get('codec_type')=='audio']
    subs=[s for s in streams if s.get('codec_type')=='subtitle']
    errors=[];warnings=[]
    if len(videos)!=1:errors.append('expected exactly one video stream')
    if subs:errors.append('unexpected subtitle stream: subtitles OFF by default')
    v=videos[0] if videos else {}
    try:n=int(v.get('nb_read_frames') or v.get('nb_frames') or 0)
    except (ValueError,TypeError):n=0
    fps=_fps(v.get('avg_frame_rate','0/1'))
    try:duration=float(meta.get('format',{}).get('duration') or 0)
    except (TypeError,ValueError):duration=0.0
    if not math.isfinite(duration):duration=0.0
    if v.get('codec_name')!='h264':errors.append('video must use H.264')
    if v.get('pix_fmt')!='yuv420p':errors.append('video must use yuv420p')
    graph=None
    if graph_path:
        try:graph=load_json(inside(root,graph_path,must_exist=True))
        except (OSError,ValueError) as exc:errors.append('graph unavailable: '+str(exc))
    if graph:
        validation=validate_graph(graph,root=root)
        if validation['status']!='PASS':errors+=validation['errors']
        expected=validation['total_frames']
        if (v.get('width'),v.get('height'))!=(graph['width'],graph['height']):errors.append('resolution differs from shot graph')
        if abs(fps-graph['fps'])>0.02:errors.append('FPS differs from shot graph')
        if n != expected:errors.append(f'actual decoded frame count {n} vs expected {expected}')
        if abs(duration-validation['duration_s'])>max(0.12,2/graph['fps']):errors.append('video duration mismatch')
        if graph.get('audio') and not audios:errors.append('required soundtrack missing')
        if not graph.get('audio') and audios:errors.append('unrequested audio present')
    if not n:errors.append('ffprobe could not count actual video frames')
    if not duration:errors.append('duration unknown or zero')
    decoded=False;events=[]
    if deep:
        rc,stdout,stderr=run_checked([ffmpeg,'-hide_banner','-nostdin','-v','error','-xerror','-i',str(src),'-f','null','-'],timeout=900)
        if rc:errors.append('full MP4 decode failed: '+stderr[-500:])
        else:decoded=True
        # Diagnostic anomalies are not automatically defects: dramatic black/silent holds can be intentional.
        rc,stdout,log=run_checked([ffmpeg,'-hide_banner','-nostdin','-v','info','-i',str(src),
                                  '-vf','blackdetect=d=0.3:pix_th=0.08,freezedetect=n=-60dB:d=0.5',
                                  '-an','-f','null','-'],timeout=900)
        for tag,pattern in [('black',r'black_start:[^\r\n]+'),('freeze',r'freeze_start:[^\r\n]+')]:
            events.extend({'kind':tag,'details':m.group(0)} for m in re.finditer(pattern,log))
        if rc:warnings.append('black/freeze analysis filter failed')
        if audios:
            rc,stdout,log=run_checked([ffmpeg,'-hide_banner','-nostdin','-v','info','-i',str(src),
                                      '-vn','-af','silencedetect=noise=-55dB:d=0.8','-f','null','-'],timeout=900)
            events.extend({'kind':'silence','details':m.group(0)} for m in re.finditer(r'silence_start:[^\r\n]+',log))
            if rc:warnings.append('audio silence analysis filter failed')
        if events:warnings.append('Anomaly candidates require shot-level human/vision inspection')
    else:warnings.append('full decode not requested')
    if not decoded:errors.append('full decode has not passed')
    video_stats={'path':str(src),'sha256':sha256(src),'width':v.get('width'),'height':v.get('height'),
                 'codec':v.get('codec_name'),'pixel_format':v.get('pix_fmt'),
                 'fps':fps,'frames':n,'duration_s':duration,'audio_streams':len(audios),
                 'subtitle_streams':len(subs),'fully_decoded':decoded}
    return {'status':'PASS' if not errors else 'FAIL','errors':errors,'warnings':warnings,'events':events,
            'video':video_stats,'visual_qa':'NOT_PERFORMED',
            'finished_verified':False}

def extract_review_frames(root:Path,video:str,graph_path:str)->dict:
    """One decode/select pass for all shot samples; never reuse tampered review stills."""
    source=inside(root,video,must_exist=True)
    graph=load_json(inside(root,graph_path,must_exist=True))
    v=validate_graph(graph,root=root)
    if v['status']!='PASS':return result('BLOCKED',issues=v['errors'])
    checked=verify_mp4(root,video,graph_path,deep=True)
    if checked['status']!='PASS':return result('BLOCKED',gate='VIDEO',details=checked)
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:return result('BLOCKED',error='ffmpeg missing')
    markers=[]
    for s in graph['shots']:
        for f in sorted(set([s['start'],(s['start']+s['end'])//2,s['end']])):
            markers.append((s['id'],f))
    marker_positions=sorted(set(f for _,f in markers))
    # Unique directory prevents old/tampered evidence from masquerading as a new review.
    packet=inside(root,Path('review')/sha256(source)[:20]/uuid.uuid4().hex[:12])
    packet.mkdir(parents=True,exist_ok=False)
    expression='+'.join(f'eq(n\\,{f})' for f in marker_positions)
    sequence=packet/'sample_%06d.png'
    rc,_,stderr=run_checked([ffmpeg,'-hide_banner','-nostdin','-v','error','-i',str(source),
                 '-vf',f'select={expression}','-fps_mode','passthrough','-start_number','0',str(sequence)],timeout=900)
    samples=sorted(packet.glob('sample_*.png'))
    if rc or len(samples)!=len(marker_positions):
        return result('PARTIAL',gate='REVIEW_EXTRACTION',error='Sample count or extraction failed',
                      expected=len(marker_positions),actual=len(samples),stderr=stderr[-800:])
    by_frame={f:p for f,p in zip(marker_positions,samples)}
    frames=[]
    for shot_id,f in markers:
        original=by_frame[f]
        # A frame at a shared cut position may be referenced by two shots.
        frames.append({'shot':shot_id,'frame':f,'time_s':round(f/graph['fps'],3),
                       'path':str(original),'sha256':sha256(original)})
    packet_data={'format':'codevideo.review-packet.v1','video_hash':sha256(source),
                 'status':'AWAITING_VISUAL_REVIEW','frames':frames,
                 'checklist':['identifiable volumetric character','visible nonroot acting','contact physics',
                              'no clipping or deformation failures','framing/continuity','lip sync if applicable',
                              'meaningful directing and emotional readability']}
    from .common import save_json
    save_json(packet/'review-packet.json',packet_data)
    return result('AWAITING_VISUAL_REVIEW',packet=str(packet/'review-packet.json'),
                  frames=len(frames),decoded_in_one_pass=True)
