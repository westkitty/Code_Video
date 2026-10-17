"""Blender child process: render explicit absolute timestamps without scene mutation."""
import bpy, sys, json, os, struct, uuid
from pathlib import Path

def main():
    a=sys.argv[sys.argv.index('--')+1:]
    recipe=json.loads(Path(a[a.index('--recipe')+1]).read_text(encoding='utf-8'))
    scene=bpy.context.scene
    if not bpy.data.filepath or not Path(bpy.data.filepath).exists():raise ValueError('Scene not saved')
    cam=bpy.data.objects.get(recipe['camera'])
    if not cam or cam.type!='CAMERA':raise ValueError('Required Blender camera not found: '+recipe['camera'])
    scene.camera=cam
    scene.render.resolution_x=recipe['width'];scene.render.resolution_y=recipe['height']
    scene.render.resolution_percentage=100
    scene.render.film_transparent=False
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.render.use_file_extension=True
    scene.render.fps=recipe['fps']
    for frame in recipe['frames']:
        scene.frame_set(frame)
        target=Path(recipe['output']) / f'{frame:06d}.png'
        target.parent.mkdir(parents=True,exist_ok=True)
        # Requested frames are intentionally rerendered. Reuse is decided by the
        # caller from signed per-frame SHA-256 evidence, never by a PNG header.
        if target.exists():
            quarantine=target.parent/'quarantine'
            quarantine.mkdir(exist_ok=True)
            os.replace(target,quarantine/(target.stem+'-'+uuid.uuid4().hex+'.png'))
        temp=target.with_suffix('.partial.png')
        scene.render.filepath=str(temp)
        bpy.ops.render.render(write_still=True)
        if not temp.exists() or temp.stat().st_size<32:
            raise IOError('Failed to render frame '+str(frame))
        os.replace(temp,target)
        print('CODEVIDEO_FRAME='+str(target),flush=True)

if __name__=='__main__':main()
