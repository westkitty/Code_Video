"""Cold-start contract, non-destructive safety and real CLI routing for new film jobs."""
import copy
import json
from pathlib import Path
import pytest
from codevideo import production_job as p
from codevideo.common import GateError
from codevideo.cli import main as cli_main

EXAMPLE=Path(__file__).resolve().parents[1]/"examples"/"weight_of_light"/"job.json"

@pytest.fixture
def source(tmp_path):
    doc=json.loads(EXAMPLE.read_text())
    (tmp_path/"job.json").write_text(json.dumps(doc))
    return tmp_path,doc

def test_new_job_contract_has_three_complete_motivated_shots(source):
    root,doc=source
    clean=p.normalize(doc)
    assert clean["job_sha256"]==p.normalize(doc)["job_sha256"]
    assert clean["shots"][0]["start"]==1
    assert clean["shots"][-1]["end"]==360
    assert clean["fps"]==30 and clean["width"]==1920
    assert p.preflight(root,"job.json")["status"]=="PASS"
    assert not (root/"jobs").exists()

@pytest.mark.parametrize("mutation",[
    lambda d:d.update(audio={"asset":"unapproved.wav"}),
    lambda d:d.update(subtitles=True),
    lambda d:d.update(anatomy="flyer"),
    lambda d:d.update(action="an_unimplemented_story"),
    lambda d:d.update(canon="CANON_VERIFIED"),
    lambda d:d.update(fps=29),
    lambda d:d.update(width=1921),
    lambda d:d.update(duration_frames=30),
    lambda d:d["shots"][1].update(start=121+2),
    lambda d:d["shots"][2].update(end=359),
    lambda d:d["shots"][0].update(camera="Invalid_Camera"),
    lambda d:d["shots"][0].update(performance=" "),
    lambda d:d.update(job_id="../../outside")
])
def test_invalid_audio_canon_timing_camera_or_story_fails_closed(source,mutation):
    root,doc=source
    bad=copy.deepcopy(doc)
    mutation(bad)
    with pytest.raises(GateError):
        p.normalize(bad)

def test_no_blender_does_not_create_any_job_artifacts(source,monkeypatch):
    root,doc=source
    monkeypatch.setattr(p,"renderer",lambda:None)
    result=p.build(root,"job.json")
    assert result["status"]=="BLOCKED" and result["gate"]=="BLENDER_RUNTIME"
    assert not (root/"jobs").exists()

def test_job_ids_never_overwrite_preexisting_documents(source):
    root,doc=source
    clean=p.normalize(doc)
    folder=p._ensure_job(root,clean)
    assert folder.is_dir()
    assert p._ensure_job(root,clean)==folder
    altered=dict(clean,title="An incompatible second job")
    with pytest.raises(GateError):
        p._ensure_job(root,altered)
    assert json.loads((folder/"job.normalized.json").read_text())==clean

def test_resuming_missing_scene_cannot_invent_rig_proof(source):
    root,doc=source
    clean=p.normalize(doc)
    out=p._ensure_job(root,clean)
    with pytest.raises(GateError):
        p._frames_check(out,clean)
    with pytest.raises(GateError):
        p._frames_check(out,clean,require_complete=True)

def test_new_public_cli_preflight(source,capsys):
    root,doc=source
    rc=cli_main(["--workspace",str(root),"job-preflight","job.json"])
    result=json.loads(capsys.readouterr().out)
    assert rc==0 and result["status"]=="PASS"
    assert result["classification"]=="SUPPORTED_TEMPLATE_PREFLIGHT_NOT_RENDERED"
