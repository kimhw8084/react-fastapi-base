import { defaultSchedule, validatePresentation } from './presentation.js';
import { EngineeringElement, register, badge } from './base.js';
import { tasks, stateRows, calendarEvents, trace } from './fixtures.js';
import { escapeHtml as h, localId, moveTask, validateTasks } from './model.js';
export class GanttSchedule extends EngineeringElement {
    selected = 'T3';
    dayWidth = 27;
    constructor() { super(tasks); }
    render() {
        const config = this.options.presentation?.schedule ?? defaultSchedule, days = config.days, start = new Date(config.startDate + 'T00:00:00Z'), locale = this.options.presentation?.locale ?? 'en';
        const dateAt = (day) => new Date(start.getTime() + day * 86400000);
        const dayLabel = (day) => new Intl.DateTimeFormat(locale, { month: 'short', day: 'numeric', timeZone: 'UTC' }).format(dateAt(day));
        const period = new Intl.DateTimeFormat(locale, { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(start);
        const selected = this.value.find(t => t.id === this.selected) ?? this.value[0];
        const w = this.dayWidth;
        this.frame(`<div class="component-toolbar"><span class="badge tone-info">${h(period)}</span><span class="subtle">Finish-to-start dependencies</span><div class="toolbar-spacer"></div><button class="button" data-zoom-out aria-label="Zoom schedule out">−</button><button class="button" data-zoom-in aria-label="Zoom schedule in">+</button></div><div class="gantt-scroll"><div class="gantt" style="--day-width:${w}px;min-width:${240 + days * w}px"><div class="gantt-row gantt-heading"><div class="gantt-label">Workstream / owner</div><div class="gantt-days">${Array.from({ length: days }, (_, i) => `<span class="${[0, 6].includes(dateAt(i).getUTCDay()) ? 'weekend' : ''}">${dateAt(i).getUTCDate()}</span>`).join('')}</div></div>${this.value.map((t, i) => `<div class="gantt-row ${t.id === this.selected ? 'selected' : ''}"><div class="gantt-label"><button class="record-link" data-task="${h(t.id)}">${h(t.name)}</button><small>${h(t.owner)}${t.dependencies.length ? ` · after ${t.dependencies.map(h).join(', ')}` : ''}</small></div><div class="gantt-lane" style="background-size:${w}px 100%"><button class="gantt-task series-${i % 4}" data-task="${h(t.id)}" aria-label="${h(t.name)}, ${h(dayLabel(t.start))} through ${h(dayLabel(t.start + t.duration - 1))}, ${t.progress}% complete. Select to change dates." style="left:${t.start * w}px;width:${t.duration * w - 4}px"><span class="gantt-progress" style="width:${t.progress}%"></span><span>${h(t.name)}</span></button></div></div>`).join('')}</div></div>
  ${selected ? `<form class="inline-inspector" data-task-form><div><strong>${h(selected.name)}</strong><span>Selected task · offset days from ${h(config.startDate)}</span></div><label>Start day<input name="start" type="number" min="1" max="${days}" value="${selected.start + 1}" required ${this.readonlyMode ? 'disabled' : ''}></label><label>Duration<input name="duration" type="number" min="1" max="${days}" value="${selected.duration}" required ${this.readonlyMode ? 'disabled' : ''}></label><button class="button primary" type="submit" ${this.readonlyMode ? 'disabled' : ''}>Apply dates</button></form>` : ''}<p class="component-note">Dates are model-controlled. Invalid dependency overlaps and circular dependencies are rejected. No automatic scheduling or critical-path solver is claimed.</p>`);
        this.on('[data-task]', 'click', e => { this.selected = e.currentTarget.dataset.task; this.render(); });
        this.on('[data-task-form]', 'submit', e => { e.preventDefault(); const form = e.currentTarget; const data = new FormData(form); try {
            this.change(moveTask(this.value, this.selected, Number(data.get('start')) - 1, Number(data.get('duration')), days), 'reschedule');
        }
        catch (error) {
            this.fail(error.message);
        } });
        this.on('[data-zoom-in]', 'click', () => { this.dayWidth = Math.min(48, this.dayWidth + 4); this.render(); });
        this.on('[data-zoom-out]', 'click', () => { this.dayWidth = Math.max(18, this.dayWidth - 4); this.render(); });
    }
    configure(value, options = {}) { validatePresentation(options.presentation); const errors = validateTasks(value, (options.presentation?.schedule ?? defaultSchedule).days); if (errors.length)
        throw new Error(errors.join(' ')); if (!value.some(t => t.id === this.selected))
        this.selected = value[0]?.id ?? ''; super.configure(value, options); }
}
export class StateTimeline extends EngineeringElement {
    selected = null;
    constructor() { super(stateRows); }
    render() { this.frame(`<div class="legend">${['Productive', 'Standby', 'Maintenance', 'Engineering'].map((s, i) => badge(s, ['success', 'neutral', 'warning', 'info'][i])).join('')}</div><div class="state-timeline"><div class="state-scale"><span></span><div>${['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'].map(t => `<span>${t}</span>`).join('')}</div></div>${this.value.map(row => `<div class="state-row"><strong>${h(row.name)}</strong><div class="state-track">${row.segments.map((s, i) => `<button class="state-block fill-${s.tone}" style="left:${s.start / 24 * 100}%;width:${s.duration / 24 * 100}%" data-segment="${h(row.name)}|${i}" aria-label="${h(row.name)}: ${h(s.label)} from ${s.start}:00 for ${s.duration} hours"><span>${h(s.label)}</span></button>`).join('')}</div></div>`).join('')}</div><div class="timeline-detail" role="status">${h(this.selected ?? 'Select an interval to inspect its state and duration.')}</div><p class="component-note">Synthetic operational-state intervals. These are not a SEMI E10/E116 compliance implementation.</p>`); this.on('[data-segment]', 'click', e => { const [name, index] = e.currentTarget.dataset.segment.split('|'); const s = this.value.find(v => v.name === name)?.segments[Number(index)]; this.selected = s ? `${name} · ${s.label} · ${s.start.toFixed(1)}–${(s.start + s.duration).toFixed(1)} h · duration ${s.duration.toFixed(1)} h` : null; this.render(); }); }
}
export class MonthCalendar extends EngineeringElement {
    year = 2026;
    month = 8;
    selected = '2026-09-08';
    constructor() { super(calendarEvents); }
    render() {
        const days = new Date(Date.UTC(this.year, this.month + 1, 0)).getUTCDate(), offset = (new Date(Date.UTC(this.year, this.month, 1)).getUTCDay() + 6) % 7;
        const key = (day) => `${this.year}-${String(this.month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const title = new Intl.DateTimeFormat('en', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(Date.UTC(this.year, this.month, 1)));
        this.frame(`<div class="component-toolbar"><h3>${h(title)}</h3><div class="toolbar-spacer"></div><button class="button" data-prev-month aria-label="Previous month">‹</button><button class="button" data-next-month aria-label="Next month">›</button></div><div class="calendar-weekdays">${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(s => `<span>${s}</span>`).join('')}</div><div class="calendar-days">${Array.from({ length: offset }, () => '<div class="calendar-day outside"></div>').join('')}${Array.from({ length: days }, (_, i) => { const date = key(i + 1), events = this.value.filter(e => e.date === date); return `<button class="calendar-day ${date === this.selected ? 'is-selected' : ''}" data-date="${date}" aria-label="${date}, ${events.length} events"><span>${i + 1}</span>${events.map(e => `<small class="tone-${e.tone}">${h(e.title)}</small>`).join('')}</button>`; }).join('')}</div><form class="inline-inspector" data-event-form><div><strong>${h(this.selected)}</strong><span>${this.value.filter(e => e.date === this.selected).length} events on this day</span></div><label>Event title<input name="title" placeholder="Add a local example event" maxlength="100" required ${this.readonlyMode ? 'disabled' : ''}></label><button class="button primary" ${this.readonlyMode ? 'disabled' : ''}>Add event</button></form><p class="component-note">Date-only calendar. Recurrence, shared availability, and external calendar synchronization remain separate capabilities.</p>`);
        this.on('[data-date]', 'click', e => { this.selected = e.currentTarget.dataset.date; this.render(); });
        this.on('[data-event-form]', 'submit', e => { e.preventDefault(); const title = String(new FormData(e.currentTarget).get('title')).trim(); if (title)
            this.change([...this.value, { id: localId(), title, date: this.selected, tone: 'info' }], 'create-event'); });
        const shift = (by) => { const d = new Date(Date.UTC(this.year, this.month + by, 1)); this.year = d.getUTCFullYear(); this.month = d.getUTCMonth(); this.selected = key(1); this.render(); };
        this.on('[data-prev-month]', 'click', () => shift(-1));
        this.on('[data-next-month]', 'click', () => shift(1));
    }
}
export class TraceWaterfall extends EngineeringElement {
    selected = 's3';
    constructor() { super(trace); }
    render() { const total = Math.max(1, ...this.value.map(s => s.start + s.duration)); const s = this.value.find(v => v.id === this.selected); this.frame(`<div class="component-toolbar"><span class="mono trace-id">Trace 7c29b6e1</span>${badge(this.value.some(span => span.status === 'error') ? 'Contains errors' : 'Successful', this.value.some(span => span.status === 'error') ? 'danger' : 'success')}<div class="toolbar-spacer"></div><strong>${total} ms</strong><span class="subtle">${this.value.length} spans</span></div><div class="trace-waterfall"><div class="trace-heading"><span>Operation / service</span><div>${[0, .25, .5, .75, 1].map(v => `<span>${Math.round(v * total)} ms</span>`).join('')}</div></div>${this.value.map(row => `<button class="trace-row ${row.id === this.selected ? 'selected' : ''}" data-span="${h(row.id)}" aria-label="${h(row.name)}, ${row.duration} milliseconds"><span style="padding-left:${row.depth * 16}px"><strong>${h(row.name)}</strong><small>${h(row.service)}</small></span><span class="trace-track"><span class="trace-bar fill-${row.status === 'error' ? 'danger' : 'info'}" style="left:${row.start / total * 100}%;width:${row.duration / total * 100}%">${row.duration}ms</span></span></button>`).join('')}</div>${s ? `<div class="property-strip"><div><small>Service</small><strong>${h(s.service)}</strong></div><div><small>Duration</small><strong>${s.duration} ms</strong></div><div><small>Start offset</small><strong>+${s.start} ms</strong></div><div><small>Operation</small><strong>${h(s.name)}</strong></div></div>` : ''}<p class="component-note">Synthetic trace. Production tracing requires a configured telemetry source.</p>`); this.on('[data-span]', 'click', e => { this.selected = e.currentTarget.dataset.span; this.render(); }); }
}
register('rf-gantt', GanttSchedule);
register('rf-state-timeline', StateTimeline);
register('rf-calendar', MonthCalendar);
register('rf-trace-waterfall', TraceWaterfall);
//# sourceMappingURL=scheduling.js.map