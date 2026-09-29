import json, copy, html
from pathlib import Path

ROOT = Path(__file__).parent
def read(name): return json.loads((ROOT/name).read_text())
haus = read('lovelace.dashboard_haus')['data']['config']
overview = read('lovelace.ipad_basic')['data']['config']
entities = read('core.entity_registry')['data']['entities']
devices = {d['id']: d for d in read('core.device_registry')['data']['devices']}
registry = {e['entity_id']: e for e in entities if e.get('disabled_by') is None}
rooms = [('wohnzimmer','Wohnzimmer','licht-wohnzimmer','mdi:sofa-outline'),('kuche','Küche','licht-kueche','mdi:countertop-outline'),('esszimmer','Esszimmer','licht-esszimmer','mdi:table-chair'),('schlafzimmer','Schlafzimmer','licht-schlafzimmer','mdi:bed-king-outline'),('gastezimmer','Gästezimmer','raum-gaestezimmer','mdi:bed-outline'),('flur','Flur','raum-flur','mdi:door'),('toilette','Gäste WC','raum-gaeste-wc','mdi:toilet'),('abstellkammer','Abstellkammer','raum-abstellkammer','mdi:archive-outline'),('homepod_bad','Bad','raum-bad','mdi:shower-head'),('terrasse','Terrasse','raum-terrasse','mdi:balcony')]
room_by_name={n:(a,p,i) for a,n,p,i in rooms}
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def fix_links(config):
    for o in walk(config):
        p=o.get('navigation_path','')
        if p.startswith('/dashboard-haus/haussteuerung/'): o['navigation_path']=p.replace('/haussteuerung/','/')
        if p=='/dashboard-haus/zuhause': o['navigation_path']='/dashboard-haus/haussteuerung'
        if p=='/dashboard-energie2/energie': o['navigation_path']='/dashboard-energie2/verbrauch'
fix_links(haus); fix_links(overview)
def heading(text,icon=None):
    return dict(type='heading',heading=text,**({'icon':icon} if icon else {}))
def nav(text,path,icon='mdi:arrow-left'):
    return {'type':'custom:button-card','name':text,'icon':icon,'tap_action':{'action':'navigate','navigation_path':path},'grid_options':{'columns':12,'rows':1},'styles':{'card':[{'height':'48px'},{'border-radius':'12px'},{'padding':'8px 12px'}],'grid':[{'grid-template-areas':"'i n'"},{'grid-template-columns':'30px 1fr'}],'icon':[{'width':'22px'}],'name':[{'justify-self':'start'},{'font-size':'14px'}]}}
def tile(e,name=None,features=None):
    c={'type':'tile','entity':e,'vertical':False,'grid_options':{'columns':6,'rows':1}}
    if name: c['name']=name
    if features: c.update(features=[{'type':f} for f in features],features_position='bottom',grid_options={'columns':12,'rows':1+len(features)})
    if e.startswith('switch.'):
        c.update(tap_action={'action':'more-info'},icon_tap_action={'action':'more-info'})
    return c
def section(title,cards,icon=None): return {'type':'grid','cards':[heading(title,icon)]+cards}
def area(e): return e.get('area_id') or devices.get(e.get('device_id'),{}).get('area_id')
def label(e):
    d=devices.get(e.get('device_id'),{})
    dn=d.get('name_by_user') or d.get('name') or ''
    name=e.get('name') or e.get('original_name') or dn or e['entity_id'].split('.')[1].replace('_',' ')
    short={'Tv und Yamaha':'TV & Yamaha','Tv und yamaha':'TV & Yamaha','Apple tv switch backlight':'Apple TV / Backlight','Plug TV Gästezimmer':'TV Gästezimmer','Plug TX Gästezimmer':'TV Gästezimmer','Stecker Kaffeemaschine':'Kaffeemaschine','Stecker Wäschetrockner':'Trockner','Stecker Waschmaschine ':'Waschmaschine','Plug QNAP':'QNAP','Shelly Plug QNAP':'QNAP','Weather Station':'Wohnzimmer','Weather Station Bad':'Bad','Weather Station Schlafzimmer':'Schlafzimmer','Weather Station Gästezimmer':'Gästezimmer'}
    dn=short.get(dn,dn)
    if name in ['Leistung','Energie','Energieverbrauch'] and dn: name=f'{dn} · {name}'
    return short.get(name,name).replace('Kohlendioxid','CO₂').replace(' power',' · Leistung (geschätzt)').replace(' energy',' · Energie (geschätzt)')
