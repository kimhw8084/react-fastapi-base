import { defaultRack, validatePresentation } from './presentation.js';
import { EngineeringElement, register, badge } from './base.js';
import { devices, dies, graph } from './fixtures.js';
import { escapeHtml as h, moveDevice, validateRack, waferYield, validateGraph, localId } from './model.js';
export class RackElevation extends EngineeringElement {
    selected = 'D3';
    side = 'Front';
    constructor() { super(devices); }
    render() {
        const config = this.options.presentation?.rack ?? defaultRack, capacity = config.units;
        const d = this.value.find(v => v.id === this.selected) ?? this.value[0], occupied = this.value.reduce((n, v) => n + v.units, 0), watts = this.value.reduce((n, v) => n + v.watts, 0);
        this.frame(`<div class="rack-layout"><div class="rack-frame"><header><span class="mono">${h(config.label)}</span><div class="segment-control">${['Front', 'Rear'].map(s => `<button data-side="${s}" aria-pressed="${this.side === s}" class="${this.side === s ? 'active' : ''}">${s}</button>`).join('')}</div></header><div class="rack-units">${Array.from({ length: capacity }, (_, i) => capacity - i).map(u => `<div class="rack-unit"><span>${u}</span><i></i><span>${u}</span></div>`).join('')}<div class="rack-devices">${this.value.map(v => `<button class="rack-device ${v.id === this.selected ? 'selected' : ''} device-${v.status}" data-device="${h(v.id)}" style="top:${(capacity - v.start - v.units + 1) * 13}px;height:${v.units * 13 - 2}px" aria-label="${h(v.name)}, U${v.start} to U${v.start + v.units - 1}, ${v.status}"><span class="rack-vents" aria-hidden="true">${this.side === 'Rear' ? '▣ ▣ ▣ ▣' : '▥ ▥ ▥'}</span><span>${h(v.name)}</span><span class="led ${v.status}" aria-hidden="true"></span></button>`).join('')}</div></div><footer>${capacity}U · ${this.side.toLowerCase()} elevation</footer></div><aside class="rack-inspector"><div class="metric-pair"><div><small>Space utilization</small><strong>${Math.round(occupied / capacity * 100)}<em>%</em></strong><span>${occupied} of ${capacity}U occupied</span></div><div><small>Estimated load</small><strong>${(watts / 1000).toFixed(2)}<em>kW</em></strong><span>${(config.maxWatts / 1000).toFixed(2)} kW configured budget</span></div></div>${d ? `<div class="inspector-card"><span class="eyebrow">SELECTED EQUIPMENT</span><h3>${h(d.name)}</h3>${badge(d.status, d.status === 'healthy' ? 'success' : 'warning')}<dl><dt>Identifier</dt><dd class="mono">${h(d.id)}</dd><dt>Height</dt><dd>${d.units}U</dd><dt>Position</dt><dd>U${d.start}–U${d.start + d.units - 1}</dd><dt>Power</dt><dd>${d.watts} W</dd></dl><form data-rack-form><label>Move to starting unit<input name="unit" aria-label="Starting rack unit" type="number" min="1" max="${capacity}" value="${d.start}" required ${this.readonlyMode ? 'disabled' : ''}></label><button class="button primary full" ${this.readonlyMode ? 'disabled' : ''}>Move equipment</button></form></div>` : ''}<div class="info-card"><strong>Placement is validated</strong><p>Capacity, overlapping units, and the configured power budget are checked before a move is accepted.</p></div><p class="component-note">Rear view is a presentation variant, not a port/cabling model. Local demonstration only.</p></aside></div>`);
        this.on('[data-device]', 'click', e => { this.selected = e.currentTarget.dataset.device; this.render(); });
        this.on('[data-side]', 'click', e => { this.side = e.currentTarget.dataset.side; this.render(); });
        this.on('[data-rack-form]', 'submit', e => { e.preventDefault(); try {
            this.change(moveDevice(this.value, this.selected, Number(new FormData(e.currentTarget).get('unit')), capacity, config.maxWatts), 'move-device');
        }
        catch (error) {
            this.fail(error.message);
        } });
    }
    configure(value, options = {}) { validatePresentation(options.presentation); const config = options.presentation?.rack ?? defaultRack; const errors = validateRack(value, config.units, config.maxWatts); if (errors.length)
        throw new Error(errors.join(' ')); if (!value.some(d => d.id === this.selected))
        this.selected = value[0]?.id ?? ''; super.configure(value, options); }
}
export class WaferMap extends EngineeringElement {
    selected = '0,0';
    filter = 'all';
    constructor() { super(dies); }
    render() {
        if (!this.value.some(d => d.id === this.selected))
            this.selected = this.value[0]?.id ?? '';
        const stats = waferYield(this.value), selected = this.value.find(d => d.id === this.selected);
        this.frame(`<div class="wafer-layout"><div><div class="component-toolbar"><span class="mono">${h(this.options.presentation?.wafer?.label ?? 'Synthetic wafer · W-028')}</span><div class="toolbar-spacer"></div><select aria-label="Wafer bin filter" data-bin>${['all', 'pass', 'fail', 'edge', 'untested'].map(s => `<option value="${s}" ${s === this.filter ? 'selected' : ''}>${s === 'all' ? 'All bins' : s}</option>`).join('')}</select></div><div class="wafer-canvas"><svg viewBox="0 0 540 540" role="group" aria-label="Wafer die map. Use arrow keys to inspect adjacent dies." class="wafer-svg"><circle cx="270" cy="270" r="247" class="wafer-outline"/><path d="M257 516 L270 503 L283 516" class="wafer-notch"/>${this.value.map(d => `<rect x="${270 + d.x * 18 - 8}" y="${270 + d.y * 18 - 8}" width="16" height="16" rx="2" class="die bin-${d.bin} ${d.id === this.selected ? 'selected' : ''} ${this.filter !== 'all' && this.filter !== d.bin ? 'dimmed' : ''}" role="button" tabindex="${d.id === this.selected ? '0' : '-1'}" data-die="${h(d.id)}" aria-label="Die ${h(d.id)}, ${d.bin}, value ${d.value.toFixed(2)}"/>`).join('')}<text x="270" y="22" text-anchor="middle" class="svg-text">Y− (up)</text><text x="520" y="274" class="svg-text">X+</text></svg></div></div><aside><div class="inspector-card"><span class="eyebrow">MAP SUMMARY</span><div class="wafer-yield">${stats.percent?.toFixed(1) ?? '—'}<small>%</small></div><p class="subtle">Tested-die yield · excludes edge & untested</p><div class="bin-legend">${['pass', 'fail', 'edge', 'untested'].map(b => `<div><span class="swatch bin-${b}"></span><span>${b}</span><strong>${this.value.filter(d => d.bin === b).length}</strong></div>`).join('')}</div></div>${selected ? `<div class="inspector-card"><span class="eyebrow">SELECTED DIE</span><h3 class="mono">X ${selected.x} / Y ${selected.y}</h3>${badge(selected.bin, selected.bin === 'pass' ? 'success' : selected.bin === 'fail' ? 'danger' : 'neutral')}<dl><dt>Measurement</dt><dd>${selected.value.toFixed(3)}</dd><dt>Fixture unit</dt><dd>${h(this.options.presentation?.wafer?.unit ?? 'arbitrary units')}</dd></dl></div>` : ''}<p class="component-note">Synthetic square die map. Positive X is right and positive Y is down; real wafer formats, reticle geometry, and bin definitions require domain adapters.</p></aside></div>`);
        this.on('[data-die]', 'click', e => { this.selected = e.currentTarget.dataset.die; this.render(); });
        this.on('[data-die]', 'keydown', e => { const event = e; const current = this.value.find(d => d.id === e.currentTarget.dataset.die); if (!current)
            return; const offset = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }; const delta = offset[event.key]; if (delta) {
            event.preventDefault();
            const next = this.value.find(d => d.x === current.x + delta[0] && d.y === current.y + delta[1]);
            if (next) {
                this.selected = next.id;
                this.render();
                this.querySelector(`[data-die="${CSS.escape(next.id)}"]`)?.focus();
            }
        } if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            this.select(current);
        } });
        this.on('[data-bin]', 'change', e => { this.filter = e.target.value; this.render(); });
    }
}
export class TopologyGraph extends EngineeringElement {
    selected = 'b';
    zoom = 1;
    svgId = localId('topology');
    constructor() { super(graph); }
    render() {
        if (!this.value.nodes.some(n => n.id === this.selected))
            this.selected = this.value.nodes[0]?.id ?? '';
        const byId = new Map(this.value.nodes.map(n => [n.id, n]));
        const selected = byId.get(this.selected);
        this.frame(`<div class="component-toolbar"><span class="badge tone-success">${this.value.nodes.length} services</span><span class="subtle">${this.value.edges.length} connections</span><div class="toolbar-spacer"></div><button class="button" data-fit>Fit view</button><button class="button" data-zoom-out aria-label="Zoom topology out">−</button><button class="button" data-zoom-in aria-label="Zoom topology in">+</button></div><div class="topology-canvas"><svg viewBox="0 0 ${900 / this.zoom} ${400 / this.zoom}" role="group" aria-label="Service dependency topology" class="topology-svg"><defs><pattern id="${this.svgId}-grid" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" class="grid-dot"/></pattern><marker id="${this.svgId}-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" class="edge-marker"/></marker></defs><rect width="100%" height="100%" fill="url(#${this.svgId}-grid)"/>${this.value.edges.map(e => { const a = byId.get(e.from), b = byId.get(e.to); return `<path class="graph-edge ${this.selected === a.id || this.selected === b.id ? 'active' : ''}" d="M${a.x + 168} ${a.y + 32} C${a.x + 205} ${a.y + 32},${b.x - 35} ${b.y + 32},${b.x} ${b.y + 32}" marker-end="url(#${this.svgId}-arrow)"/>`; }).join('')}${this.value.nodes.map(n => `<g role="button" tabindex="0" data-node="${h(n.id)}" aria-label="${h(n.label)}, ${h(n.kind)}, ${n.status}" class="graph-node ${n.id === this.selected ? 'selected' : ''}" transform="translate(${n.x},${n.y})"><rect width="168" height="66" rx="10"/><circle cx="18" cy="21" r="4" class="fill-${n.status === 'healthy' ? 'success' : 'warning'}"/><text x="29" y="25" class="node-kind">${h(n.kind)}</text><text x="16" y="47" class="node-label">${h(n.label)}</text></g>`).join('')}</svg></div>${selected ? `<div class="property-strip"><div><small>Selected node</small><strong>${h(selected.label)}</strong></div><div><small>Adapter</small><strong>${h(selected.kind)}</strong></div><div><small>Health</small><strong>${h(selected.status)}</strong></div><div><small>Connections</small><strong>${this.value.edges.filter(e => e.from === selected.id || e.to === selected.id).length}</strong></div></div>` : ''}<p class="component-note">Select nodes with mouse or keyboard. This is a dependency viewer, not an arbitrary workflow execution engine.</p>`);
        const choose = (e) => { this.selected = e.currentTarget.dataset.node; this.render(); };
        this.on('[data-node]', 'click', choose);
        this.on('[data-node]', 'keydown', e => { if (['Enter', ' '].includes(e.key)) {
            e.preventDefault();
            choose(e);
            this.querySelector(`[data-node="${CSS.escape(this.selected)}"]`)?.focus();
        } });
        this.on('[data-fit]', 'click', () => { this.zoom = 1; this.render(); });
        this.on('[data-zoom-in]', 'click', () => { this.zoom = Math.min(1.5, this.zoom + .1); this.render(); });
        this.on('[data-zoom-out]', 'click', () => { this.zoom = Math.max(.7, this.zoom - .1); this.render(); });
    }
    configure(value, options = {}) { const errors = validateGraph(value); if (errors.length)
        throw new Error(errors.join(' ')); super.configure(value, options); }
}
register('rf-rack', RackElevation);
register('rf-wafer', WaferMap);
register('rf-topology', TopologyGraph);
//# sourceMappingURL=spatial.js.map