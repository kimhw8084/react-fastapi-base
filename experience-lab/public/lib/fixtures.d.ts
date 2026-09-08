/** Deterministic synthetic fixtures; never company/customer/manufacturing records. */
import type { RecordRow, Task, RackDevice, Die, TraceSpan, LogEntry, GraphModel, StateSegment, ScheduleEvent } from './model.js';
export declare const records: RecordRow[];
export declare const tasks: Task[];
export declare const devices: RackDevice[];
export declare const dies: Die[];
export declare const trace: TraceSpan[];
export declare const logs: LogEntry[];
export declare const graph: GraphModel;
export declare const processValues: number[];
export declare const stateRows: {
    name: string;
    segments: StateSegment[];
}[];
export declare const calendarEvents: ScheduleEvent[];
