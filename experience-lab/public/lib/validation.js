const object = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
const text = (v) => typeof v === 'string' && v.length <= 65536;
const number = (v) => typeof v === 'number' && Number.isFinite(v);
const integer = (v) => number(v) && Number.isInteger(v);
const one = (v, values) => typeof v === 'string' && values.includes(v);
const tone = (v) => one(v, ['neutral', 'info', 'success', 'warning', 'danger']);
const strings = (v) => Array.isArray(v) && v.length <= 1000 && v.every(text);
function records(value, check, max = 100000) { return Array.isArray(value) && value.length <= max && value.every(v => object(v) && check(v)); }
function unique(value, key) { if (!Array.isArray(value))
    return false; const ids = value.map(v => object(v) ? v[key] : undefined); return new Set(ids).size === ids.length; }
const identity = (v) => text(v.id) && String(v.id).length > 0;
const position = (v, min, max) => number(v) && v >= min && v <= max;
export function validateWidgetModel(tag, value) {
    let valid = false;
    switch (tag) {
        case 'rf-record-table':
        case 'rf-work-board':
            valid = records(value, v => identity(v) && ['title', 'owner', 'status', 'priority', 'updated'].every(k => text(v[k]))) && unique(value, 'id');
            break;
        case 'rf-gantt':
            valid = records(value, v => identity(v) && text(v.name) && text(v.owner) && integer(v.start) && integer(v.duration) && position(v.progress, 0, 100) && strings(v.dependencies), 10000) && unique(value, 'id');
            break;
        case 'rf-state-timeline':
            valid = records(value, v => text(v.name) && records(v.segments, s => text(s.label) && position(s.start, 0, 24) && position(s.duration, 0, 24) && Number(s.start) + Number(s.duration) <= 24 && tone(s.tone), 1000), 1000);
            break;
        case 'rf-calendar':
            valid = records(value, v => identity(v) && text(v.title) && typeof v.date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v.date) && !Number.isNaN(Date.parse(v.date)) && tone(v.tone)) && unique(value, 'id');
            break;
        case 'rf-rack':
            valid = records(value, v => identity(v) && text(v.name) && integer(v.start) && integer(v.units) && position(v.watts, 0, 1e9) && one(v.status, ['healthy', 'warning', 'offline']), 100) && unique(value, 'id');
            break;
        case 'rf-wafer':
            valid = records(value, v => identity(v) && integer(v.x) && integer(v.y) && position(v.x, -10000, 10000) && position(v.y, -10000, 10000) && one(v.bin, ['pass', 'fail', 'edge', 'untested']) && number(v.value)) && unique(value, 'id');
            break;
        case 'rf-process-chart':
            valid = object(value) && Array.isArray(value.values) && value.values.length <= 100000 && value.values.every(number) && text(value.title) && text(value.unit) && number(value.low) && number(value.high) && Number(value.low) < Number(value.high);
            break;
        case 'rf-chart-collection':
            valid = Array.isArray(value) && value.length <= 1000 && value.every(v => position(v, 0, 1e12));
            break;
        case 'rf-topology':
            valid = object(value) && records(value.nodes, n => identity(n) && text(n.label) && text(n.kind) && position(n.x, -100000, 100000) && position(n.y, -100000, 100000) && one(n.status, ['healthy', 'warning', 'offline']), 10000) && records(value.edges, e => text(e.from) && text(e.to) && (e.label === undefined || text(e.label)), 50000);
            break;
        case 'rf-trace-waterfall':
            valid = records(value, v => identity(v) && text(v.name) && text(v.service) && position(v.start, 0, 1e12) && position(v.duration, 0, 1e12) && integer(v.depth) && position(v.depth, 0, 100) && one(v.status, ['ok', 'error'])) && unique(value, 'id');
            break;
        case 'rf-log-explorer':
            valid = records(value, v => identity(v) && text(v.timestamp) && text(v.service) && text(v.message) && one(v.level, ['INFO', 'WARN', 'ERROR'])) && unique(value, 'id');
            break;
        case 'rf-config-diff':
            valid = object(value) && text(value.before) && text(value.after) && text(value.leftLabel) && text(value.rightLabel);
            break;
        case 'rf-json-inspector':
            valid = object(value) && JSON.stringify(value).length <= 65536;
            break;
        case 'rf-engineering-form':
            valid = object(value) && text(value.name) && text(value.category) && number(value.target) && position(value.tolerance, 0, 1e12) && text(value.unit) && typeof value.enabled === 'boolean';
            break;
        case 'rf-windows':
            valid = object(value) && text(value.lastAction);
            break;
        case 'rf-carrier':
            valid = records(value, v => integer(v.slot) && position(v.slot, 1, 25) && (v.waferId === null || text(v.waferId)) && one(v.status, ['ready', 'hold', 'empty']), 25);
            break;
        case 'rf-lot-traveler':
            valid = records(value, v => identity(v) && text(v.name) && text(v.equipment) && text(v.duration) && one(v.status, ['queued', 'running', 'complete', 'hold']), 1000) && unique(value, 'id');
            break;
        case 'rf-floorplan':
            valid = records(value, v => identity(v) && text(v.name) && number(v.x) && number(v.y) && number(v.width) && number(v.height) && one(v.status, ['healthy', 'warning', 'offline']), 1000) && unique(value, 'id');
            break;
        case 'rf-permission-matrix':
            valid = object(value) && strings(value.roles) && strings(value.actions) && object(value.grants) && Object.values(value.grants).every(strings);
            break;
        case 'rf-split-workspace':
            valid = object(value) && position(value.ratio, 20, 65) && text(value.selected);
            break;
        case 'rf-pipeline':
            valid = records(value, v => identity(v) && text(v.name) && text(v.duration) && one(v.status, ['queued', 'running', 'passed', 'failed']), 1000) && unique(value, 'id');
            break;
        case 'rf-notifications':
            valid = records(value, v => identity(v) && text(v.title) && text(v.body) && text(v.time) && typeof v.read === 'boolean' && one(v.tone, ['info', 'warning', 'success']), 10000) && unique(value, 'id');
            break;
        default: throw new Error(`Unknown engineering widget: ${tag}`);
    }
    if (!valid)
        throw new TypeError(`Invalid ${tag} model: check the documented field types, bounds, and unique identifiers.`);
}
//# sourceMappingURL=validation.js.map