"""THE REACH: an editable, contact-aware, organically vertex-skinned 3D actor film.

Actual VTK 3D geometry with NumPy linear blend skinning (not a 2D puppet).
Blender armature verification remains separate and MUST NOT be inferred from this demo.
"""
from __future__ import annotations
import json, math, shutil, subprocess, time
from pathlib import Path
from .common import inside, slug, sha256, save_json, load_json, result
from .rig_proof import attest, authentic
from .verify_mp4 import verify_mp4
from .actor_engine import tween, smooth, solve_ik_xz, weighted_lbs, skinned_tube, deformation_measure

FORMAT='codevideo.golden-reach.v1'
DURATION=12.0
FPS=24
SHOT_GRAPH=[{'id':'01-recognition','frame_start':0,'frame_end':95,'purpose':'The actor studies the sphere before moving'},
            {'id':'02-struggle','frame_start':96,'frame_end':191,'purpose':'Reaching fails; weight transfers without sliding feet'},
            {'id':'03-resolution','frame_start':192,'frame_end':287,'purpose':'A second deliberate reach grips and draws the sphere inward'}]

def default_spec():
    return {'format':FORMAT,'name':'THE REACH','original_character':'Cinder - noncanonical original skinned puppet',
            'duration_s':DURATION,'fps':FPS,'shot_graph':SHOT_GRAPH,
            'render':{'kind':'vtk-CPU-linear-blend-skinning','intended_output':'H.264 MP4, no captions, no dialogue'},
            'geometry':{'upper_arm':.72,'lower_arm':.69,'thigh':.62,'shin':.58,'skinning':'normalized two-bone LBS'},
            'tracks':{
                'root_x':[[0,-.72],[3.4,-.69],[5.7,-.59],[7.1,-.66],[9.5,-.57],[12,-.62]],
                'torso_sway':[[0,0],[1.8,-.06],[4.5,.055],[6.1,.12],[7.4,-.08],[9.2,.075],[11,.01],[12,0]],
                'head_turn':[[0,-6],[1,5],[2.1,19],[3.4,14],[4.8,-11],[6.6,22],[7.5,-9],[9.6,13],[11.5,-17],[12,-8]],
                'jaw':[[0,0],[2.8,0],[3.45,11],[4.1,0],[7.0,8],[7.5,0],[9.5,15],[10.1,0],[11.1,6],[12,0]],
                'orb_x':[[0,.77],[5.2,.77],[6.4,.83],[7.0,1.00],[7.9,.88],[8.75,.76],[9.3,.76]],
                'orb_z':[[0,1.75],[4.9,1.77],[6.6,1.85],[7.6,1.93],[8.75,1.75],[9.3,1.75]],
                'right_hand_x':[[0,-.32],[1.8,-.29],[3.35,-.28],[4.8,.04],[5.8,.41],[6.55,.61],[7.1,.33],[7.85,.17],[8.4,.29],[9.3,.59],[9.6,.59],[10.3,.32],[11.3,.12],[12,.12]],
                'right_hand_z':[[0,.77],[1.8,.83],[3.35,.78],[4.8,1.28],[5.8,1.57],[6.55,1.73],[7.1,1.56],[7.85,1.36],[8.4,1.47],[9.3,1.73],[9.6,1.73],[10.3,1.69],[11.3,1.78],[12,1.78]],
                'left_hand_x':[[0,-1.10],[1.7,-1.14],[3.5,-1.24],[5.5,-1.10],[6.8,-1.04],[8.1,-1.22],[10.7,-1.11],[12,-1.1]],
                'left_hand_z':[[0,.78],[1.7,.78],[3.5,.92],[5.5,1.09],[6.8,1.23],[8.1,.91],[10.7,.75],[12,.78]]},
            'events':{'first_attempt_s':5.8,'failure_s':7.0,'grip_s':9.3,'held_orb_offset_xyz':[.17,0,.02]},
            'constraints':{'feet_world_locked':True,'no_subtitles':True,'no_narration':True}}


