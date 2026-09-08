/** Framework-independent engineering contracts. No application or infrastructure imports. */
export type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';
export type ViewState = 'ready' | 'loading' | 'empty' | 'error' | 'readonly';
export type ThemeMode = 'light' | 'dark' | 'system';
export type Density = 'comfortable' | 'compact';
export interface RecordRow {
    id: string;
    title: string;
    owner: string;
    status: string;
    priority: string;
    updated: string;
}
export interface Task {
    id: string;
    name: string;
    start: number;
    duration: number;
    progress: number;
    owner: string;
    dependencies: string[];
}
export interface RackDevice {
    id: string;
    name: string;
    start: number;
    units: number;
    watts: number;
    status: 'healthy' | 'warning' | 'offline';
}
export interface Die {
    id: string;
    x: number;
    y: number;
    bin: 'pass' | 'fail' | 'edge' | 'untested';
    value: number;
}
export interface TraceSpan {
    id: string;
    name: string;
    start: number;
    duration: number;
    service: string;
    status: 'ok' | 'error';
    depth: number;
}
export interface LogEntry {
    id: string;
    timestamp: string;
    level: 'INFO' | 'WARN' | 'ERROR';
    service: string;
    message: string;
}
export interface GraphNode {
    id: string;
    label: string;
    kind: string;
    x: number;
    y: number;
    status: 'healthy' | 'warning' | 'offline';
}
export interface GraphEdge {
    from: string;
    to: string;
    label?: string;
}
export interface GraphModel {
    nodes: GraphNode[];
    edges: GraphEdge[];
}
export interface Point {
    x: number;
    y: number;
    label?: string;
}
export interface StateSegment {
    label: string;
    start: number;
    duration: number;
    tone: Tone;
}
export interface ScheduleEvent {
    id: string;
    title: string;
    date: string;
    tone: Tone;
}
export interface Change<T> {
    value: T;
    reason: string;
}
export declare function clamp(v: number, min: number, max: number): number;
export declare function finite(v: unknown, fallback: number): number;
export declare function escapeHtml(value: unknown): string;
export declare function assertUnique(ids: string[]): void;
export declare function validateTasks(tasks: Task[], horizon?: number): string[];
export declare function moveTask(tasks: Task[], id: string, start: number, duration: number, horizon?: number): Task[];
export declare function validateRack(devices: RackDevice[], capacity?: number, maxWatts?: number): string[];
export declare function moveDevice(devices: RackDevice[], id: string, start: number, capacity?: number, maxWatts?: number): RackDevice[];
export declare function waferYield(dies: Die[]): {
    tested: number;
    passed: number;
    percent: number | null;
};
export declare function sampleStats(values: number[]): {
    mean: number;
    std: number;
    count: number;
} | null;
export declare function violations(values: number[], limits: {
    low: number;
    high: number;
}): number[];
export declare function paginate<T>(rows: T[], page: number, size: number): T[];
export declare function csvCell(value: unknown): string;
export declare function recordsCsv(rows: RecordRow[]): string;
export declare function diffLines(before: string, after: string): {
    before: string;
    after: string;
    changed: boolean;
}[];
export declare function validateGraph(model: GraphModel): string[];
export declare function storageRead<T>(key: string, fallback: T, validate: (v: unknown) => v is T): T;
export declare function downloadText(name: string, text: string, type?: string): void;
/** Local UI/fixture identifier, never an authentication token. Works without secure-context randomUUID. */
export declare function localId(prefix?: string): string;
