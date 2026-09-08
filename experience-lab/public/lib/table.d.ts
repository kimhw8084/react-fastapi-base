import { EngineeringElement } from './base.js';
import { type RecordRow } from './model.js';
export declare class RecordTable extends EngineeringElement<RecordRow[]> {
    private search;
    private status;
    private sort;
    private descending;
    private page;
    private grouped;
    private selected;
    constructor();
    render(): void;
}
export declare class WorkBoard extends EngineeringElement<RecordRow[]> {
    private dragId;
    constructor();
    render(): void;
    private move;
}
