"""Offline tests: no network or Home Assistant service calls."""
import json
import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import yaml
from jinja2.nativetypes import NativeEnvironment

cfg = yaml.safe_load(Path('bad_heizung_lernen.yaml').read_text())
seq = cfg['script']['bad_heizung_lernereignis']['sequence']
env = NativeEnvironment()
template = env.from_string(seq[1]['variables']['neues_model'])
tz = ZoneInfo('Europe/Berlin')

def run(model, hour=7, minute=0, event='check', manual=False,
        source=True, temp=22.5, mode='heat', target=22.5, external='on', **extra):
    dt = datetime(2026, 9, 29, hour, minute, tzinfo=tz)
    values = {'climate.heizkorper_bad_thermostat': mode,
              'switch.heizkorper_bad_externer_temperatursensor': external,
              'sensor.weather_station_bad_temperatur': str(temp)}
    result = template.render(model=model, ereignis=event, heute='2026-09-29',
        minute=hour*60+minute, zeit=int(dt.timestamp()), quelle_ok=source,
        manuell=manual, now=lambda:dt, states=lambda s:values.get(s,'unknown'),
        is_state=lambda s,v:values.get(s)==v, state_attr=lambda *a:target,
        as_timestamp=lambda t:t.timestamp(), today_at=lambda t:datetime.fromisoformat('2026-09-29T'+t).replace(tzinfo=tz),
        **extra)
    if isinstance(result,str):
        result=ast.literal_eval(result.strip())  # HA strips and parses template results.
    assert isinstance(result,dict), result
    assert len(json.dumps(result)) <= 255, result
    return result

start=run({},5,10,event='start',temp=22,starttemperatur=22,start_gueltig=True,vorlauf=60)
assert start['invalid'] is False and start['correction']==0
assert run(start,5,20,event='start')==start
reach=run(start,5,55,temp=22.5)
assert reach['reached']>0
done=run(reach)
assert done['result']=='unchanged' and done['samples']==1
assert run(done)==done  # exactly once per day
late=run(run(start,6,20))
assert late['correction']==5 and late['result']=='earlier'
early=run(run(start,5,40))
assert early['correction']==-5
never=run(start)
assert never['correction']==5
for kw in [dict(manual=True),dict(source=False),dict(mode='unavailable'),dict(mode='off'),dict(target=24),dict(external='off'),dict(event='restart')]:
    bad=run(start,5,30,**kw)
    assert bad['invalid'], kw
    skipped=run(bad)
    assert skipped['result']=='skipped' and skipped['correction']==0 and skipped['samples']==0
assert run(dict(start,lead=90))['correction']==0 # no integrator windup at earliest start
assert run(dict(start,correction=60))['correction']==60
assert run(dict(reach,correction=-30,reached=early['reached']))['correction']==-30
for temp in [22.5,24]:
    assert run({},5,event='start',starttemperatur=temp,start_gueltig=True,vorlauf=0)['invalid']
assert run({},6,event='start',starttemperatur=22,start_gueltig=True,vorlauf=60)['invalid']
assert run({},5,event='start',starttemperatur=22,start_gueltig=False,vorlauf=60)['invalid']
assert run(dict(start,day='2026-09-28'))==dict(start,day='2026-09-28')
main=yaml.safe_load(Path('bad_heizung_morgens.yaml').read_text())['automation'][0]
assert 'script.bad_heizung_lernereignis' in str(main)
assert '22.5' in str(main) and '23.5' not in str(main)
old=dict(start, target=23.5, correction=15, samples=3)
changed=run(old,6,20)
assert changed['invalid'] and changed['correction']==0 and changed['samples']==0
assert changed['learned']=='2026-09-29' and changed['result']=='retargeted'
assert run(changed)==changed
print('PASS: early/late/on-time learning, persistence, one update per day, invalidation, size limit, correction bounds')
