"""Shot graph and project contract validation. No implicit storyboard invention."""
from __future__ import annotations
from .common import GateError, inside, load_json
from pathlib import Path
import math

SHOT_FIELDS = ('id', 'start', 'end', 'purpose', 'emotion', 'performance',
               'camera', 'lens_mm', 'lighting', 'continuity', 'visibility')

def _positive(x):
    return isinstance(x, (int,float)) and not isinstance(x,bool) and math.isfinite(x) and x > 0

def validate_graph(graph: dict, *, root: Path | None = None) -> dict:
    errors = []
    if graph.get('format') != 'codevideo.shotgraph.v1':
        errors.append('format must be codevideo.shotgraph.v1')
    for key in ('title','scene','shots'):
        if key not in graph:
            errors.append(f'missing {key}')
    fps=graph.get('fps')
    if not isinstance(graph.get('title'),str) or not graph['title'].strip(): errors.append('title must be a nonempty string')
    if not isinstance(graph.get('scene'),str) or not graph['scene'].lower().endswith('.blend'):
        errors.append('scene must be a .blend path string')
    width=graph.get('width')
    height=graph.get('height')
    if type(fps) is not int or not 1 <= fps <= 120: errors.append('fps must be an integer from 1 to 120')
    if not isinstance(width,int) or isinstance(width,bool) or width < 64 or width > 8192 or width%2: errors.append('width must be even, 64-8192')
    if not isinstance(height,int) or isinstance(height,bool) or height < 64 or height > 8192 or height%2: errors.append('height must be even, 64-8192')
    shots=graph.get('shots',[])
    if not isinstance(shots,list) or not shots:
        errors.append('shots must be nonempty list')
        shots=[]
    prev_end = -1
    ids = set()
    for i,s in enumerate(shots):
        if not isinstance(s,dict):
            errors.append(f'shot {i} must be object')
            continue
        for field in SHOT_FIELDS:
            value=s.get(field)
            if value is None or (isinstance(value,str) and not value.strip()):
                errors.append(f'shot {i}: missing {field}')
        name=s.get('id')
        if not isinstance(name,str) or not name.isascii() or not name.replace('-','').replace('_','').isalnum():
            errors.append(f'shot {i}: invalid id')
        elif name in ids:
            errors.append(f'shot {i}: duplicate id')
        ids.add(name)
        start=s.get('start'); end=s.get('end')
        if type(start) is not int or type(end) is not int or start < 0 or end < start:
            errors.append(f'shot {i}: invalid frame range')
        elif start != prev_end+1:
            errors.append(f'shot {i}: frame gap or overlap (expected start {prev_end+1})')
        if type(end) is int and end>=0: prev_end=end
        if not _positive(s.get('lens_mm')) or s['lens_mm']>500:
            errors.append(f'shot {i}: invalid lens_mm')
        for f in ('purpose','emotion','performance','camera','lighting','continuity','visibility'):
            if not isinstance(s.get(f),str) or not s.get(f,'').strip():
                errors.append(f'shot {i}: invalid {f}')
    if prev_end > 500000:
        errors.append('film exceeds 500,001 frames; split into projects')
    scene=graph.get('scene')
    if root and isinstance(scene,str):
        try:
            scene_path=inside(root,scene,must_exist=True)
            if scene_path.suffix.lower() != '.blend': errors.append('scene must be .blend')
        except (ValueError,OSError) as exc: errors.append(f'scene unavailable: {exc}')
    audio=graph.get('audio')
    if audio is not None:
        if not isinstance(audio,str) or not audio:
            errors.append('audio must be non-empty workspace path or null')
        elif root:
            try: inside(root,audio,must_exist=True)
            except (ValueError,OSError) as exc: errors.append(f'audio unavailable: {exc}')
    if graph.get('subtitles',False) is not False:
        errors.append('default contract disallows subtitles; configure explicit separate opt-in')
    return {'status':'PASS' if not errors else 'FAIL','errors':errors,
            'total_frames':max(0,prev_end+1),'duration_s':round((prev_end+1)/fps,4) if type(fps) is int and 1 <= fps <= 120 else None,
            'shot_count':len(shots)}

def inspect_graph(graph_path: Path, root: Path) -> dict:
    graph=load_json(graph_path)
    return validate_graph(graph,root=root)
