// Local Home Assistant card. Suggestions stay in the browser; no external spellchecker.
export const normalize = (s) => String(s || '').trim().toLocaleLowerCase('de')
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ß/g, 'ss');

export function distance(a, b) {
  let row = Array.from({length: b.length + 1}, (_, i) => i);
  for (let i = 0; i < a.length; i++) {
    const next = [i + 1];
    for (let j = 0; j < b.length; j++) {
      next.push(Math.min(next[j] + 1, row[j + 1] + 1, row[j] + (a[i] !== b[j])));
    }
    row = next;
  }
  return row[b.length];
}

export function suggestions(query, items, stats = []) {
  const choices = new Map();
  for (const p of items) {
    const key = normalize(p.summary);
    if (!key) continue;
    const old = choices.get(key);
    choices.set(key, {name: p.summary, count: 0, active: p.status === 'needs_action' || !!old?.active});
  }
  for (const p of stats) {
    const key = normalize(p.name);
    if (!key) continue;
    const old = choices.get(key);
    choices.set(key, {name: old?.name || p.name, active: !!old?.active, count: Number(p.anzahl) || 0});
  }
  const q = normalize(query);
  return [...choices.entries()].map(([key, p]) => {
    const exact = key === q;
    const prefix = key.startsWith(q);
    const contains = key.includes(q);
    const fuzzy = !!q && q.length >= 3 && distance(q, key) <= (q.length >= 6 ? 2 : 1);
    return {...p, match: !q || contains || fuzzy, fuzzy: !!q && !contains,
      score: !q ? 0 : exact ? 4 : prefix ? 3 : contains ? 2 : 1};
  }).filter(p => p.match).sort((a, b) => b.score - a.score || b.count - a.count || a.name.localeCompare(b.name, 'de')).slice(0, 8);
}

