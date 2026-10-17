"""Live rendered negative/positive controls for the optional segmented 3D stage."""
import json, shutil, copy
from pathlib import Path
import pytest

from codevideo.common import load_json,save_json
from codevideo.vtk_stage import RIG, TRACKS, _read_tracks, run_stage, check_stage, replay_stage


def source_scene():
    return copy.deepcopy({'format':'codevideo.vtk-rigscene.v1',
        'bones':[{'name':n,'parent':parent,'pivot_xyz':pivot} for n,(parent,pivot) in RIG.items()],
        'joint_tracks':{n:{'axis':ax,'keys':keys} for n,(ax,keys) in TRACKS.items()}})


def test_rig_scene_has_real_parent_hierarchy_and_many_distinct_joint_actions():
    assert len(RIG)>=12
    assert all(p in RIG for n,(p,_) in RIG.items() if p is not None)
    assert len(TRACKS)>=10
    assert _read_tracks(source_scene())['left_elbow'][0]=='x'


def test_editable_joint_tracks_validate_executable_constraints():
    model=source_scene()
    model['joint_tracks']['head']['keys'][2] = (1.4,31)
    assert _read_tracks(model)['head'][1][2]==(1.4,31.0)
    model['joint_tracks']['head']['keys'][2]=(1.4,987)
    with pytest.raises(ValueError,match='bounded'): _read_tracks(model)


def test_scene_rejects_fake_bones_and_changed_pivots():
    model=source_scene()
    model['bones'][0]['name']='bogus'
    with pytest.raises(ValueError):_read_tracks(model)
    model=source_scene()
    model['bones'][1]['pivot_xyz']=(100,100,100)
    with pytest.raises(ValueError,match='mesh/rig'): _read_tracks(model)

@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='FFmpeg missing')
def test_invalid_demo_settings_prevent_renderer(tmp_path):
    assert run_stage(tmp_path,'short',width=300,height=161)['status']=='BLOCKED'

@pytest.fixture(scope='module')
def real_demo(tmp_path_factory):
    pytest.importorskip('vtk')
    pytest.importorskip('PIL')
    root=tmp_path_factory.mktemp('vtk-live')
    out=run_stage(root,'real',width=320,height=180,fps=12,seconds=1)
    assert out['status']=='TECHNICAL_PASS_VISUAL_PENDING',out
    return root,out


def test_real_render_proves_multiple_nonroot_joints_are_visible(real_demo):
    root,out=real_demo
    receipt=load_json(Path(out['receipt']))
    assert receipt['backend'].startswith('VTK')
    assert receipt['visible_joint_count']>=4
    assert receipt['independent_joint_count']>=4
    assert receipt['root_camera_fixed_during_diagnostics'] is True
    assert receipt['encoded_video']['fully_decoded'] is True
    assert len(receipt['rendered_frame_hashes'])==12
    assert check_stage(root, out['receipt'])['status']=='PASS'


def test_replaying_an_edited_scene_produces_different_real_video(real_demo):
    root,out=real_demo
    model=load_json(Path(out['rig_scene']))
    model['joint_tracks']['head']['keys'][1][1] = 55
    temp=root/'replay_scene.json';save_json(temp,model)
    replay=replay_stage(root,str(temp),'take2',width=320,height=180,fps=12,seconds=1)
    assert replay['status']=='TECHNICAL_PASS_VISUAL_PENDING',replay
    p1=load_json(Path(out['receipt']))
    p2=load_json(Path(replay['receipt']))
    assert p1['mp4_sha256']!=p2['mp4_sha256']
    assert check_stage(root,replay['receipt'])['status']=='PASS'


def test_mutated_encoded_mp4_is_detected(real_demo):
    root,out=real_demo
    source=Path(out['video'])
    original=source.read_bytes()
    try:
        source.write_bytes(original+b'forged')
        assert check_stage(root,out['receipt'])['status']=='FAIL'
    finally:source.write_bytes(original)


def test_mutated_diagnostic_png_is_detected(real_demo):
    root,out=real_demo
    frame=Path(out['diagnostics'])/'head.png'
    original=frame.read_bytes()
    try:
        frame.write_bytes(original+b'tamper')
        assert check_stage(root,out['receipt'])['status']=='FAIL'
    finally:frame.write_bytes(original)


def test_static_joint_tracks_block_before_creating_render_outputs(tmp_path):
    scene=source_scene()
    for track in scene['joint_tracks'].values():
        track['keys']=[[0,0],[3,0],[6,0]]
    res=run_stage(tmp_path,'fake_static',width=320,height=180,fps=12,seconds=1,scene_data=scene)
    assert res['status']=='BLOCKED' and res['gate']=='ARTICULATION'
    assert not (tmp_path/'projects'/'fake_static').exists()
