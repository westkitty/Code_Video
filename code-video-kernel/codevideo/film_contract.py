"""Source-bound actor/prop/audio/shot contract for films beyond The Reach.

Only planning/preflight: a valid film contract is NEVER evidence that a renderer
has completed or visually verified its performance.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib, json, math, re
from .common import inside, result, sha256

ID = re.compile(r'^[a-z][a-z0-9_-]{0,47}$')
ALLOWED_ACTOR_FORMATS = {'.glb', '.blend'}

@dataclass(frozen=True)
class FilmContract:
    film_id: str
    fps: int
    width: int
    height: int
    duration_frames: int
    actors: tuple[dict,...]
    shots: tuple[dict,...]
    events: tuple[dict,...]
    audio: dict|None
    soundtrack_required: bool
    subtitles: bool

    @property
    def duration_s(self): return self.duration_frames/self.fps

    @property
    def hash(self):
        content={k:getattr(self,k) for k in self.__dataclass_fields__ if k!='soundtrack_required'}
        return hashlib.sha256(json.dumps(content,sort_keys=True,default=list,separators=(',',':')).encode()).hexdigest()


def _file_source(root, asset, field):
    if not isinstance(asset,str) or not asset or '\x00' in asset or '://' in asset:
        raise ValueError(f'{field}: local asset path required')
    p=inside(root,asset,must_exist=True)
    if not p.is_file() or p.stat().st_size<64: raise ValueError(f'{field}: invalid file')
    return p


def load_film(root:Path,source:dict|str|Path):
    """Fail closed for invented cast, unspecified assets, missing shot coverage.

    No render, no network, no arbitrary code or subprocess execution.
    """
    if not isinstance(source,dict):
        p=inside(root,source,must_exist=True)
        if not p.is_file() or p.stat().st_size>512_000:raise ValueError('Invalid film contract file')
        source=json.loads(p.read_text(encoding='utf8'))
    if not isinstance(source,dict) or source.get('format')!='codevideo.film.v2':
        raise ValueError('Unsupported film contract format')
    film_id=source.get('film_id')
    if not isinstance(film_id,str) or not ID.fullmatch(film_id):raise ValueError('Invalid film id')
    fps=source.get('fps');width=source.get('width');height=source.get('height');frames=source.get('duration_frames')
    if type(fps)!=int or fps not in (24,25,30,60):raise ValueError('Supported FPS: 24,25,30,60')
    if type(width)!=int or type(height)!=int or width<320 or width>3840 or height<180 or height>2160 or width%2 or height%2:
        raise ValueError('Invalid dimensions')
    if type(frames)!=int or frames<fps or frames>fps*300:raise ValueError('Duration outside 1..300 seconds')
    cast=source.get('actors');shots=source.get('shots');events=source.get('events',[])
    if not isinstance(cast,list) or not 1<=len(cast)<=8:raise ValueError('Expected 1..8 actors')
    seen=set();actors=[]
    for idx,a in enumerate(cast):
        if not isinstance(a,dict) or not isinstance(a.get('id'),str) or not ID.fullmatch(a['id']) or a['id'] in seen:
            raise ValueError('Duplicate/invalid actor identifier')
        seen.add(a['id'])
        path=_file_source(root,a.get('asset'),f'actors[{idx}].asset')
        if path.suffix.lower() not in ALLOWED_ACTOR_FORMATS:raise ValueError('Actor must be a GLB or .blend')
        if path.suffix.lower()=='.glb':
            from .portable_rig import parse_glb
            parse_glb(path.read_bytes())  # parse structure; geometric proof is a separate gate
        if path.suffix.lower()=='.blend' and path.open('rb').read(7)!=b'BLENDER':
            raise ValueError('Not Blender scene bytes')
        expected=a.get('sha256')
        if expected and (not isinstance(expected,str) or expected!=sha256(path)):
            raise ValueError('Actor asset hash mismatch')
        if a.get('canon') not in (None,'NONCANONICAL','CANON_VERIFIED'):
            raise ValueError('Unknown canon status')
        if a.get('canon')=='CANON_VERIFIED' and not a.get('canon_receipt'):
            raise ValueError('Canonical actor requires independent approval receipt')
        actors.append({'id':a['id'],'asset':str(path),'sha256':sha256(path),
                       'canon':a.get('canon','NONCANONICAL'),'canon_receipt':a.get('canon_receipt')})
    if not isinstance(shots,list) or not shots or len(shots)>96:raise ValueError('Nonempty <=96 shots required')
    expected_start=1;shot_ids=set();normshots=[]
    for s in shots:
        if not isinstance(s,dict):raise ValueError('Invalid shot')
        name=s.get('id');start=s.get('start');end=s.get('end');cam=s.get('camera')
        if not isinstance(name,str) or not ID.fullmatch(name) or name in shot_ids:raise ValueError('Invalid shot id')
        if type(start)!=int or type(end)!=int or start!=expected_start or end<start or end>frames:
            raise ValueError('Shot gaps/overlaps or out-of-bounds frames')
        if not isinstance(cam,str) or not cam.strip():raise ValueError('Every shot needs an actual camera name')
        actors_in=s.get('actors')
        if not isinstance(actors_in,list) or not actors_in or len(set(actors_in))!=len(actors_in) or any(a not in seen for a in actors_in):
            raise ValueError('Shot must reference known actor(s)')
        for label in ('purpose','performance','emotion','continuity'):
            if not isinstance(s.get(label),str) or not s[label].strip():raise ValueError('Missing shot intent: '+label)
        normshots.append({k:s[k] for k in ('id','start','end','camera','actors','purpose','performance','emotion','continuity')})
        shot_ids.add(name);expected_start=end+1
    if expected_start!=frames+1:raise ValueError('Shots do not cover complete timeline')
    if not isinstance(events,list):raise ValueError('Events must be an array')
    normevents=[]
    for e in events:
        if not isinstance(e,dict) or type(e.get('frame'))!=int or not 1<=e['frame']<=frames:
            raise ValueError('Invalid prop event frame')
        if e.get('type') not in ('grasp','release','transfer','contact','notice'):
            raise ValueError('Unsupported event type')
        if e.get('actor') not in seen:raise ValueError('Event actor not in cast')
        if not isinstance(e.get('prop'),str) or not ID.fullmatch(e['prop']):raise ValueError('Invalid prop name')
        normevents.append(e)
    normevents=sorted(normevents,key=lambda e:e['frame'])
    audio=source.get('audio')
    if audio is not None:
        if not isinstance(audio,dict) or audio.get('kind') not in ('supplied','licensed'):
            raise ValueError('Audio source must be supplied or licensed')
        p=_file_source(root,audio.get('asset'),'audio.asset')
        if p.suffix.lower() not in ('.mp3','.wav','.flac','.m4a'):
            raise ValueError('Unsupported soundtrack file')
        if audio.get('sha256') and audio['sha256']!=sha256(p):
            raise ValueError('Audio source hash mismatch')
        audio={'asset':str(p),'sha256':sha256(p),'kind':audio['kind'],'verified_words':bool(audio.get('verified_words',False))}
    if source.get('subtitles',False) is not False:
        raise ValueError('Subtitles default OFF; explicit separate authorization required for enabled tracks')
    return FilmContract(film_id,fps,width,height,frames,tuple(actors),tuple(normshots),tuple(normevents),
                        audio,audio is not None,False)


def preflight_film(root:Path,source):
    try:
        f=load_film(root,source)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        return result('BLOCKED',error=str(exc))
    return result('PASS',classification='FILM_SOURCE_PREFLIGHT_ONLY_NOT_RENDERED',film_id=f.film_id,
                  fps=f.fps,dimensions=[f.width,f.height],duration_s=f.duration_s,frames=f.duration_frames,
                  actors=list(f.actors),shots=list(f.shots),events=list(f.events),audio=f.audio,
                  canon_gate='PENDING' if any(a['canon']=='CANON_VERIFIED' for a in f.actors) else 'NOT_APPLICABLE',
                  required_proofs=['ACTUAL_SKINNING','JOINT_MOTION','CONTACT','NATIVE_RENDER','ENCODED_DECODE','VISUAL_QA'],
                  contract_sha256=f.hash)
