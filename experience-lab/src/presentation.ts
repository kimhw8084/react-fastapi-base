/** Optional presentation configuration. Models remain free of company infrastructure. */
export interface SchedulePresentation {startDate:string;days:number;}
export interface RackPresentation {label:string;units:number;maxWatts:number;}
export interface WaferPresentation {label:string;unit:string;}
export interface WidgetPresentation {
 title?:string;locale?:string;
 schedule?:SchedulePresentation;
 rack?:RackPresentation;
 wafer?:WaferPresentation;
}
export const defaultSchedule:SchedulePresentation={startDate:'2026-09-01',days:30};
export const defaultRack:RackPresentation={label:'Reference rack',units:42,maxWatts:12000};
export function validatePresentation(p:WidgetPresentation|undefined):void {
 if(!p)return;
 if(p.title!==undefined&&(typeof p.title!=='string'||p.title.length>200))throw new TypeError('Title must be at most 200 characters.');
 if(p.locale!==undefined){if(typeof p.locale!=='string')throw new TypeError('Locale must be a string.');new Intl.DateTimeFormat(p.locale);}
 if(p.schedule){const {startDate,days}=p.schedule;const date=new Date(startDate+'T00:00:00Z');if(!/^\d{4}-\d{2}-\d{2}$/.test(startDate)||!Number.isFinite(date.getTime())||date.toISOString().slice(0,10)!==startDate||!Number.isInteger(days)||days<1||days>366)throw new TypeError('Schedule needs a valid ISO date and 1–366 days.');}
 if(p.rack){const {label,units,maxWatts}=p.rack;if(typeof label!=='string'||label.length>100||!Number.isInteger(units)||units<1||units>100||!Number.isFinite(maxWatts)||maxWatts<0)throw new TypeError('Rack needs a label, 1–100 units and a nonnegative power budget.');}
 if(p.wafer&&(typeof p.wafer.label!=='string'||p.wafer.label.length>100||typeof p.wafer.unit!=='string'||p.wafer.unit.length>40))throw new TypeError('Wafer label/unit are invalid.');
}
