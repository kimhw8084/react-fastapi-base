import { type WidgetPresentation } from './presentation.js';
import { type ViewState } from './model.js';
export interface WidgetOptions {
    state?: ViewState;
    readonly?: boolean;
    presentation?: WidgetPresentation;
}
/** Light DOM preserves one token/stylesheet/accessibility contract across React and the lab. */
export declare abstract class EngineeringElement<T> extends HTMLElement {
    protected value: T;
    protected options: WidgetOptions;
    protected initialized: boolean;
    private error;
    protected constructor(initial: T);
    configure(value: T, options?: WidgetOptions): void;
    get model(): T;
    connectedCallback(): void;
    protected get readonlyMode(): boolean;
    protected change(value: T, reason: string): void;
    protected select(detail: unknown): void;
    protected fail(message: string): void;
    protected frame(content: string): void;
    protected on(selector: string, event: string, handler: (e: Event) => void): void;
    protected input(selector: string): HTMLInputElement;
    abstract render(): void;
}
export declare function register(name: string, component: CustomElementConstructor): void;
export declare const badge: (label: string, tone?: string) => string;
export declare const sectionHeading: (eyebrow: string, title: string, description?: string) => string;
