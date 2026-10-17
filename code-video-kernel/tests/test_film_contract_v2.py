import copy, json
from pathlib import Path
import pytest
from codevideo.film_contract import load_film, preflight_film

def make(tmp):
    p=tmp/'puppet.blend';p.write_bytes(b'BLENDER'+b'\x00'*1500)
    return {'format':'codevideo.film.v2','film_id':'my_film','fps':24,'width':640,'height':360,'duration_frames':48,
            'actors':[{'id':'puppet','asset':'puppet.blend','canon':'NONCANONICAL'}],
            'shots':[{'id':'one','start':1,'end':24,'camera':'Camera-A','actors':['puppet'],
                      'purpose':'Notice the orb','emotion':'curiosity','performance':'Head turn','continuity':'Object on right'},
                     {'id':'two','start':25,'end':48,'camera':'Camera-B','actors':['puppet'],
                      'purpose':'Reach for orb','emotion':'frustration','performance':'Arm reaches','continuity':'Object on right'}],
            'events':[{'frame':33,'type':'grasp','actor':'puppet','prop':'orb'}], 'subtitles':False}

def test_generic_production_contract_passes_and_is_explicitly_not_a_render(tmp_path):
    doc=make(tmp_path); a=preflight_film(tmp_path,doc)
    assert a['status']=='PASS' and a['classification'].endswith('NOT_RENDERED')
    assert a['frames']==48 and len(a['shots'])==2 and a['audio'] is None

def test_invalid_population_or_timing_fails_closed(tmp_path):
    doc=make(tmp_path)
    for mutation in [lambda d: d['actors'].append(d['actors'][0]),
                     lambda d: d['shots'][1].update(start=24),
                     lambda d: d['shots'][0].update(end=23),
                     lambda d: d['shots'][1].update(actors=['ghost']),
                     lambda d: d.update(subtitles=True),
                     lambda d: d['actors'][0].update(canon='CANON_VERIFIED'),
                     lambda d: d['events'][0].update(frame=999),
                     lambda d: d['actors'][0].update(asset='../puppet.blend')]:
        bad=copy.deepcopy(doc);mutation(bad)
        assert preflight_film(tmp_path,bad)['status']=='BLOCKED'

def test_asset_hash_change_fails(tmp_path):
    doc=make(tmp_path);doc['actors'][0]['sha256']='0'*64
    assert preflight_film(tmp_path,doc)['status']=='BLOCKED'

def test_writing_spec_and_preflight(tmp_path):
    doc=make(tmp_path);p=tmp_path/'film.json';p.write_text(json.dumps(doc))
    assert preflight_film(tmp_path,'film.json')['status']=='PASS'
