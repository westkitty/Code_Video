"""Negative-control tests for the portable actual glTF skeletal rig bridge."""
import json,struct,copy
from pathlib import Path
import numpy as np
import pytest
from codevideo.portable_rig import (
  build_glb,verify_glb_bytes,parse_glb,read_accessor,export_reach,check_export,uv_sphere)
from codevideo.golden_reach import default_spec

@pytest.fixture(scope='module')
def valid():
    return build_glb(default_spec())[0]


def replace_json(data,fn):
    doc,raw=parse_glb(data);fn(doc)
    part=json.dumps(doc,separators=(',',':')).encode('utf8');part+=b' '*((-len(part))%4)
    size=12+8+len(part)+8+len(raw)
    return b'glTF'+struct.pack('<II',2,size)+struct.pack('<I4s',len(part),b'JSON')+part+struct.pack('<I4s',len(raw),b'BIN\0')+raw


def replace_buffer(data,fn):
    doc,raw=parse_glb(data);bb=bytearray(raw);fn(doc,bb)
    length=struct.unpack_from('<I',data,12)[0];prefix=data[:20+length+8]
    return bytes(prefix)+bytes(bb)


def test_four_real_skins_animated_geometry_and_every_frame(valid):
    report=verify_glb_bytes(valid)
    assert report['skin_count']==4
    assert report['animated_joints']>=8
    assert report['total_joint_animation_channels']>=16
    assert report['samples_per_channel']==289
    assert all(m['frames_checked']==289 and m['animated_deformation_range_m']>.005 for m in report['meshes'])
    assert report['max_skinning_error_m']<1e-5
    assert report['blender_import']=='UNVERIFIED'


def test_standalone_loader_can_parse_meshes(valid,tmp_path):
    trimesh=pytest.importorskip('trimesh')
    path=tmp_path/'actor.glb';path.write_bytes(valid)
    scene=trimesh.load(str(path),force='scene')
    assert len(scene.geometry)>=10
    assert len(scene.graph.nodes_geometry)>=10


def test_export_receipt_matches_bytes_and_refuses_overwrite(tmp_path):
    root=tmp_path
    r=export_reach(root,'staged_actor'); assert r['status']=='PASS'
    assert Path(r['asset']).is_file()
    assert check_export(root,r['receipt'])['status']=='PASS'
    assert export_reach(root,'staged_actor')['status']=='BLOCKED'
    with open(r['asset'],'r+b') as fh:
        fh.seek(-10,2);b=fh.read(1);fh.seek(-10,2);fh.write(bytes([b[0]^0x20]))
    assert check_export(root,r['receipt'])['status']=='FAIL'


def test_export_refuses_escape_path(tmp_path):
    with pytest.raises(ValueError):export_reach(tmp_path,'../escape')


def test_invalid_spec_rejected_without_project_creation(tmp_path):
    spec=default_spec();spec['tracks']['right_hand_x'][0][1]=300
    p=tmp_path/'invalid.json';p.write_text(json.dumps(spec))
    assert export_reach(tmp_path,'wrong','invalid.json')['status']=='BLOCKED'
    assert not (tmp_path/'portable_rigs'/'wrong').exists()


def test_glb_missing_skin_is_rejected(valid):
    def mut(doc):doc['skins'].pop()
    with pytest.raises(ValueError,match='skin'):verify_glb_bytes(replace_json(valid,mut))


def test_glb_bad_axis_root_is_rejected(valid):
    def mut(doc):doc['nodes'][0]['rotation']=[0,0,0,1]
    with pytest.raises(ValueError,match='Coordinate'):verify_glb_bytes(replace_json(valid,mut))


def test_glb_orphaned_bone_is_rejected(valid):
    def mut(doc):
        n=doc['skins'][0]['joints'][0]
        doc['nodes'][n]['children']=[]
    with pytest.raises(ValueError,match='hierarchy'):verify_glb_bytes(replace_json(valid,mut))


def test_glb_wrong_weights_rejected(valid):
    def mut(doc,bb):
        mesh=doc['meshes'][0]['primitives'][0]
        a=doc['accessors'][mesh['attributes']['WEIGHTS_0']]
        view=doc['bufferViews'][a['bufferView']]
        struct.pack_into('<f',bb,view['byteOffset'],.12)
    with pytest.raises(ValueError,match='weights|Rest'):verify_glb_bytes(replace_buffer(valid,mut))


