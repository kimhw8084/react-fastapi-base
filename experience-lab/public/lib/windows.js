import { containDialogFocus } from './dialog.js';
import { EngineeringElement, register, badge } from './base.js';
import { escapeHtml as h, localId } from './model.js';
export class WindowGallery extends EngineeringElement {
    opener = null;
    dirty = false;
    step = 1;
    draftName = '';
    draftLayout = 'Table + inspector';
    windowCounter = 0;
    constructor() { super({ lastAction: 'No action yet' }); }
    render() {
        this.frame(`<div class="windows-grid">${[
            ['dialog', 'Modal dialog', 'Focused tasks with trapped focus and guarded dismissal.'], ['drawer', 'Inspector drawer', 'Right-hand context without abandoning the workspace.'], ['sheet', 'Bottom sheet', 'A compact responsive action surface.'], ['fullscreen', 'Full-screen workspace', 'An expanded editor with a stable action footer.'], ['wizard', 'Guided wizard', 'Validated steps, progress, back navigation and review.'], ['confirm', 'Confirmation dialog', 'Explicit confirmation for a consequential action.']
        ].map(([kind, title, desc]) => `<button class="window-demo-card" data-window="${kind}"><span class="window-mini mini-${kind}" aria-hidden="true"><i></i><b></b></span><strong>${title}</strong><span>${desc}</span><small>Open example ↗</small></button>`).join('')}</div><div class="overlay-extras"><div><span class="eyebrow">NON-MODAL SURFACES</span><h3>Anchored actions & feedback</h3></div><details class="popover-example"><summary class="button">Action popover ▾</summary><div class="popover-panel"><strong>Workspace actions</strong><button data-popover-action="Duplicate view">Duplicate view</button><button data-popover-action="Export selection">Export selection</button><button data-popover-action="Pin workspace">Pin workspace</button></div></details><button class="button" data-toast>Show notification</button><button class="button" title="Supporting information never hides a required action.">Hover tooltip</button></div><div class="last-action" role="status">${h(this.value.lastAction)}</div>`);
        this.on('[data-window]', 'click', e => { this.opener = e.currentTarget; this.open(this.opener.dataset.window); });
        this.on('[data-toast]', 'click', () => this.dispatchEvent(new CustomEvent('lab-notify', { detail: 'Notification delivered. This message is announced without moving focus.', bubbles: true })));
        this.on('[data-popover-action]', 'click', e => { this.value.lastAction = e.currentTarget.dataset.popoverAction + ' requested in the example.'; this.render(); });
    }
    open(kind) {
        this.dirty = false;
        this.step = 1;
        this.draftName = '';
        this.draftLayout = 'Table + inspector';
        const dialog = document.createElement('dialog');
        dialog.className = `lab-dialog placement-${kind}`;
        const titleId = `rf-window-title-${++this.windowCounter}-${localId()}`;
        dialog.setAttribute('aria-labelledby', titleId);
        const render = () => {
            const title = { dialog: 'Create a workspace', drawer: 'Record inspector', sheet: 'Quick actions', fullscreen: 'Full-screen editor', wizard: 'Configure your workspace', confirm: 'Archive this example?' }[kind];
            dialog.innerHTML = `<header><div><span class="eyebrow">${kind === 'wizard' ? `STEP ${this.step} OF 3` : 'WINDOW SYSTEM'}</span><h2 id="${titleId}">${title}</h2></div><button class="button icon-button" aria-label="Close window" data-close>×</button></header><div class="dialog-body">${kind === 'confirm' ? '<p>This only records a confirmation in the lab. No application data will be archived.</p>' : kind === 'sheet' ? '<p>Choose an action without leaving the current view.</p><div class="sheet-actions"><button class="button" data-finish>Copy reference</button><button class="button" data-finish>Inspect definition</button></div>' : kind === 'wizard' ? `<div class="stepper">${[1, 2, 3].map(s => `<span class="${s <= this.step ? 'complete' : ''}">${s}</span>`).join('')}</div>${this.step === 1 ? '<label>Workspace name<input data-draft placeholder="e.g. Equipment registry" minlength="2" required></label>' : this.step === 2 ? '<label>Layout<select><option>Table + inspector</option><option>Board</option><option>Timeline</option></select></label>' : '<div class="info-card"><strong>Ready to create the local example</strong><p>Review completed. No production workspace is created by this demonstration.</p></div>'}` : kind === 'drawer' ? `<div class="dossier-avatar">WR</div><h3>Workspace reference</h3>${badge('Active', 'success')}<dl><dt>Owner</dt><dd>Engineering team</dd><dt>Revision</dt><dd>4</dd><dt>Visibility</dt><dd>Team</dd></dl><label>Notes<textarea rows="5" data-draft placeholder="Add a local note"></textarea></label>` : `<p>Consistent focus, keyboard behavior, and unsaved-change handling across every editor surface.</p><label>Workspace name<input data-draft placeholder="Equipment registry" required></label><label>Description<textarea data-draft rows="${kind === 'fullscreen' ? 10 : 4}" placeholder="What will this workspace help your team do?"></textarea></label>`}<div class="dialog-validation" role="alert"></div></div><footer>${kind === 'wizard' && this.step > 1 ? '<button class="button" data-back>Back</button>' : ''}<div class="toolbar-spacer"></div><button class="button" data-close>Cancel</button>${kind !== 'sheet' ? `<button class="button ${kind === 'confirm' ? 'danger' : 'primary'}" data-finish ${this.readonlyMode ? 'disabled' : ''}>${kind === 'confirm' ? 'Confirm archive' : kind === 'wizard' && this.step < 3 ? 'Continue' : 'Save example'}</button>` : ''}</footer>`;
            if (kind === 'wizard') {
                const name = dialog.querySelector('input[data-draft]');
                if (name)
                    name.value = this.draftName;
                const layout = dialog.querySelector('select');
                if (layout) {
                    layout.value = this.draftLayout;
                    layout.addEventListener('change', () => { this.draftLayout = layout.value; this.dirty = true; });
                }
            }
            if (this.readonlyMode)
                dialog.querySelectorAll('input,textarea,select').forEach(el => el.disabled = true);
            dialog.querySelectorAll('[data-draft]').forEach(el => el.addEventListener('input', () => { this.dirty = true; if (kind === 'wizard' && el instanceof HTMLInputElement)
                this.draftName = el.value; }));
            dialog.querySelectorAll('[data-close]').forEach(el => el.addEventListener('click', () => requestClose()));
            dialog.querySelector('[data-back]')?.addEventListener('click', () => { this.step--; render(); });
            dialog.querySelectorAll('[data-finish]').forEach(el => el.addEventListener('click', () => {
                if (this.readonlyMode)
                    return;
                if (kind === 'wizard' && this.step < 3) {
                    const draft = dialog.querySelector('input[data-draft]');
                    if (draft && draft.value.trim().length < 2) {
                        dialog.querySelector('.dialog-validation').textContent = 'Enter at least two characters.';
                        draft.focus();
                        return;
                    }
                    this.step++;
                    this.dirty = true;
                    render();
                    return;
                }
                if (kind === 'dialog' || kind === 'fullscreen') {
                    const draft = dialog.querySelector('input[data-draft]');
                    if (!draft?.value.trim()) {
                        dialog.querySelector('.dialog-validation').textContent = 'Workspace name is required.';
                        draft?.focus();
                        return;
                    }
                }
                this.dirty = false;
                this.value.lastAction = `${title}: local example completed.`;
                dialog.close();
                this.render();
            }));
            queueMicrotask(() => dialog.querySelector('input,select,[data-close]')?.focus());
        };
        const requestClose = () => {
            if (!this.dirty) {
                dialog.close();
                return;
            }
            if (dialog.querySelector('[data-discard]'))
                return;
            const guard = document.createElement('div');
            guard.className = 'discard-guard';
            guard.setAttribute('role', 'alert');
            guard.innerHTML = '<strong>Discard unsaved changes?</strong><p>Your local edits will be lost.</p><button class="button" data-keep>Keep editing</button><button class="button danger" data-discard>Discard changes</button>';
            dialog.querySelector('.dialog-body')?.append(guard);
            guard.querySelector('[data-keep]')?.addEventListener('click', () => { guard.remove(); dialog.querySelector('[data-draft]')?.focus(); });
            guard.querySelector('[data-discard]')?.addEventListener('click', () => { this.dirty = false; dialog.close(); });
            guard.querySelector('[data-keep]')?.focus();
        };
        dialog.addEventListener('cancel', e => { e.preventDefault(); requestClose(); });
        dialog.addEventListener('click', e => { if (e.target === dialog) {
            const r = dialog.getBoundingClientRect();
            if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom)
                requestClose();
        } });
        dialog.addEventListener('close', () => { dialog.remove(); if (this.opener?.isConnected)
            this.opener.focus();
        else
            this.querySelector(`[data-window="${kind}"]`)?.focus(); });
        render();
        containDialogFocus(dialog);
        document.body.append(dialog);
        dialog.showModal();
    }
}
register('rf-windows', WindowGallery);
//# sourceMappingURL=windows.js.map