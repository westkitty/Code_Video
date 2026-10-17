"""Optional Blender-only REAL segmented 3D rig demonstration; not a film deliverable."""
import bpy, math, sys
from mathutils import Vector, Euler
from pathlib import Path

def main():
    a=sys.argv[sys.argv.index('--')+1:]
    destination=Path(a[a.index('--out')+1]).resolve()
    if destination.exists():raise ValueError('Refusing to overwrite existing Blender scene')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    arm_data=bpy.data.armatures.new('Puppet_Skeleton')
    arm=bpy.data.objects.new('Puppet_Rig',arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active=arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bones={
      'root':(None,(0,0,0),(0,0,.4)),
      'pelvis':('root',(0,0,.4),(0,0,.65)),
      'torso':('pelvis',(0,0,.65),(0,0,1.40)),
      'neck':('torso',(0,0,1.40),(0,0,1.57)),
      'head':('neck',(0,0,1.57),(0,0,2.0)),
      'left_upper_arm':('torso',(-.24,0,1.29),(-.83,0,1.19)),
      'left_forearm':('left_upper_arm',(-.83,0,1.19),(-1.19,0,.93)),
      'right_upper_arm':('torso',(.24,0,1.29),(.83,0,1.19)),
      'right_forearm':('right_upper_arm',(.83,0,1.19),(1.19,0,.93)),
      'left_thigh':('pelvis',(-.17,0,.42),(-.23,0,-.3)),
      'left_shin':('left_thigh',(-.23,0,-.3),(-.23,-.07,-.92)),
      'right_thigh':('pelvis',(.17,0,.42),(.23,0,-.3)),
      'right_shin':('right_thigh',(.23,0,-.3),(.23,-.07,-.92))
    }
    for name,(parent,start,end) in bones.items():
        b=arm_data.edit_bones.new(name)
        b.head=start;b.tail=end
        if parent:b.parent=arm_data.edit_bones[parent]
        b.use_connect=False
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.select_set(False)
    def mat(name, rgb,metal=.12):
        m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1)
        m.use_nodes=True
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:
            p.inputs['Base Color'].default_value=(*rgb,1)
            p.inputs['Metallic'].default_value=metal
            p.inputs['Roughness'].default_value=.38
        return m
    enamel=mat('Oxide Red Enamel',(.48,.018,.038),.35)
    pale=mat('Bone white joint plating',(.66,.72,.76),.3)
    dark=mat('Black Ceramic',(.024,.035,.053),.42)
    gold=mat('Eye Glow',(.05,.67,.93),.25)
    for name,(parent,start,end) in bones.items():
        if name=='root':continue
        center=(Vector(start)+Vector(end))/2
        length=(Vector(end)-Vector(start)).length
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=center)
        part=bpy.context.object
        part.name='BODY_'+name
        thickness=.23 if name=='torso' else (.25 if name=='head' else .12)
        if name=='pelvis':thickness=.24
        part.scale=(thickness,thickness,max(length*.65,.1))
        # Geometric object remains volumetric and is rigidly parented to one real articulated bone.
        part.data.materials.append(enamel if name in ('torso','pelvis','head') else (pale if name.endswith('forearm') else dark))
        original=part.matrix_world.copy()
        part.parent=arm;part.parent_type='BONE';part.parent_bone=name
        part.matrix_world=original
    # Expression markers are geometry parented to head, not an image billboard.
    for sign in (-1,1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(.115*sign,-.206,1.78))
        eye=bpy.context.object;eye.name=f'Eye_{sign}'
        eye.scale=(.055,.025,.05);eye.data.materials.append(gold)
        original=eye.matrix_world.copy();eye.parent=arm;eye.parent_type='BONE';eye.parent_bone='head';eye.matrix_world=original
    # A purpose-built asymmetric performance, not synchronized sine-wave bobbing.
    tracks={
      'torso':[(0,0),(8,-.12),(17,-.05),(24,.19),(32,.12),(46,-.13),(59,.02)],
      'head':[(0,0),(8,-.25),(17,.42),(24,.16),(32,-.2),(46,-.45),(59,.15)],
      'left_upper_arm':[(0,0),(8,.02),(17,.52),(24,.91),(32,.44),(46,-.12),(59,.14)],
      'left_forearm':[(0,0),(8,.13),(17,.11),(24,-.64),(32,-.57),(46,.05),(59,.20)],
      'right_upper_arm':[(0,0),(8,.12),(17,-.25),(24,.05),(32,-.68),(46,-.29),(59,.04)],
      'right_forearm':[(0,0),(8,-.04),(17,-.18),(24,-.11),(32,.71),(46,.29),(59,.03)],
      'left_thigh':[(0,0),(8,.07),(17,-.18),(24,-.3),(32,.12),(46,.16),(59,0)],
      'right_thigh':[(0,0),(8,-.08),(17,.12),(24,.31),(32,-.05),(46,-.07),(59,0)],
      'neck':[(0,0),(8,.03),(17,-.14),(24,.14),(32,.17),(46,-.09),(59,.04)]
    }
    for name,points in tracks.items():
        pb=arm.pose.bones[name];pb.rotation_mode='QUATERNION'
        for f,angle in points:
            pb.rotation_quaternion=Euler((0,angle,0),'XYZ').to_quaternion()
            pb.keyframe_insert('rotation_quaternion',frame=f)
    def camera(name,loc,lens):
        data=bpy.data.cameras.new(name)
        obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
        obj.location=loc;direction=Vector((0,0,.7))-obj.location
        obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
        obj.data.lens=lens
        return obj
    scene=bpy.context.scene
    scene.camera=camera('Camera_Setup',(3,-6,2.9),50)
    camera('Camera_Payoff',(-3.4,-5.2,2.5),65)
    bpy.ops.mesh.primitive_cube_add(size=2,location=(0,0,-1.12))
    floor=bpy.context.object;floor.name='Stage Floor';floor.scale=(8,8,.1)
    floor.data.materials.append(dark)
    for name,loc,energy,color in [('Key',(2,-3,5),900,(.95,.69,.62)),('Rim',(-3,2,3.5),1100,(.34,.69,1.0))]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=energy;ld.color=color;ld.shape='DISK';ld.size=3
        light=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(light);light.location=loc
        light.rotation_euler=(Vector((0,0,.7))-light.location).to_track_quat('-Z','Y').to_euler()
    engines=bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
    for engine in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
        if engine in engines:
            scene.render.engine=engine;break
    scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
    scene.render.fps=30;scene.frame_start=0;scene.frame_end=59
    destination.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    print('CODEVIDEO_DEMO_SOURCE='+str(destination),flush=True)

if __name__=='__main__':main()
