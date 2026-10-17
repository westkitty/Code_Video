import os,json,math,subprocess,shutil
from pathlib import Path
import pytest
from codevideo.common import GateError,inside,load_json,save_json,sha256,workspace_root
from codevideo.contracts import validate_graph
from codevideo.preflight import preflight
from codevideo.project import create_project,create_demo_project
from codevideo.rig_proof import validate_rig_proof,attest
from codevideo.render_shots import plan_render,valid_png
from codevideo.verify_mp4 import verify_mp4,extract_review_frames
from codevideo.assemble import assemble

FRAMES=[0,8,17,24,32,46,59]
MOTIONS={
  'torso':[0,.12,.08,.3,.21,.04,.02],
  'head':[0,.3,.7,.54,.45,.21,.6],
  'arm':[0,.1,.5,.92,.68,.32,.03],
  'forearm':[0,.14,.1,.16,.73,.41,.07],
}

def bone(name, parent, angles):
    return {'name':name,'parent':parent,
            'samples':[{'frame':f,'quaternion':[math.cos(a/2),math.sin(a/2),0,0]} for f,a in zip(FRAMES,angles)]}

def fixture_proof(kind='organic'):
    names=list(MOTIONS)
    if kind=='organic':
        meshes=[{'name':'Skinned body','vertices':240,'weighted_vertices':220,'max_weight_error':.01,
                 'deformed_vertices':180,'max_deformation':.4,
                 'influences':{name:35 for name in names},'bone_parented':False}]
    else:
        meshes=[{'name':name+' part','vertices':100,'weighted_vertices':0,'max_weight_error':0,
                 'bone_parent':name,'bone_parented':True,'max_deformation':.2,'deformed_vertices':100}
                for name in names]
    return {'format':'codevideo.rigproof.v1','origin':'test-fixture','anatomy':kind,
            'scene':{'path':'fake.blend','sha256':'test'},'sample_frames':FRAMES,
            'bones':[bone('root',None,[0]*len(FRAMES))]+[bone(name,'root',angles) for name,angles in MOTIONS.items()],
            'meshes':meshes}

def film(tmp_path):
    graph={'format':'codevideo.shotgraph.v1','title':'QA short','scene':'scene.blend',
           'audio':None,'subtitles':False,'fps':30,'width':64,'height':64,
           'shots':[{'id':'test','start':0,'end':29,'purpose':'An obvious action',
                     'emotion':'urgent','performance':'Actual bone action and reaction',
                     'camera':'Camera_Main','lens_mm':35,'lighting':'Soft key',
                     'continuity':'Character stays in frame','visibility':'All joints visible'}]}
    (tmp_path/'scene.blend').write_bytes(b'Not a real Blender file - contract unit fixture')
    save_json(tmp_path/'film.json',graph)
    return graph

def test_real_shot_contract_rejects_gaps_and_subtitles(tmp_path):
    g=film(tmp_path)
    assert validate_graph(g,root=tmp_path)['status']=='PASS'
    g['shots'][0]['start']=2
    assert any('gap' in e for e in validate_graph(g)['errors'])
    g['shots'][0]['start']=0;g['subtitles']=True
    assert validate_graph(g)['status']=='FAIL'

def test_default_template_only_no_overwrite(tmp_path):
    a=create_project(tmp_path,'puppet_01')
    assert a['status']=='TEMPLATE_CREATED_UNVALIDATED'
    assert create_project(tmp_path,'puppet_01')['status']=='BLOCKED'
    assert not (tmp_path/'projects'/'puppet_01'/'scenes'/'puppet.blend').exists()

def test_outside_root_rejected(tmp_path):
    (tmp_path/'escape').symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(GateError):inside(tmp_path,'../escape.mp4')
    with pytest.raises(GateError):inside(tmp_path,'escape/whatever')

def test_workspace_must_be_dedicated(tmp_path,monkeypatch):
    monkeypatch.setenv('CODEVIDEO_WORKSPACE',str(tmp_path))
    assert workspace_root()==tmp_path.resolve()

def test_real_independent_joint_fixture_passes_only_in_fixture_mode():
    p=fixture_proof()
    assert validate_rig_proof(p,allow_fixture=True)['status']=='PASS'
    assert validate_rig_proof(p)['status']=='FAIL'

def test_root_only_animation_fails():
    p=fixture_proof()
    p['bones']=[bone('root',None,MOTIONS['head'])]+[bone(n,'root',[0]*7) for n in MOTIONS]
    assert validate_rig_proof(p,allow_fixture=True)['status']=='FAIL'

def test_universal_oscillation_fails():
    p=fixture_proof()
    p['bones']=[bone('root',None,[0]*7)]+[bone(n,'root',MOTIONS['head']) for n in MOTIONS]
    assert validate_rig_proof(p,allow_fixture=True)['status']=='FAIL'

def test_offscreen_decorative_bones_fail():
    p=fixture_proof()
    p['meshes'][0]['influences']={'torso':35}
    assert any('real mesh geometry' in e for e in validate_rig_proof(p,allow_fixture=True)['errors'])

