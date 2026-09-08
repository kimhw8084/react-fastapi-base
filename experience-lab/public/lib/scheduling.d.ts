import { EngineeringElement } from './base.js';
import { type Task, type StateSegment, type ScheduleEvent, type TraceSpan } from './model.js';
export declare class GanttSchedule extends EngineeringElement<Task[]> {
    private selected;
    private dayWidth;
    constructor();
    render(): void;
    configure(value: Task[], options?: Parameters<EngineeringElement<Task[]>['configure']>[1]): void;
}
export declare class StateTimeline extends EngineeringElement<{
    name: string;
    segments: StateSegment[];
}[]> {
    private selected;
    constructor();
    render(): void;
}
export declare class MonthCalendar extends EngineeringElement<ScheduleEvent[]> {
    private year;
    private month;
    private selected;
    constructor();
    render(): void;
}
export declare class TraceWaterfall extends EngineeringElement<TraceSpan[]> {
    private selected;
    constructor();
    render(): void;
}