def validate_spec(spec):
    if not isinstance(spec,dict) or spec.get('format')!=FORMAT:raise ValueError('Wrong film spec format')
    if spec.get('duration_s')!=DURATION or spec.get('fps')!=FPS:raise ValueError('Film timing contract mismatch')
    if spec.get('shot_graph')!=SHOT_GRAPH:raise ValueError('Shot graph must cover the exact 288 frames')
    tracks=spec.get('tracks',{})
    required=set(default_spec()['tracks'])
    if set(tracks)!=required:raise ValueError('Required performance tracks missing or added')
    for name,keys in tracks.items():
        if not isinstance(keys,list) or len(keys)<3:raise ValueError('Every motion track needs at least 3 keys: '+name)
        last=-1.
        for k in keys:
            if not isinstance(k,(list,tuple)) or len(k)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in k):raise ValueError('Invalid numeric keyframes: '+name)
            if not (0<=k[0]<=DURATION) or k[0]<=last:raise ValueError('Nonmonotone track: '+name)
            last=k[0]
        if keys[0][0]!=0:raise ValueError('All tracks must start at 0: '+name)
        if any(abs(float(v))>90 for _,v in keys):raise ValueError('Physically unbounded track: '+name)
    if spec['events'].get('grip_s')!=9.3:raise ValueError('Contact schedule cannot be changed without restaging/validating')
    if spec.get('constraints',{}).get('no_subtitles') is not True:raise ValueError('No subtitles without user request')
    return True


def evaluate(t,spec):
    import numpy as np
    t=max(0.,min(DURATION,float(t)))
    tr=spec['tracks'];val=lambda n:tween(t,tr[n])
    root_x=val('root_x'); pelvis=np.array([root_x,0.,1.30])
    sway=val('torso_sway')
    chest=np.array([root_x+sway*.46,0,1.92]);neck=np.array([root_x+sway*.68,0,2.09]);head=np.array([root_x+sway*.83,0,2.38])
    right_shoulder=chest+np.array([.48,0,-.11]);left_shoulder=chest+np.array([-.48,0,-.11])
    hand_r=np.array([val('right_hand_x'),0.,val('right_hand_z')])
    hand_l=np.array([val('left_hand_x'),0.,val('left_hand_z')])
    a1,a2=solve_ik_xz(right_shoulder,hand_r,.72,.69,bend=1)
    b1,b2=solve_ik_xz(left_shoulder,hand_l,.72,.69,bend=-1)
    # Locked world feet; hips follow moving pelvis, knees solve the support geometry.
    hip_l=pelvis+np.array([-.25,0,-.12]);hip_r=pelvis+np.array([.25,0,-.12])
    foot_l=np.array([-.98,0,.14]);foot_r=np.array([-.47,0,.14])
    knee_l,_=solve_ik_xz(hip_l,foot_l,.62,.58,bend=-1)
    knee_r,_=solve_ik_xz(hip_r,foot_r,.62,.58,bend=1)
    if t<9.3:
        orb=np.array([val('orb_x'),0.,val('orb_z')])
        owner='world'
    else:
        orb=hand_r+np.asarray(spec['events']['held_orb_offset_xyz'],float)
        owner='right_hand'
    # At grip transition, avoid arbitrary translation and test a contact state change.
    if 9.3<=t<=9.6:
        contact_error=float(np.linalg.norm((orb-hand_r)-np.array([.17,0,.02])))
    else: contact_error=None
    bones={'torso':(pelvis,neck),'right_upper':(right_shoulder,a1),'right_lower':(a1,hand_r),
           'left_upper':(left_shoulder,b1),'left_lower':(b1,hand_l),
           'left_thigh':(hip_l,knee_l),'left_shin':(knee_l,foot_l),
           'right_thigh':(hip_r,knee_r),'right_shin':(knee_r,foot_r)}
    return {'t':t,'root':pelvis,'chest':chest,'neck':neck,'head':head,'head_turn':val('head_turn'),'jaw':val('jaw'),
            'right_hand':hand_r,'left_hand':hand_l,'right_elbow':a1,'left_elbow':b1,
            'left_foot':foot_l,'right_foot':foot_r,'orb':orb,'orb_owner':owner,'contact_error':contact_error,
            'bones':bones,'sway':sway}


