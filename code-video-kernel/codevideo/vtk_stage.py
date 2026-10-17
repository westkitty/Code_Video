"""Optional true 3D segmented-puppet stage: VTK joint assemblies, EGL frame capture, MP4.

This is an executable smoke stage, not a Blender substitute for organic skinning,
not a user film, and never evidence of canonical identity or human visual QA.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import time
from pathlib import Path

from .common import inside, load_json, save_json, sha256, slug, result
from .rig_proof import attest, authentic
from .verify_mp4 import verify_mp4

FORMAT = "codevideo.vtk-stage-proof.v1"

# Every element is a real VTK assembly with a parent transform and volumetric geometry.
# The root is fixed during diagnostic renders; children rotate in local coordinates.
RIG = {
    'root': (None, (0.0, 0.0, 0.0)),
    'pelvis': ('root', (0.0, 0.0, 1.77)),
    'torso': ('pelvis', (0.0, 0.0, 0.14)),
    'neck': ('torso', (0.0, 0.0, 1.03)),
    'head': ('neck', (0.0, 0.0, 0.19)),
    'jaw': ('head', (0.0, -0.30, 0.08)),
    'left_shoulder': ('torso', (-0.67, 0.0, 0.82)),
    'left_elbow': ('left_shoulder', (0.0, 0.0, -0.63)),
    'right_shoulder': ('torso', (0.67, 0.0, 0.82)),
    'right_elbow': ('right_shoulder', (0.0, 0.0, -0.63)),
    'left_hip': ('pelvis', (-0.34, 0.0, -0.18)),
    'left_knee': ('left_hip', (0.0, 0.0, -0.72)),
    'right_hip': ('pelvis', (0.34, 0.0, -0.18)),
    'right_knee': ('right_hip', (0.0, 0.0, -0.72)),
    'left_ear': ('head', (-0.26, 0.0, 0.52)),
    'right_ear': ('head', (0.26, 0.0, 0.52)),
}
# Track values in degrees. Independent authored performance beats; no generic sine-wave joints.
TRACKS = {
    'torso': ('x', [(0, 0),(0.75, -8),(1.4, -3),(2.2, 11),(3.05, 7),(4.4, -9),(5.2, 3),(6.0, 0)]),
    'neck': ('z', [(0, 0),(.7, 0),(1.5, 16),(2.6, 0),(3.1, -12),(4.8, 8),(6.0, 0)]),
    'head': ('y', [(0, 0),(.5, -11),(1.4, 14),(2.0, 5),(2.65, -22),(3.55, -3),(4.75, 17),(5.6, 0),(6, 0)]),
    'jaw': ('x', [(0, 0),(1.2, 0),(2.0, 14),(2.25, 3),(3.1, 21),(3.4, 0),(4.65, 0),(5.05, 8),(6, 0)]),
    'left_shoulder': ('x', [(0, 0),(.45, 6),(1.2, 38),(2.0, 12),(2.9, -37),(4.1, -15),(4.8, 18),(5.7, 4),(6,0)]),
    'left_elbow': ('x', [(0, 0),(.8, -12),(1.7, -68),(2.4, -15),(3.5, -29),(4.5, -47),(5.6, -3),(6,0)]),
    'right_shoulder': ('y', [(0, 0),(.6, -20),(1.7, 15),(2.25, 46),(3.4, -23),(4.3, 24),(5.15, 5),(6,0)]),
    'right_elbow': ('x', [(0, 0),(.55, -10),(1.3, -33),(2.25, -8),(3.3, -79),(3.9, -19),(5.3, -42),(6,0)]),
    'left_hip': ('x', [(0, 0),(1.0, 6),(1.75, -9),(2.6, -4),(3.5, 16),(4.35, 2),(5.2, 0),(6,0)]),
    'left_knee': ('x', [(0, 0),(1.1, 2),(2.25, 24),(3.2, -5),(4.25, 10),(5.7, 0),(6,0)]),
    'right_hip': ('x', [(0, 0),(.45, -4),(1.5, 13),(2.2, -12),(3.4, 3),(4.6, -7),(5.4, 0),(6,0)]),
    'right_knee': ('x', [(0, 0),(.85, 12),(1.95, -3),(2.8, 16),(4.0, 2),(5.2, 7),(6,0)]),
    'left_ear': ('y', [(0, 0),(1.1, 8),(1.85, -19),(3.2, 11),(4.2, -4),(5.3, 10),(6,0)]),
    'right_ear': ('y', [(0, 0),(.75, -11),(1.6, 12),(2.55, 0),(3.4, -18),(4.75, 13),(6,0)]),
}
P = {'enamel':(.45,.018,.035),'bone':(.69,.78,.85),'black':(.018,.032,.051),
     'glow':(.08,.84,1.0),'gold':(1.0,.53,.16),'stage':(.018,.026,.044)}


def _ease(a,b,t):
    if b <= a: return 1.0
    u=max(0.0,min(1.0,(t-a)/(b-a)))
    return u*u*(3-2*u)


def value(track,t):
    if t<=track[0][0]:return track[0][1]
    for (a,va),(b,vb) in zip(track,track[1:]):
        if t<=b:return va+(vb-va)*_ease(a,b,t)
    return track[-1][1]


def _read_tracks(model):
    if not isinstance(model,dict) or model.get('format')!='codevideo.vtk-rigscene.v1':
        raise ValueError('Wrong source rig scene format')
    joints=model.get('joint_tracks')
    if not isinstance(joints,dict) or set(joints)!=set(TRACKS):
        raise ValueError('Rig scene must contain all original joint channels')
    definitions=model.get('bones')
    if not isinstance(definitions,list) or len(definitions)!=len(RIG):
        raise ValueError('Rig topology differs from fixed volumetric puppet source')
    if {str(b.get('name')):b.get('parent') for b in definitions} != {k:v[0] for k,v in RIG.items()}:
        raise ValueError('Rig topology differs from actual mesh binding')
    for b in definitions:
        if tuple(b.get('pivot_xyz',[]))!=tuple(RIG[b['name']][1]):
            raise ValueError('Changing anatomical pivots requires modifying the actual mesh/rig source code')
    out={}
    for name,track in joints.items():
        axis=track.get('axis'); keys=track.get('keys')
        if axis not in ('x','y','z') or not isinstance(keys,list) or len(keys)<3:
            raise ValueError('Joint tracks require axis and >=3 keyframes')
        pairs=[]
        for item in keys:
            if not isinstance(item,(tuple,list)) or len(item)!=2:
                raise ValueError('Malformed joint keyframe')
            t,a=item
            if type(t) not in (int,float) or type(a) not in (int,float) or not (math.isfinite(t) and math.isfinite(a)) or t<0 or t>6 or abs(a)>90:
                raise ValueError('Joint tracks require finite, bounded time/angles')
            pairs.append((float(t),float(a)))
        if pairs[0][0]!=0 or pairs[-1][0]!=6 or any(a>=b for (a,_),(b,_) in zip(pairs,pairs[1:])):
            raise ValueError('Tracks must cover 0-6s with strictly increasing key times')
        out[name]=(axis,pairs)
    return out


def _build_scene(width,height,tracks):
    import vtk
    import numpy as np
    from vtk.util.numpy_support import vtk_to_numpy
    ren=vtk.vtkRenderer()
    ren.SetBackground(.008,.015,.029)
    ren.SetBackground2(.025,.041,.075)
    ren.GradientBackgroundOn()
    win=vtk.vtkRenderWindow(); win.SetOffScreenRendering(1)
    win.AddRenderer(ren);win.SetSize(width,height)
    win.SetMultiSamples(4)
    cam=ren.GetActiveCamera();cam.SetViewAngle(49);cam.SetClippingRange(.1,100)
    assemblies={}
    for name,(parent,position) in RIG.items():
        a=vtk.vtkAssembly();a.SetPosition(*position)
        assemblies[name]=a
        if parent:assemblies[parent].AddPart(a)
        else:ren.AddActor(a)

    def material(actor,color,shine=True):
        actor.GetProperty().SetColor(*P[color]); actor.GetProperty().SetAmbient(.19 if color!='glow' else .85)
        actor.GetProperty().SetDiffuse(.72 if color!='glow' else .2)
        actor.GetProperty().SetSpecular(.45 if shine else .05)
        actor.GetProperty().SetSpecularPower(45)
        return actor

    def attach(name,kind,pos,scale,color):
        if kind=='box':source=vtk.vtkCubeSource()
        elif kind=='sphere':source=vtk.vtkSphereSource();source.SetThetaResolution(24);source.SetPhiResolution(16)
        elif kind=='cone':source=vtk.vtkConeSource();source.SetResolution(20)
        else:raise ValueError(kind)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(source.GetOutputPort())
        actor=material(vtk.vtkActor(),color)
        actor.SetMapper(mapper);actor.SetPosition(*pos);actor.SetScale(*scale)
        assemblies[name].AddPart(actor)
        return actor

    # Dense, asymmetric 3D volumes and real 3D head details; no sprites or billboards.
    attach('pelvis','box',(0,0,0),(.91,.46,.40),'black')
    attach('pelvis','box',(0,-.25,.06),(.44,.11,.17),'gold')
    attach('torso','box',(0,0,.54),(1.13,.55,.96),'enamel')
    attach('torso','box',(0,-.31,.65),(.69,.10,.43),'black')
    attach('torso','sphere',(0,-.38,.67),(.16,.06,.16),'glow')
    attach('torso','box',(0,0,1.06),(.42,.35,.17),'bone')
    attach('neck','box',(0,0,.11),(.19,.2,.34),'bone')
    attach('head','box',(0,0,.24),(.66,.48,.67),'bone')
    attach('head','box',(0,-.27,.27),(.61,.10,.36),'black')
    for x in (-.155,.155):
        attach('head','sphere',(x,-.352,.32),(.09,.045,.088),'glow')
        attach('head','sphere',(x,-.385,.315),(.035,.016,.042),'black')
    attach('head','box',(0,-.30,.08),(.42,.08,.075),'enamel')
    attach('jaw','box',(0,-.015,-.082),(.52,.2,.16),'enamel')
    for side in ('left','right'):
        shoulder=f'{side}_shoulder';elbow=f'{side}_elbow'
        hip=f'{side}_hip';knee=f'{side}_knee';ear=f'{side}_ear'
        attach(shoulder,'sphere',(0,0,.01),(.22,.20,.22),'bone')
        attach(shoulder,'box',(0,0,-.34),(.26,.28,.60),'enamel')
        attach(elbow,'sphere',(0,0,0),(.18,.19,.17),'bone')
        attach(elbow,'box',(0,-.01,-.29),(.20,.25,.52),'black')
        attach(elbow,'box',(0,-.035,-.60),(.30,.30,.15),'bone')
        attach(hip,'sphere',(0,0,0),(.25,.24,.24),'bone')
        attach(hip,'box',(0,0,-.36),(.32,.33,.62),'enamel')
        attach(knee,'sphere',(0,0,0),(.22,.24,.20),'bone')
        attach(knee,'box',(0,0,-.32),(.24,.28,.63),'black')
        attach(knee,'box',(0,-.17,-.70),(.35,.55,.20),'bone')
        attach(ear,'box',(0,0,.21),(.13,.16,.42),'enamel')
        attach(ear,'sphere',(0,-.09,.42),(.065,.06,.13),'glow')
    # Independent world geometry: raised 3D plinths, dimensional columns and glowing core.
    def stage_box(name,pos,scale,color):
        src=vtk.vtkCubeSource(); mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(src.GetOutputPort())
        a=material(vtk.vtkActor(),color);a.SetMapper(mp);a.SetPosition(*pos);a.SetScale(*scale)
        ren.AddActor(a);return a
    stage_box('floor',(0,0,-.18),(24,24,.3),'stage')
    stage_box('platform',(0,0,-.01),(4.2,3.1,.18),'black')
    stage_box('rimfront',(0,-1.56,.05),(4.4,.07,.08),'glow')
    for x in (-2.25,2.25):
        stage_box('pillar',(x,.75,1.0),(.32,.32,2.2),'black')
        stage_box('pillar_light',(x,.565,1.05),(.14,.025,1.5),'glow')
    core_src=vtk.vtkSphereSource();core_src.SetThetaResolution(36);core_src.SetPhiResolution(24)
    core_mp=vtk.vtkPolyDataMapper();core_mp.SetInputConnection(core_src.GetOutputPort())
    core=material(vtk.vtkActor(),'glow');core.SetMapper(core_mp);core.SetScale(.23,.23,.23)
    ren.AddActor(core)
    # 3D segmented ring of independent volumetric objects around the core.
    rings=[]
    for angle in range(0,360,30):
        a=math.radians(angle)
        tick=stage_box('orbital',(1.56+math.cos(a)*.39,-.15+math.sin(a)*.39,1.93),(.07,.035,.16),'gold')
        rings.append((tick,a))
    ren.AddLight(vtk.vtkLight())
    for pos,color,intensity in [((3,-4,7),(1.0,.75,.68),.95),((-4,2,6),(.3,.67,1.0),1.1)]:
        light=vtk.vtkLight();light.SetPosition(*pos);light.SetFocalPoint(0,0,1.4)
        light.SetColor(*color);light.SetIntensity(intensity);ren.AddLight(light)

    w2i=vtk.vtkWindowToImageFilter();w2i.SetInput(win);w2i.SetInputBufferTypeToRGB();w2i.ReadFrontBufferOff()

    def frame():
        win.Render();w2i.Modified();w2i.Update()
        im=w2i.GetOutput(); arr=vtk_to_numpy(im.GetPointData().GetScalars())
        return np.flipud(arr.reshape((height,width,3))).copy()

    def pose(values):
        for name,a in assemblies.items():
            if name in tracks:
                axis=tracks[name][0]
                val=values.get(name,0)
                a.SetOrientation(*(val if ax==axis else 0 for ax in ('x','y','z')))
            else:a.SetOrientation(0,0,0)

    def camera(t):
        # Three motivated shots: establish -> emotional close approach -> low angle payoff.
        if t<1.85:
            u=_ease(0,1.85,t); p=(3.5-u*.85,-7.7+u*.5,3.2-u*.2); target=(.12,0,1.52)
        elif t<4.05:
            u=_ease(1.85,4.05,t);p=(-3.5+u*.85,-6.2+u*.6,2.38-u*.25);target=(0,0,1.9)
        else:
            u=_ease(4.05,6,t);p=(3.2+u*.45,-7.2-u*.45,2.0+u*.6);target=(0,0,1.43)
        cam.SetPosition(*p);cam.SetFocalPoint(*target);cam.SetViewUp(0,0,1)
        ren.ResetCameraClippingRange()

    def update(t):
        pose({name:value(track,t) for name,(ax,track) in tracks.items()})
        core.SetPosition(1.56,-.15,1.93+.06*_ease(1.1,2.9,t)-.025*_ease(4.0,5.7,t))
        for tick,angle in rings:
            pulse=_ease(1.1,2.4,t)-_ease(3.8,5.6,t)
            tick.SetScale(.07+pulse*.07,.035,.16+pulse*.04)
        camera(t)

    return {'win':win,'renderer':ren,'rig':assemblies,'frame':frame,'pose':pose,'camera':camera,'update':update}


def _save_frame(path, frame):
    from PIL import Image
    Image.fromarray(frame,'RGB').save(path)


def run_stage(root:Path, project_id:str, *, width:int=960,height:int=540,fps:int=24,seconds:float=6.0,scene_data:dict|None=None)->dict:
    """Create an independently inspectable, true volumetric 3D articulated mechanical scene."""
    try:
        import vtk  # noqa: F401
        import numpy
        from PIL import Image
    except ImportError:
        return result('BLOCKED',gate='VTK',error='Optional vtk/numpy/pillow renderer unavailable; install .[vtk-demo]')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        return result('BLOCKED',gate='FFMPEG',error='FFmpeg/ffprobe required')
    project_id=slug(project_id)
    if width<240 or height<160 or width>1920 or height>1080 or width%2 or height%2 or type(fps)!=int or fps not in (12,24,25,30) or not (1<=seconds<=12):
        return result('BLOCKED',error='Invalid bounded demo settings')
    total=round(seconds*fps)
    if total<12:return result('BLOCKED',error='Demo requires at least 12 frames')
    tracks=_read_tracks(scene_data) if scene_data is not None else TRACKS
    # Fail BEFORE rendering when edited animation reduces the mechanical puppet to a static rig.
    candidate_signatures=set()
    for name,(axis,track) in tracks.items():
        samples=[value(track,t) for t in [i*.75 for i in range(9)]]
        peak=max(abs(v-samples[0]) for v in samples)
        if peak>9:
            candidate_signatures.add(tuple(round(abs(v-samples[0])/peak,1) for v in samples))
    if len(candidate_signatures)<4:
        return result('BLOCKED',gate='ARTICULATION',error='Edited scene has fewer than four independent nonroot motion envelopes')
    base=inside(root,Path('projects')/project_id)
    if base.exists():return result('BLOCKED',error='Project already exists; preserving existing contents',project=str(base))
    base.mkdir(parents=True)
    frames=base/'frames';frames.mkdir()
    proofdir=base/'diagnostics';proofdir.mkdir()
    model={'format':'codevideo.vtk-rigscene.v1','description':'Original, noncanonical mechanical puppet with an explicit hierarchical rigid-bone 3D rig',
           'anatomy':'segmented','bones':[{'name':name,'parent':parent,'pivot_xyz':pivot} for name,(parent,pivot) in RIG.items()],
           'joint_tracks':{name:{'axis':axis,'keys':keys} for name,(axis,keys) in tracks.items()},
           'camera_shots':[{'id':'setup','start_s':0,'end_s':1.85},{'id':'reach','start_s':1.85,'end_s':4.05},{'id':'payoff','start_s':4.05,'end_s':seconds}],
           'renderer':'VTK actual 3D mesh volumes and vtkAssembly parent transforms; no 2D source animation',
           'native_source':'codevideo/vtk_stage.py'}
    save_json(base/'rig_scene.json',model)
    t0=time.perf_counter()
    stage=_build_scene(width,height,tracks)
    # Fixed root and camera joint-isolation proof, using actual pixel outputs, not manifests alone.
    stage['pose']({});stage['camera'](1.0)
    neutral=stage['frame']()
    _save_frame(proofdir/'neutral.png',neutral)
    import numpy as np
    seen=[]
    diagnostic_hashes={'neutral.png':sha256(proofdir/'neutral.png')}
    diagnostic_joints={'torso':19,'head':30,'left_shoulder':49,'left_elbow':-56,
                       'right_shoulder':-50,'right_elbow':-62,'left_hip':25,'right_hip':-25}
    for joint,angle in diagnostic_joints.items():
        stage['pose']({joint:angle})
        img=stage['frame']()
        _save_frame(proofdir/f'{joint}.png',img)
        diagnostic_hashes[f'{joint}.png']=sha256(proofdir/f'{joint}.png')
        # Differences arise while root and camera are held fixed, and only one joint changes.
        changes=int(np.count_nonzero(np.max(np.abs(img.astype(np.int16)-neutral.astype(np.int16)),axis=2)>18))
        seen.append({'joint':joint,'angle_degrees':angle,'changed_pixels':changes,'visible':changes>=90})
    # Different authored envelopes reject synchronized joint wiggles in the actual animated timeline.
    times=[i*seconds/8 for i in range(9)]
    curves=[];active=[]
    for joint,(axis,track) in tracks.items():
        series=[value(track,t) for t in times]
        peak=max(abs(v-series[0]) for v in series)
        if peak<9:continue
        envelope=tuple(round(abs(v-series[0])/peak,1) for v in series)
        if envelope in curves:continue
        curves.append(envelope);active.append(joint)
    screen_safety=[]
    for i in range(total):
        t=i/fps
        stage['update'](t)
        image=stage['frame']()
        _save_frame(frames/f'frame_{i:05d}.png',image)
        red=(image[:,:,0]>image[:,:,1]*1.4)&(image[:,:,0]>image[:,:,2]*1.2)&(image[:,:,0]>55)
        silver=(image[:,:,0]>90)&(image[:,:,1]>90)&(image[:,:,2]>90)
        ys,xs=np.where(red|silver)
        if len(ys):
            margin=min(int(ys.min()),int(height-ys.max()-1),int(xs.min()),int(width-xs.max()-1))
            screen_safety.append({'frame':i,'edge_margin_pixels':margin})
        else:screen_safety.append({'frame':i,'edge_margin_pixels':-1})
    raster_s=time.perf_counter()-t0
    movie=base/'stage.partial.mp4'
    cmd=['ffmpeg','-hide_banner','-nostdin','-y','-loglevel','error','-framerate',str(fps),
         '-start_number','0','-i',str(frames/'frame_%05d.png'),'-frames:v',str(total),'-an',
         '-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
    if p.returncode:return result('PARTIAL',stage='encode',error=p.stderr[-900:],source=str(base/'rig_scene.json'))
    checked=verify_mp4(root,str(movie),deep=True)
    stats=checked.get('video',{})
    errors=[]
    if checked['status']!='PASS':errors.append('encoded film did not pass full decode')
    if stats.get('frames')!=total:errors.append('encoded frame count differs from exact rendered frames')
    if abs(stats.get('fps',0)-fps)>.02:errors.append('encoded FPS differs from stage profile')
    if abs(stats.get('duration_s',0)-total/fps)>.06:errors.append('encoded duration differs from stage profile')
    if len(active)<4:errors.append('insufficient unique non-root joint trajectories')
    visible=[x['joint'] for x in seen if x['visible']]
    if len(visible)<4:errors.append('fewer than four joints independently altered actual projected geometry')
    min_margin=min(x['edge_margin_pixels'] for x in screen_safety)
    if min_margin<max(4,round(height*.02)):
        worst=min(screen_safety,key=lambda x:x['edge_margin_pixels'])
        errors.append(f'framing failure at frame {worst["frame"]}: subject touches or approaches image boundary')
    final=base/'stage.mp4'
    if not errors:movie.rename(final)
    frame_hashes={f'frame_{i:05d}.png':sha256(frames/f'frame_{i:05d}.png') for i in range(total)}
    evidence={'format':FORMAT,'status':'TECHNICAL_PASS_VISUAL_PENDING' if not errors else 'FAIL',
              'backend':'VTK-EGL real 3D renderer','project':project_id,
              'model_sha256':sha256(base/'rig_scene.json'),'source_sha256':sha256(Path(__file__)),
              'rig_kind':'segmented','bone_count':len(RIG),'animated_non_root_joints':active,
              'joint_isolation':seen,'diagnostic_frame_hashes':diagnostic_hashes,
              'rendered_frame_hashes':frame_hashes,
              'independent_joint_count':len(active),'visible_joint_count':len(visible),
              'root_camera_fixed_during_diagnostics':True,'frames':total,'fps':fps,
              'resolution':[width,height],'minimum_subject_edge_margin_px':min_margin,
              'screen_safety':screen_safety,
              'render_wall_seconds':round(raster_s,3),
              'mp4':str(final if not errors else movie),
              'mp4_sha256':sha256(final if not errors else movie),
              'encoded_video':stats,'errors':errors,'visual_qa':'NOT_PERFORMED',
              'finished_verified':False,
              'limitations':['Mechanical/segmented geometry only; not organic skinning',
                             'This run does not certify the separate Blender render pipeline',
                             'Automated pixel differences do not replace human artistic review']}
    save_json(base/'stage_receipt.json',attest(evidence,root))
    return result(evidence['status'],video=str(final if not errors else movie),
                  rig_scene=str(base/'rig_scene.json'),receipt=str(base/'stage_receipt.json'),
                  diagnostics=str(proofdir),joint_count=len(active),visibly_articulated=visible,
                  frames=total,elapsed_s=round(raster_s,3),errors=errors)


def check_stage(root:Path,receipt_path:str)->dict:
    from .common import load_json
    path=inside(root,receipt_path,must_exist=True)
    receipt=load_json(path)
    issues=[]
    if receipt.get('format')!=FORMAT:issues.append('wrong proof format')
    if not authentic(receipt,root):issues.append('invalid local attestation')
    if receipt.get('finished_verified') is not False:issues.append('stage demo must not claim human visual approval')
    video=inside(root,receipt.get('mp4',''))
    model=inside(root,Path(receipt.get('mp4','')).parent/'rig_scene.json')
    if not video.is_file() or sha256(video)!=receipt.get('mp4_sha256'):issues.append('output missing or altered')
    if not model.is_file() or sha256(model)!=receipt.get('model_sha256'):issues.append('rig scene missing or altered')
    if sha256(Path(__file__))!=receipt.get('source_sha256'):issues.append('renderer source changed since evidence was generated')
    hashes=receipt.get('diagnostic_frame_hashes')
    if not isinstance(hashes,dict) or len(hashes)<5:issues.append('diagnostic evidence missing')
    else:
        for name,expected in hashes.items():
            if '/' in name or name.startswith('.') or not name.endswith('.png'):
                issues.append('invalid diagnostic evidence filename');break
            candidate=model.parent/'diagnostics'/name
            if not candidate.is_file() or sha256(candidate)!=expected:
                issues.append(f'diagnostic image altered or missing: {name}')
                break
    if len(receipt.get('animated_non_root_joints',[]))<4:issues.append('insufficient animation')
    if sum(bool(x.get('visible')) for x in receipt.get('joint_isolation',[]))<4:issues.append('insufficient visual articulation')
    frame_hashes=receipt.get('rendered_frame_hashes')
    if not isinstance(frame_hashes,dict) or len(frame_hashes)!=receipt.get('frames'):
        issues.append('frame sequence evidence missing or incomplete')
    else:
        for name,expected in frame_hashes.items():
            if not name.startswith('frame_') or not name.endswith('.png') or '/' in name:
                issues.append('invalid source frame evidence path');break
            frame=model.parent/'frames'/name
            if not frame.is_file() or sha256(frame)!=expected:
                issues.append(f'rendered source frame changed: {name}')
                break
    if not issues:
        checked=verify_mp4(root,str(video),deep=True)
        if checked['status']!='PASS':issues.append('MP4 failed full decode')
        if checked.get('video',{}).get('frames')!=receipt.get('frames'):issues.append('frame count mismatch')
    return result('PASS' if not issues else 'FAIL',errors=issues,stage_status='TECHNICAL_PASS_VISUAL_PENDING',
                  video=str(video),model=str(model),receipt=str(path))


def replay_stage(root:Path,scene_path:str,new_project_id:str,*,width:int=960,height:int=540,fps:int=24,seconds:float=6.0)->dict:
    """Rerender edited authored joint curves as a *new* versioned project; never overwrite."""
    scene=load_json(inside(root,scene_path,must_exist=True))
    _read_tracks(scene)
    return run_stage(root,new_project_id,width=width,height=height,fps=fps,seconds=seconds,scene_data=scene)
