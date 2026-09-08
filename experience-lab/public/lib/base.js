import { validatePresentation } from './presentation.js';
import { validateWidgetModel } from './validation.js';
import { escapeHtml as h } from './model.js';
/** Light DOM preserves one token/stylesheet/accessibility contract across React and the lab. */
export class EngineeringElement extends HTMLElement {
    value;
    options = {};
    initialized = false;
    error = '';
    constructor(initial) { super(); this.value = structuredClone(initial); }
    configure(value, options = {}) { validateWidgetModel(this.localName, value); validatePresentation(options.presentation); if (options.state && !['ready', 'loading', 'empty', 'error', 'readonly'].includes(options.state))
        throw new TypeError('Invalid widget state.'); this.value = structuredClone(value); this.options = structuredClone(options); if (this.initialized)
        this.render(); }
    get model() { return structuredClone(this.value); }
    connectedCallback() { this.initialized = true; this.classList.add('engineering-widget'); this.render(); }
    get readonlyMode() { return this.options.readonly === true || this.options.state === 'readonly'; }
    change(value, reason) { if (this.readonlyMode)
        return; validateWidgetModel(this.localName, value); this.value = value; this.error = ''; this.dispatchEvent(new CustomEvent('model-change', { detail: { value: structuredClone(value), reason }, bubbles: true })); this.render(); }
    select(detail) { this.dispatchEvent(new CustomEvent('record-select', { detail, bubbles: true })); }
    fail(message) { this.error = message; const el = this.querySelector('[data-widget-alert]'); if (el)
        el.textContent = message; }
    frame(content) {
        const state = this.options.state ?? 'ready';
        if (state === 'loading') {
            this.innerHTML = '<div class="widget-state" role="status"><div class="skeleton-bar"></div><div class="skeleton-bar short"></div><p>Loading this example…</p></div>';
            return;
        }
        if (state === 'empty') {
            this.innerHTML = '<div class="widget-state"><span class="state-symbol" aria-hidden="true">◫</span><h3>No records yet</h3><p>The component preserves its layout when there is no data.</p></div>';
            return;
        }
        if (state === 'error') {
            this.innerHTML = '<div class="widget-state" role="alert"><span class="state-symbol" aria-hidden="true">!</span><h3>Data could not be loaded</h3><p>Example failure state. Your existing records have not changed.</p><button data-retry class="button">Retry example</button></div>';
            this.querySelector('[data-retry]')?.addEventListener('click', () => { this.options = { ...this.options, state: 'ready' }; this.render(); });
            return;
        }
        const active = document.activeElement instanceof HTMLInputElement && this.contains(document.activeElement) ? document.activeElement : null;
        const focus = active?.dataset.focus;
        const cursor = active?.selectionStart;
        this.innerHTML = `${this.readonlyMode ? '<div class="readonly-note">Read-only preview · mutation controls disabled</div>' : ''}<div data-widget-alert role="alert" class="widget-alert">${h(this.error)}</div>${content}`;
        if (focus)
            queueMicrotask(() => { const next = this.querySelector(`[data-focus="${focus}"]`); next?.focus(); if (next && cursor !== null && cursor !== undefined)
                try {
                    next.setSelectionRange(cursor, cursor);
                }
                catch { } });
    }
    on(selector, event, handler) { this.querySelectorAll(selector).forEach(el => el.addEventListener(event, handler)); }
    input(selector) { return this.querySelector(selector); }
}
export function register(name, component) { if (!customElements.get(name))
    customElements.define(name, component); }
export const badge = (label, tone = 'neutral') => `<span class="badge tone-${h(tone)}"><span class="badge-dot" aria-hidden="true"></span>${h(label)}</span>`;
export const sectionHeading = (eyebrow, title, description = '') => `<div class="section-heading"><div><span class="eyebrow">${h(eyebrow)}</span><h2>${h(title)}</h2>${description ? `<p>${h(description)}</p>` : ''}</div></div>`;
//# sourceMappingURL=base.js.map