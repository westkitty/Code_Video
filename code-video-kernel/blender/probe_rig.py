"""Executed ONLY by Blender. Report evaluated parent-relative bones and bound geometry."""
import bpy
import sys, json, hashlib, math
from pathlib import Path

def args():
    a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    def get(flag):
        ix=a.index(flag)
        return a[ix+1]
    return Path(get('--out')), [int(v) for v in get('--frames').split(',')], get('--anatomy')

def h(path):
    hh=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            hh.update(b)
    return hh.hexdigest()

def main():
    out, frames, anatomy = args()
    src=Path(bpy.data.filepath).resolve()
    if not src.is_file() or src.suffix!='.blend': raise ValueError('No saved .blend source')
    rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE' and o.pose and len(o.pose.bones)]
    if not rigs:raise ValueError('No actual armature found')
    if len(rigs)!=1:
        raise ValueError('Multiple armatures found: each main puppet requires separate verification; this kernel currently certifies one armature per scene')
    rig=rigs[0]
    bone_names=set(rig.pose.bones.keys())
    meshes=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        deform=any(m.type=='ARMATURE' and m.object==rig and m.show_render for m in o.modifiers)
        parented=o.parent==rig and o.parent_type=='BONE' and o.parent_bone in bone_names
        if not (deform or parented):continue
        count=len(o.data.vertices)
        weighted=0;max_error=0
        groups_by_id={g.index:g.name for g in o.vertex_groups if g.name in bone_names}
        influences={}
        if deform:
            for v in o.data.vertices:
                total=sum(g.weight for g in v.groups if g.group in groups_by_id)
                for g in v.groups:
                    if g.group in groups_by_id and g.weight>0.01:
                        name=groups_by_id[g.group]
                        influences[name]=influences.get(name,0)+1
                if total>1e-6:
                    weighted+=1
                    max_error=max(max_error,abs(1-total))
        meshes.append({'name':o.name,'vertices':count,'weighted_vertices':weighted,
            'max_weight_error':round(max_error,6),'bone_parented':parented,
            'bone_parent':o.parent_bone if parented else None,'influences':influences,
            'max_deformation':0.0,'deformed_vertices':0,'_object':o})
    if not meshes:raise ValueError('No skinned or bone-parented mesh objects')
    bones=[{'name':pb.name,'parent':pb.parent.name if pb.parent else None,'samples':[]} for pb in rig.pose.bones]
    base_geo={}
    for i,frame in enumerate(frames):
        bpy.context.scene.frame_set(frame)
        deps=bpy.context.evaluated_depsgraph_get()
        for record in bones:
            pb=rig.pose.bones[record['name']]
            local=pb.parent.matrix.inverted_safe() @ pb.matrix if pb.parent else pb.matrix
            q=local.to_quaternion().normalized()
            record['samples'].append({'frame':frame, 'quaternion':[round(float(x),8) for x in q]})
        for record in meshes:
            o=record['_object']
            ev=o.evaluated_get(deps)
            if record['bone_parented']:
                # Bone-parented rigid geometry does not deform, but follows its actual bone.
                m=ev.matrix_world
                loc=m.translation[:]
                if i==0: base_geo[o.name]=tuple(loc)
                else:
                    d=math.sqrt(sum((loc[j]-base_geo[o.name][j])**2 for j in range(3)))
                    record['max_deformation']=max(record['max_deformation'],float(d))
                    if d>0.004:record['deformed_vertices']=record['vertices']
            else:
                evaluated=ev.to_mesh()
                try:
                    # Local evaluated mesh coordinates expose actual skinning, excluding root world motion.
                    coords=[v.co[:] for v in evaluated.vertices]
                    if i==0:base_geo[o.name]=coords
                    else:
                        original=base_geo[o.name]
                        maximum=0; moved=0
                        for j,coord in enumerate(coords[:len(original)]):
                            d=math.sqrt(sum((coord[k]-original[j][k])**2 for k in range(3)))
                            maximum=max(maximum,d)
                            if d>0.005:moved+=1
                        record['max_deformation']=max(record['max_deformation'],maximum)
                        record['deformed_vertices']=max(record['deformed_vertices'],moved)
                finally:
                    ev.to_mesh_clear()
    for record in meshes:del record['_object']
    out.parent.mkdir(parents=True,exist_ok=True)
    obj={'format':'codevideo.rigproof.v1','origin':'blender-evaluated-v1','scene':{'path':str(src),'sha256':h(src)},
         'armature':rig.name,'anatomy':anatomy,'sample_frames':frames,'bones':bones,'meshes':meshes}
    out.write_text(json.dumps(obj,indent=2),encoding='utf-8')
    print('CODEVIDEO_RIG_PROOF='+str(out),flush=True)

if __name__=='__main__': main()