def test_skinned_organic_mesh_is_required():
    p=fixture_proof()
    p['meshes'][0]['weighted_vertices']=0
    p['meshes'][0]['deformed_vertices']=0
    assert validate_rig_proof(p,allow_fixture=True)['status']=='FAIL'

def test_invalid_skin_weight_normalization_fails():
    p=fixture_proof()
    p['meshes'][0]['max_weight_error']=.42
    assert validate_rig_proof(p,allow_fixture=True)['status']=='FAIL'

def test_mechanical_bone_parented_segments_work():
    p=fixture_proof('segmented')
    assert validate_rig_proof(p,allow_fixture=True)['status']=='PASS'
    p['meshes'][0]['bone_parented']=False;p['meshes'][0]['bone_parent']=None
    assert validate_rig_proof(p,allow_fixture=True)['status']=='FAIL'

def test_untrusted_receipt_and_wrong_hash_rejected(tmp_path):
    f=tmp_path/'scene.blend';f.write_bytes(b'fake fixture file')
    p=fixture_proof();p['origin']='blender-evaluated-v1'
    p['scene']={'path':str(f),'sha256':sha256(f)}
    assert any('attestation' in s for s in validate_rig_proof(p,root=tmp_path)['errors'])
    signed=attest(p,tmp_path)
    assert validate_rig_proof(signed,root=tmp_path)['status']=='PASS'
    signed['bones'][1]['samples'][1]['quaternion']=[1,0,0,0]
    assert validate_rig_proof(signed,root=tmp_path)['status']=='FAIL'
    assert (tmp_path/'.codevideo'/'proof-key').stat().st_mode & 0o077 == 0

def test_stale_source_hash_rejected(tmp_path):
    f=tmp_path/'scene.blend';f.write_bytes(b'dummy file')
    p=fixture_proof();p['origin']='blender-evaluated-v1';p['scene']={'path':str(f),'sha256':sha256(f)}
    signed=attest(p,tmp_path)
    f.write_bytes(b'altered dummy file')
    assert any('mismatch' in s for s in validate_rig_proof(signed,root=tmp_path)['errors'])

def test_render_requires_legitimate_rig(tmp_path):
    film(tmp_path)
    p=fixture_proof()
    save_json(tmp_path/'proof.json',p)
    r=plan_render(tmp_path,'film.json','proof.json','test')
    assert r['status']=='BLOCKED' and r['gate']=='RIG_PROOF'

def test_render_rejects_unrelated_scene_even_with_signed_proof(tmp_path):
    film(tmp_path)
    f=tmp_path/'different.blend';f.write_bytes(b'fixture other source')
    p=fixture_proof();p['origin']='blender-evaluated-v1';p['scene']={'path':str(f),'sha256':sha256(f)}
    save_json(tmp_path/'proof.json',attest(p,tmp_path))
    r=plan_render(tmp_path,'film.json','proof.json','test')
    assert r['status']=='BLOCKED' and r['gate']=='SOURCE_MISMATCH'

def test_encode_cannot_skip_missing_frames(tmp_path):
    film(tmp_path)
    f=tmp_path/'scene.blend';p=fixture_proof();p['origin']='blender-evaluated-v1'
    p['scene']={'path':str(f),'sha256':sha256(f)}
    save_json(tmp_path/'proof.json',attest(p,tmp_path))
    r=assemble(tmp_path,'film.json','proof.json')
    assert r['status']=='BLOCKED' and r['gate']=='FRAME_COMPLETENESS'

def test_no_blender_demo_cannot_claim_success(tmp_path,monkeypatch):
    monkeypatch.setattr(shutil,'which',lambda x: None if x=='blender' else '/usr/bin/true')
    r=create_demo_project(tmp_path,'blocked')
    assert r['status']=='BLOCKED'
    assert not (tmp_path/'projects'/'blocked').exists()

