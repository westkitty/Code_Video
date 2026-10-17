"""Portable glTF 2.0 rig: four true skinned meshes, anatomical joint hierarchies,
12-second keyframe animation, head/jaw and world-space prop transfer.

This is NOT a Blender execution proof. It supplies an editable standards-based
interchange asset that must be imported and tested on a Blender-equipped host.
"""
from __future__ import annotations
import json, math, struct, hashlib
from pathlib import Path
import numpy as np
from .actor_engine import skinned_tube, weighted_lbs
from .golden_reach import default_spec, evaluate, validate_spec, FPS, DURATION
from .common import inside, slug, save_json, load_json, sha256, result

GLB_HEADER = b'glTF'
F32=5126
U16=5123
U32=5125


def quat_normalize(q):
    a=np.asarray(q,dtype=float)
    n=float(np.linalg.norm(a))
    if n < 1e-10 or not np.isfinite(n): raise ValueError('Invalid quaternion')
    return a/n


def quat_from_to(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
    c=np.cross(a,b);d=float(np.dot(a,b))
    if d < -0.999999:
        cross=np.cross(a,[1,0,0]);
        if np.linalg.norm(cross)<1e-6:cross=np.cross(a,[0,1,0])
        return quat_normalize([*cross,0])
    return quat_normalize([*c,1+d])


def quat_mul(a,b):
    x,y,z,w=a;u,v,s,t=b
    return np.array([w*u+x*t+y*s-z*v,w*v-x*s+y*t+z*u,w*s+x*v-y*u+z*t,w*t-x*u-y*v-z*s],float)


def quat_matrix(q):
    x,y,z,w=quat_normalize(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),0],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),0],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y),0],
                     [0,0,0,1]],dtype=float)


def T(p):
    m=np.eye(4);m[:3,3]=np.asarray(p,float);return m


def triangulate(faces):
    tris=[]
    for face in faces:
        for j in range(1,len(face)-1):tris.append([face[0],face[j],face[j+1]])
    return np.asarray(tris,dtype=np.uint32)


def vertex_normals(vertices,tris):
    v=np.asarray(vertices,float); f=np.asarray(tris,np.int64)
    normals=np.zeros_like(v)
    face_normals=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    for k in range(3):np.add.at(normals,f[:,k],face_normals)
    size=np.linalg.norm(normals,axis=1)
    normals/=np.maximum(size[:,None],1e-8)
    return normals.astype(np.float32)


def uv_sphere(rx,ry,rz,lat=14,lon=22):
    """Closed, nondegenerate triangulated ellipsoid (single polar vertices)."""
    if min(rx,ry,rz)<=0 or lat<4 or lon<6:raise ValueError('Invalid sphere')
    verts=[[0,0,rz]]
    for j in range(1,lat):
        theta=math.pi*j/lat
        for k in range(lon):
            phi=2*math.pi*k/lon
            verts.append([rx*math.sin(theta)*math.cos(phi),ry*math.sin(theta)*math.sin(phi),rz*math.cos(theta)])
    south=len(verts);verts.append([0,0,-rz]);tris=[]
    for k in range(lon):tris.append([0,1+k,1+(k+1)%lon])
    for j in range(lat-2):
        for k in range(lon):
            a=1+j*lon+k;b=1+j*lon+(k+1)%lon
            c=1+(j+1)*lon+k;d=1+(j+1)*lon+(k+1)%lon
            tris.extend([[a,c,b],[b,c,d]])
    last=1+(lat-2)*lon
    for k in range(lon):tris.append([south,last+(k+1)%lon,last+k])
    return np.asarray(verts,np.float32),np.asarray(tris,np.uint32)