export class BringSuggestCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity?.startsWith('todo.')) throw new Error('Eine To-do-Liste ist erforderlich.');
    this.config = config;
    this.items = [];
    if (!this.shadowRoot) this.attachShadow({mode: 'open'});
    this.shadowRoot.innerHTML = `
      <style>
        :host {display:block} ha-card {padding:20px; color:var(--primary-text-color)}
        h2 {font-size:20px;font-weight:500;margin:0 0 14px} label {display:block;font-size:13px;margin:10px 0 5px}
        input {box-sizing:border-box;width:100%;padding:12px;font:inherit;color:var(--primary-text-color);background:var(--secondary-background-color);border:1px solid var(--divider-color);border-radius:8px}
        input:focus {outline:2px solid var(--primary-color)}
        button {font:inherit;cursor:pointer;border-radius:8px;border:1px solid var(--divider-color);padding:10px 12px;background:var(--card-background-color);color:var(--primary-text-color)}
        button:focus-visible {outline:2px solid var(--primary-color)}
        .add {background:var(--primary-color);color:var(--text-primary-color,white);border:0;flex:1}
        button:disabled {opacity:.55;cursor:default} .actions {display:flex;gap:8px;margin-top:12px}
        .choices {display:flex;gap:7px;flex-wrap:wrap;margin-top:10px} .choice {text-align:left;font-size:14px}
        small {display:block;font-size:11px;color:var(--secondary-text-color);margin-top:3px}
        p {font-size:13px;line-height:1.5;color:var(--secondary-text-color);margin:10px 0 0}
        .status {min-height:20px} .error {color:var(--error-color,#db4437)}
      </style>
      <ha-card>
        <h2>Zu Bring! hinzufügen</h2>
        <form>
          <label for="article">Artikel</label>
          <input id="article" name="article" placeholder="z. B. Tomaten" autocomplete="off" autocorrect="off" spellcheck="false" maxlength="200" required>
          <div class="choices" role="group" aria-label="Artikelvorschläge"></div>
          <p>Vorschläge antippen, dann hinzufügen. Ähnliche Schreibweisen werden nicht automatisch ersetzt.</p>
          <label for="detail">Menge / Zusatz (optional)</label>
          <input id="detail" name="detail" placeholder="z. B. 500 g oder 2 Packungen" maxlength="200">
          <div class="actions"><button class="add" type="submit">Hinzufügen</button><button class="refresh" type="button" aria-label="Vorschläge aktualisieren">↻</button></div>
          <p class="status" role="status" aria-live="polite"></p>
        </form>
      </ha-card>`;
    this.input = this.shadowRoot.querySelector('#article');
    this.detail = this.shadowRoot.querySelector('#detail');
    this.status = this.shadowRoot.querySelector('.status');
    this.input.addEventListener('input', () => { this.message(''); this.renderChoices(); });
    this.input.addEventListener('focus', () => this.load());
    this.shadowRoot.querySelector('.refresh').addEventListener('click', () => this.load(true));
    this.shadowRoot.querySelector('form').addEventListener('submit', e => { e.preventDefault(); this.add(); });
  }
  set hass(hass) {
    this._hass = hass;
    if (!this.config) return;
    const stats = hass.states[this.config.statistics_entity]?.attributes.artikel || [];
    if (stats !== this.stats) { this.stats = stats; this.renderChoices(); }
    if (!this.loadedAt && !this.loading) this.load();
  }
  getCardSize() { return 5; }
  getGridOptions() { return {columns:12, rows:'auto'}; }
  message(text, error = false) { this.status.textContent = text; this.status.classList.toggle('error', error); }
  async fetchItems() {
    const result = await this._hass.callWS({type:'call_service', domain:'todo', service:'get_items',
      target:{entity_id:this.config.entity}, service_data:{status:['needs_action','completed']}, return_response:true});
    const items = result?.response?.[this.config.entity]?.items;
    if (!Array.isArray(items)) throw new Error('Die Einkaufsliste konnte nicht gelesen werden.');
    return items;
  }
  async load(force = false) {
    if (!this._hass || this.loading || (!force && Date.now() - (this.loadedAt || 0) < 30000)) return;
    this.loading = true;
    try { this.items = await this.fetchItems(); this.loadedAt = Date.now(); this.renderChoices(); }
    catch (e) { this.loadedAt = Date.now(); this.message('Vorschläge nicht verfügbar. Mit ↻ erneut versuchen.', true); }
    finally { this.loading = false; }
  }
  renderChoices() {
    if (!this.input) return;
    const box = this.shadowRoot.querySelector('.choices');
    box.replaceChildren();
    for (const p of suggestions(this.input.value, this.items, this.stats)) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'choice';
      button.append(document.createTextNode((p.fuzzy ? 'Meintest du: ' : '') + p.name));
      const note = document.createElement('small');
      note.textContent = p.active ? 'Bereits auf der Liste' : p.count ? `${p.count}× erkannt gekauft` : 'Bisheriger Artikel';
      button.append(note);
      button.addEventListener('click', () => { this.input.value = p.name; this.message(''); this.renderChoices(); this.detail.focus(); });
      box.append(button);
    }
  }
  async add() {
    if (this.busy) return;
    const name = this.input.value.trim();
    if (!name) { this.message('Bitte einen Artikel eingeben.', true); this.input.focus(); return; }
    this.busy = true;
    this.shadowRoot.querySelectorAll('input,button').forEach(el => el.disabled = true);
    try {
      // Refresh the HA list snapshot before any write, and never overwrite an active item.
      const items = await this.fetchItems();
      if (items.some(p => p.status === 'needs_action' && normalize(p.summary) === normalize(name))) {
        this.message('Dieser Artikel steht bereits auf der Liste. Seine Menge bleibt unverändert.', true);
        return;
      }
      await this._hass.callService('todo', 'add_item', {entity_id:this.config.entity, item:name, description:this.detail.value.trim()});
      this.items = items.filter(p => normalize(p.summary) !== normalize(name));
      this.items.push({summary:name,status:'needs_action'});
      this.input.value = ''; this.detail.value = ''; this.loadedAt = 0;
      this.message(`${name} wurde zu Bring! hinzugefügt.`);
    } catch (e) { this.message('Nicht bestätigt. Bitte Bring! prüfen, bevor du es erneut versuchst. ' + (e.message || ''), true); }
    finally {
      this.busy = false;
      this.renderChoices();
      this.shadowRoot.querySelectorAll('input,button').forEach(el => el.disabled = false);
    }
  }
}
if (!customElements.get('bring-suggest-card')) customElements.define('bring-suggest-card', BringSuggestCard);
