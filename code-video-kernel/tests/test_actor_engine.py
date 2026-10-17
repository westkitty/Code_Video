import copy
import numpy as np
import pytest
from codevideo.actor_engine import skinned_tube, weighted_lbs, solve_ik_xz, deformation_measure
from codevideo.golden_reach import default_spec, validate_spec, evaluate, SHOT_GRAPH,render,check


def test_normalized_skin_and_actual_deforming_mesh():
    a=np.array([0.,0,2.]);b=np.array([0.,0,1.]);c=np.array([0.,0,0.])
    v,w,f=skinned_tube(a,b,c,sections=31,sides=18)
    assert len(f)>900
    assert (w>=0).all() and np.allclose(w.sum(axis=1),1)
    # Sideways right bend at the elbow, bone lengths stay fixed.
    a1=np.array([0.,0,2.]);b1=np.array([.6,0,1.2]);c1=np.array([1.5,0,.7641101])
    # Precise on-circle target to respect both 1.0 lengths.
    b1=np.array([.6,0,1.2]); c1=b1+np.array([.8,0,-.6])
    posed=weighted_lbs(v,w,[(a,b,a1,b1),(b,c,b1,c1)])
    assert deformation_measure(v,posed)>.2
    assert np.isfinite(posed).all()
    with pytest.raises(ValueError,match='normalized'):
        weighted_lbs(v,w*.8,[(a,b,a1,b1),(b,c,b1,c1)])


def test_ik_rejects_unreachable_and_preserves_bone_length():
    shoulder=np.array([-.2,0,1.9]);target=np.array([.65,0,1.55])
    elbow,hand=solve_ik_xz(shoulder,target,.72,.69,bend=1)
    assert np.linalg.norm((elbow-shoulder)[[0,2]])==pytest.approx(.72)
    assert np.linalg.norm((hand-elbow)[[0,2]])==pytest.approx(.69)
    with pytest.raises(ValueError,match='unreachable'):solve_ik_xz(shoulder,np.array([5.,0,1.9]),.72,.69)


def test_all_288_frames_contact_and_world_locked_feet():
    spec=default_spec();assert validate_spec(spec)
    frames=[evaluate(i/24,spec) for i in range(288)]
    assert len(SHOT_GRAPH)==3 and sum(shot['frame_end']-shot['frame_start']+1 for shot in SHOT_GRAPH)==288
    for part in ('left','right'):
        positions=[p[f'{part}_foot'] for p in frames]
        assert max(np.linalg.norm(p-positions[0]) for p in positions)<1e-8
    assert frames[0]['orb_owner']=='world'
    assert frames[224]['orb_owner']=='right_hand'
    assert max(float(p['contact_error'] or 0) for p in frames if p['orb_owner']=='right_hand')<1e-6
    for p in frames:
        for bone in p['bones'].values():
            assert np.isfinite(bone[0]).all() and np.isfinite(bone[1]).all()
    assert np.linalg.norm(frames[0]['right_elbow']-frames[110]['right_elbow'])>.15


def test_edited_timeline_can_replay_but_corrupt_inputs_are_rejected():
    source=default_spec();source['tracks']['head_turn'][2][1]=26
    assert validate_spec(source)
    broken=copy.deepcopy(source);broken['tracks']['right_hand_x'][3][0]=-4
    with pytest.raises(ValueError):validate_spec(broken)
    broken=copy.deepcopy(source);broken['constraints']['no_subtitles']=False
    with pytest.raises(ValueError):validate_spec(broken)
    broken=copy.deepcopy(source);broken['tracks']['left_hand_x'][3][1]=-40
    # Unreachable poses are rejected before creating a project.
    from tempfile import TemporaryDirectory
    from pathlib import Path
    with TemporaryDirectory() as tmp:
        from codevideo.common import save_json
        p=Path(tmp)/'invalid.json';save_json(p,broken)
        r=render(Path(tmp),'invalid',spec_path=str(p),frames_limit=1)
        assert r['status']=='BLOCKED' and not (Path(tmp)/'projects'/'invalid').exists()


def test_partial_receipt_cannot_be_promoted_to_film(tmp_path):
    pytest.importorskip('vtk')
    import shutil
    if not shutil.which('ffmpeg'):pytest.skip('FFmpeg missing')
    r=render(tmp_path,'short',width=320,height=180,frames_limit=1)
    assert r['status']=='PARTIAL'
    assert check(tmp_path,r['receipt'])['status']=='FAIL'
