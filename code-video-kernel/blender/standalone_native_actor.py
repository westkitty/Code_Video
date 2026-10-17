"""Native Blender articulated actor / independent diagnostic and film render.

This is an original, noncanonical character. It builds a *real* armature,
continuous normalized-weight limbs, joint keyframes, IK goals, grounded feet,
a prop contact event, three physical cameras, a saved .blend and resumable PNG
batches. It does not substitute for the separate imported-GLB gate.
"""
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path

import bpy
from mathutils import Vector

VERSION = 'codevideo.native_actor.v1'
ROOT = Path(os.environ.get('CODEVIDEO_NATIVE_ROOT', str(Path.home() / 'Projects' / 'CodeVideoStudio' / 'NativeReach'))).expanduser().resolve()
SHOTS = {'recognition': (1, 96, 'CV_Camera_Wide'), 'struggle': (97, 192, 'CV_Camera_Reaching'), 'resolution': (193, 288, 'CV_Camera_Resolution')}
FRAMES = [1, 49, 96, 97, 145, 192, 193, 224, 245, 288]

def h(path):
    d = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            d.update(chunk)
    return d.hexdigest()

def write_json_atomic(path, obj):
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj, indent=2, sort_keys=True))
    os.replace(temp,path)

def mat(name, rgb, metallic=0., roughness=.4, emission=0.):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1.);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value=(*rgb,1.)
    n.inputs['Metallic'].default_value=metallic;n.inputs['Roughness'].default_value=roughness
    if emission:
        n.inputs['Emission Color'].default_value=(*rgb,1.)
        n.inputs['Emission Strength'].default_value=emission
    return m

def render_settings(scene,width=480,height=270):
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.resolution_percentage=100;scene.render.fps=24
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.color_depth='8'
    scene.render.film_transparent=False
    scene.render.use_file_extension=True

def bone(arm, name, start,end,parent=None):
    b=arm.edit_bones.new(name);b.head=start;b.tail=end
    if parent:b.parent=arm.edit_bones[parent]
    return b

def uv_ellipsoid(name, center, scale, material, rig=None, joint=None, segments=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=12,location=center)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    if rig and joint:
        o.parent=rig
        group=o.vertex_groups.new(name=joint)
        group.add(list(range(len(o.data.vertices))),1.,'REPLACE')
        m=o.modifiers.new('Bone skinning','ARMATURE');m.object=rig
    return o

