import type {WidgetPresentation} from '../../../../experience-lab/src/presentation'
import type {CarrierSlot,TravelerStep,FloorAsset} from '../../../../experience-lab/src/manufacturing'
import type {PermissionModel,PipelineStage,Notification} from '../../../../experience-lab/src/composition'
import { useEffect, useRef, useState, type CSSProperties } from 'react'
import type {RecordRow,Task,RackDevice,Die,GraphModel,TraceSpan,LogEntry,StateSegment,ScheduleEvent,ViewState,Change} from '../../../../experience-lab/src/model'
import type {ChartModel} from '../../../../experience-lab/src/charts'
import type {DiffModel} from '../../../../experience-lab/src/editors'

export interface WidgetModels {
 carrier:CarrierSlot[];traveler:TravelerStep[];floorplan:FloorAsset[];permissions:PermissionModel;split:{ratio:number;selected:string};pipeline:PipelineStage[];notifications:Notification[];
 tables: RecordRow[];boards:RecordRow[];gantt:Task[];calendar:ScheduleEvent[];
 timeline:{name:string;segments:StateSegment[]}[];rack:RackDevice[];wafer:Die[];
 process:ChartModel;charts:number[];topology:GraphModel;traces:TraceSpan[];
 logs:LogEntry[];diff:DiffModel;json:Record<string,unknown>;
 forms:{name:string;unit:string;target:number;tolerance:number;category:string;enabled:boolean};
 windows:{lastAction:string};
}
export type WidgetKind=keyof WidgetModels
const tags:Record<WidgetKind,string>={carrier:'rf-carrier',traveler:'rf-lot-traveler',floorplan:'rf-floorplan',permissions:'rf-permission-matrix',split:'rf-split-workspace',pipeline:'rf-pipeline',notifications:'rf-notifications',tables:'rf-record-table',boards:'rf-work-board',gantt:'rf-gantt',calendar:'rf-calendar',timeline:'rf-state-timeline',rack:'rf-rack',wafer:'rf-wafer',process:'rf-process-chart',charts:'rf-chart-collection',topology:'rf-topology',traces:'rf-trace-waterfall',logs:'rf-log-explorer',diff:'rf-config-diff',json:'rf-json-inspector',forms:'rf-engineering-form',windows:'rf-windows'}
interface Host<T> extends HTMLElement {configure(value:T,options:{state:ViewState;readonly:boolean;presentation?:WidgetPresentation}):void}
let loading:Promise<unknown>|undefined
function ensureWidgets():Promise<unknown>{
 return loading??=Promise.all([
 import('../../../../experience-lab/src/manufacturing'),import('../../../../experience-lab/src/composition'),
  import('../../../../experience-lab/src/table'),import('../../../../experience-lab/src/scheduling'),
  import('../../../../experience-lab/src/spatial'),import('../../../../experience-lab/src/charts'),
  import('../../../../experience-lab/src/editors'),import('../../../../experience-lab/src/windows'),
 ])
}
export interface EngineeringWidgetProps<K extends WidgetKind> {
 kind:K;value:WidgetModels[K];state?:ViewState;readOnly?:boolean;
 presentation?:WidgetPresentation;
 onChange?:(change:Change<WidgetModels[K]>)=>void;
 onSelect?:(record:unknown)=>void;
 onError?:(error:Error)=>void;
 className?:string;style?:CSSProperties;
}
/**
 * Controlled React integration for the same tested DOM/SVG implementation used by
 * the offline Lab. Mutations emit intent; the application persists through its API.
 * Include experience-lab/public/styles.css in the host's chosen theme boundary.
 */
export function EngineeringWidget<K extends WidgetKind>(props:EngineeringWidgetProps<K>){
 const mount=useRef<HTMLDivElement>(null),host=useRef<Host<WidgetModels[K]>|null>(null)
 const latest=useRef(props);latest.current=props
 const [error,setError]=useState<Error|null>(null)
 useEffect(()=>{
  let disposed=false;let element:Host<WidgetModels[K]>|null=null
  setError(null)
  void ensureWidgets().then(()=>{
   if(disposed||!mount.current)return
   element=document.createElement(tags[props.kind]) as Host<WidgetModels[K]>
   element.configure(latest.current.value,{state:latest.current.state??'ready',readonly:latest.current.readOnly??false,...(latest.current.presentation?{presentation:latest.current.presentation}:{})})
   element.addEventListener('model-change',event=>latest.current.onChange?.((event as CustomEvent<Change<WidgetModels[K]>>).detail))
   element.addEventListener('record-select',event=>latest.current.onSelect?.((event as CustomEvent<unknown>).detail))
   host.current=element;mount.current.replaceChildren(element)
  }).catch((reason:unknown)=>{if(!disposed){const e=reason instanceof Error?reason:new Error(String(reason));setError(e);latest.current.onError?.(e)}})
  return()=>{disposed=true;element?.remove();host.current=null}
 },[props.kind])
 useEffect(()=>{
  try{host.current?.configure(props.value,{state:props.state??'ready',readonly:props.readOnly??false,...(props.presentation?{presentation:props.presentation}:{})});setError(null)}
  catch(reason:unknown){const e=reason instanceof Error?reason:new Error(String(reason));setError(e);props.onError?.(e)}
 },[props.value,props.state,props.readOnly,props.presentation])
 return <>{error&&<div role="alert">This engineering widget could not be configured: {error.message}</div>}<div ref={mount} className={props.className} style={props.style} hidden={Boolean(error)}/></>
}
