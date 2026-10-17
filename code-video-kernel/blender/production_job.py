"""New-job native Blender producer. Actual bpy armature, weighted mesh and pose proof.
Only supports the explicitly declared uncover_sprout humanoid template. No arbitrary
prompt-to-film claim, no network calls, no legacy Reach scene dependency.
"""
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from standalone_native_actor import bone, mat, uv_ellipsoid, skin_tube, rot_keys, loc_keys, look_at

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def atomic_json(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf8")
    os.replace(tmp, path)

def frame(job, base):
    return max(1, min(job["duration_frames"], round(base * job["duration_frames"] / 360)))

def settings(scene, job, width=None, height=None):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width or job["width"]
    scene.render.resolution_y = height or job["height"]
    scene.render.resolution_percentage = 100
    scene.render.fps = job["fps"]
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True

def keys_rot(pb, job, keyed):
    rot_keys(pb, [(frame(job, f), xyz) for f, xyz in keyed])

def keys_loc(ob, job, keyed):
    loc_keys(ob, [(frame(job, f), xyz) for f, xyz in keyed])

def build(job, out):
    if (out / "scene.blend").exists():
        raise RuntimeError("Refusing to overwrite an existing scene")
    if job["anatomy"] != "humanoid" or job["action"] != "uncover_sprout":
        raise RuntimeError("Unsupported anatomy or action template")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, job["duration_frames"]
    settings(s, job)
    s.world = bpy.data.worlds.new('Film World')
    s.world.color = (.012, .015, .024)
    red = mat("Oxide lacquer", (.40,.038,.065), .28, .28)
    frame_mat = mat("Joint graphite", (.030,.042,.060), .4, .29)
    cream = mat("Ceramic mask", (.72,.77,.70), .12, .28)
    brass = mat("Brushed brass", (.72,.38,.16), .50, .27)
    cyan = mat("Beacon azure", (.012,.66,.80), .12, .25, 2.0)
    green = mat("Sprout", (.13,.55,.25), .08, .47)
    soil = mat("Stage graphite", (.023,.030,.043), .15, .57)
    cube_mat = mat("Weight block", (.27,.28,.34), .50, .38)
    armature = bpy.data.armatures.new("Puppet_Armature")
    rig = bpy.data.objects.new("Puppet_Rig", armature)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    skeleton = {
       "root":((0,0,.10),(0,0,1.04),None),
       "pelvis":((0,0,1.04),(0,0,1.31),"root"),
       "spine":((0,0,1.31),(0,0,1.78),"pelvis"),
       "chest":((0,0,1.78),(0,0,1.97),"spine"),
       "neck":((0,0,1.97),(0,0,2.15),"chest"),
       "head":((0,0,2.15),(0,0,2.56),"neck"),
       "jaw":((0,-.20,2.25),(0,-.34,2.21),"head"),
       "L_upper":((-.38,0,1.87),(-.79,0,1.68),"chest"),
       "L_fore":((-.79,0,1.68),(-1.12,0,1.30),"L_upper"),
       "L_hand":((-1.12,0,1.30),(-1.22,0,1.16),"L_fore"),
       "R_upper":((.38,0,1.87),(.79,0,1.68),"chest"),
       "R_fore":((.79,0,1.68),(1.12,0,1.30),"R_upper"),
       "R_hand":((1.12,0,1.30),(1.22,0,1.16),"R_fore"),
       "L_thigh":((-.25,0,1.05),(-.28,0,.61),"pelvis"),
       "L_shin":((-.28,0,.61),(-.31,0,.20),"L_thigh"),
       "L_foot":((-.31,0,.20),(-.31,-.19,.11),"L_shin"),
       "R_thigh":((.25,0,1.05),(.28,0,.61),"pelvis"),
       "R_shin":((.28,0,.61),(.31,0,.20),"R_thigh"),
       "R_foot":((.31,0,.20),(.31,-.19,.11),"R_shin")
    }
    for name, (a,b,parent) in skeleton.items():
        bone(armature,name,a,b,parent)
    bpy.ops.object.mode_set(mode="OBJECT")
    uv_ellipsoid("Carapace", (0,0,1.60), (.48,.32,.51), red,rig,"spine",32)
    uv_ellipsoid("Heart Plate",(0,-.29,1.67),(.28,.07,.32),frame_mat,rig,"chest")
    uv_ellipsoid("Heart Glow",(0,-.364,1.72),(.10,.045,.12),cyan,rig,"chest")
    uv_ellipsoid("Face Shell",(0,0,2.43),(.33,.30,.36),cream,rig,"head",32)
    uv_ellipsoid("Dark Face",(0,-.25,2.42),(.29,.10,.15),frame_mat,rig,"head")
    for x in (-.125,.125):
        uv_ellipsoid("Eye", (x,-.335,2.44),(.048,.033,.071),cyan,rig,"head")
    uv_ellipsoid("Jaw", (0,-.30,2.24),(.19,.08,.073),brass,rig,"jaw")
    uv_ellipsoid("Pelvis", (0,0,1.10),(.33,.24,.24),frame_mat,rig,"pelvis")
    for side,sgn in (("L",-1),("R",1)):
        uv_ellipsoid(side+"_Palm",(sgn*1.17,0,1.20),(.14,.12,.16),brass,rig,side+"_hand")
        uv_ellipsoid(side+"_Boot",(sgn*.31,-.18,.12),(.18,.32,.12),cream,rig,side+"_foot")
        skin_tube(side+"_Arm",skeleton[side+"_upper"][0],skeleton[side+"_upper"][1],
                  skeleton[side+"_fore"][1],rig,side+"_upper",side+"_fore",red,radius=.145)
        skin_tube(side+"_Leg",skeleton[side+"_thigh"][0],skeleton[side+"_thigh"][1],
                  skeleton[side+"_shin"][1],rig,side+"_thigh",side+"_shin",
                  frame_mat,radius=.16)
    # IK anchors: fixed feet, hand-on-block contact. Root stays stationary.
    targets = {}
    for name, xyz in (("R_Hand_Target",(1.04,-.5,1.2)),
                      ("R_Pole",(1,-1.6,1.5)),
                      ("L_Foot",(-.31,-.18,.12)),("R_Foot",(.31,-.18,.12)),
                      ("L_Pole",(-1,-1,.5)),("RF_Pole",(1,-1,.5))):
        bpy.ops.object.empty_add(type="SPHERE",location=xyz)
        ob=bpy.context.object
        ob.name="IK_"+name
        ob.empty_display_size=.07
        targets[name]=ob
    for side, pole in (("L","L_Pole"),("R","RF_Pole")):
        c=rig.pose.bones[side+"_shin"].constraints.new("IK")
        c.target=targets[side+"_Foot"]
        c.chain_count=2
        c.pole_target=targets[pole]
    arm_ik=rig.pose.bones["R_fore"].constraints.new("IK")
    arm_ik.target=targets["R_Hand_Target"]
    arm_ik.chain_count=2
    arm_ik.pole_target=targets["R_Pole"]
    keys_rot(rig.pose.bones["spine"],job,[
        (1,(0,0,0)),(72,(0,-.04,-.10)),(145,(0,.19,-.13)),
        (215,(0,.29,-.03)),(271,(0,.01,.07)),(332,(.30,.01,0)),(360,(.30,0,0))])
    keys_rot(rig.pose.bones["neck"],job,[
        (1,(0,0,-.10)),(70,(0,0,.35)),(160,(0,0,.20)),
        (252,(0,0,.48)),(320,(0,0,.03)),(360,(0,0,.12))])
    keys_rot(rig.pose.bones["head"],job,[
        (1,(.04,-.09,0)),(75,(-.16,.04,-.27)),(155,(.17,.04,.06)),
        (241,(-.11,.06,.18)),(312,(-.18,-.08,-.1)),(340,(.21,-.04,0)),(360,(.18,0,0))])
    keys_rot(rig.pose.bones["jaw"],job,[
        (1,(0,0,0)),(128,(.13,0,0)),(175,(0,0,0)),
        (287,(.21,0,0)),(340,(0,0,0)),(360,(0,0,0))])
    keys_rot(rig.pose.bones["L_upper"],job,[
        (1,(0,0,0)),(112,(.10,.05,.18)),(183,(.40,.24,.12)),
        (255,(.30,.20,-.12)),(324,(0,.04,-.04)),(360,(0,0,0))])
    keys_rot(rig.pose.bones["L_fore"],job,[
        (1,(0,0,0)),(135,(-.20,.14,.03)),(202,(-.36,.21,.12)),
        (272,(-.18,.12,0)),(360,(0,0,0))])
    keys_rot(rig.pose.bones["pelvis"],job,[
        (1,(0,0,0)),(130,(0,.04,.04)),(220,(0,.09,-.06)),
        (300,(0,-.04,0)),(360,(0,0,0))])
    keys_loc(targets["R_Hand_Target"],job,[
        (1,(.96,-.3,1.28)),(84,(.98,-.37,1.27)),
        (132,(.98,-.50,1.02)),(176,(.98,-.50,1.02)),
        (200,(1.03,-.50,1.02)),(220,(1.08,-.50,1.02)),
        (235,(1.15,-.50,1.02)),(260,(1.28,-.50,1.02)),
        (272,(1.35,-.50,1.02)),(295,(1.20,-.35,1.23)),
        (360,(.96,-.3,1.28))])
    # The block physically moves only after the right hand makes contact.
    bpy.ops.mesh.primitive_cube_add(size=1,location=(1.36,-.5,.51))
    block=bpy.context.object
    block.name="Block_Obstacle"
    block.scale=(.76,.76,1.02)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    block.data.materials.append(cube_mat)
    edge=block.modifiers.new("Rounded load-bearing edges","BEVEL")
    edge.width=.055
    edge.segments=3
    block.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    keys_loc(block,job,[
        (1,(1.36,-.50,.51)),(176,(1.36,-.50,.51)),
        (200,(1.39,-.50,.51)),(220,(1.43,-.50,.51)),
        (235,(1.44,-.50,.51)),(260,(1.50,-.50,.51)),
        (272,(1.52,-.50,.51)),(360,(1.52,-.50,.51))])
    # A genuinely modeled sprout is revealed as the block slides away.
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.045, depth=.39, location=(.57,.08,.23))
    stem=bpy.context.object
    stem.name="Sprout_Stem"
    stem.data.materials.append(green)
    uv_ellipsoid("Sprout_Leaf_L",(.47,.05,.38),(.16,.08,.04),green)
    uv_ellipsoid("Sprout_Leaf_R",(.67,.07,.43),(.16,.08,.04),green)
    bloom=uv_ellipsoid("Sprout_Light",(.57,.06,.51),(.155,.155,.14),cyan,segments=32)
    for ff,size in ((1,.35),(205,.35),(286,1.3),(360,1.70)):
        bloom.scale=(size,size,size)
        bloom.keyframe_insert(data_path="scale",frame=frame(job,ff))
    bpy.ops.object.light_add(type="AREA",location=(.57,-.10,.95))
    bloom_light=bpy.context.object
    bloom_light.name="Sprout_Reveal_Light"
    bloom_light.data.energy=0
    bloom_light.data.shape="DISK"
    bloom_light.data.size=1.2
    bloom_light.data.color=(.10,.85,1.0)
    look_at(bloom_light,(.57,0,.35))
    for ff,energy in ((1,0),(235,0),(290,140),(360,230)):
        bloom_light.data.energy=energy
        bloom_light.data.keyframe_insert(data_path="energy",frame=frame(job,ff))
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.19))
    ground=bpy.context.object
    ground.name="Stage"
    ground.scale=(12,12,.36)
    ground.data.materials.append(soil)
    # Cast real shadows and use motivated three-quarter/key/rim lighting.
    for name,position,energy,color in [
        ("Warm_Key",(1.6,-3.4,4.6),1050,(1.0,.76,.56)),
        ("Cold_Fill",(-3,-1.2,3.0),610,(.29,.65,1.0)),
        ("Back_Rim",(1,4,4.5),1100,(.29,.68,.91))]:
        bpy.ops.object.light_add(type="AREA",location=position)
        light=bpy.context.object
        light.name=name
        light.data.energy=energy
        light.data.color=color
        light.data.shape="DISK"
        light.data.size=2.5
        look_at(light,(0,0,1.35))
    camera_defs=[
        ("CV_Shot_01",(3.6,-6.7,3.0),(.35,0,1.40),35),
        ("CV_Shot_02",(-1.6,-3.6,1.78),(1.16,-.35,1.03),48),
        ("CV_Shot_03",(2.4,-5.6,2.9),(.53,0,1.32),35)]
    for name, pos, at, lens in camera_defs:
        bpy.ops.object.camera_add(location=pos)
        cam=bpy.context.object
        cam.name=name
        cam.data.lens=lens
        look_at(cam,at)
    s.camera=bpy.data.objects["CV_Shot_01"]
    s["CODEVIDEO_JOB_FORMAT"]="codevideo.job.v1"
    s["CODEVIDEO_JOB_ID"]=job["job_id"]
    s["CODEVIDEO_JOB_HASH"]=job["job_sha256"]
    s["CODEVIDEO_SOURCE"]= "actual native Blender weighted and articulated puppet"
    s.frame_set(1)
    source=out/"scene.blend"
    bpy.context.preferences.filepaths.use_file_compression = False
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    # Root/camera fixed, actual evaluated parent-relative animation and mesh evidence.
    poses=[frame(job,f) for f in (1,112,183,236,310,360)]
    arms=[o for o in bpy.data.objects if o.get("CV_SKIN_CONTINUOUS")]
    if len(arms)!=4:
        raise RuntimeError("Expected exactly four continuous weighted limb meshes")
    bone_samples={}
    mesh_samples={}
    for fr in poses:
        s.frame_set(fr)
        dg=bpy.context.evaluated_depsgraph_get()
        bone_samples[fr]={
            n:tuple(round(q,5) for q in ((p.parent.matrix.inverted() @ p.matrix)
                         if p.parent else p.matrix).to_quaternion())
            for n,p in rig.pose.bones.items()}
        mesh_samples[fr]={}
        for o in arms:
            ev=o.evaluated_get(dg)
            mm=ev.to_mesh()
            mesh_samples[fr][o.name]=[tuple(v.co) for v in mm.vertices]
            ev.to_mesh_clear()
    moving={}
    for n in rig.pose.bones.keys():
        if n=="root": continue
        delta=max(max(abs(a-b) for a,b in zip(bone_samples[poses[0]][n],
                                                bone_samples[fr][n]))
                  for fr in poses[1:])
        if delta>.015: moving[n]=round(delta,5)
    deformation={}
    for o in arms:
        first=mesh_samples[poses[0]][o.name]
        delta=max(math.dist(a,b) for fr in poses[1:]
                  for a,b in zip(first,mesh_samples[fr][o.name]))
        deformation[o.name]=round(delta,5)
    if len(moving)<4 or any(d<.015 for d in deformation.values()):
        raise RuntimeError("Articulation/continuous mesh deformation gate failed")
    # Explicit parent graph, binding and anchors recorded, no unproven claim about visuals.
    manifest={
        "job_id":job["job_id"],"scene_sha256":digest(source),
        "worker_sha256":digest(Path(__file__).resolve()),
        "helper_sha256":digest(Path(__file__).resolve().parent/"standalone_native_actor.py"),
        "root_fixed":True,"diagnostic_camera_fixed":True,
        "bone_parents":{b.name:(b.parent.name if b.parent else None) for b in rig.data.bones},
        "weighted_meshes":{o.name:[v.name for v in o.vertex_groups] for o in arms},
        "animated_nonroot_deltas":moving,"deforming_mesh_deltas_m":deformation,
        "ik_targets":[o.name for o in targets.values()],
        "sample_frames":poses,
        "prop_contact":{"type":"push","frame_begin":frame(job,176),
                        "frame_end":frame(job,260),
                        "block":"Block_Obstacle","target":"IK_R_Hand_Target"},
        "classification":"REAL_BLENDER_RIG_TECHNICAL_PROOF_VISUAL_REVIEW_REQUIRED"}
    # Actual evaluated hand geometry must stay in physical contact during push.
    contact_samples={}
    for sample in (176,200,220,235,260):
        fr=frame(job,sample)
        s.frame_set(fr)
        deps=bpy.context.evaluated_depsgraph_get()
        bounds=[]
        for part in (bpy.data.objects["R_Palm"],block):
            evaluated=part.evaluated_get(deps)
            mesh=evaluated.to_mesh()
            world_pts=[evaluated.matrix_world @ v.co for v in mesh.vertices]
            evaluated.to_mesh_clear()
            bounds.append(([min(p[i] for p in world_pts) for i in range(3)],
                           [max(p[i] for p in world_pts) for i in range(3)]))
        (lo_a,hi_a),(lo_b,hi_b)=bounds
        gaps=[max(0.0,lo_b[i]-hi_a[i],lo_a[i]-hi_b[i]) for i in range(3)]
        gap=math.sqrt(sum(g*g for g in gaps))
        if gap>.03:
            raise RuntimeError(f"Hand/prop contact failed frame {fr}: {gap:.4f}m")
        contact_samples[str(fr)]={"geometry_bbox_clearance_m":round(gap,5),
             "method":"evaluated skinned palm/obstacle world bounding volumes"}
    manifest["prop_contact"]["measured_samples"]=contact_samples
    diagnostics=out/"diagnostics"
    diagnostics.mkdir(exist_ok=False)
    settings(s,job,512,288)
    for fr in (poses[0],poses[2],poses[3],poses[-1]):
        s.frame_set(fr)
        s.camera=bpy.data.objects["CV_Shot_01"]
        s.render.filepath=str(diagnostics/f"pose_{fr:05d}.png")
        bpy.ops.render.render(write_still=True)
    # Per-shot entrance/mid/exit preflight exposes framing defects before full-HD rendering.
    for shot in job["shots"]:
        for fr in sorted({shot["start"],(shot["start"]+shot["end"])//2,shot["end"]}):
            s.frame_set(fr)
            s.camera=bpy.data.objects[shot["camera"]]
            s.render.filepath=str(diagnostics/f"shot_{shot['id']}_{fr:05d}.png")
            bpy.ops.render.render(write_still=True)
    manifest["diagnostic_hashes"]={p.name:digest(p) for p in sorted(diagnostics.glob("*.png"))}
    atomic_json(out/"rig_manifest.json",manifest)
    print("CODEVIDEO_BUILD_PASS="+str(out/"rig_manifest.json"),flush=True)

def render(job, out, first, last):
    if last<first or last-first>47 or first<1 or last>job["duration_frames"]:
        raise RuntimeError("Unsafe render range")
    source=out/"scene.blend"
    manifest=out/"rig_manifest.json"
    if not source.exists() or not manifest.exists():
        raise RuntimeError("No rig-tested source scene")
    state=json.loads(manifest.read_text())
    if digest(source)!=state["scene_sha256"]:
        raise RuntimeError("Native scene changed after rig proof")
    if state.get("worker_sha256") and digest(Path(__file__).resolve())!=state["worker_sha256"]:
        raise RuntimeError("Blender worker source changed after rig proof")
    if state.get("helper_sha256") and digest(Path(__file__).resolve().parent/"standalone_native_actor.py")!=state["helper_sha256"]:
        raise RuntimeError("Rig helper source changed after proof")
    scene=bpy.context.scene
    if scene.get("CODEVIDEO_JOB_HASH")!=job["job_sha256"]:
        raise RuntimeError("Scene is not bound to this job contract")
    settings(scene,job)
    output=out/"frames"
    output.mkdir(exist_ok=True)
    receipt_path=output/"frame_manifest.json"
    base={"scene_sha256":state["scene_sha256"],"job_sha256":job["job_sha256"],
          "width":job["width"],"height":job["height"],"fps":job["fps"],"frames":{}}
    if receipt_path.exists():
        saved=json.loads(receipt_path.read_text())
        for k in ("scene_sha256","job_sha256","width","height","fps"):
            if saved.get(k)!=base[k]:
                raise RuntimeError("Incompatible resumed frame ledger: "+k)
        base=saved
    for fr in range(first,last+1):
        name=f"frame_{fr:06d}.png"
        fpath=output/name
        if name in base["frames"]:
            if not fpath.is_file() or digest(fpath)!=base["frames"][name]:
                raise RuntimeError("Cached rendered frame was changed: "+name)
            continue
        if fpath.exists():
            raise RuntimeError("Unverified existing frame, refusing overwrite: "+name)
        shot=next((sh for sh in job["shots"] if sh["start"]<=fr<=sh["end"]),None)
        if shot is None:
            raise RuntimeError("Shot graph failed to cover frame "+str(fr))
        camera=bpy.data.objects.get(shot["camera"])
        if camera is None or camera.type!="CAMERA":
            raise RuntimeError("Invalid shot camera")
        scene.camera=camera
        scene.frame_set(fr)
        scene.render.filepath=str(fpath)
        t0=time.monotonic()
        bpy.ops.render.render(write_still=True)
        if not fpath.is_file() or fpath.stat().st_size<500:
            raise RuntimeError("Rendered frame absent or malformed")
        base["frames"][name]=digest(fpath)
        atomic_json(receipt_path,base)
        print(f"CODEVIDEO_RENDERED {fr} {time.monotonic()-t0:.2f}",flush=True)
    print("CODEVIDEO_BATCH_PASS="+str(receipt_path),flush=True)

def main():
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=["build","render"])
    p.add_argument("--job",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--first",type=int)
    p.add_argument("--last",type=int)
    opts=p.parse_args(a)
    job=json.loads(Path(opts.job).read_text(encoding="utf8"))
    out=Path(opts.out).resolve()
    if not out.is_dir():
        raise RuntimeError("Job output directory must exist")
    if job.get("format")!="codevideo.job.v1":
        raise RuntimeError("Job schema is not codevideo.job.v1")
    if opts.mode=="build":
        build(job,out)
    else:
        if opts.first is None or opts.last is None:
            raise RuntimeError("Frame range is mandatory")
        render(job,out,opts.first,opts.last)

if __name__=="__main__":
    main()