def skin_tube(name,a,b,c,rig,upper,lower,material,radius=.14,rings=23,sides=12):
    a,b,c=Vector(a),Vector(b),Vector(c)
    points=[];faces=[];groups=[]
    for j in range(rings):
        t=j/(rings-1)
        base=a.lerp(b,t*2) if t<=.5 else b.lerp(c,(t-.5)*2)
        taper=.82+.15*math.sin(math.pi*t)
        for k in range(sides):
            phi=math.tau*k/sides
            points.append((base.x+radius*taper*math.cos(phi),base.y+radius*taper*math.sin(phi),base.z))
            s=max(0.,min(1.,(t-.39)/.22));v=s*s*(3-2*s)
            groups.append((1-v,v))
    for j in range(rings-1):
        for k in range(sides):
            a0=j*sides+k;a1=j*sides+(k+1)%sides
            b0=(j+1)*sides+k;b1=(j+1)*sides+(k+1)%sides
            faces.extend(((a0,b0,b1),(a0,b1,a1)))
    mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(points,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    for f in mesh.polygons:f.use_smooth=True
    obj.parent=rig
    groups_bpy=[obj.vertex_groups.new(name=upper),obj.vertex_groups.new(name=lower)]
    for i,(u,v) in enumerate(groups):
        if u>0:groups_bpy[0].add([i],u,'REPLACE')
        if v>0:groups_bpy[1].add([i],v,'REPLACE')
    mod=obj.modifiers.new('Weighted skin','ARMATURE');mod.object=rig
    obj['CV_SKIN_CONTINUOUS']=True
    return obj

def loc_keys(ob, frames):
    for fr,xyz in frames:
        ob.location=xyz;ob.keyframe_insert(data_path='location',frame=fr,group='Actor')

def rot_keys(pb, frames):
    pb.rotation_mode='XYZ'
    for fr,euler in frames:
        pb.rotation_euler=euler;pb.keyframe_insert(data_path='rotation_euler',frame=fr,group='Actor')

def look_at(ob,target):
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()

def build():
    if ROOT.exists() and list(ROOT.iterdir()):
        raise ValueError('Existing native actor root is nonempty: use a new CODEVIDEO_NATIVE_ROOT to avoid overwrite')
    ROOT.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.frame_start=1;s.frame_end=288
    render_settings(s)
    s.world.color=(.013,.016,.028)
    ruby=mat('Ruby enamel',(.33,.017,.035),.6,.24)
    dark=mat('Obsidian chassis',(.023,.03,.05),.52,.22)
    pale=mat('Ceramic alloy',(.65,.74,.76),.4,.3)
    brass=mat('Oxidized brass',(.56,.28,.12),.6,.25)
    teal=mat('Azure core',(.02,.65,.77),.14,.3,2.)
    floor=mat('Graphite floor',(.028,.032,.051),.2,.57)
    arm_data=bpy.data.armatures.new('CV_Actor_Armature')
    rig=bpy.data.objects.new('CV_Actor_Rig',arm_data)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    skeleton={
        'root':((0,0,.15),(0,0,1.05),None),
        'pelvis':((0,0,1.05),(0,0,1.34),'root'),
        'spine':((0,0,1.34),(0,0,1.79),'pelvis'),
        'chest':((0,0,1.79),(0,0,1.99),'spine'),
        'neck':((0,0,1.99),(0,0,2.21),'chest'),
        'head':((0,0,2.21),(0,0,2.59),'neck'),
        'jaw':((0,-.16,2.29),(0,-.32,2.26),'head'),
        'L_upper':((-.38,0,1.89),(-.78,0,1.68),'chest'),
        'L_fore':((-.78,0,1.68),(-1.10,0,1.28),'L_upper'),
        'L_hand':((-1.10,0,1.28),(-1.22,0,1.16),'L_fore'),
        'R_upper':((.38,0,1.89),(.78,0,1.68),'chest'),
        'R_fore':((.78,0,1.68),(1.10,0,1.28),'R_upper'),
        'R_hand':((1.10,0,1.28),(1.22,0,1.16),'R_fore'),
        'L_thigh':((-.25,0,1.07),(-.28,0,.63),'pelvis'),
        'L_shin':((-.28,0,.63),(-.31,0,.20),'L_thigh'),
        'L_foot':((-.31,0,.20),(-.31,-.18,.13),'L_shin'),
        'R_thigh':((.25,0,1.07),(.28,0,.63),'pelvis'),
        'R_shin':((.28,0,.63),(.31,0,.20),'R_thigh'),
        'R_foot':((.31,0,.20),(.31,-.18,.13),'R_shin')}
    for name,(a,b,parent) in skeleton.items():bone(arm_data,name,a,b,parent)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv_ellipsoid('Torso', (0,0,1.64),(.46,.29,.53),ruby,rig,'spine',32)
    uv_ellipsoid('Chest panel',(0,-.26,1.70),(.29,.08,.36),dark,rig,'chest')
    uv_ellipsoid('Chest light',(0,-.335,1.68),(.14,.055,.17),teal,rig,'chest')
    uv_ellipsoid('Head',(0,0,2.45),(.35,.31,.40),pale,rig,'head',32)
    uv_ellipsoid('Visor',(0,-.285,2.46),(.31,.095,.18),dark,rig,'head')
    for x in (-.12,.12):uv_ellipsoid('Eye',(x,-.37,2.48),(.065,.035,.075),teal,rig,'head')
    uv_ellipsoid('Jaw',(0,-.33,2.26),(.21,.06,.08),brass,rig,'jaw')
    uv_ellipsoid('Pelvis',(0,0,1.12),(.36,.25,.24),dark,rig,'pelvis')
    for side in ('L','R'):
        for part,center,sc,joint in [('Hand',(-1.16,0,1.24) if side=='L' else (1.16,0,1.24),(.13,.13,.15),side+'_hand'),
                                   ('Foot',(-.31,-.18,.14) if side=='L' else (.31,-.18,.14),(.17,.32,.13),side+'_foot')]:
            uv_ellipsoid(side+part,center,sc,brass if part=='Hand' else pale,rig,joint)
        for limb,a,b,c,u,l,r,m in (
            ('arm',skeleton[side+'_upper'][0],skeleton[side+'_upper'][1],skeleton[side+'_fore'][1],side+'_upper',side+'_fore',.135,ruby),
            ('leg',skeleton[side+'_thigh'][0],skeleton[side+'_thigh'][1],skeleton[side+'_shin'][1],side+'_thigh',side+'_shin',.165,dark)):
            skin_tube(side+'_'+limb,a,b,c,rig,u,l,m,radius=r)
    # IK target/driver empties are not proof: actual evaluated armature and mesh will be measured.
    controllers={}
    for name,location in [('R_Reach', (1.08,-.1,1.24)),('R_Pole',(1,-1.5,1.35)),
                          ('L_Foot',(-.31,-.18,.13)),('R_Foot',(.31,-.18,.13)),
                          ('L_Pole',(-1,-1,.56)),('RF_Pole',(1,-1,.56))]:
        bpy.ops.object.empty_add(type='SPHERE',location=location)
        o=bpy.context.object;o.name='CV_'+name;o.empty_display_size=.085;controllers[name]=o
    for side,pole in [('L','L_Pole'),('R','RF_Pole')]:
        c=rig.pose.bones[side+'_shin'].constraints.new('IK')
        c.name='Planted support IK';c.target=controllers[side+'_Foot'];c.chain_count=2
        c.pole_target=controllers[pole]
    c=rig.pose.bones['R_fore'].constraints.new('IK')
    c.name='Reach and grip IK';c.target=controllers['R_Reach'];c.chain_count=2
    c.pole_target=controllers['R_Pole']
    # Dramatic beats: curiosity / frustrated miss / decisive grasp / recovery.
    rot_keys(rig.pose.bones['spine'],[(1,(0,0,0)),(75,(0,.045,-.03)),(142,(0,.09,-.08)),(207,(0,.06,.03)),(288,(0,0,0))])
    rot_keys(rig.pose.bones['neck'],[(1,(0,0,-.16)),(56,(0,0,.25)),(121,(0,0,.35)),(225,(0,0,-.05)),(288,(0,0,.12))])
    rot_keys(rig.pose.bones['head'],[(1,(.03,-.05,.10)),(70,(-.10,.09,-.12)),(142,(.16,.08,-.08)),(225,(-.10,-.12,.18)),(288,(-.08,0,0))])
    rot_keys(rig.pose.bones['jaw'],[(1,(0,0,0)),(154,(.16,0,0)),(175,(0,0,0)),(236,(.27,0,0)),(288,(0,0,0))])
    rot_keys(rig.pose.bones['L_upper'],[(1,(0,0,0)),(90,(.09,.12,.15)),(150,(.24,.32,-.15)),(218,(.13,.05,-.19)),(288,(0,0,0))])
    rot_keys(rig.pose.bones['L_fore'],[(1,(0,0,0)),(122,(-.17,.1,0)),(202,(-.42,.05,.13)),(288,(-.08,0,0))])
    rot_keys(rig.pose.bones['pelvis'],[(1,(0,0,0)),(129,(0,.032,.02)),(211,(0,-.06,-.04)),(288,(0,0,0))])
    loc_keys(controllers['R_Reach'],[(1,(1.08,-.1,1.24)),(72,(1.10,-.12,1.50)),(130,(1.48,-.13,1.56)),(165,(1.20,-.15,1.48)),(211,(1.10,-.15,1.58)),(224,(1.06,-.18,1.60)),(288,(.96,-.23,1.53))])
    # External prop remains in the scene; ownership changes to reach target on frame 224.
    orb=uv_ellipsoid('CV_Orb',(1.2,-.15,1.63),(.16,.16,.16),teal,segments=32)
    loc_keys(orb,[(1,(1.22,-.15,1.63)),(86,(1.29,-.15,1.69)),(145,(1.70,-.15,1.60)),(190,(1.29,-.15,1.61)),(223,(1.07,-.18,1.60))])
    follow=orb.constraints.new('COPY_LOCATION');follow.target=controllers['R_Reach'];follow.influence=0.
    for fr,influence in [(1,0.),(223,0.),(224,1.),(288,1.)]:
        follow.influence=influence;follow.keyframe_insert(data_path='influence',frame=fr)
    # Ground, actual lights, and camera parallax. All components are volumetric.
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.13))
    stage=bpy.context.object;stage.name='CV_Ground';stage.scale=(12,12,.25);stage.data.materials.append(floor)
    for i,(pos,power,color) in enumerate([((1.5,-4,5),1000,(1.,.7,.52)),((-3,-1,3),750,(.25,.7,1.)),((1,4,4),850,(.55,.5,1.))]):
        bpy.ops.object.light_add(type='AREA',location=pos)
        light=bpy.context.object;light.name=f'CV_Key_{i}';light.data.energy=power;light.data.color=color
        light.data.shape='DISK';light.data.size=3.;look_at(light,(0,0,1.35))
    cameras={}
    for name,pos,focal,lens in [('CV_Camera_Wide',(3,-6.5,3.2),(0,0,1.55),38),
                                 ('CV_Camera_Reaching',(-2.8,-5.3,2.65),(.45,0,1.62),41),
                                 ('CV_Camera_Resolution',(2.2,-4.8,2.55),(.54,0,1.72),43)]:
        bpy.ops.object.camera_add(location=pos)
        o=bpy.context.object;o.name=name;o.data.lens=lens;look_at(o,focal);cameras[name]=o
    s.camera=cameras['CV_Camera_Wide']
    s['CODEVIDEO_SOURCE_FORMAT']=VERSION
    s['CODEVIDEO_RENDER_OWNER']='Blender armature/weighted native actor'
    s.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'native_reach.blend'))
    diagnostics={'format':VERSION,'scene_sha256':h(ROOT/'native_reach.blend'),'pose_frames':FRAMES,
                 'rig':rig.name,'skin_meshes':[], 'moving_nonroot':[], 'contacts':{}}
    skin_objs=[o for o in bpy.data.objects if o.type=='MESH' and o.get('CV_SKIN_CONTINUOUS')]
    if len(skin_objs)!=4:raise ValueError('Four skinned continuous limbs are mandatory')
    frames=(1,96,145,224,288)
    bone_poses={}; mesh_poses={}
    for frame in frames:
        s.frame_set(frame); deps=bpy.context.evaluated_depsgraph_get()
        bone_poses[frame]={n: tuple(round(v,6) for v in ((pb.parent.matrix.inverted()@pb.matrix) if pb.parent else pb.matrix).to_quaternion())
                           for n,pb in rig.pose.bones.items()}
        mesh_poses[frame]={ob.name: [tuple(v.co) for v in ob.evaluated_get(deps).to_mesh().vertices] for ob in skin_objs}
        for ob in skin_objs:ob.evaluated_get(deps).to_mesh_clear()
    for n in rig.pose.bones.keys():
        if n=='root':continue
        q0=bone_poses[1][n]
        if any(max(abs(a-b) for a,b in zip(q0,bone_poses[f][n]))>.015 for f in frames[1:]):
            diagnostics['moving_nonroot'].append(n)
    if len(diagnostics['moving_nonroot'])<4:raise ValueError('Not enough articulated independent nonroot joints')
    for o in skin_objs:
        a=mesh_poses[1][o.name]
        maxima=[]
        for fr in frames[1:]:
            b=mesh_poses[fr][o.name]
            maxima.append(max(math.dist(v,w) for v,w in zip(a,b)))
        delta=max(maxima)
        if delta<.015:raise ValueError('Weighted mesh failed to deform: '+o.name)
        diagnostics['skin_meshes'].append({'mesh':o.name,'max_delta_m':round(delta,5)})
    s.frame_set(224);deps=bpy.context.evaluated_depsgraph_get();orbpos=orb.evaluated_get(deps).matrix_world.translation
    goal=controllers['R_Reach'].evaluated_get(deps).matrix_world.translation
    diagnostics['contacts']['prop_to_hand_goal_at_grip_m']=round((orbpos-goal).length,6)
    if (orbpos-goal).length > .008:raise ValueError('Orb failed to follow grasp target')
    for f in (1,96,145,224,288):
        s.frame_set(f);s.camera=cameras[SHOTS['recognition' if f<=96 else 'struggle' if f<=192 else 'resolution'][2]]
        s.render.filepath=str(ROOT/f'pose_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
    diagnostics['rendered_poses']={p.name:h(p) for p in sorted(ROOT.glob('pose_*.png'))}
    write_json_atomic(ROOT/'native_diagnostic.json',diagnostics)
    print('CODEVIDEO_NATIVE_DIAGNOSTIC='+json.dumps(diagnostics),flush=True)

def render_chunk(shot,first,last):
    if shot not in SHOTS:raise ValueError('Unknown shot')
    start,end,cam=SHOTS[shot]
    if first<start or last>end or first>last or last-first+1>24:raise ValueError('Max 24 sequential native frames per invocation')
    source=ROOT/'native_reach.blend'
    if not source.is_file():raise ValueError('Missing native .blend')
    s=bpy.context.scene
    if s.get('CODEVIDEO_SOURCE_FORMAT')!=VERSION:raise ValueError('Untrusted source scene')
    render_settings(s)
    camera=bpy.data.objects.get(cam)
    if not camera:raise ValueError('Missing camera')
    s.camera=camera
    d=ROOT/'shots'/shot;d.mkdir(parents=True,exist_ok=True)
    manifest=d/'frames.json'
    proof={'format':VERSION,'native_blend_sha256':h(source),'shot':shot,'camera':cam,'width':s.render.resolution_x,'height':s.render.resolution_y,'fps':24,'hashes':{}}
    if manifest.is_file():
        previous=json.loads(manifest.read_text())
        for field in ('format','native_blend_sha256','shot','camera','width','height','fps'):
            if previous.get(field)!=proof[field]:raise ValueError('Stale frame receipt: '+field)
        for name,digest in previous.get('hashes',{}).items():
            file=d/name
            if not file.is_file() or h(file)!=digest:raise ValueError('Corrupt/stale previously rendered frame: '+name)
        proof=previous
    for frame in range(first,last+1):
        name=f'frame_{frame:06d}.png'
        if name in proof['hashes']:continue
        target=d/name
        if target.exists():raise ValueError('Unsigned existing frame requires manual isolation: '+name)
        s.frame_set(frame);s.render.filepath=str(target)
        t0=time.monotonic();bpy.ops.render.render(write_still=True)
        if not target.is_file() or target.stat().st_size<500:raise ValueError('Invalid render frame')
        proof['hashes'][name]=h(target)
        write_json_atomic(manifest,proof)
        print(f'CODEVIDEO_FRAME {frame} {time.monotonic()-t0:.3f}s',flush=True)
    print('CODEVIDEO_NATIVE_BATCH='+str(manifest),flush=True)

def main():
    a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['build','chunk'],required=True)
    parser.add_argument('--shot',choices=list(SHOTS));parser.add_argument('--first',type=int);parser.add_argument('--last',type=int)
    args=parser.parse_args(a)
    if args.mode=='build':build()
    else:
        if not args.shot or args.first is None or args.last is None:raise ValueError('Shot and inclusive range required')
        render_chunk(args.shot,args.first,args.last)

if __name__=='__main__':main()
