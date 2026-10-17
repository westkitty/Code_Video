"""Execute INSIDE real Blender. Import animated GLB, inspect deformers and bones,
render diagnostic frames, save native scene, emit byte-hashed proof data.

This script has NOT run until a verified Blender host executes it. The result
MUST be checked and inspected outside Blender before claiming certification.
"""
import bpy,sys,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector

SAMPLES=[1,49,97,145,193,225,289]


def arg(flag):
    a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    i=a.index(flag)
    return Path(a[i+1]).resolve()


def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for x in iter(lambda:fh.read(1024*1024),b''):h.update(x)
    return h.hexdigest()


def inspect_and_render(source,out):
    if not source.is_file() or source.suffix.lower()!='.glb':raise ValueError('GLB missing')
    out.mkdir(parents=True,exist_ok=True)
    bpy.context.scene.render.fps=24
    bpy.ops.import_scene.gltf(filepath=str(source))
    rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE' and len(o.pose.bones)>0]
    models=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        modifiers=[m for m in ob.modifiers if m.type=='ARMATURE' and m.object in rigs and m.show_render]
        if modifiers:
            models.append(ob)
    if not rigs or len(models)<4:raise ValueError('Blender importer did not create 4 skinned meshes and genuine armatures')

    rig_records=[];bone_keys=[]
    for rig in rigs:
        for b in rig.pose.bones:
            bone_keys.append((rig,b.name))
        rig_records.append({'name':rig.name,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None} for b in rig.pose.bones]})
    base_mesh={};mesh_motion={o.name:0.0 for o in models};bone_samples={}
    for frame in SAMPLES:
        bpy.context.scene.frame_set(frame)
        deps=bpy.context.evaluated_depsgraph_get()
        for rig,name in bone_keys:
            pb=rig.pose.bones.get(name)
            local=pb.parent.matrix.inverted_safe()@pb.matrix if pb.parent else pb.matrix
            q=local.to_quaternion().normalized()
            bone_samples.setdefault(rig.name+'/'+name,[]).append((frame,[float(q.x),float(q.y),float(q.z),float(q.w)]))
        for ob in models:
            evaluated=ob.evaluated_get(deps)
            mesh=evaluated.to_mesh()
            try:
                coords=[tuple(v.co) for v in mesh.vertices]
                if frame==SAMPLES[0]:base_mesh[ob.name]=coords
                else:
                    old=base_mesh[ob.name]
                    if len(coords)!=len(old):raise ValueError('Evaluated vertex count changed')
                    maximum=max((math.dist(a,b) for a,b in zip(coords,old)),default=0.0)
                    mesh_motion[ob.name]=max(mesh_motion[ob.name],maximum)
            finally:evaluated.to_mesh_clear()

    moving=[]
    for joint,values in bone_samples.items():
        if len(values)<2:continue
        base=values[0][1]
        maximum=max(2*math.acos(min(1,max(-1,abs(sum(x*y for x,y in zip(base,q)))))) for _,q in values[1:])
        name=joint.split('/',1)[1]
        rigname=joint.split('/',1)[0]
        parent=next((b['parent'] for r in rig_records if r['name']==rigname for b in r['bones'] if b['name']==name),None)
        if parent and maximum>math.radians(1.0):moving.append({'name':joint,'relative_rotation_rad':maximum})
    moving_meshes=[{'name':name,'max_local_vertex_delta_m':delta,'count':len(base_mesh[name])} for name,delta in mesh_motion.items() if delta>.005]
    if len(moving)<4 or len(moving_meshes)<4:
        raise ValueError('Blender did not demonstrate >=4 moving nonroot joints and 4 actually deforming meshes')

    # New, fixed camera/light; repeated samples prove subject movement rather than camera tricks.
    bpy.ops.object.camera_add(location=(3.1,-5.0,3.25));camera=bpy.context.object;camera.name='CodeVideo_RigTest_FixedCamera'
    camera.rotation_euler=(Vector((-.45,0,1.45))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=4.7
    bpy.context.scene.camera=camera
    bpy.ops.object.light_add(type='AREA',location=(2,-4,5))
    light=bpy.context.object;light.name='CodeVideo_RigTest_Key';light.data.energy=1100;light.data.shape='DISK';light.data.size=3
    light.rotation_euler=(Vector((-.5,0,1.5))-light.location).to_track_quat('-Z','Y').to_euler()
    scene=bpy.context.scene
    scene.frame_start=1;scene.frame_end=288;scene.render.fps=24
    scene['CODEVIDEO_IMPORTED_SOURCE_SHA256']=sha256(source)
    # Independent director cameras: scene-space framing over changing geometry.
    # These cameras are not evidence of independent motion; pose proof precedes them.
    from mathutils import Vector as V
    tracked=[]
    for sample_frame in (1,49,97,145,193,225,289):
        scene.frame_set(sample_frame)
        deps=bpy.context.evaluated_depsgraph_get()
        for ob in bpy.context.scene.objects:
            if ob.type!='MESH':continue
            ev=ob.evaluated_get(deps)
            world=ev.matrix_world
            for corner in ev.bound_box:
                tracked.append(world @ V(corner))
    if not tracked:raise ValueError('No actual actor bounds after native GLB import')
    minp=V([min(v[i] for v in tracked) for i in range(3)])
    maxp=V([max(v[i] for v in tracked) for i in range(3)])
    center=(minp+maxp)*.5
    for ix,(name,offset) in enumerate((
        ('CodeVideo_Shot_01',(0,-5.5,2.2)),
        ('CodeVideo_Shot_02',(-2.8,-4.8,1.8)),
        ('CodeVideo_Shot_03',(2.5,-4.2,1.7)))):
        bpy.ops.object.camera_add(location=center+V(offset))
        ob=bpy.context.object;ob.name=name
        ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.view_layer.update()
        local=[ob.matrix_world.inverted() @ v for v in tracked]
        # Ortho scale covers width and height for a 16:9 render with safety margin.
        xmin=min(q.x for q in local);xmax=max(q.x for q in local)
        ymin=min(q.y for q in local);ymax=max(q.y for q in local)
        ob.data.type='ORTHO'
        ob.data.ortho_scale=max((xmax-xmin)*1.23,(ymax-ymin)*16/9*1.23,1.6)
        marker=scene.timeline_markers.new(name,frame=1+ix*96)
        marker.camera=ob
    # A ground plane and motivated lighting give the imported actor real depth.
    floor_z=minp.z-.12
    bpy.ops.mesh.primitive_cube_add(size=1,location=(center.x,center.y,floor_z-.085))
    floor=bpy.context.object;floor.name='CodeVideo_Stage_Floor'
    floor.scale=(12,12,.15)
    mat=bpy.data.materials.new('CodeVideo_Stage_Graphite')
    mat.diffuse_color=(.025,.031,.045,1);mat.use_nodes=True
    floor.data.materials.append(mat)
    scene.camera=bpy.data.objects.get('CodeVideo_Shot_01')
    scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.render.film_transparent=False
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
    blend=out/'the_reach_imported_native.blend'
    if blend.exists():raise ValueError('Refusing native scene overwrite')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    images={}
    for frame in SAMPLES:
        scene.frame_set(frame)
        path=out/f'pose_{frame:04d}.png'
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        if not path.is_file() or path.stat().st_size<100:raise ValueError('Diagnostic render failed')
        images[path.name]=sha256(path)
    proof={'format':'codevideo.blender-import-proof.v1','origin':'actual-blender-runtime',
           'source_glb_sha256':sha256(source),'source_glb':str(source),
           'native_blend':str(blend),'native_blend_sha256':sha256(blend),
           'armatures':rig_records,'armature_count':len(rigs),
           'deform_mesh_count':len(models),'moving_deform_meshes':moving_meshes,
           'moving_nonroot_joints':moving,'fixed_camera':camera.name,
           'sample_frames':SAMPLES,'diagnostic_images':images,
           'status':'EVALUATED_IMPORT_TECHNICAL_PASS_VISUAL_PENDING',
           'not_proven':['human artistic approval','camera shot edit','full 12s Blender MP4','real-world user playback']}
    (out/'blender_import_proof.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
    print('CODEVIDEO_IMPORTED_NATIVE_BLEND='+str(blend),flush=True)
    print('CODEVIDEO_IMPORT_PROOF='+str(out/'blender_import_proof.json'),flush=True)

if __name__=='__main__':inspect_and_render(arg('--glb'),arg('--out'))
