"""Source-bound new native Blender film job, deterministic rendering and strict receipts.
Supported current lane: a single noncanonical weighted humanoid, uncover_sprout action.
Do not claim arbitrary-text-to-film, multi-character, canonical or audio support.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from .common import inside, sha256, save_json, load_json, result, GateError

IDENT = re.compile(r"^[a-z][a-z0-9_-]{0,49}$")
FORMAT = "codevideo.job.v1"
CAMERAS = ["CV_Shot_01", "CV_Shot_02", "CV_Shot_03"]

def normalize(doc):
    if not isinstance(doc, dict) or doc.get("format") != FORMAT:
        raise GateError("Expected codevideo.job.v1")
    job_id = doc.get("job_id")
    if not isinstance(job_id, str) or not IDENT.fullmatch(job_id):
        raise GateError("Invalid job_id")
    for key in ("title", "synopsis", "character_name"):
        value = doc.get(key)
        if not isinstance(value, str) or not 2 <= len(value.strip()) <= 500:
            raise GateError("Missing or invalid "+key)
    if doc.get("anatomy") != "humanoid" or doc.get("action") != "uncover_sprout":
        raise GateError("Current production profile supports only humanoid/uncover_sprout")
    if doc.get("canon", "NONCANONICAL") != "NONCANONICAL":
        raise GateError("Current profile accepts only original noncanonical characters")
    if doc.get("subtitles", False) is not False:
        raise GateError("No subtitles in this profile")
    if doc.get("audio") is not None:
        raise GateError("Audio/lip-sync profile is not implemented: original silent film only")
    fps, width, height, count = (doc.get(k) for k in
                                 ("fps","width","height","duration_frames"))
    if type(fps) is not int or fps not in (24,30):
        raise GateError("Only 24 or 30 fps is supported")
    if (type(width) is not int or type(height) is not int or
        width not in (640,960,1280,1920) or height*16 != width*9):
        raise GateError("Supported 16:9 sizes: 640x360, 960x540, 1280x720, 1920x1080")
    if type(count) is not int or count < fps*12 or count > fps*20:
        raise GateError("Duration must be between 12 and 20 seconds")
    shots=doc.get("shots")
    if not isinstance(shots, list) or len(shots)!=3:
        raise GateError("Exactly three production cameras/shots required")
    start=1
    normalized=[]
    for i, shot in enumerate(shots):
        if not isinstance(shot, dict):
            raise GateError("Malformed shot")
        if (shot.get("id") != f"s{i+1:02d}" or
            shot.get("camera") != CAMERAS[i] or
            type(shot.get("start")) is not int or
            type(shot.get("end")) is not int or
            shot["start"]!=start or shot["end"]<start):
            raise GateError("Shot chronology or camera mismatch")
        for key in ("purpose","emotion","performance","continuity"):
            if not isinstance(shot.get(key),str) or not shot[key].strip():
                raise GateError("Missing shot metadata: "+key)
        normalized.append({k:shot[k] for k in
            ("id","camera","start","end","purpose","emotion","performance","continuity")})
        start=shot["end"]+1
    if start!=count+1:
        raise GateError("Shots must cover the full timeline without gaps")
    clean={k:doc[k] for k in
        ("format","job_id","title","synopsis","character_name","anatomy",
         "action","fps","width","height","duration_frames")}
    clean["canon"]="NONCANONICAL"
    clean["subtitles"]=False
    clean["audio"]=None
    clean["shots"]=normalized
    hash_input=json.dumps(clean,sort_keys=True,separators=(",",":")).encode()
    clean["job_sha256"]=hashlib.sha256(hash_input).hexdigest()
    return clean

def read_spec(root, source):
    p=inside(root,source,must_exist=True)
    if not p.is_file() or p.stat().st_size>64000:
        raise GateError("Missing or oversized job contract")
    return normalize(load_json(p))

def preflight(root, source):
    try:
        d=read_spec(root,source)
        return result("PASS", classification="SUPPORTED_TEMPLATE_PREFLIGHT_NOT_RENDERED",
             job_id=d["job_id"],profile=d["action"],anatomy=d["anatomy"],
             frames=d["duration_frames"],fps=d["fps"],
             dimensions=[d["width"],d["height"]],job_sha256=d["job_sha256"],
             unsupported=["arbitrary anatomy","multi-character","canon","audio","lip-sync",
                          "freeform performance generation"])
    except (GateError,ValueError,TypeError,KeyError,OSError) as exc:
        return result("BLOCKED",gate="JOB_CONTRACT",error=str(exc))

def worker():
    return Path(__file__).resolve().parent.parent/"blender"/"production_job.py"

def renderer():
    path=os.environ.get("CODEVIDEO_BLENDER","").strip()
    if path:
        p=Path(path).expanduser()
        return str(p) if p.is_file() and os.access(p,os.X_OK) else None
    return shutil.which("blender") or (
        "/Applications/Blender.app/Contents/MacOS/Blender"
        if Path("/Applications/Blender.app/Contents/MacOS/Blender").is_file() else None)

def _dir(root, doc):
    return inside(root,Path("jobs")/doc["job_id"])

def _ensure_job(root,doc):
    out=_dir(root,doc)
    if out.exists():
        saved=out/"job.normalized.json"
        if not saved.is_file() or load_json(saved)!=doc:
            raise GateError("Existing job ID has different/incomplete source: preserve it and use another ID")
    else:
        out.mkdir(parents=True,exist_ok=False)
        save_json(out/"job.normalized.json",doc)
    return out

def _run(argv,log,timeout):
    with log.open("a",encoding="utf8") as fh:
        fh.write("\n$ "+ " ".join(str(a) for a in argv)+"\n")
        fh.flush()
        start=time.monotonic()
        try:
            completed=subprocess.run(argv,stdout=fh,stderr=subprocess.STDOUT,
                                     timeout=timeout,check=False)
            code=completed.returncode
        except (OSError,subprocess.TimeoutExpired) as exc:
            fh.write("WORKER_EXCEPTION "+str(exc)+"\n")
            code=124
        return code,round(time.monotonic()-start,3)

def _call_blender(binary,job,out,mode,first=None,last=None,timeout=1800):
    script=worker()
    if mode=="build":
        argv=[binary,"--background","--factory-startup","--disable-autoexec","--python-exit-code","1",
              "--python",str(script),"--","--mode","build",
              "--job",str(out/"job.normalized.json"),"--out",str(out)]
    else:
        argv=[binary,"--background",str(out/"scene.blend"),
              "--disable-autoexec","--python-exit-code","1","--python",str(script),
              "--","--mode","render",
              "--job",str(out/"job.normalized.json"),"--out",str(out),
              "--first",str(first),"--last",str(last)]
    return _run(argv,out/"production.log",timeout)

def _check_source(out,doc):
    blend=out/"scene.blend"
    proof=out/"rig_manifest.json"
    if not blend.is_file() or not proof.is_file():
        raise GateError("No Blender rig proof or scene")
    data=load_json(proof)
    if (blend.stat().st_size<1000 or (lambda head: head != b"BLENDER" and head[:4] != bytes.fromhex("28b52ffd"))(blend.open("rb").read(7)) or
        sha256(blend)!=data.get("scene_sha256")):
        raise GateError("Native source scene/proof mismatch")
    for key, path in (("worker_sha256",worker()),("helper_sha256",worker().parent/"standalone_native_actor.py")):
        if data.get(key) and data[key]!=sha256(path):
            raise GateError("Source worker differs from rig proof: "+key)
    if (len(data.get("animated_nonroot_deltas",{}))<4 or
        len(data.get("deforming_mesh_deltas_m",{}))<4 or
        min(data["deforming_mesh_deltas_m"].values())<.015):
        raise GateError("Actual armature/weighted mesh proof is inadequate")
    for name,digest in data.get("diagnostic_hashes",{}).items():
        p=out/"diagnostics"/name
        if p.name!=name or not p.is_file() or sha256(p)!=digest:
            raise GateError("Invalid pose diagnostic: "+name)
    if len(data.get("diagnostic_hashes",{}))<4:
        raise GateError("Missing render-backed diagnostic frames")
    return data

def build(root, source):
    p=preflight(root,source)
    if p["status"]!="PASS":return p
    doc=read_spec(root,source)
    binary=renderer()
    if not binary:return result("BLOCKED",gate="BLENDER_RUNTIME")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        return result("BLOCKED",gate="FFMPEG_RUNTIME")
    try:
        out=_ensure_job(root,doc)
        if (out/"rig_manifest.json").exists():
            proof=_check_source(out,doc)
            return result("PASS",stage="RIG_PROVED",reused=True,
                          scene=str(out/"scene.blend"),proof=str(out/"rig_manifest.json"),
                          nonroot_joints=len(proof["animated_nonroot_deltas"]))
        if (out/"scene.blend").exists():
            return result("BLOCKED",gate="INCOMPLETE_BUILD",detail="Preserve partial scene; new job ID required")
        code,seconds=_call_blender(binary,doc,out,"build",timeout=1200)
        if code:
            return result("PARTIAL",gate="BLENDER_BUILD",exit_code=code,
                          log=str(out/"production.log"),elapsed_s=seconds)
        proof=_check_source(out,doc)
        return result("PASS",stage="RIG_PROVED",elapsed_s=seconds,
                      scene=str(out/"scene.blend"),proof=str(out/"rig_manifest.json"),
                      joints=len(proof["animated_nonroot_deltas"]),
                      deforming_meshes=len(proof["deforming_mesh_deltas_m"]))
    except (OSError,ValueError,KeyError,TypeError,GateError) as exc:
        return result("BLOCKED",gate="BUILD_PROOF",error=str(exc))

def _frames_check(out,doc,require_complete=False):
    _check_source(out,doc)
    p=out/"frames"/"frame_manifest.json"
    if not p.is_file():
        if require_complete:raise GateError("No rendered frames")
        return {}
    m=load_json(p)
    if (m.get("scene_sha256")!=sha256(out/"scene.blend") or
        m.get("job_sha256")!=doc["job_sha256"] or
        m.get("fps")!=doc["fps"] or
        (m.get("width"),m.get("height"))!=(doc["width"],doc["height"])):
        raise GateError("Frame manifest source/output mismatch")
    hashes=m.get("frames")
    if not isinstance(hashes,dict):raise GateError("Invalid frame manifest")
    expected={f"frame_{i:06d}.png" for i in range(1,doc["duration_frames"]+1)}
    if not set(hashes).issubset(expected):raise GateError("Unexpected frame name in ledger")
    if require_complete and set(hashes)!=expected:
        raise GateError("Incomplete frame sequence")
    for name,sha in hashes.items():
        p=out/"frames"/name
        if not p.is_file() or sha256(p)!=sha:
            raise GateError("Missing/mutated frame: "+name)
    return hashes

def render(root,source,max_frames=48,max_seconds=1800):
    spec=read_spec(root,source)
    b=build(root,source)
    if b["status"]!="PASS":return b
    out=_dir(root,spec)
    try:
        recorded=_frames_check(out,spec)
        todo=[i for i in range(1,spec["duration_frames"]+1)
              if f"frame_{i:06d}.png" not in recorded]
        if not todo:
            return result("PASS",stage="FRAMES_COMPLETE",frames=len(recorded),
                          job=str(out),reused=True)
        # Contiguous bounded batch for resumable progress, with scene and job binding.
        first=todo[0]
        last=first
        while last+1 in todo and last-first+1 < min(48,max_frames):
            last+=1
        code,elapsed=_call_blender(renderer(),spec,out,"render",first,last,
                                    timeout=max_seconds)
        if code:
            return result("PARTIAL",gate="FRAME_RENDER",range=[first,last],
                          elapsed_s=elapsed,log=str(out/"production.log"))
        updated=_frames_check(out,spec)
        return result("PASS",stage="FRAME_BATCH",range=[first,last],
                      frames_complete=len(updated),total=spec["duration_frames"],
                      elapsed_s=elapsed,job=str(out))
    except (OSError,ValueError,KeyError,GateError) as exc:
        return result("BLOCKED",gate="FRAME_VALIDATION",error=str(exc))

def _ffprobe(video):
    proc=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=codec_name,pix_fmt,width,height,nb_frames,r_frame_rate",
        "-show_entries","format=duration",
        "-of","json",str(video)],capture_output=True,text=True,timeout=40)
    if proc.returncode:raise GateError("ffprobe rejected encoded MP4")
    obj=json.loads(proc.stdout)
    return obj["streams"][0],float(obj["format"]["duration"])

def encode(root,source):
    doc=read_spec(root,source)
    out=_dir(root,doc)
    try:
        hashes=_frames_check(out,doc,require_complete=True)
        video=out/"film.mp4"
        if video.exists():
            receipt=out/"film_receipt.json"
            if receipt.exists() and load_json(receipt).get("mp4_sha256")==sha256(video):
                return result("TECHNICAL_PASS_VISUAL_PENDING",video=str(video),reused=True)
            raise GateError("Unverified previous MP4 exists; refusing overwrite")
        temp=out/"film.encoding.mp4"
        if temp.exists():
            raise GateError("Leftover encoder output must be inspected before retry")
        cmd=["ffmpeg","-hide_banner","-nostdin","-v","error","-xerror",
             "-framerate",str(doc["fps"]),"-start_number","1",
             "-i",str(out/"frames"/"frame_%06d.png"),
             "-frames:v",str(doc["duration_frames"]),
             "-an","-c:v","libx264","-crf","18","-preset","medium",
             "-pix_fmt","yuv420p","-movflags","+faststart",str(temp)]
        code,seconds=_run(cmd,out/"production.log",timeout=900)
        if code or not temp.is_file():
            return result("PARTIAL",gate="ENCODING",log=str(out/"production.log"))
        stream,duration=_ffprobe(temp)
        fps_parts=stream["r_frame_rate"].split("/")
        fps=float(fps_parts[0])/float(fps_parts[1])
        if (stream.get("codec_name")!="h264" or stream.get("pix_fmt")!="yuv420p" or
            stream.get("width")!=doc["width"] or stream.get("height")!=doc["height"] or
            int(stream.get("nb_frames","-1"))!=doc["duration_frames"] or
            abs(fps-doc["fps"])>.0001 or
            abs(duration-doc["duration_frames"]/doc["fps"])>.06):
            return result("PARTIAL",gate="ENCODE_METADATA",metadata=stream,duration=duration)
        verify=["ffmpeg","-hide_banner","-nostdin","-v","error","-xerror",
                "-i",str(temp),"-f","null","-"]
        decode,dt=_run(verify,out/"production.log",timeout=900)
        if decode:return result("PARTIAL",gate="FULL_DECODE",log=str(out/"production.log"))
        os.replace(temp,video)
        markers=[]
        for shot in doc["shots"]:
            for f in (shot["start"],(shot["start"]+shot["end"])//2,shot["end"]):
                name=f"{shot['id']}_{f:06d}.jpg"
                t=(f-1)/doc["fps"]
                dest=out/"review"
                dest.mkdir(exist_ok=True)
                rc,secs=_run(["ffmpeg","-hide_banner","-nostdin","-v","error",
                             "-ss",str(t),"-i",str(video),
                             "-frames:v","1","-q:v","3",str(dest/name)],
                            out/"production.log",timeout=60)
                if rc or not (dest/name).is_file():
                    raise GateError("Encoded shot review extraction failed at frame "+str(f))
                markers.append({"shot":shot["id"],"frame":f,
                                "image":"review/"+name,"sha256":sha256(dest/name)})
        receipt={"format":"codevideo.new-film-receipt.v1","job_id":doc["job_id"],
                 "job_sha256":doc["job_sha256"],
                 "scene_sha256":sha256(out/"scene.blend"),
                 "rig_proof_sha256":sha256(out/"rig_manifest.json"),
                 "frames":len(hashes),"frame_manifest_sha256":sha256(out/"frames"/"frame_manifest.json"),
                 "mp4_sha256":sha256(video),"duration_s":duration,"fps":doc["fps"],
                 "resolution":[doc["width"],doc["height"]],
                 "full_decode":True,"technical_status":"PASS",
                 "visual_review":"PENDING","artistic_status":"NOT_CERTIFIED",
                 "review_images":markers,"subtitles":False,"audio":None}
        save_json(out/"film_receipt.json",receipt)
        return result("TECHNICAL_PASS_VISUAL_PENDING",video=str(video),
             receipt=str(out/"film_receipt.json"),scene=str(out/"scene.blend"),
             frames=len(hashes),decode="PASS",review_frames=len(markers),
             encoding_seconds=seconds,decode_seconds=dt)
    except (OSError,ValueError,KeyError,TypeError,GateError,subprocess.TimeoutExpired) as exc:
        return result("BLOCKED",gate="FINAL_ENCODE_PROOF",error=str(exc))

def produce(root,source,max_render_seconds=7200):
    start=time.monotonic()
    b=build(root,source)
    if b["status"]!="PASS":return b
    doc=read_spec(root,source)
    out=_dir(root,doc)
    # Benchmark actual final-resolution frames at all three camera angles.
    for shot in doc["shots"]:
        frame_id=shot["start"]
        if f"frame_{frame_id:06d}.png" in _frames_check(out,doc):
            continue
        code,elapsed=_call_blender(renderer(),doc,out,"render",frame_id,frame_id,timeout=300)
        if code:return result("PARTIAL",gate="SHOT_BENCHMARK",shot=shot["id"],
                               log=str(out/"production.log"))
        bench=out/"benchmark.json"
        metrics=load_json(bench) if bench.exists() else {"samples":[]}
        metrics["samples"].append({"shot":shot["id"],"frame":frame_id,"wall_s":elapsed})
        save_json(bench,metrics)
    samples=load_json(out/"benchmark.json").get("samples",[])
    # Upper bound using process startup each frame; overestimates batch performance.
    est=max(s["wall_s"] for s in samples)*doc["duration_frames"]
    if est>max_render_seconds:
        return result("PARTIAL",gate="RENDER_BUDGET",estimated_upper_s=round(est),
            budget_s=max_render_seconds,benchmarks=samples,job=str(out))
    while True:
        done=_frames_check(out,doc)
        if len(done)==doc["duration_frames"]:break
        if time.monotonic()-start>max_render_seconds:
            return result("PARTIAL",gate="TIME_BUDGET",frames=len(done),
                           total=doc["duration_frames"],job=str(out))
        r=render(root,source,max_frames=48,max_seconds=1800)
        if r["status"]!="PASS":return r
    return encode(root,source)
