"""Create empty honest projects; compute conservative production status."""
from __future__ import annotations
from pathlib import Path
from .common import inside, slug, load_json, save_json, sha256, result
from .contracts import validate_graph
from .rig_proof import validate_rig_proof
from .verify_mp4 import verify_mp4
from .preflight import preflight

def create_project(root:Path,name:str)->dict:
    name=slug(name)
    home=inside(root,Path('projects')/name)
    if home.exists():return result('BLOCKED',error='Project already exists; no overwrite performed',path=str(home))
    home.mkdir(parents=True)
    (home/'scenes').mkdir()
    graph={'format':'codevideo.shotgraph.v1','title':name,'scene':f'projects/{name}/scenes/puppet.blend',
           'audio':None,'subtitles':False,'fps':30,'width':1920,'height':1080,
           'shots':[{'id':'setup','start':0,'end':29,'purpose':'Establish the setting and intention',
                     'emotion':'curiosity','performance':'Four independently articulated non-root joints with clear anticipation',
                     'camera':'Camera_Setup','lens_mm':50,'lighting':'Motivated key and rim lights',
                     'continuity':'Character and props enter from known positions',
                     'visibility':'Complete silhouette and readable joint performance'},
                    {'id':'payoff','start':30,'end':59,'purpose':'Complete the decisive action and emotional payoff',
                     'emotion':'resolve','performance':'Character reacts with distinct head, torso, arm, leg and hand timing',
                     'camera':'Camera_Payoff','lens_mm':65,'lighting':'Motivated continuity from setup',
                     'continuity':'Maintain eyeline, screen direction and prop ownership',
                     'visibility':'Clear physical impact and articulated reaction'}]}
    path=home/'film.json'
    save_json(path,graph)
    (home/'README.txt').write_text('Template only. Replace the missing puppet.blend with a real, skin/rig-certified Blender scene; align timeline to supplied audio. Nothing here is a finished film.\n',encoding='utf-8')
    return result('TEMPLATE_CREATED_UNVALIDATED',project=str(home),graph=str(path))

def production_status(root:Path,graph_path:str,proof_path:str|None=None,video_path:str|None=None)->dict:
    health=preflight(root)
    gates={'G0_ENVIRONMENT':health['status'], 'G1_IDENTITY':'NOT_APPLICABLE_UNLESS_CANON',
           'G2_RIG':'UNKNOWN','G3_ARTICULATION':'UNKNOWN','G4_ACTING':'UNVERIFIED',
           'G5_TIMELINE':'UNKNOWN','G6_ENCODE':'UNKNOWN','G7_VISUAL_QA':'UNVERIFIED',
           'G8_ACCESS':'UNVERIFIED'}
    graph=load_json(inside(root,graph_path,must_exist=True))
    timeline=validate_graph(graph,root=root)
    gates['G5_TIMELINE']='PASS' if timeline['status']=='PASS' else 'FAIL'
    rig=None
    if proof_path:
        rig=validate_rig_proof(load_json(inside(root,proof_path,must_exist=True)),root=root)
        gates['G2_RIG']=rig['status'];gates['G3_ARTICULATION']=rig['status']
    video=None
    if video_path:
        video=verify_mp4(root,video_path,graph_path,deep=True)
        gates['G6_ENCODE']=video['status']
    # Independent visual review and user access cannot be certified from metadata.
    overall='PARTIAL' if any(v=='PASS' for v in gates.values()) else 'BLOCKED'
    if video and video['status']=='PASS' and rig and rig['status']=='PASS' and timeline['status']=='PASS':
        # An arbitrary visually unrelated, decodable MP4 is not a product of the gated pipeline.
        delivery=inside(root,video_path,must_exist=True)
        receipt=delivery.with_suffix('.receipt.json')
        if receipt.is_file():
            r=load_json(receipt)
            if r.get('format')=='codevideo.delivery.v1' and r.get('sha256')==sha256(delivery):
                overall='TECHNICAL_PASS_VISUAL_PENDING'
    return {'status':overall,'gates':gates,'timeline':timeline,'rig':rig,
            'video':video,'note':'FINISHED_VERIFIED intentionally requires independently witnessed shot review and accessible-link proof.'}


def create_demo_project(root:Path,name:str)->dict:
    """Create a genuine bone-parented 3D mechanical puppet sample when Blender exists."""
    import shutil, subprocess
    if not shutil.which('blender'):
        return result('BLOCKED',error='Blender not installed: actual 3D sample cannot be built')
    project=create_project(root,name)
    if project['status']!='TEMPLATE_CREATED_UNVALIDATED':return project
    scene=Path(project['project'])/'scenes'/'puppet.blend'
    script=Path(__file__).resolve().parent.parent/'blender'/'create_demo_puppet.py'
    try:
        p=subprocess.run([shutil.which('blender'),'--background','--factory-startup','--disable-autoexec',
                          '--python',str(script),'--','--out',str(scene)],
                          capture_output=True,text=True,timeout=120)
        if p.returncode:return result('PARTIAL',project=project['project'],error='Demo rig build failed',stderr=p.stderr[-1600:])
        return result('DEMO_RIG_CREATED_UNVERIFIED',project=project['project'],scene=str(scene),
                      note='Run rig-proof and render gates; this is a mechanical demonstration, not a final film.')
    except (OSError,subprocess.TimeoutExpired) as exc:
        return result('PARTIAL',project=project['project'],error=str(exc))