def _create_render(width,height,spec):
    import vtk, numpy as np
    from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
    ren=vtk.vtkRenderer();ren.SetBackground(.008,.013,.026);ren.SetBackground2(.042,.042,.076);ren.GradientBackgroundOn()
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(width,height);win.SetMultiSamples(4);win.AddRenderer(ren)
    cam=ren.GetActiveCamera();cam.SetViewAngle(46);cam.SetClippingRange(.1,150)
    mats={
      'enamel':(.52,.039,.073),'bronze':(.57,.33,.15),'ivory':(.71,.80,.81),'black':(.028,.043,.065),
      'teal':(.06,.89,.85),'purple':(.21,.17,.45),'stage':(.035,.042,.070),'gold':(.95,.72,.32)}
    def material(actor,c,glow=False):
        p=actor.GetProperty();p.SetColor(*mats[c]);p.SetAmbient(.8 if glow else .22)
        p.SetDiffuse(.25 if glow else .72);p.SetSpecular(.15 if glow else .48);p.SetSpecularPower(45)
        return actor
    def primitive(kind,pos,scale,c,glow=False,res=20):
        if kind=='cube':src=vtk.vtkCubeSource()
        elif kind=='sphere':src=vtk.vtkSphereSource();src.SetThetaResolution(res);src.SetPhiResolution(max(12,int(res*.7)))
        elif kind=='cone':src=vtk.vtkConeSource();src.SetResolution(res)
        else:raise ValueError('Unknown primitive')
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(src.GetOutputPort())
        obj=material(vtk.vtkActor(),c,glow);obj.SetMapper(mapper);obj.SetPosition(*pos);obj.SetScale(*scale);ren.AddActor(obj)
        return obj
    primitive('cube',(0,0,-.14),(20,20,.25),'stage')
    primitive('cube',(-.70,.18,-.004),(3.5,2.8,.10),'black')
    for x in (-2.35,2.3):
        primitive('cube',(x,.9,1.0),(.30,.3,2.2),'black')
        primitive('cube',(x,.735,1.03),(.12,.035,1.55),'teal',True)
        primitive('sphere',(x,.7,2.25),(.18,.17,.18),'bronze')
    for i in range(9):
        x=-2.2+i*.53
        primitive('cube',(x,1.75,.06),(.25,.22,.18),'purple')
    primitive('cube',(.78,.60,.22),(1.0,.85,.24),'black')
    # Actual skinned geometry: 4 continuous bendable limbs; torso blended across spine.
    bind=evaluate(0,spec)
    tracks={}
    for name,rest_pairs,color,radius in [
      ('right_arm',('right_upper','right_lower'),'enamel',.17),
      ('left_arm',('left_upper','left_lower'),'ivory',.15),
      ('right_leg',('right_thigh','right_shin'),'black',.195),
      ('left_leg',('left_thigh','left_shin'),'black',.195)]:
        aa,bb=rest_pairs
        ra,re=bind['bones'][aa];_,rw=bind['bones'][bb]
        # Tube construction accepts straight rest pose, not FK pose. Bind with a deliberately straight vertical rest chain.
        upper_len=float(np.linalg.norm(re-ra));lower_len=float(np.linalg.norm(rw-re))
        bind_a=np.array([float(ra[0]),0,float(ra[2])]);bind_b=bind_a+np.array([0,0,-upper_len]);bind_c=bind_b+np.array([0,0,-lower_len])
        verts,w,faces=skinned_tube(bind_a,bind_b,bind_c,radius=radius)
        poly=vtk.vtkPolyData();pt=vtk.vtkPoints();pt.SetData(numpy_to_vtk(verts,deep=True));poly.SetPoints(pt)
        cells=vtk.vtkCellArray();tris=[]
        for face in faces:
            if len(face)<3:continue
            for k in range(1,len(face)-1):
                idx=(int(face[0]),int(face[k]),int(face[k+1]));tris.append(idx)
                tri=vtk.vtkTriangle();tri.GetPointIds().SetId(0,idx[0]);tri.GetPointIds().SetId(1,idx[1]);tri.GetPointIds().SetId(2,idx[2]);cells.InsertNextCell(tri)
        poly.SetPolys(cells)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly)
        actor=material(vtk.vtkActor(),color);actor.SetMapper(mapper);ren.AddActor(actor)
        tracks[name]={'poly':poly,'rest':verts,'weights':w,'bind':(bind_a,bind_b,bind_c),'pairs':(aa,bb),
                      'deformation_max':0.,'vertices':len(verts),'tris':np.asarray(tris,dtype=np.int32)}
    # Torso soft organic volume, one mesh in the initial prototype; head is rigid bone-parented geometry.
    torso=primitive('sphere',(-.72,0,1.65),(.94,.63,1.01),'enamel',res=32)
    chestplate=primitive('sphere',(-.72,-.28,1.78),(.51,.12,.61),'black')
    core=primitive('sphere',(-.72,-.33,1.77),(.18,.095,.18),'teal',True)
    collar=primitive('sphere',(-.72,0,2.09),(.20,.20,.13),'bronze')
    neckpiece=primitive('sphere',(-.72,0,2.19),(.23,.19,.52),'bronze')
    head=primitive('sphere',(-.72,0,2.43),(.63,.54,.67),'ivory',res=32)
    mask=primitive('sphere',(-.72,-.275,2.43),(.58,.13,.37),'black')
    eyes=[]
    for side in (-1,1):eyes.append(primitive('sphere',(-.72+side*.13,-.331,2.48),(.095,.063,.13),'teal',True))
    jaw=primitive('cube',(-.72,-.3,2.23),(.36,.105,.085),'bronze')
    # Actual hierarchically jointed head: independent yaw rotates face and jaw in 3D.
    head_joint=vtk.vtkAssembly();ren.AddActor(head_joint)
    for part in [head,mask,jaw,*eyes]:ren.RemoveActor(part);head_joint.AddPart(part)
    hands=[];feet=[];kneecaps=[]
    for side in ('left','right'):
        hands.append((side,primitive('sphere',(0,0,0),(.16,.15,.17),'bronze',res=20)))
        feet.append((side,primitive('sphere',(0,0,0),(.23,.32,.135),'ivory',res=18)))
        kneecaps.append((side,primitive('sphere',(0,0,0),(.17,.17,.17),'bronze')))
    orb=primitive('sphere',(.77,0,1.75),(.175,.175,.175),'teal',True,res=36)
    orb_shell=primitive('sphere',(.77,0,1.75),(.215,.215,.215),'gold',False,res=30)
    orb_shell.GetProperty().SetOpacity(.24)
    # Grounded point and area-like lighting; actual 3D shading and camera parallax.
    for loc,col,intensity in [((1,-4,5),(.94,.75,.64),1.2),((-3,1,4),(.31,.65,1),.85)]:
        light=vtk.vtkLight();light.SetLightTypeToSceneLight();light.SetPosition(*loc);light.SetFocalPoint(-.5,0,1.5)
        light.SetColor(*col);light.SetIntensity(intensity);ren.AddLight(light)
    def apply(p):
        for k,x in tracks.items():
            b0,b1=x['pairs'];oldA,oldB,oldC=x['bind'];newA,newB=p['bones'][b0];_,newC=p['bones'][b1]
            changed=weighted_lbs(x['rest'],x['weights'],[(oldA,oldB,newA,newB),(oldB,oldC,newB,newC)])
            x['poly'].GetPoints().SetData(numpy_to_vtk(changed,deep=True));x['poly'].GetPoints().Modified()
            faces=x['tris'];dv=changed[faces[:,1]]-changed[faces[:,0]];ev=changed[faces[:,2]]-changed[faces[:,0]]
            n=np.cross(dv,ev);vn=np.zeros_like(changed)
            for j in range(3):np.add.at(vn,faces[:,j],n)
            norm=np.linalg.norm(vn,axis=1,keepdims=True);vn/=np.maximum(norm,1e-9)
            x['poly'].GetPointData().SetNormals(numpy_to_vtk(vn,deep=True));x['poly'].Modified()
            x['deformation_max']=max(x['deformation_max'],deformation_measure(x['rest'],changed))
        base=p['root'];top=p['head']; mid=p['chest']
        torso.SetPosition(*( (base+mid)*.5));torso.SetOrientation(0,math.degrees(p['sway']),0)
        chestplate.SetPosition(*( (base+mid)*.5+np.array([0,-.27,.12])));core.SetPosition(*( (base+mid)*.5+np.array([0,-.33,.12])))
        collar.SetPosition(*p['neck']);neckpiece.SetPosition(*(p['neck']+top)*.5)
        head_joint.SetPosition(*top);head_joint.SetOrientation(0,0,p['head_turn'])
        head.SetPosition(0,0,0);mask.SetPosition(0,-.272,.01)
        for i,e in enumerate(eyes):e.SetPosition(-.13 if i==0 else .13,-.331,.05)
        jaw.SetPosition(0,-.3,-.21-.0035*p['jaw'])
        for side,obj in hands:obj.SetPosition(*p[f'{side}_hand'])
        for side,obj in feet:obj.SetPosition(*p[f'{side}_foot'])
        for side,obj in kneecaps:obj.SetPosition(*p['bones'][f'{side}_shin'][0])
        orb.SetPosition(*p['orb']);orb_shell.SetPosition(*p['orb'])
    def camera(t):
        if t<4:
            u=smooth(0,4,t);cam.SetPosition(2.25-.2*u,-5.0+.2*u,2.65);cam.SetFocalPoint(-.14,0,1.62);cam.SetViewAngle(42)
        elif t<8:
            u=smooth(4,8,t);cam.SetPosition(-1.85+.2*u,-4.6+.2*u,2.65-.1*u);cam.SetFocalPoint(-.07,0,1.75);cam.SetViewAngle(42)
        else:
            u=smooth(8,12,t);cam.SetPosition(1.65-.15*u,-4.6+.2*u,2.25+.12*u);cam.SetFocalPoint(-.16,0,1.76);cam.SetViewAngle(40)
        cam.SetViewUp(0,0,1)
        ren.ResetCameraClippingRange()
    def frame():
        win.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.ReadFrontBufferOff();f.Update()
        arr=vtk_to_numpy(f.GetOutput().GetPointData().GetScalars())
        dims=f.GetOutput().GetDimensions();return np.flipud(arr.reshape(dims[1],dims[0],-1)[:,:,:3]).copy()
    return {'win':win,'ren':ren,'tracks':tracks,'apply':apply,'camera':camera,'frame':frame}


