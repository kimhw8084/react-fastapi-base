import { type CarrierSlot, type TravelerStep, type FloorAsset } from './manufacturing-model.js';
export { validateCarrier, reassignWafer, transitionStep, validateFloor } from './manufacturing-model.js';
export type { CarrierSlot, TravelerStep, FloorAsset } from './manufacturing-model.js';
import { EngineeringElement } from './base.js';
export declare class CarrierMap extends EngineeringElement<CarrierSlot[]> {
    private selected;
    constructor();
    render(): void;
    configure(value: CarrierSlot[], options?: Parameters<EngineeringElement<CarrierSlot[]>['configure']>[1]): void;
}
export declare class LotTraveler extends EngineeringElement<TravelerStep[]> {
    private selected;
    constructor();
    render(): void;
}
export declare class FloorPlan extends EngineeringElement<FloorAsset[]> {
    private selected;
    constructor();
    render(): void;
    configure(value: FloorAsset[], options?: Parameters<EngineeringElement<FloorAsset[]>['configure']>[1]): void;
}