main=haus['views'][0]
for s in main['sections']:
    h=next((c for c in s['cards'] if c.get('type')=='heading'),None)
    if h and h['heading'] in room_by_name:
        a,p,i=room_by_name[h['heading']]
        h.update(tap_action={'action':'navigate','navigation_path':'/dashboard-haus/'+p},heading_style='title')
    for c in s['cards']:
        if c.get('type')=='tile':
            c['grid_options']={'columns':12 if c.get('features') else 6,'rows':2 if c.get('features') else 1}
        if c.get('name') in ['Rollos öffnen','Rollos schließen']:
            c['grid_options']={'columns':6,'rows':1}
            for prop in c.get('styles',{}).get('card',[]):
                if 'height' in prop: prop['height']='48px'
    if h and h['heading']=='Gäste WC':
        s['cards'] += [tile('sensor.stecker_waschmaschine_leistung','Waschmaschine'),tile('sensor.stecker_waschetrockner_leistung','Trockner')]
    if h and h['heading']=='Flur': s['cards'].append(tile('vacuum.s8_maxv_ultra','Saugroboter'))

oldviews={v['path']:v for v in haus['views']}
newviews=[]
for aid,name,path,icon in rooms:
    es=[e for e in registry.values() if area(e)==aid and e.get('entity_category') is None]
    grouped={}
    for e in es: grouped.setdefault(e['entity_id'].split('.')[0],[]).append(e)
    included=set()
    sections=[{'type':'grid','cards':[nav('Zurück zur Haussteuerung','/dashboard-haus/haussteuerung'),nav('Zur Übersicht','/ipad-basic/flur','mdi:home-outline')]}]
    climate=[e for e in grouped.get('sensor',[]) if (e.get('device_class') or e.get('original_device_class')) in ['temperature','humidity','carbon_dioxide'] and not e['entity_id'].startswith('sensor.kuhlschrank_')]
    if climate:
        sections.append(section('Raumklima' if aid!='terrasse' else 'Wetter', [tile(e['entity_id'],label(e)) for e in climate],'mdi:thermometer'))
        included.update(e['entity_id'] for e in climate)
    lights=[]
    if path in oldviews:
        lights=[copy.deepcopy(c) for c in walk(oldviews[path]) if c.get('type')=='tile' and c.get('entity','').startswith('light.')]
        for c in lights:
            c['grid_options']={'columns':12,'rows':1+len(c.get('features',[]))}
    else:
        mainsection=next(s for s in main['sections'] if any(c.get('heading')==name for c in s['cards']))
        for c in mainsection['cards']:
            if c.get('entity','').startswith('light.'):
                lights.append(tile(c['entity'],'Licht',['light-brightness']))
    if lights:
        sections.append(section('Licht',lights,'mdi:lightbulb-outline'))
        included.update(c['entity'] for c in lights)
    individual=[{'entity':e['entity_id'],'name':label(e)} for e in grouped.get('light',[]) if e['entity_id'] not in included]
    if individual: sections.append(section('Einzelne Lampen',[{'type':'entities','show_header_toggle':False,'entities':individual}]))
    included.update(e['entity_id'] for e in grouped.get('light',[]))
    covers=grouped.get('cover',[])
    if covers:
        sections.append(section('Rollos',[tile(e['entity_id'],'Terrassenrollo' if aid=='esszimmer' else 'Rollo',['cover-open-close','cover-position']) for e in covers],'mdi:window-shutter'))
        included.update(e['entity_id'] for e in covers)
    if aid=='kuche':
        sections.append(section('Küchengeräte',[nav('Kaffeevollautomat · Details','/dashboard-haus/kaffeevollautomat','mdi:coffee-maker-outline'),tile('sensor.kaffeevollautomat_betriebszustand','Kaffeevollautomat'),nav('Kühlschrank · Details','/dashboard-haus/kuehlschrank','mdi:fridge-outline'),tile('sensor.kuhlschrank_kuhlschranktemperatur','Kühlen'),tile('sensor.kuhlschrank_gefrierschranktemperatur','Gefrieren')]))
        included.update(['sensor.kaffeevollautomat_betriebszustand','sensor.kuhlschrank_kuhlschranktemperatur','sensor.kuhlschrank_gefrierschranktemperatur'])
    if aid=='toilette':
        sections.append(section('Waschmaschine & Trockner',[tile('sensor.stecker_waschmaschine_leistung','Waschmaschine · aktuell'),tile('sensor.stecker_waschetrockner_leistung','Trockner · aktuell'),{'type':'entities','show_header_toggle':False,'entities':[{'entity':'input_boolean.trockner_lauf_aktiv','name':'Trockner-Lauferkennung','type':'simple-entity'},{'entity':'automation.trockner_lauf_fertig','name':'Letzte Fertigmeldung','type':'attribute','attribute':'last_triggered','format':'relative'}]}],'mdi:washing-machine'))
        included.update(['sensor.stecker_waschmaschine_leistung','sensor.stecker_waschetrockner_leistung'])
    if aid=='flur':
        robot=['sensor.s8_maxv_ultra_batterie','sensor.s8_maxv_ultra_status','sensor.s8_maxv_ultra_staubsauger_fehler','binary_sensor.s8_maxv_ultra_dock_frischwassertank','binary_sensor.s8_maxv_ultra_dock_schmutzwassertank']
        sections.append(section('Saugroboter',[tile('vacuum.s8_maxv_ultra','S8 MaxV Ultra',['vacuum-commands']),{'type':'entities','show_header_toggle':False,'entities':[{'entity':x,'name':label(registry[x])} for x in robot if x in registry]}],'mdi:robot-vacuum'))
        included.update(['vacuum.s8_maxv_ultra']+robot)
        # Keep vacuum actions in its standard more-info dialog; no guessed command schema.
        sections[-1]['cards'][1]=tile('vacuum.s8_maxv_ultra','S8 MaxV Ultra')
    media=grouped.get('media_player',[])
    if media:
        sections.append(section('Medien',[{'type':'media-control','entity':e['entity_id']} for e in media],'mdi:play-circle-outline'))
        included.update(e['entity_id'] for e in media)
    energy=[e for e in grouped.get('sensor',[]) if e['entity_id'] not in included and (e.get('device_class') or e.get('original_device_class')) in ['power','energy'] and 'einspeisung' not in e['entity_id'] and not any(t in e['entity_id'] for t in ['energiedifferenz','energieeinsparung','energieverbrauch'])]
    if energy:
        sections.append(section('Leistung & Energie',[{'type':'entities','show_header_toggle':False,'entities':[{'entity':e['entity_id'],'name':label(e)} for e in energy]},nav('Energie nach Zeitraum','/dashboard-energie2/jahresverbrauch','mdi:chart-box-outline')],'mdi:flash-outline'))
        included.update(e['entity_id'] for e in energy)
    switches=grouped.get('switch',[])
    if switches:
        sections.append(section('Gerätesteuerung',[tile(e['entity_id'],label(e)) for e in switches],'mdi:power-plug-outline'))
        included.update(e['entity_id'] for e in switches)
    extras=[e for e in es if e['entity_id'] not in included and e['entity_id'].split('.')[0] in ['sensor','binary_sensor','fan','climate'] and not any(t in e['entity_id'] for t in ['eingang_','einspeisung','energiedifferenz','energieeinsparung','energieverbrauch','tastaturfokus'])]
    if extras: sections.append(section('Weitere Messwerte & Status',[{'type':'entities','show_header_toggle':False,'entities':[{'entity':e['entity_id'],'name':label(e)} for e in extras]}],'mdi:information-outline'))
    newviews.append({'title':name,'path':path,'icon':icon,'type':'sections','max_columns':2,'subview':True,'back_path':'/dashboard-haus/haussteuerung','dense_section_placement':True,'sections':sections})
