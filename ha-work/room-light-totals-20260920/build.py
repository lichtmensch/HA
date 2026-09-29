import json,re,html,copy
from pathlib import Path
p=Path(__file__).parent
original=json.loads((p/'lovelace.dashboard_haus').read_text())['data']['config']
config=copy.deepcopy(original)
lights=re.findall(r'entity_id: light\.([a-z0-9_]+)',(p/'powercalc_lights.yaml').read_text())
lamp_ids={f'sensor.{name}_{suffix}' for name in lights for suffix in ['power','energy']}
changes=[]
for view in config['views']:
    for section in view.get('sections',[]):
        if not any(c.get('heading')=='Leistung & Energie' for c in section.get('cards',[])):continue
        for card in list(section['cards']):
            if card.get('type')!='entities':continue
            lamps=[r for r in card['entities'] if r['entity'] in lamp_ids]
            if not lamps:continue
            power=[r['entity'] for r in lamps if r['entity'].endswith('_power')]
            energy=[r['entity'] for r in lamps if r['entity'].endswith('_energy')]
            assert len(power)==len(energy)
            code="""[[[ const total=(ids,kind)=>{let value=0,missing=0;for(const id of ids){const s=states[id];const n=Number(s?.state);if(!s||['unknown','unavailable',''].includes(s.state)||!Number.isFinite(n)){missing++;continue;}const u=s.attributes.unit_of_measurement;if(kind==='power'&&u==='W')value+=n;else if(kind==='power'&&u==='kW')value+=n*1000;else if(kind==='energy'&&u==='kWh')value+=n;else if(kind==='energy'&&u==='Wh')value+=n/1000;else missing++;}if(missing)return 'Nicht verfügbar ('+missing+'/'+ids.length+' Werte fehlen)';return value.toLocaleString('de-DE',{maximumFractionDigits:kind==='power'?1:2})+(kind==='power'?' W':' kWh');};return 'Leistung: '+total(POWER,'power')+'\\nEnergie: '+total(ENERGY,'energy')+'\\nGeschätzt · erfasste Lampen · Energie-Zählerstände'; ]]]""".replace('POWER',json.dumps(power)).replace('ENERGY',json.dumps(energy))
            summary={'type':'custom:button-card','name':'Licht','icon':'mdi:lightbulb-group-outline','show_label':True,'label':code,'triggers_update':power+energy,'tap_action':{'action':'none'},'hold_action':{'action':'none'},'grid_options':{'columns':12,'rows':2},'styles':{'card':[{'padding':'12px 14px'},{'border-radius':'12px'}],'grid':[{'grid-template-areas':"'i n' 'i l'"},{'grid-template-columns':'36px 1fr'}],'icon':[{'width':'25px'},{'color':'var(--amber-color)'}],'name':[{'justify-self':'start'},{'font-size':'14px'},{'font-weight':'600'}],'label':[{'white-space':'pre-line'},{'text-align':'left'},{'justify-self':'start'},{'font-size':'12px'},{'line-height':'1.5'}]}}
            index=section['cards'].index(card)
            section['cards'].insert(index,summary)
            card['entities']=[r for r in card['entities'] if r['entity'] not in lamp_ids]
            if not card['entities']:section['cards'].remove(card)
            changes.append({'room':view['title'],'lamps':len(power),'power':power,'energy':energy})
assert config['views'][0]==original['views'][0]
assert len(changes)==8
out=p/'preview';out.mkdir(exist_ok=True)
(out/'haus.json').write_text(json.dumps(config,ensure_ascii=False,indent=2))
(out/'haus.html').write_text('<!doctype html><meta charset="utf-8"><h1>Lichtverbrauch pro Raum</h1><textarea readonly style="width:95vw;height:85vh">'+html.escape(json.dumps(config,ensure_ascii=False))+'</textarea>')
(p/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
print(json.dumps(changes,ensure_ascii=False))