@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='ffmpeg missing')
def test_real_video_decode_and_review_packet(tmp_path):
    vid=tmp_path/'test.mp4'
    p=subprocess.run([shutil.which('ffmpeg'),'-nostdin','-v','error','-f','lavfi',
                     '-i','testsrc2=size=64x64:rate=30','-t','1','-c:v','libx264',
                     '-pix_fmt','yuv420p',str(vid)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    graph=film(tmp_path)
    check=verify_mp4(tmp_path,'test.mp4','film.json',deep=True)
    assert check['status']=='PASS',check
    assert check['video']['fully_decoded']
    assert check['visual_qa']=='NOT_PERFORMED' and not check['finished_verified']
    review=extract_review_frames(tmp_path,'test.mp4','film.json')
    assert review['status']=='AWAITING_VISUAL_REVIEW'
    packet=load_json(Path(review['packet']))
    assert len(packet['frames'])==3
    assert all(Path(f['path']).exists() for f in packet['frames'])

@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='ffmpeg missing')
def test_incorrect_fps_rejected(tmp_path):
    vid=tmp_path/'badfps.mp4'
    subprocess.run([shutil.which('ffmpeg'),'-nostdin','-v','error','-f','lavfi',
                '-i','testsrc2=size=64x64:rate=12','-t','1','-c:v','libx264','-pix_fmt','yuv420p',str(vid)],check=True)
    film(tmp_path)
    r=verify_mp4(tmp_path,'badfps.mp4','film.json')
    assert r['status']=='FAIL' and any('FPS' in x for x in r['errors'])

def test_plugin_manifest_and_path_contract():
    root=Path(__file__).resolve().parents[1]
    j=load_json(root/'plugin.json');m=load_json(root/'mcp.json')
    assert j['name']=='code-video-production-kernel'
    assert m['mcpServers']['code-video-local']['command']=='./bin/codevideo-mcp'
    assert m['mcpServers']['code-video-local']['env']['CODEVIDEO_WORKSPACE']=='${PLUGIN_DATA}/workspace'
    assert (root/'bin'/'codevideo-mcp').exists()

@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='ffmpeg missing')
def test_full_mp4_assembly_with_synthetic_frame_fixture(tmp_path):
    """Checks encoder mechanics only; no Blender rig or finished-film claim."""
    film(tmp_path)
    source=tmp_path/'scene.blend'
    p=fixture_proof();p['origin']='blender-evaluated-v1'
    p['scene']={'path':str(source),'sha256':sha256(source)}
    save_json(tmp_path/'proof.json',attest(p,tmp_path))
    plan=plan_render(tmp_path,'film.json','proof.json','test')
    assert plan['status']=='PASS'
    cache=Path(plan['output']);cache.mkdir(parents=True)
    run=subprocess.run([shutil.which('ffmpeg'),'-hide_banner','-nostdin','-v','error',
      '-f','lavfi','-i','testsrc2=size=64x64:rate=30','-frames:v','30',
      '-start_number','0',str(cache/'%06d.png')],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    hashes={f'{f:06d}.png':sha256(cache/f'{f:06d}.png') for f in range(30)}
    assert valid_png(cache/'000001.png',64,64)
    save_json(cache/'receipt.json',attest({'format':'codevideo.render-receipt.v1','shot':'test',
              'cache_key':plan['cache_key'],'frame_start':0,'frame_end':29,
              'frame_count':30,'frame_hashes':hashes,'scene_hash':sha256(source)},tmp_path))
    output=assemble(tmp_path,'film.json','proof.json')
    assert output['status']=='TECHNICAL_PASS_VISUAL_PENDING',output
    assert Path(output['video']).exists()
    assert output['check']['video']['fully_decoded']
    assert output['check']['visual_qa']=='NOT_PERFORMED'
    assert assemble(tmp_path,'film.json','proof.json')['status']=='TECHNICAL_PASS_VISUAL_PENDING'

def test_mcp_adapter_registers_native_film_job_tools(monkeypatch,tmp_path):
    """Tool registration contract only; NOT an MCP transport integration test."""
    import sys,types
    class FakeServer:
        def __init__(self,name):self.name=name;self.tools={}
        def tool(self):
            def register(func):self.tools[func.__name__]=func;return func
            return register
    fake=types.ModuleType('mcp')
    server=types.ModuleType('mcp.server');server.MCPServer=FakeServer
    monkeypatch.setitem(sys.modules,'mcp',fake)
    monkeypatch.setitem(sys.modules,'mcp.server',server)
    from codevideo.mcp_server import build_server,serve
    app=build_server(tmp_path)
    assert len(app.tools)==33
    assert {'preflight_new_film_job','build_new_film_rig',
            'render_next_new_film_batch','encode_new_film',
            'produce_supported_new_film'}.issubset(app.tools)
    assert {"render_mechanical_3d_smoke","replay_articulated_3d_stage","check_articulated_3d_stage","render_golden_reach_actor","check_golden_reach_actor","export_portable_animated_rig","verify_portable_animated_rig"}.issubset(app.tools)
    assert app.tools['preflight']()['workspace']==str(tmp_path)
    assert app.tools['create_project']('tester')['status']=='TEMPLATE_CREATED_UNVALIDATED'
    with pytest.raises(ValueError):serve(tmp_path,host='0.0.0.0')


def test_real_blender_benchmark_blocks_when_tool_missing(tmp_path,monkeypatch):
    from codevideo.benchmark import benchmark
    film(tmp_path)
    f=tmp_path/'scene.blend';p=fixture_proof();p['origin']='blender-evaluated-v1'
    p['scene']={'path':str(f),'sha256':sha256(f)}
    save_json(tmp_path/'proof.json',attest(p,tmp_path))
    monkeypatch.setattr(shutil,'which',lambda name:None if name=='blender' else '/usr/bin/true')
    r=benchmark(tmp_path,'film.json','proof.json','test')
    assert r['status']=='BLOCKED' and r['gate']=='BLENDER'