haus['views']=[main]+newviews+[v for v in haus['views'][1:] if v['path'] not in {r[2] for r in rooms}]
for v in haus['views'][11:]:
    target='/dashboard-haus/licht-kueche' if v['path'] in ['kaffeevollautomat','kuehlschrank'] else '/dashboard-haus/haussteuerung'
    v['back_path']=target
    v['sections'].insert(0,{'type':'grid','cards':[nav('Zurück zur Küche' if 'kueche' in target else 'Zurück zur Haussteuerung',target)]})

# Reuse confirmed existing run detection. Never infer "finished" from zero watts.
monitored=[]
for v in newviews:
    for o in walk(v):
        e=o.get('entity')
        if e and e.split('.')[0] in ['light','cover','sensor','vacuum','media_player','switch'] and e not in monitored: monitored.append(e)
doors=['binary_sensor.kuhlschrank_kuhlschranktur','binary_sensor.kuhlschrank_gefrierschranktur','binary_sensor.kuhlschrank_coolselect_tur']
status_js="""[[[ const lines=[]; const doors=DOORS; const names=['Kühlschranktür offen','Gefrierschranktür offen','CoolSelect-Tür offen']; doors.forEach((id,i)=>{if(states[id]?.state==='on')lines.push('🚪 '+names[i]);}); const run=states['input_boolean.trockner_lauf_aktiv']; const end=states['automation.trockner_lauf_fertig']?.attributes?.last_triggered; if(run?.state==='on')lines.push('🧺 Trockner läuft'); else if(end && Date.now()-Date.parse(end)<86400000) lines.push('🧺 Trockner: letzte Fertigmeldung '+new Date(end).toLocaleTimeString('de-DE',{hour:'2-digit',minute:'2-digit'})); const bad=MONITORED.filter(id=>states[id]?.state==='unavailable'); if(bad.length)lines.push('⚠ '+bad.length+' Geräte/Messwerte nicht erreichbar'); return lines.length ? lines.join(' · ') : 'Keine offenen Kühlschranktüren oder gemeldeten Ausfälle'; ]]]""".replace('DOORS',json.dumps(doors)).replace('MONITORED',json.dumps(monitored))
status={'type':'custom:button-card','name':'Hinweise','label':status_js,'show_label':True,'icon':'mdi:information-outline','triggers_update':monitored+doors+['input_boolean.trockner_lauf_aktiv','automation.trockner_lauf_fertig'],'tap_action':{'action':'navigate','navigation_path':'/dashboard-haus/haussteuerung'},'styles':{'card':[{'min-height':'64px'},{'padding':'10px 12px'},{'border-radius':'14px'}],'grid':[{'grid-template-areas':"'i n' 'i l'"},{'grid-template-columns':'30px 1fr'}],'icon':[{'width':'22px'}],'name':[{'justify-self':'start'},{'font-size':'13px'}],'label':[{'white-space':'normal'},{'text-align':'left'},{'justify-self':'start'},{'font-size':'12px'}]}}
overview['views'][0]['sections'][1]['cards'].insert(0,status)
for o in walk(overview):
    if o.get('heading')=='Haus & Mobilität': o['heading']='Erfasste Geräte · kein Hausgesamtverbrauch'

