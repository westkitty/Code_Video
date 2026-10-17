"""Independent red-team cases from the 2026-10-16 audit."""
import json, math, shutil, subprocess
from pathlib import Path
import pytest
from test_kernel import film, fixture_proof
from codevideo.common import save_json, load_json, sha256
from codevideo.rig_proof import attest
from codevideo.contracts import validate_graph
from codevideo.render_shots import plan_render
from codevideo.assemble import assemble
from codevideo.project import production_status


def write_png(path, color=(200,30,40), width=64, height=64):
    """Small valid RGB PNG; no Pillow dependency in the portable test suite."""
    import struct,zlib
    signature=b'\x89PNG\r\n\x1a\n'
    def chunk(tag,payload):
        return struct.pack('>I',len(payload))+tag+payload+struct.pack('>I',zlib.crc32(tag+payload)&0xffffffff)
    rows=b''.join(b'\x00'+bytes(color)*width for _ in range(height))
    data=(signature+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))
          +chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))
    Path(path).write_bytes(data)


def signed_fixture(tmp_path):
    film(tmp_path)
    proof=fixture_proof()
    proof['origin']='blender-evaluated-v1'
    source=tmp_path/'scene.blend'
    proof['scene']={'path':str(source),'sha256':sha256(source)}
    save_json(tmp_path/'proof.json',attest(proof,tmp_path))
    return proof


def test_graph_rejects_nonintegral_fps_and_invalid_scene(tmp_path):
    g=film(tmp_path)
    g['fps']=29.97
    assert validate_graph(g)['status']=='FAIL'
    g['fps']=30;g['scene']=42
    assert validate_graph(g,root=tmp_path)['status']=='FAIL'


def test_graph_rejects_infinite_or_missing_title(tmp_path):
    g=film(tmp_path);g['title']='   '
    assert validate_graph(g)['status']=='FAIL'
    g['title']='Working';g['fps']=float('nan')
    assert validate_graph(g)['status']=='FAIL'


def test_unsigned_valid_png_is_not_trusted_as_blender_render(tmp_path):
    signed_fixture(tmp_path)
    plan=plan_render(tmp_path,'film.json','proof.json','test')
    folder=Path(plan['output']);folder.mkdir(parents=True)
    write_png(folder/'000000.png',(255,0,0))
    assert 0 in plan_render(tmp_path,'film.json','proof.json','test')['missing']


def test_sparse_signed_receipt_cannot_unlock_encode(tmp_path):
    signed_fixture(tmp_path)
    plan=plan_render(tmp_path,'film.json','proof.json','test')
    folder=Path(plan['output']);folder.mkdir(parents=True)
    for i in range(30): write_png(folder/f'{i:06d}.png',(i*7%255,0,0))
    receipt={'format':'codevideo.render-receipt.v1','shot':'test','cache_key':plan['cache_key'],
             'frame_start':0,'frame_end':29,'frame_count':30,'scene_hash':sha256(tmp_path/'scene.blend'),
             'frame_hashes':{'000000.png':sha256(folder/'000000.png')}}
    save_json(folder/'receipt.json',attest(receipt,tmp_path))
    result=assemble(tmp_path,'film.json','proof.json')
    assert result['status']=='BLOCKED'


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='ffmpeg missing')
def test_status_cannot_advance_without_rig(tmp_path):
    g=film(tmp_path)
    out=tmp_path/'looks_valid.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-nostdin','-v','error','-f','lavfi',
                    '-i','testsrc2=size=64x64:rate=30','-t','1','-c:v','libx264',
                    '-pix_fmt','yuv420p',str(out)],check=True)
    s=production_status(tmp_path,'film.json',video_path='looks_valid.mp4')
    assert s['status']!='TECHNICAL_PASS_VISUAL_PENDING'


