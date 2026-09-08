import { EngineeringElement } from './base.js';
import { type Point } from './model.js';
export interface ChartModel {
    values: number[];
    title: string;
    unit: string;
    low: number;
    high: number;
}
export declare function linePath(points: Point[], width: number, height: number, bounds: {
    min: number;
    max: number;
}): string;
export declare class ProcessChart extends EngineeringElement<ChartModel> {
    private kind;
    private point;
    private showLimits;
    constructor();
    render(): void;
}
export declare class ChartCollection extends EngineeringElement<number[]> {
    private selected;
    constructor();
    render(): void;
}