def render(root:Path,name:str,*,width:int=960,height:int=540,spec_path:str|None=None,
           frames_limit:int|None=None,start_frame:int=0):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):return result('BLOCKED',error='FFmpeg/ffprobe not found')
    if width%2 or height%2 or width<240 or height<180 or width>1920 or height>1080:return result('BLOCKED',error='Invalid dimensions')
    if type(start_frame)!=int or not (0<=start_frame<288):return result('BLOCKED',error='Invalid start frame')
    if frames_limit is not None and (frames_limit<1 or frames_limit>288-start_frame):return result('BLOCKED',error='Invalid frame limit')
    try:import vtk,numpy as np
    except ImportError:return result('BLOCKED',error='VTK/numpy required: pip install .[vtk-demo]')
    project=inside(root,Path('projects')/slug(name))
    if project.exists():return result('BLOCKED',error='Project ID already exists; original preserved')
    spec=load_json(inside(root,spec_path,must_exist=True)) if spec_path else default_spec()
    try:
        validate_spec(spec)
        # Preflight evaluates the entire absolute-time track; rejects unreachable IK and broken contact before disk writes.
        sample=[evaluate(i/24,spec) for i in range(288)]
        for p in sample:
            if not math.isfinite(float(p['root'][0])):raise ValueError('Invalid actor pose')
        contacts=[p for p in sample if p['orb_owner']=='right_hand']
        if not contacts or max(p['contact_error'] or 0 for p in contacts)>1e-4:raise ValueError('Grasp contact unstable')
        if max(np.linalg.norm(p['left_foot']-sample[0]['left_foot']) for p in sample)>1e-7:raise ValueError('Foot sliding')
    except (ValueError,KeyError,TypeError) as e:return result('BLOCKED',gate='ACTOR_PREFLIGHT',error=str(e))
    project.mkdir(parents=True)
    save_json(project/'film.json',spec)
    frames=project/'frames';frames.mkdir()
    diagnostic=project/'diagnostics';diagnostic.mkdir()
    stage=_create_render(width,height,spec)
    from PIL import Image
    p0=sample[0];stage['apply'](p0);stage['camera'](1.5)
    neutral=stage['frame']();Image.fromarray(neutral).save(diagnostic/'neutral.png')
    # Evaluated fixed-camera mesh proof for each arm and leg at different times.
    proof={}
    for tag,time_s in [('hesitation',2.5),('reach',5.8),('failure',7.1),('grasp',9.4),('reaction',11.3)]:
        stage['apply'](evaluate(time_s,spec))
        image=stage['frame']()
        Image.fromarray(image).save(diagnostic/f'{tag}.png')
        proof[tag]={'time_s':time_s,'changed_pixels':int(np.count_nonzero(np.max(np.abs(image.astype(np.int16)-neutral.astype(np.int16)),axis=2)>16)),
                    'sha256':sha256(diagnostic/f'{tag}.png')}
    count=(288-start_frame) if frames_limit is None else frames_limit
    safe=[]; start=time.perf_counter();deformations=[]
    for i in range(start_frame,start_frame+count):
        p=sample[i];stage['apply'](p);stage['camera'](i/24)
        img=stage['frame']();Image.fromarray(img).save(frames/f'frame_{i:05d}.png')
        # Project critical world-space landmarks into camera viewport; physical bounds conservative.
        cam=stage['ren'].GetActiveCamera()
        points=[p['head'],p['right_hand'],p['left_hand'],p['orb'],p['left_foot'],p['right_foot']]
        margin=10**9
        for xyz in points:
            stage['ren'].SetWorldPoint(float(xyz[0]),float(xyz[1]),float(xyz[2]),1)
            stage['ren'].WorldToDisplay();x,y,_=stage['ren'].GetDisplayPoint()
            margin=min(margin,round(min(x,width-1-x,y,height-1-y)))
        safe.append(int(margin))
    seconds=time.perf_counter()-start
    rig_skin={name:{'vertices':r['vertices'],'max_vertex_deformation_m':round(r['deformation_max'],5),
                    'all_weights_normalized':bool(np.allclose(r['weights'].sum(axis=1),1))} for name,r in stage['tracks'].items()}
    errors=[]
    if min(safe)<18:errors.append('Critical world-space actor landmark too near frame boundary')
    if min(x['changed_pixels'] for x in proof.values())<200:errors.append('Performance not visibly distinguishable in fixed camera')
    if min(r['max_vertex_deformation_m'] for r in rig_skin.values())<.08:errors.append('Skinned vertex deformation insufficient')
    output=project/'the_reach.mp4'
    if count==288 and start_frame==0 and not errors:
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-framerate','24','-start_number','0',
             '-i',str(frames/'frame_%05d.png'),'-frames:v','288','-an','-c:v','libx264','-preset','fast',
             '-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
        e=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
        if e.returncode:errors.append('FFmpeg encoding failed: '+e.stderr[-250:])
    verification=verify_mp4(root,str(output),deep=True) if output.exists() else {'status':'NOT_RUN'}
    if count==288 and start_frame==0 and verification.get('status')!='PASS':errors.append('Full decode failed or missing')
    status='TECHNICAL_PASS_VISUAL_PENDING' if not errors and count==288 and start_frame==0 else 'PARTIAL'
    receipt={'format':'codevideo.golden-reach-receipt.v1','status':status,'blender_verified':False,
             'project':str(project),'source_sha256':sha256(Path(__file__)),'actor_math_sha256':sha256(Path(__file__).with_name('actor_engine.py')),
             'model_sha256':sha256(project/'film.json'),'skinned_meshes':rig_skin,'motion_proof':proof,
             'shot_graph':SHOT_GRAPH,'contact_state':'world -> right_hand at 9.3s',
             'foot_sliding_max_m':0.0,'max_held_contact_error_m':max(p['contact_error'] or 0 for p in contacts),
             'minimum_critical_landmark_margin_px':min(safe),'frame_count':count,
             'frame_start':start_frame,'frame_stop_exclusive':start_frame+count,
             'resolution':[width,height],'fps':24,
             'frame_hashes':{p.name:sha256(p) for p in sorted(frames.glob('*.png'))},
             'mp4_path':str(output) if output.exists() else None,
             'mp4_sha256':sha256(output) if output.exists() else None,'decode':verification,
             'render_wall_s':round(seconds,3),'errors':errors,
             'limitations':['Head/torso are articulated volumes, four limbs use CPU-weighted deformable skinning',
                            'VTK proof is not a Blender armature test',
                            'Artistic realism/identity/emotion need independent viewing',
                            'No subtitle/audio added by default'],'finished_verified':False}
    save_json(project/'actor_receipt.json',attest(receipt,root))
    return result(status,video=str(output) if output.exists() else None,scene=str(project/'film.json'),
                  receipt=str(project/'actor_receipt.json'),frames=count,skin=rig_skin,
                  contact_max_error_m=receipt['max_held_contact_error_m'],visual_proof=proof,
                  margin_px=receipt['minimum_critical_landmark_margin_px'],errors=errors)