out=ROOT/'preview'; out.mkdir(exist_ok=True)
power_source=(ROOT/'haus-power-card.js').read_text()
assert power_source.count('>Haus aktuell</div>')==1
(ROOT/'haus-power-card.updated.js').write_text(power_source.replace('>Haus aktuell</div>','>Erfasste Geräte</div>'))
for name,cfg in [('haus',haus),('overview',overview)]:
    (out/(name+'.json')).write_text(json.dumps(cfg,ensure_ascii=False,indent=2))
    (out/(name+'.html')).write_text('<!doctype html><meta charset="utf-8"><title>Dashboard-Arbeitskopie '+name+'</title><h1>'+name+'</h1><textarea id="config" readonly style="width:95vw;height:85vh">'+html.escape(json.dumps(cfg,ensure_ascii=False))+'</textarea>')
paths={v['path'] for v in haus['views']}
badlinks=[o['navigation_path'] for o in walk(haus) if o.get('navigation_path','').startswith('/dashboard-haus/') and o['navigation_path'].split('/')[-1] not in paths]
assert not badlinks,badlinks
assert len(newviews)==10 and all(v['subview'] for v in newviews)
assert all(sum(1 for o in walk(v) if o.get('type')=='tile' and o.get('entity')==c['entity'])==1 for v in newviews for c in walk(v) if c.get('type')=='tile' and c.get('entity','').startswith('cover.'))
print(json.dumps({'views':[(v['title'],v['path']) for v in haus['views']], 'monitor_count':len(monitored),'badlinks':badlinks},ensure_ascii=False))
