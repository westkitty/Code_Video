"""Native Blender three-shot producer: real bpy required for EVERY green gate.

This module never substitutes VTK frames or a static GLB. Stage receipts are
HMAC-bound to this workspace and every rendered PNG is hashed. The final status
remains TECHNICAL_PASS_VISUAL_PENDING until the encoded shots are reviewed.
"""
from __future__ import annotations
import json
import os
import shutil
import struct
import subprocess
import time
from pathlib import Path
from .common import inside, slug, sha256, save_json, load_json, result
from .rig_proof import attest, authentic
from .blender_bridge import check_import, import_rig, blender_executable
from .portable_rig import verify_glb_bytes
from .verify_mp4 import verify_mp4

SHOTS = {'recognition': (1, 96, 'CodeVideo_Shot_01'),
         'struggle': (97, 192, 'CodeVideo_Shot_02'),
         'resolution': (193, 288, 'CodeVideo_Shot_03')}
FORMAT_SHOT = 'codevideo.blender-native-shot.v1'
FORMAT_FILM = 'codevideo.blender-native-film.v1'


def _blender():
    return blender_executable()


def _png_meta(p):
    with p.open('rb') as fh: header = fh.read(24)
    if len(header) < 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise ValueError('Not a real PNG image: ' + str(p))
    width, height = struct.unpack('>II', header[16:24])
    if not 0 < width <= 8192 or not 0 < height <= 8192:
        raise ValueError('Invalid PNG dimensions')
    if p.stat().st_size < 500:
        raise ValueError('Implausibly small PNG')
    return width, height


def _shot_proof(root, receipt_path):
    file = inside(root, receipt_path, must_exist=True)
    r = load_json(file)
    issues = []
    if r.get('format') != FORMAT_SHOT or not authentic(r, root):
        issues.append('Missing or invalid signed native shot receipt')
    if r.get('origin') != 'actual-blender-render-worker':
        issues.append('No recorded Blender render worker provenance')
    shot = r.get('shot')
    if shot not in SHOTS:
        issues.append('Unknown shot')
        return issues, r, file
    start, end, camera = SHOTS[shot]
    if r.get('frame_range_inclusive') != [start, end] or r.get('camera') != camera:
        issues.append('Shot range/camera mismatch')
    if r.get('fps') != 24 or type(r.get('width')) is not int or type(r.get('height')) is not int:
        issues.append('Incorrect dimensions/FPS metadata')
    paths = r.get('frame_hashes', {})
    expected = {f'frame_{i:06d}.png' for i in range(start, end + 1)}
    if not isinstance(paths, dict) or set(paths) != expected:
        issues.append('Missing, duplicated or excess native shot frames')
    else:
        directory = file.parent / 'frames'
        for name, digest in paths.items():
            p = directory / name
            try:
                if sha256(p) != digest or _png_meta(p) != (r['width'], r['height']):
                    raise ValueError('Hash or dimensions changed')
            except (OSError, ValueError, KeyError) as exc:
                issues.append('Bad native frame ' + name + ': ' + str(exc))
                break
    try:
        blend = inside(root, r['native_blend'], must_exist=True)
        if blend.suffix != '.blend' or blend.stat().st_size < 1024 or blend.open('rb').read(7) != b'BLENDER':
            raise ValueError('No genuine Blender-format source')
        if sha256(blend) != r['native_blend_sha256']:
            raise ValueError('Edited .blend source')
        imp = inside(root, r['import_proof'], must_exist=True)
        if sha256(imp) != r['import_proof_sha256'] or check_import(root, str(imp))['status'] != 'PASS':
            raise ValueError('Stale signed Blender import proof')
        if sha256(Path(__file__).resolve().parent.parent / 'blender' / 'render_native_frames.py') != r['render_worker_sha256']:
            raise ValueError('Render worker source changed')
    except (OSError, ValueError, KeyError) as exc:
        issues.append('Native source/provenance mismatch: ' + str(exc))
    return issues, r, file


def check_native_shot(root, receipt_path):
    try:
        issues, r, file = _shot_proof(root, receipt_path)
        return result('PASS' if not issues else 'FAIL', errors=issues, shot=r.get('shot'), receipt=str(file))
    except (OSError, ValueError, KeyError) as exc:
        return result('FAIL', error=str(exc))


