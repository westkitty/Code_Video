"""Adversarial checks; intentionally NEVER fabricate native Blender PASS."""
import json
import os
from pathlib import Path
import pytest
from codevideo.native_finish import (_png_meta, native_shot, finish_native, assemble_native,
                                     check_native_shot, check_native_film, SHOTS)
from codevideo.blender_bridge import blender_executable
from codevideo.golden_reach import default_spec
from codevideo.portable_rig import build_glb


def test_native_finish_blocks_unequipped_host_without_writing(tmp_path, monkeypatch):
    monkeypatch.setattr('codevideo.native_finish._blender', lambda: None)
    p=tmp_path/'original.glb';p.write_bytes(build_glb(default_spec())[0])
    r=finish_native(tmp_path,p,'first_attempt')
    assert r['status']=='BLOCKED' and r['gate']=='BLENDER_RUNTIME'
    assert not (tmp_path/'native_films').exists()
    assert not (tmp_path/'native_shots').exists()
    assert not (tmp_path/'portable_imports').exists()


def test_shot_blocks_before_mutation_without_blender(tmp_path, monkeypatch):
    monkeypatch.setattr('codevideo.native_finish._blender', lambda: None)
    r=native_shot(tmp_path,'untrusted.json','recognition','first_shot')
    assert r['status']=='BLOCKED' and r['gate']=='BLENDER_RUNTIME'
    assert not (tmp_path/'native_shots').exists()


def test_bad_blender_override_disables_fallback(tmp_path,monkeypatch):
    monkeypatch.setenv('CODEVIDEO_BLENDER',str(tmp_path/'missing-blender'))
    assert blender_executable() is None


def test_glb_worker_not_a_proof(tmp_path):
    d=tmp_path/'native_shots'/'fake';d.mkdir(parents=True)
    r={'format':'codevideo.blender-native-shot.v1','origin':'actual-blender-render-worker',
       'shot':'recognition','fps':24,'width':960,'height':540,'frame_range_inclusive':[1,96]}
    p=d/'native_shot_receipt.json';p.write_text(json.dumps(r))
    assert check_native_shot(tmp_path,str(p))['status']=='FAIL'


def test_unsigned_film_fails(tmp_path):
    p=tmp_path/'forged.json';p.write_text(json.dumps({'format':'codevideo.blender-native-film.v1',
          'finished_verified':True,'film_path':'nowhere.mp4'}))
    assert check_native_film(tmp_path,str(p))['status']=='FAIL'


def test_assembly_blocks_missing_signed_shots(tmp_path):
    r=assemble_native(tmp_path,'movie_1', ['one','two','three'])
    assert r['status']=='BLOCKED'
    assert not (tmp_path/'native_films').exists()


def test_png_meta_cannot_accept_fake(tmp_path):
    p=tmp_path/'fake.png';p.write_bytes(b'just text'*100)
    with pytest.raises(ValueError,match='Not a real PNG'):_png_meta(p)


def test_render_worker_is_bpy_and_has_source_contract():
    src=Path(__file__).resolve().parents[1]/'blender'/'render_native_frames.py'
    s=src.read_text();compile(s,str(src),'exec')
    assert 'import bpy' in s and 'bpy.ops.render.render' in s
    assert 'scene.render.engine = \'CYCLES\'' in s
    assert 'CODEVIDEO_IMPORTED_SOURCE_SHA256' in s
    assert '--probe' in s and 'RENDERED_UNSIGNED_AWAITING_HOST_VALIDATION' in s


def test_blender_import_has_director_cameras():
    src=Path(__file__).resolve().parents[1]/'blender'/'import_portable_rig.py'
    s=src.read_text();compile(s,str(src),'exec')
    for name in ('CodeVideo_Shot_01','CodeVideo_Shot_02','CodeVideo_Shot_03'):
        assert name in s
    assert 'CODEVIDEO_IMPORTED_SOURCE_SHA256' in s
    assert 'bpy.ops.import_scene.gltf' in s


def test_exact_shot_coverage():
    assert [(x[0],x[1]) for x in SHOTS.values()]==[(1,96),(97,192),(193,288)]


def test_mac_runner_is_syntactically_valid_and_non_destructive():
    import subprocess
    script=Path(__file__).resolve().parents[1]/'bin'/'finish-native-on-mac.sh'
    p=subprocess.run(['bash','-n',str(script)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    s=script.read_text()
    assert 'CODEVIDEO_BLENDER' in s and 'CodeVideoNativeWorkspace' in s
    assert 'native-finish' in s
    assert 'sudo ' not in s and 'docker ' not in s and 'rm -rf' not in s


def test_command_line_fails_closed_without_blender(tmp_path,monkeypatch):
    import subprocess,sys
    from codevideo.portable_rig import build_glb
    f=tmp_path/'example.glb';f.write_bytes(build_glb(default_spec())[0])
    env=os.environ.copy();env['CODEVIDEO_BLENDER']=str(tmp_path/'missing')
    env['CODEVIDEO_WORKSPACE']=str(tmp_path)
    root=Path(__file__).resolve().parents[1]
    env['PYTHONPATH']=str(root)
    p=subprocess.run([sys.executable,'-m','codevideo.cli','--workspace',str(tmp_path),
          'native-finish','example.glb','test0'],env=env,capture_output=True,text=True)
    assert p.returncode==2
    assert 'BLENDER_RUNTIME' in p.stdout
    assert not (tmp_path/'portable_imports').exists()


def test_plugin_mcp_launcher_is_executable_and_has_fail_closed_runtime_probe():
    import subprocess
    p=Path(__file__).resolve().parents[1]/'bin'/'codevideo-mcp'
    assert os.access(p,os.X_OK)
    cmd=subprocess.run(['sh','-n',str(p)],capture_output=True,text=True)
    assert cmd.returncode==0,cmd.stderr
    text=p.read_text()
    assert 'mcp.server' in text and 'CODEVIDEO_WORKSPACE' in text
