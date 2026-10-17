"""Reject paper rigs and synchronized cosmetic oscillations. Run Blender to gather proof."""
from __future__ import annotations
import json, math, shutil, subprocess, hmac, hashlib, os, secrets
from pathlib import Path
from .common import GateError, inside, load_json, save_json, sha256, stable_hash, result

def _attestation_key(root:Path,create:bool=False)->bytes|None:
    """Local runtime secret; deliberately excluded from distributable evidence."""
    secret=root/'.codevideo'/'proof-key'
    if create:
        secret.parent.mkdir(mode=0o700,exist_ok=True)
        if not secret.exists():
            fd=os.open(str(secret),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as f:f.write(secrets.token_bytes(32))
    if not secret.exists():return None
    return secret.read_bytes()

def attest(proof:dict,root:Path)->dict:
    key=_attestation_key(root,create=True)
    body={k:v for k,v in proof.items() if k!='attestation'}
    sig=hmac.new(key,stable_hash(body).encode(),hashlib.sha256).hexdigest()
    return {**body,'attestation':{'algorithm':'hmac-sha256','signature':sig}}

def authentic(proof:dict,root:Path)->bool:
    key=_attestation_key(root)
    if not key:return False
    signature=proof.get('attestation',{}).get('signature','')
    if not isinstance(signature,str):return False
    body={k:v for k,v in proof.items() if k!='attestation'}
    target=hmac.new(key,stable_hash(body).encode(),hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature,target)

FORMAT = 'codevideo.rigproof.v1'

def _angle(q0, q1):
    dot=sum(float(a)*float(b) for a,b in zip(q0,q1))
    return 2*math.acos(max(0.0,min(1.0,abs(dot))))

def _curve(bone):
    samples=bone.get('samples',[])
    if len(samples)<5: return None
    try:
        quats=[p['quaternion'] for p in samples]
        if any(len(q)!=4 or any(not math.isfinite(float(v)) for v in q) or abs(sum(float(v)**2 for v in q)-1.0)>0.08 for q in quats):return None
        base=quats[0]
        return [_angle(base,q) for q in quats]
    except (TypeError,KeyError,ValueError,OverflowError):
        return None

def validate_rig_proof(proof:dict, *, root:Path | None=None, allow_fixture:bool=False) ->dict:
    errors=[]
    if proof.get('format')!=FORMAT: errors.append('wrong proof format')
    if proof.get('origin')!='blender-evaluated-v1':
        if not (allow_fixture and proof.get('origin')=='test-fixture'):
            errors.append('origin must be direct Blender-evaluated evidence')
    scene=proof.get('scene',{})
    if not isinstance(scene,dict): scene={}
    if root and not allow_fixture:
        if not authentic(proof,root):errors.append('missing or invalid locally signed Blender probe attestation')
        try:
            src=inside(root,scene['path'],must_exist=True)
            if not src.name.endswith('.blend') or sha256(src)!=scene.get('sha256'):
                errors.append('scene file/hash mismatch: rig evidence is stale')
        except (KeyError,GateError,OSError):
            errors.append('source .blend missing, inaccessible or outside workspace')
    bones=proof.get('bones',[])
    if not isinstance(bones,list) or not bones: bones=[]; errors.append('no armature bones')
    names={b.get('name') for b in bones if isinstance(b,dict)}
    if len(names)!=len(bones): errors.append('bone names must be distinct')
    roots=[b for b in bones if isinstance(b,dict) and b.get('parent') is None]
    if not roots: errors.append('no root bone')
    # Reject missing/cyclic parent chains even when a disconnected root is present.
    parents={b.get('name'):b.get('parent') for b in bones if isinstance(b,dict)}
    for name in parents:
        seen=set(); current=name
        while current is not None and current in parents:
            if current in seen:
                errors.append(f'{name}: cyclic bone ancestry')
                break
            seen.add(current); current=parents[current]
    frames=proof.get('sample_frames')
    if (not isinstance(frames,list) or len(frames)<5 or len(frames)!=len(set(map(str,frames)))
            or any(type(f) is not int or f<0 for f in frames)):
        errors.append('need >=5 unique, valid diagnostic frames')
        frames=[]
    for b in bones:
        if not isinstance(b,dict):continue
        samples=b.get('samples',[])
        if not isinstance(samples,list) or [p.get('frame') for p in samples if isinstance(p,dict)]!=frames:
            errors.append(f"{b.get('name')}: sample frame mapping differs from manifest")
    moving=[]
    signatures=set()
    for b in bones:
        if not isinstance(b,dict):continue
        if b.get('parent') is not None and b.get('parent') not in names:
            errors.append(f"{b.get('name')}: missing parent")
        if b.get('parent') is None: continue
        curve=_curve(b)
        if curve is None:continue
        if max(curve)<0.11:continue  # actual anatomical motion, not float noise
        # Unique temporal envelopes: scaling a universal sine wave doesn't count as independent acting.
        peak=max(curve)
        normalized=tuple(round(x/peak,1) for x in curve)
        if normalized in signatures:continue
        signatures.add(normalized)
        moving.append({'name':b.get('name'), 'max_angle_radians':round(peak,3)})
    if len(moving)<4: errors.append(f'only {len(moving)} meaningfully independent non-root joints (need >=4)')
    meshes=proof.get('meshes',[])
    if not isinstance(meshes,list) or not meshes:meshes=[]; errors.append('no rigged volumetric meshes')
    kind=proof.get('anatomy','organic')
    if kind not in ('organic','segmented'):errors.append('anatomy must be organic or segmented')
    total_verts=sum(max(0,int(m.get('vertices',0))) for m in meshes if isinstance(m,dict))
    weighted=sum(max(0,int(m.get('weighted_vertices',0))) for m in meshes if isinstance(m,dict))
    max_deformation=max((float(m.get('max_deformation',0)) for m in meshes if isinstance(m,dict)),default=0)
    deformed=sum(max(0,int(m.get('deformed_vertices',0))) for m in meshes if isinstance(m,dict))
    rigid_bound=sum(int(bool(m.get('bone_parented'))) for m in meshes if isinstance(m,dict))
    if total_verts<24:errors.append('insufficient real mesh geometry')
    # Every counted joint must influence real geometry, not merely move in a report.
    visible=[]
    for moving_joint in moving:
        name=moving_joint['name']
        if any((m.get('bone_parent')==name if kind=='segmented' else m.get('influences',{}).get(name,0)>=3) for m in meshes if isinstance(m,dict)):
            visible.append(name)
    if len(visible)<4:
        errors.append(f'only {len(visible)} independently moving joints influence real mesh geometry (need >=4)')
    if kind=='organic':
        if weighted/max(1,total_verts)<0.65:errors.append('organic mesh has insufficient skinned vertices')
        if max_deformation<0.005 or deformed<6:errors.append('no convincing evaluated skin deformation')
        for m in meshes:
            if not isinstance(m,dict):continue
            if m.get('weighted_vertices',0)>0 and float(m.get('max_weight_error',0))>0.12:
                errors.append(f"{m.get('name')}: invalid normalized weights")
    elif rigid_bound<1:
        errors.append('segmented rig lacks bone-parented mesh segments')
    return {'status':'PASS' if not errors else 'FAIL','errors':errors,'independent_joints':moving,
            'independent_count':len(moving),'geometry_driving_joints':visible,'mesh_count':len(meshes),'vertices':total_verts,
            'max_deformation':max_deformation,'deformed_vertices':deformed,
            'evidence_origin':proof.get('origin'),'scene_sha256':scene.get('sha256')}

def probe_blend(root:Path, blend:str, frames:list[int], anatomy:str='organic') ->dict:
    """Run real Blender evaluation. A fabricated manifest never substitutes for this call."""
    blender=shutil.which('blender')
    if not blender: return result('BLOCKED',error='Blender executable unavailable; rig cannot be certified')
    source=inside(root,blend,must_exist=True)
    if source.suffix.lower()!='.blend':return result('BLOCKED',error='Source must be a .blend')
    if anatomy not in ('organic','segmented'):return result('FAIL',error='Unsupported anatomy')
    if len(frames)<5 or len(frames)>120 or any(type(i)!=int or i<0 or i>1000000 for i in frames):
        return result('FAIL',error='Provide 5-120 distinct, nonnegative diagnostic frames')
    frames=sorted(set(frames))
    if len(frames)<5:return result('FAIL',error='Need >=5 distinct frames')
    destination=inside(root,Path('proof')/(source.stem+'-'+sha256(source)[:12]+'.json'))
    script=Path(__file__).resolve().parent.parent/'blender'/'probe_rig.py'
    args=[blender,'--background','--disable-autoexec',str(source),'--python',str(script),'--','--out',str(destination),
          '--frames',','.join(map(str,frames)),'--anatomy',anatomy]
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=180)
        if p.returncode:return result('FAIL',error='Blender rig probe failed',stderr=p.stderr[-2200:],stdout=p.stdout[-600:])
        proof=load_json(destination)
        if proof.get('scene',{}).get('sha256')!=sha256(source):return result('FAIL',error='Blender output source mismatch')
        proof=attest(proof,root)
        save_json(destination,proof)
        checked=validate_rig_proof(proof,root=root)
        return {**checked,'proof_file':str(destination)}
    except (OSError,subprocess.TimeoutExpired,ValueError) as exc:
        return result('FAIL',error=str(exc))
