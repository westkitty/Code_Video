"""Fail-closed native-Blender GLB import gate. Does not claim PASS without bpy."""
from pathlib import Path
import shutil,subprocess,json
from .common import inside,slug,sha256,load_json,result
from .portable_rig import verify_glb_bytes
from .rig_proof import authentic,attest
from .common import save_json


def check_import(root,proof_path,*,_unsigned_after_real_execution=False):
    try:
        proof=load_json(inside(root,proof_path,must_exist=True))
        if proof.get('format')!='codevideo.blender-import-proof.v1' or proof.get('origin')!='actual-blender-runtime':
            return result('FAIL',error='Wrong Blender proof origin')
        if not _unsigned_after_real_execution and not authentic(proof,root):
            return result('FAIL',error='Blender execution receipt is unsigned or has invalid local attestation')
        source=inside(root,proof['source_glb'],must_exist=True)
        scene=inside(root,proof['native_blend'],must_exist=True)
        if sha256(source)!=proof['source_glb_sha256'] or sha256(scene)!=proof['native_blend_sha256']:
            return result('FAIL',error='Source or native Blender scene drift')
        if scene.suffix.lower()!='.blend' or scene.stat().st_size<1024 or scene.open('rb').read(7)!=b'BLENDER':
            return result('FAIL',error='Missing genuine native Blender scene bytes')
        verify_glb_bytes(source.read_bytes())
        if proof.get('armature_count',0)<1 or proof.get('deform_mesh_count',0)<4:
            return result('FAIL',error='Missing real Blender deformers')
        if len(proof.get('moving_nonroot_joints',[]))<4 or len(proof.get('moving_deform_meshes',[]))<4:
            return result('FAIL',error='Insufficient live Blender evaluated movement')
        required_frames=[1,49,97,145,193,225,289]
        if proof.get('sample_frames')!=required_frames or not proof.get('fixed_camera'):
            return result('FAIL',error='Missing complete fixed-camera diagnostic frame contract')
        required_pngs={f'pose_{i:04d}.png' for i in required_frames}
        if set(proof.get('diagnostic_images',{}))!=required_pngs:
            return result('FAIL',error='Exact seven diagnostic images required')
        for name,h in proof['diagnostic_images'].items():
            if Path(name).name!=name or not name.endswith('.png'):
                return result('FAIL',error='Unsafe diagnostic image name')
            p=inside(root,Path(proof_path).parent/name,must_exist=True)
            if sha256(p)!=h:return result('FAIL',error='Diagnostic frame altered: '+name)
            if p.stat().st_size<500 or p.open('rb').read(8)!=b'\x89PNG\r\n\x1a\n':
                return result('FAIL',error='Not an actual diagnostic PNG: '+name)
        return result('PASS',classification='BLENDER_IMPORT_TECHNICAL_PASS_VISUAL_PENDING',
                      armatures=proof['armature_count'],deformed_meshes=len(proof['moving_deform_meshes']),
                      nonroot_joints=len(proof['moving_nonroot_joints']),native_blend=str(scene))
    except (KeyError,OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        return result('FAIL',error=str(exc))


def blender_executable():
    override = __import__('os').environ.get('CODEVIDEO_BLENDER', '').strip()
    if override:
        candidate=Path(override).expanduser()
        return str(candidate) if candidate.is_absolute() and candidate.is_file() and __import__('os').access(candidate,__import__('os').X_OK) else None
    command=shutil.which('blender')
    if command:return command
    app=Path('/Applications/Blender.app/Contents/MacOS/Blender')
    return str(app) if app.is_file() and __import__('os').access(app,__import__('os').X_OK) else None


def import_rig(root,glb_path,asset_id):
    blender=blender_executable()
    if not blender:return result('BLOCKED',gate='BLENDER',error='No Blender executable found; actual native armature import remains unverified')
    try:
        source=inside(root,glb_path,must_exist=True)
        if source.suffix.lower()!='.glb':return result('BLOCKED',error='Not a GLB input')
        verify_glb_bytes(source.read_bytes())
        target=inside(root,Path('portable_imports')/slug(asset_id))
        if target.exists():return result('BLOCKED',error='Import output ID exists; original preserved')
        target.mkdir(parents=True,exist_ok=False)
        script=Path(__file__).resolve().parent.parent/'blender'/'import_portable_rig.py'
        cmd=[blender,'--background','--factory-startup','--disable-autoexec','--python',str(script),'--','--glb',str(source),'--out',str(target)]
        run=subprocess.run(cmd,text=True,capture_output=True,timeout=900)
        (target/'blender_import.log').write_text((run.stdout[-12000:]+'\n'+run.stderr[-12000:]),encoding='utf8')
        if run.returncode:return result('FAIL',error='Actual Blender import or render failed',log=str(target/'blender_import.log'))
        proof=target/'blender_import_proof.json'
        if not proof.exists():return result('FAIL',error='Blender did not emit proof',log=str(target/'blender_import.log'))
        checked=check_import(root,str(proof),_unsigned_after_real_execution=True)
        if checked['status']!='PASS':return {**checked,'log':str(target/'blender_import.log')}
        save_json(proof,attest(load_json(proof),root))
        checked=check_import(root,str(proof))
        return {**checked,'proof':str(proof),'log':str(target/'blender_import.log')}
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:
        return result('FAIL',error=str(e))
