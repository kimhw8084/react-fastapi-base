import { EngineeringElement, register, badge } from './base.js';
import { records as fixture } from './fixtures.js';
import { escapeHtml as h, paginate, recordsCsv, downloadText } from './model.js';
export class RecordTable extends EngineeringElement {
    search = '';
    status = 'All statuses';
    sort = 'id';
    descending = false;
    page = 1;
    grouped = false;
    selected = new Set();
    constructor() { super(fixture); }
    render() {
        const filtered = this.value.filter(r => `${r.id} ${r.title} ${r.owner}`.toLowerCase().includes(this.search.toLowerCase()) && (this.status === 'All statuses' || r.status === this.status));
        const sorted = [...filtered].sort((a, b) => String(a[this.sort]).localeCompare(String(b[this.sort])) * (this.descending ? -1 : 1));
        const pages = Math.max(1, Math.ceil(sorted.length / 12));
        this.page = Math.min(this.page, pages);
        const rows = paginate(sorted, this.page, 12);
        const cell = (r) => `<tr data-row="${h(r.id)}"><td><input type="checkbox" aria-label="Select ${h(r.id)}" data-select="${h(r.id)}" ${this.selected.has(r.id) ? 'checked' : ''}></td><td class="mono subtle">${h(r.id)}</td><td><button class="record-link" data-open="${h(r.id)}">${h(r.title)}</button></td><td>${badge(r.status, r.status === 'Done' ? 'success' : r.status === 'Review' ? 'warning' : r.status === 'In progress' ? 'info' : 'neutral')}</td><td><span class="priority ${h(r.priority.toLowerCase())}"><span aria-hidden="true">${r.priority === 'High' ? '▰' : r.priority === 'Medium' ? '▱' : '−'}</span> ${h(r.priority)}</span></td><td><span class="person"><span class="avatar small" aria-hidden="true">${h(r.owner.split(' ').map(s => s[0]).join(''))}</span>${h(r.owner)}</span></td><td class="subtle">${h(r.updated.slice(5))}</td></tr>`;
        const bodies = this.grouped ? [...new Set(rows.map(r => r.status))].map(s => `<tr class="group-row"><th colspan="7" scope="rowgroup">${h(s)} <span>${rows.filter(r => r.status === s).length}</span></th></tr>${rows.filter(r => r.status === s).map(cell).join('')}`).join('') : rows.map(cell).join('');
        this.frame(`<div class="component-toolbar"><div class="search-field"><span aria-hidden="true">⌕</span><input aria-label="Search records" data-focus="table-search" placeholder="Search by title, ID, or owner…" value="${h(this.search)}"></div><select aria-label="Filter status" data-filter>${['All statuses', 'Backlog', 'In progress', 'Review', 'Done', 'Archived'].map(v => `<option ${v === this.status ? 'selected' : ''}>${v}</option>`).join('')}</select><button class="button ${this.grouped ? 'is-active' : ''}" data-group aria-pressed="${this.grouped}">☷ Group</button><button class="button" data-export>↓ Export</button></div>
  ${this.selected.size ? `<div class="selection-bar"><strong>${this.selected.size} selected on this page</strong><button class="button" data-clear>Clear selection</button><button class="button" data-archive ${this.readonlyMode ? 'disabled' : ''}>Archive selected</button></div>` : ''}
  <div class="table-scroll"><table class="data-table"><caption class="sr-only">Work items, ${filtered.length} matching records</caption><thead><tr><th><input type="checkbox" aria-label="Select current page" data-all ${rows.length && rows.every(r => this.selected.has(r.id)) ? 'checked' : ''}></th>${['id', 'title', 'status', 'priority', 'owner', 'updated'].map(k => `<th scope="col" aria-sort="${this.sort === k ? (this.descending ? 'descending' : 'ascending') : 'none'}"><button data-sort="${k}">${{ id: 'Record', title: 'Work item', status: 'Status', priority: 'Priority', owner: 'Owner', updated: 'Updated' }[k]} <span aria-hidden="true">${this.sort === k ? (this.descending ? '↓' : '↑') : '↕'}</span></button></th>`).join('')}</tr></thead><tbody>${bodies || '<tr><td colspan="7" class="empty-cell">No records match your filters.</td></tr>'}</tbody></table></div>
  <footer class="table-footer"><span>${sorted.length ? ((this.page - 1) * 12 + 1) : 0}–${Math.min(this.page * 12, sorted.length)} of ${sorted.length} records</span><span class="subtle">Synthetic fixture · local edits only</span><div class="pagination"><button class="button icon-button" aria-label="Previous page" data-prev ${this.page === 1 ? 'disabled' : ''}>‹</button><span>Page ${this.page} of ${pages}</span><button class="button icon-button" aria-label="Next page" data-next ${this.page === pages ? 'disabled' : ''}>›</button></div></footer>`);
        this.on('[data-focus="table-search"]', 'input', e => { this.search = e.target.value; this.page = 1; this.selected.clear(); this.render(); });
        this.on('[data-filter]', 'change', e => { this.status = e.target.value; this.page = 1; this.selected.clear(); this.render(); });
        this.on('[data-group]', 'click', () => { this.grouped = !this.grouped; this.render(); });
        this.on('[data-sort]', 'click', e => { const key = e.currentTarget.dataset.sort; this.descending = this.sort === key ? !this.descending : false; this.sort = key; this.render(); });
        this.on('[data-select]', 'change', e => { const input = e.currentTarget; input.checked ? this.selected.add(input.dataset.select) : this.selected.delete(input.dataset.select); this.render(); });
        this.on('[data-all]', 'change', e => { if (e.target.checked)
            rows.forEach(r => this.selected.add(r.id));
        else
            this.selected.clear(); this.render(); });
        this.on('[data-prev]', 'click', () => { this.page--; this.selected.clear(); this.render(); });
        this.on('[data-next]', 'click', () => { this.page++; this.selected.clear(); this.render(); });
        this.on('[data-clear]', 'click', () => { this.selected.clear(); this.render(); });
        this.on('[data-archive]', 'click', () => { const ids = new Set(this.selected); this.selected.clear(); this.change(this.value.map(r => ids.has(r.id) ? { ...r, status: 'Archived' } : r), 'archive'); });
        this.on('[data-open]', 'click', e => this.select(this.value.find(r => r.id === e.currentTarget.dataset.open)));
        this.on('[data-export]', 'click', () => downloadText('work-items.csv', recordsCsv(sorted), 'text/csv'));
    }
}
export class WorkBoard extends EngineeringElement {
    dragId = null;
    constructor() { super(fixture.slice(0, 12)); }
    render() {
        const statuses = ['Backlog', 'In progress', 'Review', 'Done'];
        this.frame(`<div class="board">${statuses.map((status, i) => `<section class="board-column" data-lane="${status}" aria-label="${status}"><header>${badge(status, ['neutral', 'info', 'warning', 'success'][i])}<span class="count">${this.value.filter(r => r.status === status).length}</span></header>${this.value.filter(r => r.status === status).map(r => `<article class="board-card" draggable="${!this.readonlyMode}" data-card="${h(r.id)}"><div class="card-meta"><span class="mono">${h(r.id)}</span><span class="priority ${h(r.priority.toLowerCase())}">${h(r.priority)}</span></div><button class="record-link" data-detail="${h(r.id)}">${h(r.title)}</button><footer><span class="avatar small" title="${h(r.owner)}">${h(r.owner.split(' ').map(s => s[0]).join(''))}</span><select aria-label="Move ${h(r.id)}" data-move="${h(r.id)}" ${this.readonlyMode ? 'disabled' : ''}>${statuses.map(s => `<option ${s === status ? 'selected' : ''}>${s}</option>`).join('')}</select></footer></article>`).join('')}</section>`).join('')}</div><p class="component-note">Drag a card or use its status selector. Both paths update the same model.</p>`);
        this.on('[data-card]', 'dragstart', e => { if (this.readonlyMode) {
            e.preventDefault();
            return;
        } this.dragId = e.currentTarget.dataset.card; e.dataTransfer?.setData('text/plain', this.dragId); });
        this.on('[data-card]', 'dragend', () => { this.dragId = null; });
        this.on('[data-lane]', 'dragover', e => { if (!this.readonlyMode)
            e.preventDefault(); });
        this.on('[data-lane]', 'drop', e => { e.preventDefault(); if (this.dragId) {
            this.move(this.dragId, e.currentTarget.dataset.lane);
            this.dragId = null;
        } });
        this.on('[data-move]', 'change', e => { const el = e.target; this.move(el.dataset.move, el.value); });
        this.on('[data-detail]', 'click', e => this.select(this.value.find(r => r.id === e.currentTarget.dataset.detail)));
    }
    move(id, status) { this.change(this.value.map(r => r.id === id ? { ...r, status } : r), 'move-status'); }
}
register('rf-record-table', RecordTable);
register('rf-work-board', WorkBoard);
//# sourceMappingURL=table.js.map