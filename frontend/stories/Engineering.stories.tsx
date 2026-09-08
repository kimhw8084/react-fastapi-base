import {useEffect,useState} from 'react'
import type {Meta,StoryObj} from '@storybook/react-vite'
import {EngineeringWidget,type WidgetKind,type WidgetModels} from '../src/platform/engineering/EngineeringWidget'
import type {ViewState} from '../../experience-lab/src/model'
import examples from '../../catalog/examples.json'

// Generated deterministic synthetic data. Runtime widget validators enforce the public boundary.
function Example({kind,state,readOnly}:{kind:WidgetKind;state:ViewState;readOnly:boolean}){
  const [value,setValue]=useState<WidgetModels[WidgetKind]>(examples[kind] as WidgetModels[WidgetKind])
  useEffect(()=>setValue(examples[kind] as WidgetModels[WidgetKind]),[kind])
  return <EngineeringWidget kind={kind} value={value} state={state} readOnly={readOnly} onChange={change=>setValue(change.value)}/>
}
const meta={title:'Engineering/Interactive widgets',component:Example,tags:['autodocs'],args:{kind:'tables',state:'ready',readOnly:false},argTypes:{kind:{control:'select',options:Object.keys(examples)},state:{control:'select',options:['ready','loading','empty','error','readonly']},readOnly:{control:'boolean'}}} satisfies Meta<typeof Example>
export default meta
type Story=StoryObj<typeof meta>
export const Table:Story={args:{kind:'tables'}}
export const Board:Story={args:{kind:'boards'}}
export const Gantt:Story={args:{kind:'gantt'}}
export const Calendar:Story={args:{kind:'calendar'}}
export const EquipmentTimeline:Story={args:{kind:'timeline'}}
export const Rack:Story={args:{kind:'rack'}}
export const Wafer:Story={args:{kind:'wafer'}}
export const Process:Story={args:{kind:'process'}}
export const Charts:Story={args:{kind:'charts'}}
export const Topology:Story={args:{kind:'topology'}}
export const Traces:Story={args:{kind:'traces'}}
export const Logs:Story={args:{kind:'logs'}}
export const Diff:Story={args:{kind:'diff'}}
export const Forms:Story={args:{kind:'forms'}}
export const Windows:Story={args:{kind:'windows'}}
export const JSON:Story={args:{kind:'json'}}
export const Carrier:Story={args:{kind:'carrier'}}
export const Traveler:Story={args:{kind:'traveler'}}
export const FloorPlan:Story={args:{kind:'floorplan'}}
export const Permissions:Story={args:{kind:'permissions'}}
export const Split:Story={args:{kind:'split'}}
export const Pipeline:Story={args:{kind:'pipeline'}}
export const Notifications:Story={args:{kind:'notifications'}}
