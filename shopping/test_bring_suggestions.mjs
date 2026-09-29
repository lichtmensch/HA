import assert from 'node:assert/strict';
import fs from 'node:fs';
globalThis.HTMLElement = class {};
globalThis.customElements = {get: () => true};
const code = fs.readFileSync(new URL('./bring-suggest-card.js', import.meta.url), 'utf8');
const {suggestions, normalize, BringSuggestCard} = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'));
const items = [{summary:'Tomaten',status:'completed'}, {summary:'Milch',status:'needs_action'}, {summary:'Möhren',status:'completed'}];
assert.equal(suggestions('Tom', items)[0].name, 'Tomaten');
assert.equal(suggestions('Tomatn', items)[0].fuzzy, true);
assert.equal(suggestions('Möhr', items)[0].name, 'Möhren');
assert.equal(suggestions('xyz', items).length, 0);
assert.equal(suggestions('Milch', items)[0].active, true);
assert.equal(suggestions('', items, [{name:'Tomaten',anzahl:4}])[0].name, 'Tomaten');
assert.equal(normalize('  TOMATEN '), 'tomaten');
let writes = [];
const fake = Object.assign(Object.create(BringSuggestCard.prototype), {
  config:{entity:'todo.test'}, input:{value:'Milch',focus(){}}, detail:{value:'1 Liter'},
  shadowRoot:{querySelectorAll:()=>[]}, message(text){this.lastMessage=text;}, renderChoices(){},
  fetchItems:async()=>items,
  _hass:{callService:async(...args)=>writes.push(args)}
});
await fake.add();
assert.equal(writes.length,0,'Existing open items remain untouched');
fake.input.value='Tomaten';
await fake.add();
assert.equal(writes.length,1);
assert.deepEqual(writes[0],['todo','add_item',{entity_id:'todo.test',item:'Tomaten',description:'1 Liter'}]);
assert.equal(fake.input.value,'');
fake.input.value='  ';
await fake.add();
assert.equal(writes.length,1,'Empty form never writes');
console.log('Suggestion, typo, normalization, duplicate and submit tests passed with mocked HA; no real purchases written.');