def test_glb_edited_joint_keyframe_rejected(valid):
    def mut(doc,bb):
        ani=doc['animations'][0]
        c=next(c for c in ani['channels'] if c['target']['path']=='rotation')
        a=doc['accessors'][ani['samplers'][c['sampler']]['output']]
        view=doc['bufferViews'][a['bufferView']]
        struct.pack_into('<4f',bb,view['byteOffset']+96*4*4,0.,0.,0.,1.)
    with pytest.raises(ValueError,match='GLB skin mismatch|quaternion'):verify_glb_bytes(replace_buffer(valid,mut))


def test_glb_edited_mesh_coordinates_rejected(valid):
    def mut(doc,bb):
        mesh=doc['meshes'][0]['primitives'][0]
        a=doc['accessors'][mesh['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
        struct.pack_into('<f',bb,v['byteOffset'],10.)
    with pytest.raises(ValueError,match='Rest geometry'):verify_glb_bytes(replace_buffer(valid,mut))


def test_glb_prop_contact_drift_rejected(valid):
    def mut(doc,bb):
        ani=doc['animations'][0]
        c=next(c for c in ani['channels'] if doc['nodes'][c['target']['node']]['name'].startswith('Orb_'))
        a=doc['accessors'][ani['samplers'][c['sampler']]['output']];v=doc['bufferViews'][a['bufferView']]
        struct.pack_into('<f',bb,v['byteOffset']+223*3*4,16.)
    with pytest.raises(ValueError,match='Prop contact drift'):verify_glb_bytes(replace_buffer(valid,mut))


def test_non_degenerate_display_mesh():
    verts,faces=uv_sphere(.2,.3,.5)
    e1=verts[faces[:,1]]-verts[faces[:,0]];e2=verts[faces[:,2]]-verts[faces[:,0]]
    assert float(np.min(np.linalg.norm(np.cross(e1,e2),axis=1)))>1e-6


def test_gltf_animation_has_keyframes_and_no_subtitles(valid):
    doc,bb=parse_glb(valid)
    assert doc['asset']['extras']['subtitles'] is False
    assert doc['asset']['extras']['certificate'].startswith('PORTABLE_SKINNED_ASSET_ONLY')
    assert doc['animations'][0]['channels']
    assert len(doc['skins'])==4
    for n in [n for n in doc['nodes'] if 'skin' in n]:
        p=doc['meshes'][n['mesh']]['primitives'][0]
        assert 'WEIGHTS_0' in p['attributes'] and 'JOINTS_0' in p['attributes']


def test_native_blender_bridge_is_honestly_blocked_without_binary(tmp_path,monkeypatch,valid):
    from codevideo.blender_bridge import import_rig
    import shutil
    monkeypatch.setattr(shutil,'which',lambda name: None if name=='blender' else '/usr/bin/true')
    p=tmp_path/'actor.glb';p.write_bytes(valid)
    r=import_rig(tmp_path,str(p),'host_import')
    assert r['status']=='BLOCKED' and r['gate']=='BLENDER'
    assert not (tmp_path/'portable_imports'/'host_import').exists()


def test_fabricated_blender_import_receipt_is_rejected(tmp_path,valid):
    from codevideo.blender_bridge import check_import
    p=tmp_path/'actor.glb';p.write_bytes(valid)
    fake=tmp_path/'fake.blend';fake.write_bytes(b'not a real blend')
    d=tmp_path/'fake.json'
    from codevideo.common import sha256
    d.write_text(json.dumps({'format':'codevideo.blender-import-proof.v1','origin':'actual-blender-runtime',
        'source_glb':str(p),'source_glb_sha256':sha256(p),'native_blend':str(fake),
        'native_blend_sha256':sha256(fake),'armature_count':99,'deform_mesh_count':99,
        'moving_nonroot_joints':[1,2,3,4], 'moving_deform_meshes':[1,2,3,4],
        'sample_frames':[1,2,3,4,5],'fixed_camera':'fake','diagnostic_images':{}}))
    r=check_import(tmp_path,str(d))
    assert r['status']=='FAIL' and 'unsigned' in r['error'].lower()


def test_blender_import_worker_has_bpy_and_genuine_evaluation():
    from pathlib import Path
    worker=Path(__file__).resolve().parents[1]/'blender'/'import_portable_rig.py'
    compile(worker.read_text(),str(worker),'exec')
    s=worker.read_text()
    assert 'bpy.ops.import_scene.gltf' in s
    assert 'evaluated_get' in s and 'to_mesh' in s
    assert 'bpy.ops.render.render' in s