def _run_blender(binary, scene, script, shot, out, blend_sha, width, height, samples, probe):
    argv = [binary, '--background', str(scene), '--disable-autoexec', '--python', str(script), '--',
            '--shot', shot, '--out', str(out), '--width', str(width), '--height', str(height),
            '--samples', str(samples), '--blend-sha', blend_sha]
    if probe:argv.append('--probe')
    t0 = time.monotonic()
    try:proc = subprocess.run(argv, capture_output=True, text=True, timeout=3600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, time.monotonic()-t0, str(exc)
    return proc.returncode, time.monotonic()-t0, (proc.stdout + '\n' + proc.stderr)[-18000:]


def native_shot(root, import_receipt, shot, run_id, *, width=960, height=540, samples=12,
                max_estimated_seconds=7200):
    binary = _blender()
    if not binary:
        return result('BLOCKED', gate='BLENDER_RUNTIME', error='No executable Blender on authorized host')
    if shot not in SHOTS:return result('BLOCKED', error='Unknown native shot')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        return result('BLOCKED', gate='ENCODER_RUNTIME', error='FFmpeg and ffprobe required')
    if (type(width) is not int or type(height) is not int or width < 320 or height < 180
        or width > 1920 or height > 1080 or width % 2 or height % 2 or type(samples) is not int
        or not 4 <= samples <= 64 or max_estimated_seconds <= 0):
        return result('BLOCKED', error='Invalid render configuration')
    try:
        import_path = inside(root, import_receipt, must_exist=True)
        validated = check_import(root, str(import_path))
        if validated['status'] != 'PASS':return result('BLOCKED', gate='NATIVE_IMPORT_PROOF', detail=validated)
        ip = load_json(import_path)
        scene = inside(root, ip['native_blend'], must_exist=True)
        scene_hash = sha256(scene)
        script = Path(__file__).resolve().parent.parent/'blender'/'render_native_frames.py'
        run_dir = inside(root, Path('native_shots')/slug(run_id))
        if run_dir.exists():
            candidate = run_dir/'native_shot_receipt.json'
            if candidate.is_file():
                check = check_native_shot(root, str(candidate))
                if check['status']=='PASS':
                    prior=load_json(candidate)
                    if (prior['shot']==shot and prior['import_proof_sha256']==sha256(import_path)
                        and prior['width']==width and prior['height']==height and prior['samples']==samples):
                        return result('PASS', receipt=str(candidate), reused_verified_shot=True, shot=shot)
            return result('BLOCKED', error='Existing shot has incomplete/stale proof; use a new run ID')
        run_dir.mkdir(parents=True)
        probe_dir = run_dir/'benchmark';probe_dir.mkdir()
        rc, seconds, log = _run_blender(binary,scene,script,shot,probe_dir,scene_hash,width,height,samples,True)
        (run_dir/'benchmark.log').write_text(log,encoding='utf8')
        sample_name = f'frame_{(SHOTS[shot][0]+SHOTS[shot][1])//2:06d}.png'
        if rc!=0 or not (probe_dir/sample_name).is_file():
            return result('PARTIAL', gate='BLENDER_BENCHMARK', error='Real frame probe failed', log=str(run_dir/'benchmark.log'))
        if _png_meta(probe_dir/sample_name) != (width, height):
            return result('PARTIAL', gate='BLENDER_BENCHMARK', error='Benchmark dimensions invalid')
        estimate=seconds * (SHOTS[shot][1]-SHOTS[shot][0]+1)
        if estimate > max_estimated_seconds:
            return result('PARTIAL', gate='RENDER_BUDGET', estimated_seconds=round(estimate,1),
                max_seconds=max_estimated_seconds, error='Benchmark predicts budget overrun; no full shot started')
        frames_dir=run_dir/'frames';frames_dir.mkdir()
        rc, elapsed, log=_run_blender(binary,scene,script,shot,frames_dir,scene_hash,width,height,samples,False)
        (run_dir/'blender_render.log').write_text(log,encoding='utf8')
        if rc!=0:return result('PARTIAL', gate='BLENDER_RENDER', error='Real Blender shot failed', log=str(run_dir/'blender_render.log'))
        worker=load_json(frames_dir/'blender_worker_frames.json')
        first,last,cam=SHOTS[shot]
        hashes=worker.get('image_hashes',{})
        expected={f'frame_{f:06d}.png' for f in range(first,last+1)}
        if (worker.get('status')!='RENDERED_UNSIGNED_AWAITING_HOST_VALIDATION'
            or worker.get('source_glb_sha256')!=ip['source_glb_sha256']
            or worker.get('blend_sha256_expected')!=scene_hash
            or worker.get('frame_range_inclusive')!=[first,last]
            or worker.get('camera')!=cam or worker.get('shot')!=shot
            or set(hashes)!=expected):
            return result('PARTIAL', gate='FRAME_COMPLETENESS', error='Blender worker did not output exact frames')
        for name,digest in hashes.items():
            if _png_meta(frames_dir/name)!=(width,height) or sha256(frames_dir/name)!=digest:
                return result('PARTIAL', gate='FRAME_INTEGRITY', error='Frame changed: '+name)
        proof = {'format': FORMAT_SHOT,'origin':'actual-blender-render-worker',
                 'shot':shot,'camera':cam,'frame_range_inclusive':[first,last],
                 'fps':24,'width':width,'height':height,'samples':samples,
                 'frame_hashes':hashes,'native_blend':str(scene),'native_blend_sha256':scene_hash,
                 'import_proof':str(import_path),'import_proof_sha256':sha256(import_path),
                 'render_worker_sha256':sha256(script),'benchmark_probe_s':round(seconds,3),
                 'benchmark_estimated_seconds':round(estimate,2),
                 'elapsed_render_seconds':round(elapsed,2),'finished_verified':False}
        receipt=run_dir/'native_shot_receipt.json'
        save_json(receipt,attest(proof,root))
        check=check_native_shot(root,str(receipt))
        if check['status']!='PASS':return result('PARTIAL',gate='SIGNED_SHOT_RECEIPT',details=check)
        return result('PASS',shot=shot,receipt=str(receipt),frames=96,
                      estimate_seconds=round(estimate,2),render_seconds=round(elapsed,2))
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        return result('PARTIAL', error=str(exc))


def assemble_native(root, film_id, shot_receipts):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        return result('BLOCKED', error='FFmpeg+ffprobe required')
    if len(shot_receipts)!=3:return result('BLOCKED',error='Exactly three independent signed shot receipts required')
    batches=[];issues=[]
    for rp in shot_receipts:
        try:
            a,r,p=_shot_proof(root,rp)
            issues.extend(a);batches.append((r,p))
        except (OSError,ValueError,KeyError) as exc:issues.append(str(exc))
    if issues:return result('BLOCKED',gate='SIGNED_BLENDER_SHOTS',errors=issues)
    batches.sort(key=lambda x:x[0]['frame_range_inclusive'][0])
    if [r['shot'] for r,_ in batches]!=list(SHOTS):return result('BLOCKED',error='Shot coverage/order mismatch')
    baseline=batches[0][0]
    fields=('native_blend_sha256','import_proof_sha256','render_worker_sha256','width','height','fps','samples')
    if any(any(r[k]!=baseline[k] for k in fields) for r,_ in batches[1:]):
        return result('BLOCKED',gate='SOURCE_CONTINUITY',error='Native shot sources or render configs differ')
    try:
        dst=inside(root,Path('native_films')/slug(film_id))
        if dst.exists():return result('BLOCKED',error='Final project exists; no overwrite')
        dst.mkdir(parents=True)
        frames=dst/'frames';frames.mkdir()
        all_hashes={}
        for r,p in batches:
            for name,h in sorted(r['frame_hashes'].items()):
                source=p.parent/'frames'/name
                target=frames/name
                shutil.copy2(source,target)
                if sha256(target)!=h:raise ValueError('Copied frame integrity failure')
                all_hashes[name]=h
        if set(all_hashes)!={f'frame_{i:06d}.png' for i in range(1,289)}:
            return result('PARTIAL',gate='FRAME_COVERAGE',error='Not exactly 288 unique verified frames')
        mp4=dst/'the_reach_blender.mp4'
        ffmpeg=shutil.which('ffmpeg')
        argv=[ffmpeg,'-hide_banner','-nostdin','-v','error','-framerate','24','-start_number','1',
              '-i',str(frames/'frame_%06d.png'),'-frames:v','288','-an','-c:v','libx264',
              '-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(mp4)]
        result_encode=subprocess.run(argv,capture_output=True,text=True,timeout=1200)
        if result_encode.returncode:return result('PARTIAL',error='Encoding failed',stderr=result_encode.stderr[-1500:])
        video=verify_mp4(root,str(mp4),deep=True)
        v=video.get('video',{})
        if (video['status']!='PASS' or v.get('frames')!=288 or abs(v.get('duration_s',0)-12)>.08
            or abs(v.get('fps',0)-24)>.02 or (v.get('width'),v.get('height'))!=(baseline['width'],baseline['height'])
            or v.get('audio_streams')!=0 or v.get('subtitle_streams')!=0):
            return result('ENCODED_UNVERIFIED',gate='POST_ENCODE',details=video)
        receipt={'format':FORMAT_FILM,'origin':'signed-real-blender-shots',
                 'production_status':'TECHNICAL_PASS_VISUAL_PENDING','finished_verified':False,
                 'human_visual_approval':'PENDING','source_glb_sha256':load_json(inside(root,baseline['import_proof']))['source_glb_sha256'],
                 'native_blend_sha256':baseline['native_blend_sha256'],
                 'film_path':str(mp4),'film_sha256':sha256(mp4),
                 'frame_hashes':all_hashes,'shot_receipts':[{'path':str(p),'sha256':sha256(p)} for _,p in batches],
                 'video':v,'subtitles':'OFF','audio':'NONE'}
        rp=dst/'native_film_receipt.json'
        save_json(rp,attest(receipt,root))
        return result('TECHNICAL_PASS_VISUAL_PENDING',video=str(mp4),receipt=str(rp),frames=288,shots=3)
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        return result('PARTIAL',error=str(exc))


def check_native_film(root, receipt_path):
    try:
        file=inside(root,receipt_path,must_exist=True)
        r=load_json(file);issues=[]
        if r.get('format')!=FORMAT_FILM or not authentic(r,root):issues.append('Bad film signature')
        if r.get('finished_verified') is not False:issues.append('Unsupported artistic completion claim')
        movie=inside(root,r['film_path'],must_exist=True)
        if sha256(movie)!=r.get('film_sha256'):issues.append('Encoded film changed')
        hashes=r.get('frame_hashes',{})
        if not isinstance(hashes,dict) or set(hashes)!={f'frame_{i:06d}.png' for i in range(1,289)}:
            issues.append('Missing/excess encoded source frame hashes')
        else:
            for name,digest in hashes.items():
                if sha256(movie.parent/'frames'/name)!=digest:
                    issues.append('Altered frame '+name);break
        if len(r.get('shot_receipts',[]))!=3:issues.append('Missing signed shots')
        else:
            for entry in r['shot_receipts']:
                sp=inside(root,entry['path'],must_exist=True)
                if sha256(sp)!=entry['sha256'] or check_native_shot(root,str(sp))['status']!='PASS':
                    issues.append('Native shot proof invalid')
        if not issues:
            vid=verify_mp4(root,str(movie),deep=True)
            v=vid.get('video',{})
            expected_v=r.get('video',{})
            if (vid['status']!='PASS' or v.get('frames')!=288 or abs(v.get('fps',0)-24)>.02
                or abs(v.get('duration_s',0)-12)>.08 or v.get('audio_streams')!=0
                or v.get('subtitle_streams')!=0
                or (v.get('width'),v.get('height'))!=(expected_v.get('width'),expected_v.get('height'))):
                issues.append('Video independent decode/metadata failed')
        return result('PASS' if not issues else 'FAIL',errors=issues,
                      production_status='TECHNICAL_PASS_VISUAL_PENDING',video=str(movie))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return result('FAIL',error=str(exc))


def finish_native(root, glb_path, run_id, *, width=960, height=540, samples=12,
                  max_estimated_seconds=7200):
    # Check every execution dependency BEFORE creating a project folder.
    if not _blender():return result('BLOCKED',gate='BLENDER_RUNTIME',error='Blender unavailable; no native render attempted')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        return result('BLOCKED',gate='ENCODER_RUNTIME',error='FFmpeg unavailable')
    try:
        glb=inside(root,glb_path,must_exist=True)
        if glb.suffix.lower()!='.glb':return result('BLOCKED',error='Expected GLB')
        verify_glb_bytes(glb.read_bytes())
        slug(run_id)
    except (OSError,ValueError) as exc:return result('BLOCKED',error=str(exc))
    imp_id=run_id+'_native'
    imp_path=inside(root,Path('portable_imports')/imp_id/'blender_import_proof.json')
    if imp_path.exists():
        check=check_import(root,str(imp_path))
        if check['status']!='PASS' or load_json(imp_path)['source_glb_sha256']!=sha256(glb):
            return result('BLOCKED',error='Existing import is stale or incomplete; new run ID required')
        stage=result('PASS',proof=str(imp_path),reused=True)
    else:stage=import_rig(root,str(glb),imp_id)
    if stage.get('status')!='PASS':return {**stage,'gate':'BLENDER_IMPORT'}
    receipts=[]
    for ix,shot in enumerate(SHOTS,1):
        s=native_shot(root,str(imp_path),shot,f'{run_id}_shot{ix}',width=width,height=height,samples=samples,
                      max_estimated_seconds=max_estimated_seconds)
        if s.get('status')!='PASS':return {**s,'completed_shots':receipts,'gate':s.get('gate','BLENDER_SHOT')}
        receipts.append(s['receipt'])
    return assemble_native(root,run_id,receipts)
