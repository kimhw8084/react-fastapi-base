import { EngineeringElement, register, badge } from './base.js';
import { logs } from './fixtures.js';
import { escapeHtml as h, diffLines } from './model.js';
export class LogExplorer extends EngineeringElement {
    search = '';
    level = 'ALL';
    selected = null;
    constructor() { super(logs); }
    render() {
        const rows = this.value.filter(v => (this.level === 'ALL' || v.level === this.level) && `${v.message} ${v.service}`.toLowerCase().includes(this.search.toLowerCase()));
        this.frame(`<div class="component-toolbar"><div class="search-field"><span aria-hidden="true">⌕</span><input data-focus="log-search" aria-label="Search logs" placeholder="Search service or message…" value="${h(this.search)}"></div><select aria-label="Log severity" data-level>${['ALL', 'INFO', 'WARN', 'ERROR'].map(s => `<option ${s === this.level ? 'selected' : ''}>${s}</option>`).join('')}</select><span class="badge tone-neutral">${rows.length} events</span></div><div class="log-console" tabindex="0" aria-label="Log entries"><div class="log-heading"><span>Timestamp</span><span>Level</span><span>Service</span><span>Message</span></div>${rows.map(v => `<button class="log-row ${v.id === this.selected ? 'selected' : ''}" data-log="${h(v.id)}" aria-label="${h(v.timestamp)} ${h(v.level)} ${h(v.message)}"><span>${h(v.timestamp)}.000</span><span class="log-level ${h(v.level)}">${h(v.level)}</span><span>${h(v.service)}</span><span>${h(v.message)}</span></button>`).join('') || '<p class="empty-cell">No matching events.</p>'}</div><p class="component-note">Bounded synthetic log buffer. Messages are escaped. Streaming, retention, and real telemetry are not simulated as live connections.</p>`);
        this.on('[data-focus="log-search"]', 'input', e => { this.search = e.target.value; this.render(); });
        this.on('[data-level]', 'change', e => { this.level = e.target.value; this.render(); });
        this.on('[data-log]', 'click', e => { this.selected = e.currentTarget.dataset.log; this.select(this.value.find(v => v.id === this.selected)); });
    }
}
export class ConfigurationDiff extends EngineeringElement {
    constructor() { super({ before: '{\n  "process": "qualification",\n  "temperature": 320,\n  "pressure": 1.8,\n  "duration": 60,\n  "revision": 4\n}', after: '{\n  "process": "qualification",\n  "temperature": 325,\n  "pressure": 1.8,\n  "duration": 75,\n  "revision": 5\n}', leftLabel: 'Revision 4', rightLabel: 'Revision 5' }); }
    render() { const rows = diffLines(this.value.before, this.value.after); this.frame(`<div class="component-toolbar">${badge(`${rows.filter(r => r.changed).length} changed lines`, 'info')}<span class="subtle">Positional line comparison</span></div><div class="diff-grid"><section><header><span>${h(this.value.leftLabel)}</span><span>Before</span></header>${rows.map((r, i) => `<div class="diff-line ${r.changed ? 'removed' : ''}"><span>${i + 1}</span><code>${h(r.before) || ' '}</code></div>`).join('')}</section><section><header><span>${h(this.value.rightLabel)}</span><span>After</span></header>${rows.map((r, i) => `<div class="diff-line ${r.changed ? 'added' : ''}"><span>${i + 1}</span><code>${h(r.after) || ' '}</code></div>`).join('')}</section></div><details class="editor-details"><summary>Edit comparison input</summary><form data-diff-form><label>Before<textarea name="before" rows="8" ${this.readonlyMode ? 'disabled' : ''}>${h(this.value.before)}</textarea></label><label>After<textarea name="after" rows="8" ${this.readonlyMode ? 'disabled' : ''}>${h(this.value.after)}</textarea></label><button class="button primary" ${this.readonlyMode ? 'disabled' : ''}>Compare</button></form></details><p class="component-note">Exact line-position comparison. Semantic recipe validation, approvals, and executable recipe control are separate domain services.</p>`); this.on('[data-diff-form]', 'submit', e => { e.preventDefault(); const data = new FormData(e.currentTarget); this.change({ ...this.value, before: String(data.get('before')), after: String(data.get('after')) }, 'compare'); }); }
}
export class JsonInspector extends EngineeringElement {
    constructor() { super({ workspace: 'equipment', capabilities: ['table', 'history', 'savedViews'], presentation: { density: 'comfortable', theme: 'system' }, version: 1 }); }
    render() { this.frame(`<div class="json-editor-layout"><form data-json-form><label class="eyebrow">JSON CONFIGURATION<textarea name="json" aria-label="JSON configuration" class="code-input" rows="15" spellcheck="false" ${this.readonlyMode ? 'disabled' : ''}>${h(JSON.stringify(this.value, null, 2))}</textarea></label><div class="form-actions"><button class="button primary" ${this.readonlyMode ? 'disabled' : ''}>Validate & format</button></div></form><aside class="info-card"><h3>Typed at the boundary</h3><p>This editor accepts a JSON object and emits a model change. It does not evaluate JavaScript or apply configuration to production.</p><dl><dt>Top-level keys</dt><dd>${Object.keys(this.value).length}</dd><dt>Payload size</dt><dd>${new TextEncoder().encode(JSON.stringify(this.value)).length} bytes</dd></dl><p>Application adapters must validate their own schemas before persisting configuration.</p></aside></div>`); this.on('[data-json-form]', 'submit', e => { e.preventDefault(); try {
        const raw = String(new FormData(e.currentTarget).get('json'));
        if (raw.length > 64000)
            throw new Error('Maximum editor input is 64 KB.');
        const value = JSON.parse(raw);
        if (!value || typeof value !== 'object' || Array.isArray(value))
            throw new Error('Expected a JSON object.');
        this.change(value, 'validate-json');
    }
    catch (error) {
        this.fail(error.message);
    } }); }
}
export class EngineeringForm extends EngineeringElement {
    constructor() { super({ name: 'Film thickness', unit: 'nm', target: 52, tolerance: 1.8, category: 'Measurement', enabled: true }); }
    render() { this.frame(`<form class="engineering-form" data-parameter-form><div class="form-section"><div><span class="eyebrow">IDENTITY</span><h3>Parameter definition</h3><p>Reusable field layout with required, unit-aware and conditional inputs.</p></div><div class="field-grid"><label>Parameter name <span aria-hidden="true">*</span><input name="name" value="${h(this.value.name)}" required minlength="2" maxlength="100" ${this.readonlyMode ? 'disabled' : ''}><small>A descriptive name for the measured quantity.</small></label><label>Category<select name="category" ${this.readonlyMode ? 'disabled' : ''}>${['Measurement', 'Control', 'Configuration'].map(c => `<option ${this.value.category === c ? 'selected' : ''}>${c}</option>`).join('')}</select></label></div></div><div class="form-section"><div><span class="eyebrow">ENGINEERING VALUES</span><h3>Limits & precision</h3><p>Target and tolerance share the same configured unit.</p></div><div class="field-grid"><label>Target value<input name="target" type="number" step="any" required value="${this.value.target}" ${this.readonlyMode ? 'disabled' : ''}></label><label>Engineering unit<select name="unit" ${this.readonlyMode ? 'disabled' : ''}>${['nm', 'µm', '°C', 'kPa', 's', 'V'].map(c => `<option ${c === this.value.unit ? 'selected' : ''}>${c}</option>`).join('')}</select></label><label>Tolerance ±<input name="tolerance" type="number" step="any" min="0" required value="${this.value.tolerance}" ${this.readonlyMode ? 'disabled' : ''}></label><label class="switch-field"><input name="enabled" type="checkbox" role="switch" ${this.value.enabled ? 'checked' : ''} ${this.readonlyMode ? 'disabled' : ''}><span>Enable parameter</span></label></div></div><footer class="form-actions"><span class="subtle" data-form-message>Changes affect the local fixture only.</span><button class="button primary" ${this.readonlyMode ? 'disabled' : ''}>Save parameter</button></footer></form>`); this.on('[data-parameter-form]', 'submit', e => { e.preventDefault(); const data = new FormData(e.currentTarget), target = Number(data.get('target')), tolerance = Number(data.get('tolerance')); if (!Number.isFinite(target) || !Number.isFinite(tolerance) || tolerance < 0) {
        this.fail('Enter finite numbers and a nonnegative tolerance.');
        return;
    } this.change({ name: String(data.get('name')).trim(), category: String(data.get('category')), unit: String(data.get('unit')), target, tolerance, enabled: data.has('enabled') }, 'save-parameter'); const message = this.querySelector('[data-form-message]'); if (message)
        message.textContent = 'Parameter saved in the local fixture.'; }); }
}
register('rf-log-explorer', LogExplorer);
register('rf-config-diff', ConfigurationDiff);
register('rf-json-inspector', JsonInspector);
register('rf-engineering-form', EngineeringForm);
//# sourceMappingURL=editors.js.map