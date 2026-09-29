"""Offline regression tests for the actual Jinja counting templates."""
from pathlib import Path
from types import SimpleNamespace
import ast
import yaml
from jinja2.nativetypes import NativeEnvironment

config = yaml.safe_load(Path(__file__).with_name('bring_statistics.yaml').read_text())
templates = config['template'][0]['actions'][1]['variables']
env = NativeEnvironment()

def tick(old, items, clock, platform='time_pattern'):
    ctx = dict(this=SimpleNamespace(attributes=old),
               state_attr=lambda entity, attr: old.get(attr),
               einkauf={'todo.timo_seli': {'items': items}},
               trigger=SimpleNamespace(platform=platform),
               now=lambda: clock, as_timestamp=lambda x: x)
    for key, template in templates.items():
        value = env.from_string(template).render(**ctx)
        if isinstance(value, str):
            try:
                value = ast.literal_eval(value.strip())
            except (ValueError, SyntaxError):
                pass
        ctx[key] = value
    return dict(artikel=ctx['statistik'], vorher_offen=ctx['jetzt_offen'],
                initialisiert=True, letzte_pruefung=clock)

def item(name, status):
    return dict(summary=name, status=status)

def total(s):
    return sum(x['anzahl'] for x in s['artikel'])

done = item('Milch', 'completed')
open_item = item('Milch', 'needs_action')
s = tick({}, [done], 10000)
assert total(s) == 0, 'No backfill'
s = tick(s, [open_item], 10060)
assert total(s) == 0, 'Adding is not buying'
s = tick(s, [done], 10120)
assert total(s) == 1, 'First observed purchase'
s = tick(s, [done], 10180)
assert total(s) == 1, 'Repeated polling is idempotent'
s = tick(s, [open_item], 10240)
s = tick(s, [done], 10300)
assert total(s) == 1, 'Undo/recheck debounce'
for t in range(10360, 10900, 60):
    s = tick(s, [open_item], t)
s = tick(s, [done], 10900)
assert total(s) == 2, 'Later purchase increments'
s = tick(s, [open_item], 10960)
s = tick(s, [], 11020)
assert total(s) == 2, 'Deletion is not buying'
s = tick(s, [open_item], 11080)
s = tick(s, [done], 12000)
assert total(s) == 2, 'No speculation across long gaps'
s = tick(s, [open_item], 12060)
s = tick(s, [done], 12120, 'homeassistant')
assert total(s) == 2, 'No startup backfill'
s = tick(s, [item('MILCH', 'needs_action'), item('Brot', 'needs_action')], 12180)
s = tick(s, [done, item('Brot', 'completed')], 12240)
assert total(s) == 4 and len(s['artikel']) == 2, 'Batch + normalized names'
assert s['artikel'][0]['anzahl'] == 3, 'Top items sorted'
print('11 regression checks passed; no cloud writes.')
