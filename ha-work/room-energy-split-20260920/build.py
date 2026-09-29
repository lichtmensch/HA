import json,copy,re,html
from pathlib import Path
p=Path(__file__).parent
old=json.loads((p/'original.json').read_text())['data']['config']
cfg=copy.deepcopy(old)
changed=[]
for view in cfg['views']:
    result=[]
    for section in view.get('sections',[]):
        if not any(c.get('heading')=='Leistung & Energie' for c in section.get('cards',[])):
            result.append(section);continue
        power={'type':'grid','cards':[{'type':'heading','heading':'Leistung aktuell (W)','icon':'mdi:flash-outline'}]}
        energy={'type':'grid','cards':[{'type':'heading','heading':'Energieverbrauch (kWh)','icon':'mdi:counter'}]}
        for card in section['cards']:
            if card.get('type')=='heading':continue
            if card.get('name')=='Licht':
                prefix=card['label'].split("};return 'Leistung: '")[0]
                assert prefix!=card['label']
                for kind,target,suffix in [('power',power,'power'),('energy',energy,'energy')]:
                    c=copy.deepcopy(card)
                    ids=[x for x in c['triggers_update'] if x.endswith('_'+suffix)]
                    assert ids
                    c['triggers_update']=ids
                    note='Geschätzt · erfasste Lampen' if kind=='power' else 'Geschätzt · Energie-Zählerstände'
                    c['label']=prefix+'};return total('+json.dumps(ids)+','+json.dumps(kind)+")+'\\n"+note+"'; ]]]"
                    c['grid_options']['rows']=2
                    target['cards'].append(c)
            elif card.get('type')=='entities':
                for target,suffixes in [(power,('_leistung','_power')),(energy,('_energie','_energy'))]:
                    rows=[copy.deepcopy(r) for r in card['entities'] if r['entity'].endswith(suffixes)]
                    for r in rows:
                        r['name']=re.sub(r'\s*(?:·\s*)?(?:Leistung|Energie)(?=\s*\(geschätzt\)|$)','',r.get('name','')).strip()
                    if rows:target['cards'].append(dict(type='entities',show_header_toggle=False,entities=rows))
                assert all(r['entity'].endswith(('_leistung','_power','_energie','_energy')) for r in card['entities'])
            else:energy['cards'].append(card)
        if view['title']=='Gäste WC':
            existing=next(c for c in power['cards'] if c.get('type')=='entities')
            existing['entities'] += [{'entity':'sensor.stecker_waschmaschine_leistung','name':'Waschmaschine'},{'entity':'sensor.stecker_waschetrockner_leistung','name':'Trockner'}]
        result.extend([power,energy]);changed.append(view['title'])
    view['sections']=result
assert len(changed)==10
assert cfg['views'][0]==old['views'][0]
for v,b in zip(cfg['views'],old['views']):
    if v['title'] not in changed:assert v==b
out=p/'preview';out.mkdir(exist_ok=True)
(out/'haus.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2))
(out/'haus.html').write_text('<!doctype html><meta charset="utf-8"><h1>Leistung und Energieverbrauch</h1><textarea readonly style="width:95vw;height:85vh">'+html.escape(json.dumps(cfg,ensure_ascii=False))+'</textarea>')
print(json.dumps(changed,ensure_ascii=False))
