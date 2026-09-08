export function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
export function finite(v, fallback) { return typeof v === 'number' && Number.isFinite(v) ? v : fallback; }
export function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
export function assertUnique(ids) { if (new Set(ids).size !== ids.length)
    throw new Error('Duplicate identifiers are not allowed.'); }
export function validateTasks(tasks, horizon = 30) {
    const errors = [];
    const byId = new Map(tasks.map(t => [t.id, t]));
    if (byId.size !== tasks.length)
        errors.push('Task identifiers must be unique.');
    for (const t of tasks) {
        if (!t.id || !t.name.trim())
            errors.push('A task needs an identifier and name.');
        if (!Number.isInteger(t.start) || !Number.isInteger(t.duration) || t.start < 0 || t.duration < 1 || t.start + t.duration > horizon)
            errors.push(`${t.name}: dates are outside the schedule.`);
        if (!Number.isFinite(t.progress) || t.progress < 0 || t.progress > 100)
            errors.push(`${t.name}: progress must be 0–100.`);
        for (const id of t.dependencies) {
            const d = byId.get(id);
            if (!d)
                errors.push(`${t.name}: dependency ${id} is missing.`);
            else if (d.start + d.duration > t.start)
                errors.push(`${t.name}: overlaps prerequisite ${d.name}.`);
        }
    }
    const visiting = new Set(), done = new Set();
    const visit = (id) => { if (visiting.has(id))
        return true; if (done.has(id))
        return false; visiting.add(id); for (const next of byId.get(id)?.dependencies ?? [])
        if (visit(next))
            return true; visiting.delete(id); done.add(id); return false; };
    if (tasks.some(t => visit(t.id)))
        errors.push('Circular task dependencies are not allowed.');
    return [...new Set(errors)];
}
export function moveTask(tasks, id, start, duration, horizon = 30) {
    if (!tasks.some(t => t.id === id))
        throw new Error('Task not found.');
    const next = tasks.map(t => t.id === id ? { ...t, start, duration } : t);
    const errors = validateTasks(next, horizon);
    if (errors.length)
        throw new Error(errors.join(' '));
    return next;
}
export function validateRack(devices, capacity = 42, maxWatts = 12000) {
    const errors = [];
    const occupied = new Set();
    if (!Number.isInteger(capacity) || capacity < 1 || capacity > 100)
        errors.push('Invalid rack capacity.');
    if (new Set(devices.map(d => d.id)).size !== devices.length)
        errors.push('Device identifiers must be unique.');
    for (const d of devices) {
        if (!Number.isInteger(d.start) || !Number.isInteger(d.units) || d.start < 1 || d.units < 1 || d.start + d.units - 1 > capacity) {
            errors.push(`${d.name}: outside rack capacity.`);
            continue;
        }
        if (!Number.isFinite(d.watts) || d.watts < 0)
            errors.push(`${d.name}: invalid power.`);
        for (let u = d.start; u < d.start + d.units; u++) {
            if (occupied.has(u))
                errors.push(`Collision at U${u}.`);
            occupied.add(u);
        }
    }
    if (devices.reduce((n, d) => n + d.watts, 0) > maxWatts)
        errors.push('Configured rack power budget exceeded.');
    return errors;
}
export function moveDevice(devices, id, start, capacity = 42, maxWatts = 12000) {
    if (!devices.some(d => d.id === id))
        throw new Error('Device not found.');
    const next = devices.map(d => d.id === id ? { ...d, start } : d);
    const errors = validateRack(next, capacity, maxWatts);
    if (errors.length)
        throw new Error(errors.join(' '));
    return next;
}
export function waferYield(dies) { const tested = dies.filter(d => d.bin === 'pass' || d.bin === 'fail').length, passed = dies.filter(d => d.bin === 'pass').length; return { tested, passed, percent: tested ? passed / tested * 100 : null }; }
export function sampleStats(values) { const valid = values.filter(Number.isFinite); if (valid.length < 2)
    return null; const mean = valid.reduce((a, b) => a + b, 0) / valid.length; return { mean, std: Math.sqrt(valid.reduce((n, v) => n + (v - mean) ** 2, 0) / (valid.length - 1)), count: valid.length }; }
export function violations(values, limits) { if (!Number.isFinite(limits.low) || !Number.isFinite(limits.high) || limits.low >= limits.high)
    throw new Error('Invalid control limits.'); return values.flatMap((v, i) => Number.isFinite(v) && (v < limits.low || v > limits.high) ? [i] : []); }
export function paginate(rows, page, size) { if (!Number.isInteger(size) || size < 1 || !Number.isInteger(page) || page < 1)
    throw new Error('Invalid pagination.'); return rows.slice((page - 1) * size, page * size); }
export function csvCell(value) { let s = String(value ?? ''); if (/^[\s]*[=+@-]/.test(s))
    s = "'" + s; return '"' + s.replaceAll('"', '""') + '"'; }
export function recordsCsv(rows) { return ['id,title,owner,status,priority,updated', ...rows.map(r => [r.id, r.title, r.owner, r.status, r.priority, r.updated].map(csvCell).join(','))].join('\r\n'); }
export function diffLines(before, after) { const a = before.split('\n'), b = after.split('\n'); return Array.from({ length: Math.max(a.length, b.length) }, (_, i) => ({ before: a[i] ?? '', after: b[i] ?? '', changed: a[i] !== b[i] })); }
export function validateGraph(model) { const ids = new Set(model.nodes.map(n => n.id)); const errors = []; if (ids.size !== model.nodes.length)
    errors.push('Node identifiers must be unique.'); for (const n of model.nodes)
    if (!Number.isFinite(n.x) || !Number.isFinite(n.y))
        errors.push('Invalid node position.'); for (const e of model.edges)
    if (!ids.has(e.from) || !ids.has(e.to))
        errors.push('An edge references a missing node.'); return errors; }
export function storageRead(key, fallback, validate) { try {
    const v = JSON.parse(localStorage.getItem(key) ?? 'null');
    return validate(v) ? v : fallback;
}
catch {
    return fallback;
} }
export function downloadText(name, text, type = 'text/plain') { const blob = new Blob([text], { type }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000); }
/** Local UI/fixture identifier, never an authentication token. Works without secure-context randomUUID. */
export function localId(prefix = 'example') { const bytes = new Uint8Array(16); globalThis.crypto.getRandomValues(bytes); return prefix + '-' + Array.from(bytes, b => b.toString(16).padStart(2, '0')).join(''); }
//# sourceMappingURL=model.js.map