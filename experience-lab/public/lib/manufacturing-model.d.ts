export interface CarrierSlot {
    slot: number;
    waferId: string | null;
    status: 'ready' | 'hold' | 'empty';
}
export declare function validateCarrier(slots: CarrierSlot[], capacity?: number): string[];
export declare function reassignWafer(slots: CarrierSlot[], from: number, to: number): CarrierSlot[];
export interface TravelerStep {
    id: string;
    name: string;
    equipment: string;
    status: 'queued' | 'running' | 'complete' | 'hold';
    duration: string;
}
export declare function transitionStep(steps: TravelerStep[], id: string, status: TravelerStep['status']): TravelerStep[];
export interface FloorAsset {
    id: string;
    name: string;
    x: number;
    y: number;
    width: number;
    height: number;
    status: 'healthy' | 'warning' | 'offline';
}
export declare function validateFloor(assets: FloorAsset[], width?: number, height?: number): string[];