def test_proof_must_have_mapped_frames_and_no_bone_cycles():
    from codevideo.rig_proof import validate_rig_proof
    p=fixture_proof();p['bones'][1]['samples'][1]['frame']=999
    assert validate_rig_proof(p,allow_fixture=True)['status']=='FAIL'
    p=fixture_proof();p['bones'][1]['parent']='head';p['bones'][2]['parent']='torso'
    assert validate_rig_proof(p,allow_fixture=True)['status']=='FAIL'


def synthetic_film_ready(tmp_path):
    """Unit fixture: synthetically generated PNGs; *not* proof of a Blender film."""
    signed_fixture(tmp_path)
    plan=plan_render(tmp_path,'film.json','proof.json','test')
    folder=Path(plan['output']);folder.mkdir(parents=True)
    for frame in range(30):
        write_png(folder/f'{frame:06d}.png',(frame*7%256,32,23))
    receipt={'format':'codevideo.render-receipt.v1','shot':'test','cache_key':plan['cache_key'],
             'frame_start':0,'frame_end':29,'frame_count':30,'scene_hash':sha256(tmp_path/'scene.blend'),
             'frame_hashes':{f'{f:06d}.png':sha256(folder/f'{f:06d}.png') for f in range(30)}}
    save_json(folder/'receipt.json',attest(receipt,tmp_path))
    return folder,receipt


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='ffmpeg missing')
def test_changed_frame_produces_fresh_encode_cache(tmp_path):
    folder,receipt=synthetic_film_ready(tmp_path)
    first=assemble(tmp_path,'film.json','proof.json')
    assert first['status']=='TECHNICAL_PASS_VISUAL_PENDING',first
    write_png(folder/'000010.png',(255,0,255))
    receipt['frame_hashes']['000010.png']=sha256(folder/'000010.png')
    save_json(folder/'receipt.json',attest(receipt,tmp_path))
    second=assemble(tmp_path,'film.json','proof.json')
    assert second['status']=='TECHNICAL_PASS_VISUAL_PENDING',second
    assert first['video']!=second['video']
    assert second['check']['video']['fully_decoded']


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='ffmpeg missing')
def test_corrupt_cached_segment_blocks_rather_than_reuses(tmp_path):
    synthetic_film_ready(tmp_path)
    out=assemble(tmp_path,'film.json','proof.json')
    assert out['status']=='TECHNICAL_PASS_VISUAL_PENDING',out
    delivery=Path(out['video'])
    (delivery).unlink()  # isolated test fixture: simulate interrupted stage/delivery
    (delivery.with_suffix('.receipt.json')).unlink()
    segment=tmp_path/'staging'/delivery.stem/'test.mp4'
    assert segment.exists()
    segment.write_bytes(b'not an MP4')
    blocked=assemble(tmp_path,'film.json','proof.json')
    assert blocked['status']=='BLOCKED' and blocked['gate']=='STAGE_INTEGRITY'


def test_signed_partial_progress_reuses_only_exact_hashes(tmp_path):
    signed_fixture(tmp_path)
    p=plan_render(tmp_path,'film.json','proof.json','test')
    folder=Path(p['output']);folder.mkdir(parents=True)
    for f in (0,3,7):write_png(folder/f'{f:06d}.png',(0,155,0))
    data={'format':'codevideo.render-progress.v1','shot':'test','cache_key':p['cache_key'],
          'scene_hash':sha256(tmp_path/'scene.blend'),
          'frame_hashes':{f'{f:06d}.png':sha256(folder/f'{f:06d}.png') for f in (0,3,7)}}
    save_json(folder/'progress.json',attest(data,tmp_path))
    p=plan_render(tmp_path,'film.json','proof.json','test')
    assert p['remaining']==27 and not ({0,3,7}&set(p['missing']))
    (folder/'000003.png').write_bytes(b'tampered')
    assert 3 in plan_render(tmp_path,'film.json','proof.json','test')['missing']


