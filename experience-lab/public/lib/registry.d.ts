export interface CatalogEntry {
    id: string;
    title: string;
    category: string;
    tag: string;
    description: string;
    source: string;
    capabilities: string[];
    limits: string[];
}
/** This registry drives navigation, example discovery and coverage. Application-owned configuration. */
export declare const catalog: CatalogEntry[];
export declare const groups: string[];
