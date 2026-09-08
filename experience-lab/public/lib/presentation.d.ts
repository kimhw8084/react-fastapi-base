/** Optional presentation configuration. Models remain free of company infrastructure. */
export interface SchedulePresentation {
    startDate: string;
    days: number;
}
export interface RackPresentation {
    label: string;
    units: number;
    maxWatts: number;
}
export interface WaferPresentation {
    label: string;
    unit: string;
}
export interface WidgetPresentation {
    title?: string;
    locale?: string;
    schedule?: SchedulePresentation;
    rack?: RackPresentation;
    wafer?: WaferPresentation;
}
export declare const defaultSchedule: SchedulePresentation;
export declare const defaultRack: RackPresentation;
export declare function validatePresentation(p: WidgetPresentation | undefined): void;
