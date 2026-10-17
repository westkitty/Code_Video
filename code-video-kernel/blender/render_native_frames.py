"""Run ONLY inside Blender after a verified GLB import.

This is a render worker, never a proof or certificate. Its caller must hash and
verify every output and inspect the decoded MP4. No subtitles or audio added.
"""
import bpy
import hashlib
import json
import sys
from pathlib import Path

SHOTS = {'recognition': (1, 96, 'CodeVideo_Shot_01'),
         'struggle': (97, 192, 'CodeVideo_Shot_02'),
         'resolution': (193, 288, 'CodeVideo_Shot_03')}


def args():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    flags = {}
    for key in ('--shot', '--out', '--width', '--height', '--samples', '--blend-sha'):
        if key not in a or a.index(key) + 1 >= len(a):
            raise ValueError('Missing required flag ' + key)
        flags[key] = a[a.index(key) + 1]
    flags['probe'] = '--probe' in a
    return flags


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fd:
        for chunk in iter(lambda: fd.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    f = args()
    shot = f['--shot']
    if shot not in SHOTS:
        raise ValueError('Unknown shot')
    start, end, camera_name = SHOTS[shot]
    output = Path(f['--out']).resolve()
    if not output.is_dir() or list(output.iterdir()):
        raise ValueError('Output directory must exist and be empty')
    width = int(f['--width']); height = int(f['--height'])
    samples = int(f['--samples'])
    if width < 320 or width > 1920 or height < 180 or height > 1080 or width % 2 or height % 2:
        raise ValueError('Unsupported frame dimensions')
    if samples < 4 or samples > 64:
        raise ValueError('Unsupported sample count')
    scene = bpy.context.scene
    if scene.get('CODEVIDEO_IMPORTED_SOURCE_SHA256') is None:
        raise ValueError('Not a Code Video import scene')
    if scene.frame_end < 288:
        raise ValueError('Missing required actor timeline')
    camera = bpy.data.objects.get(camera_name)
    if not camera or camera.type != 'CAMERA':
        raise ValueError('Missing verified shot camera: ' + camera_name)
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.render.film_transparent = False
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    image_hashes = {}
    active_frames = [int((start + end) // 2)] if f['probe'] else range(start, end + 1)
    for frame in active_frames:
        scene.frame_set(frame)
        path = output / ('frame_%06d.png' % frame)
        if path.exists():
            raise ValueError('Refusing to reuse unsigned output frame')
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        if not path.is_file() or path.stat().st_size < 500:
            raise ValueError('Render frame missing or implausibly small: ' + str(path))
        image_hashes[path.name] = sha256(path)
    receipt = {'format': 'codevideo.blender-native-shot.worker.v1',
               'source_glb_sha256': scene['CODEVIDEO_IMPORTED_SOURCE_SHA256'],
               'scene_render_engine': scene.render.engine,
               'frame_range_inclusive': [start, end], 'shot': shot,
               'camera': camera_name, 'fps': 24, 'width': width, 'height': height,
               'samples': samples, 'image_hashes': image_hashes,
               'blend_sha256_expected': f['--blend-sha'],
               'status': 'PROBE_UNSIGNED' if f['probe'] else 'RENDERED_UNSIGNED_AWAITING_HOST_VALIDATION'}
    (output / 'blender_worker_frames.json').write_text(json.dumps(receipt, indent=2), encoding='utf8')
    print('CODEVIDEO_NATIVE_SHOT_RENDERED=' + shot, flush=True)


if __name__ == '__main__':
    main()
