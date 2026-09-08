import { EngineeringElement } from './base.js';
import { type RackDevice, type Die, type GraphModel } from './model.js';
export declare class RackElevation extends EngineeringElement<RackDevice[]> {
    private selected;
    private side;
    constructor();
    render(): void;
    configure(value: RackDevice[], options?: Parameters<EngineeringElement<RackDevice[]>['configure']>[1]): void;
}
export declare class WaferMap extends EngineeringElement<Die[]> {
    private selected;
    private filter;
    constructor();
    render(): void;
}
export declare class TopologyGraph extends EngineeringElement<GraphModel> {
    private selected;
    private zoom;
    private readonly svgId;
    constructor();
    render(): void;
    configure(value: GraphModel, options?: Parameters<EngineeringElement<GraphModel>['configure']>[1]): void;
}