def test_sparse_final_receipt_rejected_even_with_full_signed_progress(tmp_path):
    folder,receipt=synthetic_film_ready(tmp_path)
    progress={'format':'codevideo.render-progress.v1','shot':'test','cache_key':receipt['cache_key'],
              'scene_hash':sha256(tmp_path/'scene.blend'),'frame_hashes':receipt['frame_hashes']}
    save_json(folder/'progress.json',attest(progress,tmp_path))
    receipt['frame_hashes']={'000000.png':receipt['frame_hashes']['000000.png']}
    save_json(folder/'receipt.json',attest(receipt,tmp_path))
    assert plan_render(tmp_path,'film.json','proof.json','test')['remaining']==0
    out=assemble(tmp_path,'film.json','proof.json')
    assert out['status']=='BLOCKED' and out['gate']=='FRAME_RECEIPT',out


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='ffmpeg missing')
def test_review_packet_is_fresh_and_not_reused_after_tampering(tmp_path):
    film(tmp_path)
    subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',
                    'testsrc2=size=64x64:rate=30','-t','1','-c:v','libx264',
                    '-pix_fmt','yuv420p',str(tmp_path/'test.mp4')],check=True)
    from codevideo.verify_mp4 import extract_review_frames
    first=extract_review_frames(tmp_path,'test.mp4','film.json')
    assert first['status']=='AWAITING_VISUAL_REVIEW'
    packet=load_json(Path(first['packet']))
    sample=Path(packet['frames'][0]['path']); digest=sha256(sample)
    sample.write_bytes(b'tampered')
    second=extract_review_frames(tmp_path,'test.mp4','film.json')
    fresh=load_json(Path(second['packet']))
    assert first['packet']!=second['packet']
    assert sha256(Path(fresh['frames'][0]['path']))==digest


def test_malformed_ffprobe_frame_value_returns_fail_not_exception(tmp_path,monkeypatch):
    from codevideo import verify_mp4 as module
    bad=tmp_path/'bad.mp4';bad.write_bytes(b'fixture')
    def fake_run(args,timeout=600):
        return 0,json.dumps({'streams':[{'codec_type':'video','nb_read_frames':'N/A',
            'avg_frame_rate':'0/0','codec_name':'h264','pix_fmt':'yuv420p'}],
            'format':{'duration':'N/A'}}),''
    monkeypatch.setattr(module,'run_checked',fake_run)
    res=module.verify_mp4(tmp_path,'bad.mp4',deep=False)
    assert res['status']=='FAIL'


def test_cli_reports_missing_mcp_as_blocked_not_traceback(tmp_path,capsys):
    import sys
    from codevideo.cli import main
    # Independently observed runtime has no MCP SDK; use a missing import sentinel.
    if __import__('importlib').util.find_spec('mcp') is not None: pytest.skip('MCP SDK available; use transport test')
    code=main(['--workspace',str(tmp_path),'serve','--stdio'])
    captured=capsys.readouterr()
    assert code==2 and json.loads(captured.out)['status']=='BLOCKED'


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='ffmpeg missing')
def test_full_audio_mux_preserves_duration_and_no_subtitles(tmp_path):
    synthetic_film_ready(tmp_path)
    wav=tmp_path/'original_audio.wav'
    subprocess.run(['ffmpeg','-hide_banner','-nostdin','-v','error','-f','lavfi',
                    '-i','sine=frequency=440:sample_rate=44100','-t','1',str(wav)],check=True)
    graph=load_json(tmp_path/'film.json');graph['audio']='original_audio.wav'
    save_json(tmp_path/'film.json',graph)
    out=assemble(tmp_path,'film.json','proof.json')
    assert out['status']=='TECHNICAL_PASS_VISUAL_PENDING',out
    check=out['check']['video']
    assert check['audio_streams']==1 and check['subtitle_streams']==0
    assert check['fully_decoded']
    assert abs(check['duration_s']-1.0)<0.12
