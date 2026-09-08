import { EngineeringElement } from './base.js';
export type WindowKind = 'dialog' | 'drawer' | 'sheet' | 'fullscreen' | 'wizard' | 'confirm';
export declare class WindowGallery extends EngineeringElement<{
    lastAction: string;
}> {
    private opener;
    private dirty;
    private step;
    private draftName;
    private draftLayout;
    private windowCounter;
    constructor();
    render(): void;
    private open;
}
