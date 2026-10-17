"""Construct 'The Reach' as an editable Blender armature, weighted meshes and 3-shot scene.

Run with Blender 4.5+ on a verified host:
blender -b --factory-startup --disable-autoexec --python blender/create_organic_reach.py -- --out /ABS/PATH/reach.blend

This script is not a proof of successful execution until the actual .blend, rig probe,
rendered frames, and MP4 have been separately verified on that host.
"""
import sys, json, math
from pathlib import Path
import bpy
from mathutils import Vector,Matrix,Quaternion
import numpy as np

PKG=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PKG))
from codevideo.golden_reach import default_spec,evaluate,validate_spec,DURATION,FPS
from codevideo.actor_engine import skinned_tube


def find_flag(flag,default=None):
    a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if flag not in a:return default
    return a[a.index(flag)+1]


def make_mat(name,rgb,metal=.0,glow=0):
    mat=bpy.data.materials.new(name);mat.diffuse_color=(*rgb,1);mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    if shader:
        shader.inputs['Base Color'].default_value=(*rgb,1)
        shader.inputs['Metallic'].default_value=metal
        shader.inputs['Roughness'].default_value=.32
        if glow and 'Emission Color' in shader.inputs:
            shader.inputs['Emission Color'].default_value=(*rgb,1)
            shader.inputs['Emission Strength'].default_value=glow
    return mat


def sphere(name,position,scale,mat,segments=28):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=16,location=position)
    ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in ob.data.polygons:p.use_smooth=True
    return ob


def parent_bone(ob,rig,bone):
    old=ob.matrix_world.copy()
    ob.parent=rig;ob.parent_type='BONE';ob.parent_bone=bone
    ob.matrix_world=old


def bind_mesh(name,verts,weights,faces,rig,bone1,bone2,mat):
    mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(verts.tolist(),[],[list(f) for f in faces]);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:p.use_smooth=True
    va=ob.vertex_groups.new(name=bone1);vb=ob.vertex_groups.new(name=bone2)
    for i,(w1,w2) in enumerate(weights):
        if w1>1e-6:va.add([i],float(w1),'REPLACE')
        if w2>1e-6:vb.add([i],float(w2),'REPLACE')
    deform=ob.modifiers.new(name='REAL_ARMATURE_SKIN',type='ARMATURE')
    deform.object=rig;deform.use_vertex_groups=True;deform.use_bone_envelopes=False
    ob.parent=rig
    return ob


def pose_bone_world(rig,bone_name,a,b):
    # Bone's local +Y points along its physical segment.
    aa=Vector(a);bb=Vector(b);vec=bb-aa
    if vec.length<.001:raise ValueError('Degenerate pose bone '+bone_name)
    q=Vector((0,1,0)).rotation_difference(vec.normalized())
    pb=rig.pose.bones[bone_name];pb.rotation_mode='QUATERNION'
    pb.matrix=Matrix.Translation(aa) @ q.to_matrix().to_4x4()
    pb.keyframe_insert('location',frame=bpy.context.scene.frame_current)
    pb.keyframe_insert('rotation_quaternion',frame=bpy.context.scene.frame_current)


