"""No fake capability claims: inspect executables, media and free space."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import json, shutil, subprocess, os
from .common import inside, sha256

def probe_media(path: Path, *, ffprobe: str | None = None) -> dict:
    ffprobe=ffprobe or shutil.which('ffprobe')
    if not ffprobe:
        return {'status':'BLOCKED','error':'ffprobe not found'}
    try:
        p=subprocess.run([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,timeout=35)
        if p.returncode: return {'status':'FAIL','error':p.stderr[-1500:]}
        info=json.loads(p.stdout)
        return {'status':'PASS','source':str(path),'sha256':sha256(path),'size':path.stat().st_size,
                'duration_s':float(info.get('format',{}).get('duration') or 0),
                'streams':[{'type':s.get('codec_type'),'codec':s.get('codec_name'),
                            'width':s.get('width'),'height':s.get('height'),'sample_rate':s.get('sample_rate')}
                           for s in info.get('streams',[])]}
    except (subprocess.TimeoutExpired,OSError,ValueError) as exc:
        return {'status':'FAIL','error':str(exc)}

def preflight(root: Path, media: str | None = None) -> dict:
    found={name:shutil.which(name) for name in ('python3','blender','ffmpeg','ffprobe')}
    vtk_available=importlib.util.find_spec('vtk') is not None
    disk=shutil.disk_usage(root)
    report={'status':'PASS' if all(found.values()) else 'PARTIAL',
            'vtk_segmented_demo_available':vtk_available,
            'workspace':str(root), 'tools':{k:{'available':bool(v),'path':v} for k,v in found.items()},
            'disk_free_bytes':disk.free,'disk_total_bytes':disk.total,
            'note':'MCP support requires optional official mcp SDK; tools report capability only, not render proof.'}
    if media:
        try:
            candidate=inside(root,media,must_exist=True)
            report['media']=probe_media(candidate)
        except (ValueError,OSError) as exc:
            report['media']={'status':'BLOCKED','error':str(exc)}
    return report