class GLBWriter:
    def __init__(self):
        self.data={'asset':{'version':'2.0','generator':'Code Video Portable Rig 0.3.1'},'scene':0,
          'scenes':[{'nodes':[]}], 'nodes':[], 'meshes':[], 'skins':[], 'materials':[],
          'accessors':[], 'bufferViews':[], 'buffers':[{'byteLength':0}], 'animations':[]}
        self.raw=bytearray()
    def add_accessor(self, arr, kind, component, target=None, bounds=False):
        dt={F32:np.float32,U16:np.uint16,U32:np.uint32}[component]
        arr=np.ascontiguousarray(arr,dtype=dt)
        while len(self.raw)%4:self.raw.extend(b'\0')
        offset=len(self.raw);bb=arr.tobytes(order='C');self.raw.extend(bb)
        view={'buffer':0,'byteOffset':offset,'byteLength':len(bb)}
        if target is not None:view['target']=target
        vi=len(self.data['bufferViews']);self.data['bufferViews'].append(view)
        count=int(arr.shape[0]);a={'bufferView':vi,'componentType':component,'count':count,'type':kind}
        if bounds:
            r=arr.reshape(count,-1);a['min']=r.min(axis=0).tolist();a['max']=r.max(axis=0).tolist()
        idx=len(self.data['accessors']);self.data['accessors'].append(a);return idx
    def node(self,name,parent=None,**props):
        d={'name':name,**props};n=len(self.data['nodes']);self.data['nodes'].append(d)
        if parent is None:self.data['scenes'][0]['nodes'].append(n)
        else:self.data['nodes'][parent].setdefault('children',[]).append(n)
        return n
    def material(self,name,color,metallic=.15,emissive=None):
        mat={'name':name,'pbrMetallicRoughness':{'baseColorFactor':[float(c) for c in color]+[1.],
             'metallicFactor':metallic,'roughnessFactor':.45},'doubleSided':True}
        if emissive:mat['emissiveFactor']=list(emissive)
        idx=len(self.data['materials']);self.data['materials'].append(mat);return idx
    def mesh(self,name,verts,faces,material,weights=None,skin_indices=None):
        verts=np.asarray(verts,dtype=np.float32);faces=np.asarray(faces,dtype=np.uint32)
        attr={'POSITION':self.add_accessor(verts,'VEC3',F32,target=34962,bounds=True),
              'NORMAL':self.add_accessor(vertex_normals(verts,faces),'VEC3',F32,target=34962)}
        if weights is not None:
            weights=np.asarray(weights,dtype=np.float32)
            if weights.shape!=(len(verts),2):raise ValueError('Incorrect skin weights')
            if not np.allclose(weights.sum(axis=1),1,atol=1e-6):raise ValueError('Unnormalized weights')
            attr['JOINTS_0']=self.add_accessor(np.tile(np.array([[0,1,0,0]],np.uint16),(len(verts),1)), 'VEC4',U16,target=34962)
            attr['WEIGHTS_0']=self.add_accessor(np.c_[weights,np.zeros((len(verts),2),np.float32)],'VEC4',F32,target=34962)
        primitive={'attributes':attr,'indices':self.add_accessor(faces.reshape(-1),'SCALAR',U32,target=34963),'mode':4,'material':material}
        n=len(self.data['meshes']);self.data['meshes'].append({'name':name,'primitives':[primitive]});return n
    def animation(self, times, tracks):
        tacc=self.add_accessor(np.asarray(times,np.float32),'SCALAR',F32,bounds=True)
        ani={'name':'THE_REACH_ACTOR_12s_24fps','samplers':[], 'channels':[]}
        for node,path,values in tracks:
            typ='VEC4' if path=='rotation' else 'VEC3'
            v=np.asarray(values,np.float32)
            if len(v)!=len(times):raise ValueError('Mismatched track count')
            acc=self.add_accessor(v,typ,F32)
            idx=len(ani['samplers']);ani['samplers'].append({'input':tacc,'output':acc,'interpolation':'LINEAR'})
            ani['channels'].append({'sampler':idx,'target':{'node':node,'path':path}})
        self.data['animations'].append(ani)
    def encode(self):
        while len(self.raw)%4:self.raw.extend(b'\0')
        self.data['buffers'][0]['byteLength']=len(self.raw)
        src=json.dumps(self.data,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('utf8')
        src+=b' '*((-len(src))%4)
        whole=12+8+len(src)+8+len(self.raw)
        return b'glTF'+struct.pack('<II',2,whole)+struct.pack('<I4s',len(src),b'JSON')+src+struct.pack('<I4s',len(self.raw),b'BIN\0')+self.raw


def build_glb(spec):
    validate_spec(spec)
    writer=GLBWriter()
    # Film coordinates are Z-up, glTF is conventionally Y-up. Parent root rotates once.
    rotate=[-math.sqrt(.5),0,0,math.sqrt(.5)]
    space=writer.node('Cinder_RigSpace_Zup_to_Yup',rotation=rotate,extras={'coordinate_system':'source Z-up; exported scene Y-up'})
    colors={'enamel':writer.material('Red enamel',(.52,.04,.07),.3),
            'ivory':writer.material('Porcelain',(.72,.81,.84),.1),
            'black':writer.material('Graphite',(.035,.05,.08),.3),
            'copper':writer.material('Copper',(.64,.37,.13),.6),
            'orb':writer.material('Ion core',(.02,.78,.83),.1,(.02,.6,.65))}
    times=np.arange(289,dtype=np.float32)/FPS
    samples=[evaluate(float(t),spec) for t in times]
    rest_records=[];tracks=[];meshes_meta=[]
    base=samples[0]
    for side,which,color,radius in [('right','arm','enamel',.17),('left','arm','ivory',.15),('right','leg','black',.195),('left','leg','black',.195)]:
        names=(f'{side}_upper',f'{side}_lower') if which=='arm' else (f'{side}_thigh',f'{side}_shin')
        a,b=base['bones'][names[0]];_,c=base['bones'][names[1]]
        upper=float(np.linalg.norm(b-a));lower=float(np.linalg.norm(c-b))
        bind_a=np.array([float(a[0]),0,float(a[2])]);bind_b=bind_a+np.array([0,0,-upper]);bind_c=bind_b+np.array([0,0,-lower])
        verts,w,faces=skinned_tube(bind_a,bind_b,bind_c,sections=29,sides=16,radius=radius)
        triangles=triangulate(faces)
        up_idx=writer.node(f'{side}_{which}_upper_bone',parent=space,translation=bind_a.tolist())
        lo_idx=writer.node(f'{side}_{which}_lower_bone',parent=up_idx,translation=[0,0,-upper])
        mat=np.stack([np.linalg.inv(T(bind_a)).flatten(order='F'),np.linalg.inv(T(bind_b)).flatten(order='F')]).astype(np.float32)
        imb=writer.add_accessor(mat,'MAT4',F32)
        skin_id=len(writer.data['skins']);writer.data['skins'].append({'name':f'{side}_{which}_skinning', 'joints':[up_idx,lo_idx],
                                                'skeleton':up_idx,'inverseBindMatrices':imb})
        mesh_id=writer.mesh(f'{side}_{which}_continuous_skin',verts,triangles,colors[color],weights=w)
        writer.node(f'{side}_{which}_SKINNED_MESH',parent=space,mesh=mesh_id,skin=skin_id)
        q_upper=[];q_lower=[];position=[]
        for s in samples:
            ap,bp=s['bones'][names[0]];_,cp=s['bones'][names[1]]
            q1=quat_from_to([0,0,-1],bp-ap);q2=quat_from_to([0,0,-1],cp-bp)
            local=quat_mul(q1*np.array([-1,-1,-1,1]),q2)
            q_upper.append(q1);q_lower.append(quat_normalize(local));position.append(ap)
        tracks.extend([(up_idx,'translation',position),(up_idx,'rotation',q_upper),(lo_idx,'rotation',q_lower)])
        # Hand or foot rigid volume is attached to the animated distal joint end.
        end=writer.mesh(f'{side}_{which}_end',*uv_sphere(.16 if which=='arm' else .24,.16 if which=='arm' else .3,.16 if which=='arm' else .11),colors['copper' if which=='arm' else 'ivory'])
        writer.node(f'{side}_{which}_effector',parent=lo_idx,translation=[0,0,-lower],mesh=end)
        rest_records.append({'id':f'{side}_{which}','upper':up_idx,'lower':lo_idx,'skin':skin_id,
                             'bind_a':bind_a.tolist(),'bind_b':bind_b.tolist(),'bind_c':bind_c.tolist(),
                             'bones':list(names),'upper_length':upper,'lower_length':lower,'mesh':mesh_id})
        meshes_meta.append({'name':f'{side}_{which}','vertices':len(verts),'faces':len(triangles),'weights_normalized':True})
    # Torso and head are rigid puppet volumes, driven by their own transform channels.
    torso_mesh=writer.mesh('Torso',*uv_sphere(.48,.34,.55),colors['enamel'])
    torso=writer.node('Cinder_Chest_Joint',parent=space,mesh=torso_mesh)
    tracks.append((torso,'translation',[(p['root']+p['chest'])*.5 for p in samples]))
    head_mesh=writer.mesh('Head',*uv_sphere(.33,.28,.34),colors['ivory'])
    head=writer.node('Cinder_Head_Joint',parent=space,mesh=head_mesh)
    tracks.append((head,'translation',[p['head'] for p in samples]))
    tracks.append((head,'rotation',[[0,0,math.sin(math.radians(p['head_turn'])/2),math.cos(math.radians(p['head_turn'])/2)] for p in samples]))
    for sign in [-1,1]:
        eye_mesh=writer.mesh(f'Eye_{sign}',*uv_sphere(.065,.039,.075),colors['orb'])
        writer.node(f'Eye_{sign}_HeadParent',parent=head,translation=[sign*.13,-.28,.04],mesh=eye_mesh)
    jaw_mesh=writer.mesh('Jaw',*uv_sphere(.21,.09,.06),colors['copper'])
    jaw=writer.node('Cinder_Jaw_Joint',parent=head,translation=[0,-.25,-.22],mesh=jaw_mesh)
    tracks.append((jaw,'translation',[[0,-.25,-.22-.0035*p['jaw']] for p in samples]))
    orb_mesh=writer.mesh('Orb',*uv_sphere(.18,.18,.18),colors['orb'])
    orb=writer.node('Orb_World_To_Hand_At_9p3s',parent=space,mesh=orb_mesh,
                    extras={'contact_event_second':9.3,'owner_before':'world','owner_after':'right_hand'})
    tracks.append((orb,'translation',[p['orb'] for p in samples]))
    writer.animation(times,tracks)
    writer.data['asset']['extras']={'name':'THE REACH','fps':FPS,'frame_count':288,'timeline_seconds':DURATION,
        'source_format':spec['format'],'skin_kind':'actual glTF JOINTS_0/WEIGHTS_0, not vertex cache',
        'certificate':'PORTABLE_SKINNED_ASSET_ONLY; BLENDER_IMPORT_UNVERIFIED; FILM_NOT_INCLUDED',
        'ownership_transition_s':spec['events']['grip_s'],'subtitles':False}
    return writer.encode(),rest_records,meshes_meta


def parse_glb(data:bytes):
    if len(data)<28 or data[:4]!=GLB_HEADER:raise ValueError('Invalid GLB header')
    ver,size=struct.unpack_from('<II',data,4)
    if ver!=2 or size!=len(data):raise ValueError('GLB version/length mismatch')
    n,typ=struct.unpack_from('<I4s',data,12)
    if typ!=b'JSON' or n%4 or n<=0:raise ValueError('Invalid GLB JSON chunk')
    doc=json.loads(data[20:20+n]);p=20+n
    bsize,btype=struct.unpack_from('<I4s',data,p)
    if btype!=b'BIN\0' or bsize%4 or p+8+bsize!=len(data):raise ValueError('Invalid GLB BIN chunk')
    buf=data[p+8:]
    if doc['buffers'][0]['byteLength']!=len(buf):raise ValueError('Bad buffer size')
    return doc,buf


def read_accessor(doc,buf,index):
    a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
    typ=a['type'];count=a['count'];fmt={F32:'<f4',U16:'<u2',U32:'<u4'}[a['componentType']]
    cols={'SCALAR':1,'VEC3':3,'VEC4':4,'MAT4':16}[typ]
    ofs=int(view.get('byteOffset',0))+int(a.get('byteOffset',0));length=count*cols*np.dtype(fmt).itemsize
    if ofs<0 or length>view['byteLength'] or ofs+length>len(buf):raise ValueError('Accessor bounds exceeded')
    return np.frombuffer(buf,dtype=fmt,count=count*cols,offset=ofs).reshape((count,cols))


def verify_glb_bytes(data:bytes,spec=None, *, tolerance=2e-4):
    spec=spec or default_spec();validate_spec(spec)
    doc,buf=parse_glb(data)
    if doc['asset']['version']!='2.0' or len(doc['skins'])!=4:raise ValueError('Wrong glTF skin contract')
    if len(doc['animations'])!=1:raise ValueError('Missing skeletal animation')
    space=next((n for n in doc['nodes'] if n.get('name')=='Cinder_RigSpace_Zup_to_Yup'),None)
    if space is None or not np.allclose(space.get('rotation',[]),[-math.sqrt(.5),0,0,math.sqrt(.5)],atol=1e-5):
        raise ValueError('Coordinate-conversion root missing or invalid')
    ani=doc['animations'][0];nodes=doc['nodes']
    channels={(c['target']['node'],c['target']['path']):read_accessor(doc,buf,ani['samplers'][c['sampler']]['output']) for c in ani['channels']}
    times=read_accessor(doc,buf,ani['samplers'][0]['input']).ravel()
    if len(times)!=289 or not np.allclose(times,np.arange(289)/FPS,rtol=0,atol=1e-6):raise ValueError('Incorrect animation timing')
    records=[];largest=0;lowest_motion=math.inf
    for skin in doc['skins']:
        names=skin['name'].split('_');side,which=names[0],names[1]
        pair=(f'{side}_upper',f'{side}_lower') if which=='arm' else (f'{side}_thigh',f'{side}_shin')
        meshnode=next(n for n in nodes if 'skin' in n and doc['skins'][n['skin']] is skin)
        prim=doc['meshes'][meshnode['mesh']]['primitives'][0]
        attrib=prim['attributes'];v=read_accessor(doc,buf,attrib['POSITION']);w=read_accessor(doc,buf,attrib['WEIGHTS_0']);js=read_accessor(doc,buf,attrib['JOINTS_0'])
        if v.shape[1]!=3 or w.shape[1]!=4 or js.shape[1]!=4:raise ValueError('Malformed vertex skin data')
        if (js[:,0]!=0).any() or (js[:,1]!=1).any() or (js[:,2:]!=0).any() or np.min(w)<-1e-7 or not np.allclose(w.sum(axis=1),1,atol=1e-5):
            raise ValueError('Bad joint indices or normalized weights')
        joint1,joint2=skin['joints'];nb1,nb2=nodes[joint1],nodes[joint2]
        if joint2 not in nb1.get('children',[]):raise ValueError('Broken joint hierarchy')
        bind=read_accessor(doc,buf,skin['inverseBindMatrices'])
        if bind.shape!=(2,16):raise ValueError('Bad inverse-bind matrices')
        bind1=np.asarray(bind[0].reshape((4,4),order='F'));bind2=np.asarray(bind[1].reshape((4,4),order='F'))
        initial=evaluate(0,spec);oldA,oldB=initial['bones'][pair[0]];_,oldC=initial['bones'][pair[1]]
        ua=float(np.linalg.norm(oldB-oldA));lo=float(np.linalg.norm(oldC-oldB))
        ra=np.array([oldA[0],0,oldA[2]]);rb=ra+[0,0,-ua];rc=rb+[0,0,-lo]
        if not np.allclose(bind1,np.linalg.inv(T(ra)),atol=3e-5) or not np.allclose(bind2,np.linalg.inv(T(rb)),atol=3e-5):
            raise ValueError('Invalid inverse bind transform')
        radius=.17 if side=='right' and which=='arm' else .15 if which=='arm' else .195
        expected_rest, expected_weights, expected_faces=skinned_tube(ra,rb,rc,sections=29,sides=16,radius=radius)
        if not np.allclose(v,expected_rest,rtol=0,atol=1e-5) or not np.allclose(w[:,:2],expected_weights,rtol=0,atol=1e-6):
            raise ValueError('Rest geometry or weights do not match the authored puppet')
        if not np.array_equal(read_accessor(doc,buf,prim['indices']).ravel(),triangulate(expected_faces).ravel()):
            raise ValueError('Triangle topology does not match authored puppet')
        dist=[]
        for fi in range(289):
            p=evaluate(fi/FPS,spec);newA,newB=p['bones'][pair[0]];_,newC=p['bones'][pair[1]]
            qu=channels.get((joint1,'rotation'));ql=channels.get((joint2,'rotation'));tr=channels.get((joint1,'translation'))
            if qu is None or ql is None or tr is None:raise ValueError('Missing joint animation')
            if not np.isclose(np.linalg.norm(qu[fi]),1,atol=2e-5) or not np.isclose(np.linalg.norm(ql[fi]),1,atol=2e-5):
                raise ValueError('Invalid animated quaternion')
            upper=T(tr[fi]) @ quat_matrix(qu[fi]);lower=upper @ T([0,0,-ua]) @ quat_matrix(ql[fi]);
            r=np.c_[v,np.ones(len(v))]
            moved=((r@(upper@bind1).T)[:,:3]*w[:,0,None]+(r@(lower@bind2).T)[:,:3]*w[:,1,None])
            expected=weighted_lbs(v,w[:,:2],[(ra,rb,newA,newB),(rb,rc,newB,newC)])
            err=float(np.max(np.linalg.norm(moved-expected,axis=1)));largest=max(largest,err)
            if err>tolerance:raise ValueError(f'GLB skin mismatch {side} {which} frame {fi}: {err:.7f}')
            dist.append(float(np.linalg.norm(moved-v,axis=1).max()))
        motion=max(dist)-min(dist)
        if motion<.005:raise ValueError('Skin has no animated deformation')
        for joint in (joint1,joint2):
            q=channels[(joint,'rotation')]
            if np.min(np.sum(q[:-1]*q[1:],axis=1))<0:
                raise ValueError('Quaternion sign flip would cause false motion')
        lowest_motion=min(lowest_motion,motion)
        records.append({'skin':skin['name'],'vertices':len(v),'frames_checked':289,'max_skinning_error_m':max(largest,0.),'animated_deformation_range_m':motion})
    for key in ['Cinder_Head_Joint','Cinder_Chest_Joint','Cinder_Jaw_Joint','Orb_World_To_Hand_At_9p3s']:
        ix=next((i for i,n in enumerate(nodes) if n['name']==key),None)
        if ix is None or not any(target==ix for target,path in channels):raise ValueError('Missing actor channel: '+key)
    orbnode=next((i for i,n in enumerate(nodes) if n['name']=='Orb_World_To_Hand_At_9p3s'),None)
    if orbnode is None or (orbnode,'translation') not in channels:raise ValueError('Missing prop animation')
    orb_track=channels[(orbnode,'translation')]
    for fi in range(289):
        pose=evaluate(fi/FPS,spec)
        if np.linalg.norm(orb_track[fi]-pose['orb'])>2e-5:raise ValueError('Prop contact drift in GLB')
    return {'status':'PASS','format':'codevideo.portable-rig-proof.v1','skin_count':len(records),
            'animated_joints':len({node for node,path in channels if path=='rotation'}),
            'total_joint_animation_channels':len(channels),'samples_per_channel':len(times),
            'max_skinning_error_m':largest,'meshes':records,
            'blender_import':'UNVERIFIED','mp4_film':'NOT_INCLUDED'}


def export_reach(root:Path,name:str,spec_path:str|None=None):
    from .common import GateError
    project=inside(root,Path('portable_rigs')/slug(name))
    if project.exists():return result('BLOCKED',error='Asset ID exists; preserving original release')
    spec=load_json(inside(root,spec_path,must_exist=True)) if spec_path else default_spec()
    try:
        data,_,_=build_glb(spec); report=verify_glb_bytes(data,spec)
    except (ValueError,KeyError,TypeError,IndexError) as e:
        return result('BLOCKED',error='Portable rig proof failed: '+str(e))
    project.mkdir(parents=True,exist_ok=False)
    (project/'the_reach_skeletal_animated.glb').write_bytes(data)
    save_json(project/'film.json',spec)
    proof={**report,'format':'codevideo.portable-rig-receipt.v1',
           'proof_format':report['format'],'spec_sha256':sha256(project/'film.json'),
           'glb_sha256':sha256(project/'the_reach_skeletal_animated.glb')}
    save_json(project/'portable_rig_receipt.json',proof)
    return {**report,'classification':'PORTABLE_RIG_VERIFIED_BLENDER_UNVERIFIED',
            'asset':str(project/'the_reach_skeletal_animated.glb'),'receipt':str(project/'portable_rig_receipt.json')}


def check_export(root:Path,receipt_path:str):
    p=inside(root,receipt_path,must_exist=True);rec=load_json(p); base=p.parent
    if rec.get('format')!='codevideo.portable-rig-receipt.v1':return result('FAIL',error='Incorrect receipt format')
    scene=base/'film.json';model=base/'the_reach_skeletal_animated.glb'
    if not scene.is_file() or not model.is_file():return result('FAIL',error='Asset missing')
    if sha256(scene)!=rec['spec_sha256'] or sha256(model)!=rec['glb_sha256']:
        return result('FAIL',error='Source or portable rig altered')
    try:
        report=verify_glb_bytes(model.read_bytes(),load_json(scene))
    except (ValueError,KeyError,TypeError,IndexError) as e:return result('FAIL',error=str(e))
    if report['skin_count']!=rec.get('skin_count') or report['max_skinning_error_m']!=rec.get('max_skinning_error_m'):
        return result('FAIL',error='Proof mismatch')
    return {**report,'classification':'PORTABLE_RIG_VERIFIED_BLENDER_UNVERIFIED'}