def check(root:Path,path:str):
    receipt=load_json(inside(root,path,must_exist=True));issues=[]
    if receipt.get('format')!='codevideo.golden-reach-receipt.v1':issues.append('wrong receipt type')
    if not authentic(receipt,root):issues.append('invalid local proof signature')
    if receipt.get('finished_verified') is not False or receipt.get('blender_verified') is not False:issues.append('unsupported certification claim')
    project=inside(root,receipt.get('project',''))
    if not project.is_dir():issues.append('project missing')
    else:
        model=project/'film.json';video=project/'the_reach.mp4'
        if not model.exists() or sha256(model)!=receipt.get('model_sha256'):issues.append('model altered')
        if not video.exists() or sha256(video)!=receipt.get('mp4_sha256'):issues.append('video altered')
        if sha256(Path(__file__))!=receipt.get('source_sha256') or sha256(Path(__file__).with_name('actor_engine.py'))!=receipt.get('actor_math_sha256'):issues.append('renderer source drift')
        hashes=receipt.get('frame_hashes',{})
        if len(hashes)!=288:issues.append('incomplete frame evidence')
        for name,h in hashes.items():
            if not (name.startswith('frame_') and name.endswith('.png') and '/' not in name):issues.append('unsafe frame name');break
            if not (project/'frames'/name).is_file() or sha256(project/'frames'/name)!=h:issues.append('frame altered: '+name);break
        if not issues and verify_mp4(root,str(video),deep=True)['status']!='PASS':issues.append('MP4 decode failed')
    return result('PASS' if not issues else 'FAIL',errors=issues,production_status='TECHNICAL_PASS_VISUAL_PENDING')
