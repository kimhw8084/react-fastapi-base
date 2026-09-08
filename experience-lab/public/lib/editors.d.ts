import { EngineeringElement } from './base.js';
import { type LogEntry } from './model.js';
export declare class LogExplorer extends EngineeringElement<LogEntry[]> {
    private search;
    private level;
    private selected;
    constructor();
    render(): void;
}
export interface DiffModel {
    before: string;
    after: string;
    leftLabel: string;
    rightLabel: string;
}
export declare class ConfigurationDiff extends EngineeringElement<DiffModel> {
    constructor();
    render(): void;
}
export declare class JsonInspector extends EngineeringElement<Record<string, unknown>> {
    constructor();
    render(): void;
}
export declare class EngineeringForm extends EngineeringElement<{
    name: string;
    unit: string;
    target: number;
    tolerance: number;
    category: string;
    enabled: boolean;
}> {
    constructor();
    render(): void;
}
