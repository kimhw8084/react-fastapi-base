import { EngineeringElement } from './base.js';
export interface PermissionModel {
    roles: string[];
    actions: string[];
    grants: Record<string, string[]>;
}
export declare class PermissionMatrix extends EngineeringElement<PermissionModel> {
    constructor();
    render(): void;
}
export declare class SplitWorkspace extends EngineeringElement<{
    ratio: number;
    selected: string;
}> {
    constructor();
    render(): void;
}
export interface PipelineStage {
    id: string;
    name: string;
    status: 'queued' | 'running' | 'passed' | 'failed';
    duration: string;
}
export declare class PipelineViewer extends EngineeringElement<PipelineStage[]> {
    private selected;
    constructor();
    render(): void;
}
export interface Notification {
    id: string;
    title: string;
    body: string;
    time: string;
    read: boolean;
    tone: 'info' | 'warning' | 'success';
}
export declare class NotificationFeed extends EngineeringElement<Notification[]> {
    private unreadOnly;
    constructor();
    render(): void;
}