def make_scene(out:Path,spec):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    root=bpy.context.scene;root.frame_start=1;root.frame_end=288;root.render.fps=FPS
    root.render.resolution_x=1920;root.render.resolution_y=1080;root.render.resolution_percentage=100
    root.render.image_settings.file_format='PNG'
    engine_options=bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
    for opt in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
        if opt in engine_options:root.render.engine=opt;break
    if root.render.engine=='CYCLES':root.cycles.samples=32
    root.world.color=(.009,.012,.02)
    enamel=make_mat('Oxide Red enamel',(.48,.026,.048),.32)
    dark=make_mat('Dark graphite',(.02,.028,.047),.38)
    pale=make_mat('Ivory shell',(.68,.76,.80),.24)
    copper=make_mat('Warm copper',(.55,.31,.12),.58)
    cyan=make_mat('Ion core',(.015,.72,.82),.10,3.0)

    arm=bpy.data.armatures.new('Cinder_Organic_Skeleton')
    rig=bpy.data.objects.new('Cinder_Rig',arm);bpy.context.collection.objects.link(rig)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    # Rest pose: anatomically useful neutral down-arm layout, parented real hierarchy.
    bones={
      'root':(None,(-.72,0,0),(-.72,0,.2)),
      'pelvis':('root',(-.72,0,1.30),(-.72,0,1.50)),
      'spine':('pelvis',(-.72,0,1.30),(-.72,0,2.09)),
      'neck':('spine',(-.72,0,2.09),(-.72,0,2.36)),
      'head':('neck',(-.72,0,2.36),(-.72,0,2.58)),
      'right_upper':('spine',(-.24,0,1.81),(-.24,0,1.09)),
      'right_lower':('right_upper',(-.24,0,1.09),(-.24,0,.40)),
      'left_upper':('spine',(-1.20,0,1.81),(-1.20,0,1.09)),
      'left_lower':('left_upper',(-1.20,0,1.09),(-1.20,0,.40)),
      'right_thigh':('pelvis',(-.47,0,1.18),(-.47,0,.56)),
      'right_shin':('right_thigh',(-.47,0,.56),(-.47,0,-.02)),
      'left_thigh':('pelvis',(-.97,0,1.18),(-.97,0,.56)),
      'left_shin':('left_thigh',(-.97,0,.56),(-.97,0,-.02)),
    }
    for name,(parent,a,b) in bones.items():
        eb=arm.edit_bones.new(name);eb.head=a;eb.tail=b;eb.use_deform=True
        if parent:eb.parent=arm.edit_bones[parent];eb.use_connect=False
    bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
    bind=evaluate(0,spec)
    for side in ('right','left'):
        for which,radius,material in [('arm',.16,enamel if side=='right' else pale),('leg',.185,dark)]:
            upper=f'{side}_upper' if which=='arm' else f'{side}_thigh'
            lower=f'{side}_lower' if which=='arm' else f'{side}_shin'
            oldA=Vector(bones[upper][1]);oldB=Vector(bones[upper][2]);oldC=Vector(bones[lower][2])
            vv,ww,faces=skinned_tube(np.array(oldA),np.array(oldB),np.array(oldC),sections=38,sides=20,radius=radius)
            bind_mesh(f'{side}_{which}_continuous_skinned',vv,ww,faces,rig,upper,lower,material)
    # Expressive rigid facial controls are parented to the head bone; limb/body meshes deform by armature.
    torso=sphere('Organic Torso',(-.72,0,1.65),(.49,.33,.53),enamel)
    parent_bone(torso,rig,'spine')
    head=sphere('Cinder Head',(-.72,0,2.40),(.34,.29,.35),pale)
    parent_bone(head,rig,'head')
    for s in (-1,1):
        e=sphere(f'Eye_{s}',(-.72+s*.13,-.276,2.46),(.064,.035,.086),cyan,20)
        parent_bone(e,rig,'head')
    jaw=sphere('Jaw',(-.72,-.25,2.17),(.25,.09,.055),copper)
    parent_bone(jaw,rig,'head')
    for side in ('right','left'):
        h=sphere(f'{side}_hand',(-.24 if side=='right' else -1.2,0,.4),(.17,.16,.16),copper)
        parent_bone(h,rig,f'{side}_lower')
    for x in (-2.3,2.3):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,.65,1.15))
        pillar=bpy.context.object;pillar.name='Stage pillar';pillar.scale=(.30,.30,2.3);pillar.data.materials.append(dark)
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.16))
    floor=bpy.context.object;floor.name='Stage floor';floor.scale=(20,20,.30);floor.data.materials.append(dark)
    orb=sphere('Sphere__WORLD_TO_HAND_CONTACT',(0.77,0,1.75),(.175,.175,.175),cyan,36)
    # Standalone scene lights.
    for name,location,energy,color in [('Key',(2,-4,5),950,(1,.76,.61)),('Rim',(-3,2,4),1100,(.33,.70,1))]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=energy;ld.color=color;ld.shape='DISK';ld.size=3
        obj=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(obj);obj.location=location
        obj.rotation_euler=(Vector((-.6,0,1.5))-obj.location).to_track_quat('-Z','Y').to_euler()
    for idx,(name,loc,focal,lens,frame) in enumerate([
        ('01-recognition',(2.25,-5.0,2.65),(-.14,0,1.62),50,1),
        ('02-struggle',(-1.75,-4.6,2.62),(-.07,0,1.75),62,97),
        ('03-resolution',(1.65,-4.6,2.35),(-.16,0,1.76),67,193)]):
        dat=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,dat);bpy.context.collection.objects.link(cam)
        cam.location=loc;cam.rotation_euler=(Vector(focal)-cam.location).to_track_quat('-Z','Y').to_euler();dat.lens=lens
        marker=root.timeline_markers.new(name,frame=frame);marker.camera=cam
        if idx==0:root.camera=cam
    def eval_key_frame(frame):
        root.frame_set(frame)
        t=(frame-1)/FPS;p=evaluate(t,spec)
        pp=p['bones'];
        # Input bone hierarchy evaluated in parent-first order.
        pose_bone_world(rig,'root',(-.72,0,0),(-.72,0,.2))
        pose_bone_world(rig,'pelvis',p['root'],p['root']+np.array([0,0,.2]))
        pose_bone_world(rig,'spine',*pp['torso'])
        pose_bone_world(rig,'neck',p['neck'],p['head'])
        pose_bone_world(rig,'head',p['head'],p['head']+np.array([0,0,.22]))
        for n in ('right_upper','right_lower','left_upper','left_lower','right_thigh','right_shin','left_thigh','left_shin'):
            pose_bone_world(rig,n,*pp[n])
        orb.location=p['orb'];orb.keyframe_insert('location',frame=frame)
        # Mouth motion visibly changes the actual geometry relative to its head parent.
        jaw.location.z=-.08*math.sin(math.radians(p['jaw']))
        jaw.keyframe_insert('location',frame=frame)
    for f in range(1,289):eval_key_frame(f)
    root.frame_set(1)
    root['CODE_VIDEO_STAGE']='Golden Reach organic Blender implementation - host verification required'
    root['CODE_VIDEO_FPS']=FPS
    root['CODE_VIDEO_CONTACT_FRAME']=1+round(spec['events']['grip_s']*FPS)
    root['CODE_VIDEO_SUBTITLES']='OFF'
    out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print('CODEVIDEO_REAL_SKIN_BLEND='+str(out),flush=True)
    print('CODEVIDEO_REAL_ARMATURE_BONES='+str(len(arm.bones)),flush=True)

if __name__=='__main__':
    out=find_flag('--out');sp=find_flag('--spec')
    if not out:raise SystemExit('Missing --out /absolute/new/scene.blend')
    dest=Path(out).resolve()
    if dest.exists():raise SystemExit('Refusing overwrite: '+str(dest))
    spec=json.loads(Path(sp).read_text()) if sp else default_spec()
    validate_spec(spec)
    make_scene(dest,spec)
