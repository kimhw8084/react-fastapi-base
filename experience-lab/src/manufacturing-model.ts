export interface CarrierSlot {slot:number;waferId:string|null;status:'ready'|'hold'|'empty';}
export function validateCarrier(slots:CarrierSlot[],capacity=25):string[]{
 const errors:string[]=[];const occupied=new Set<number>(),ids=new Set<string>();
 for(const s of slots){if(!Number.isInteger(s.slot)||s.slot<1||s.slot>capacity)errors.push('Slot outside carrier capacity.');if(occupied.has(s.slot))errors.push('Duplicate slot.');occupied.add(s.slot);if(s.waferId){if(ids.has(s.waferId))errors.push('A wafer cannot occupy two slots.');ids.add(s.waferId);}if(s.status==='empty'&&s.waferId!==null)errors.push('An empty slot cannot contain a wafer.');if(s.status!=='empty'&&!s.waferId)errors.push('Occupied slots require a wafer identifier.');}
 return errors;
}
export function reassignWafer(slots:CarrierSlot[],from:number,to:number):CarrierSlot[]{
 const origin=slots.find(s=>s.slot===from),target=slots.find(s=>s.slot===to);
 if(!origin?.waferId)throw new Error('Source slot is empty.');if(!target)throw new Error('Target slot does not exist.');if(target.waferId)throw new Error('Target slot is occupied.');
 const next=slots.map(s=>s.slot===from?{slot:from,waferId:null,status:'empty' as const}:s.slot===to?{...origin,slot:to}:s);const errors=validateCarrier(next);if(errors.length)throw new Error(errors.join(' '));return next;
}

export interface TravelerStep {id:string;name:string;equipment:string;status:'queued'|'running'|'complete'|'hold';duration:string;}
export function transitionStep(steps:TravelerStep[],id:string,status:TravelerStep['status']):TravelerStep[]{
 const index=steps.findIndex(s=>s.id===id);if(index<0)throw new Error('Process step not found.');const step=steps[index]!;
 const allowed:Record<TravelerStep['status'],TravelerStep['status'][]>= {queued:['running'],running:['complete','hold'],complete:[],hold:['running']};
 if(!allowed[step.status].includes(status))throw new Error('Transition is not allowed.');
 if(status==='running'&&steps.slice(0,index).some(s=>s.status!=='complete'))throw new Error('Complete prerequisite steps first.');
 return steps.map(s=>s.id===id?{...s,status}:s);
}

export interface FloorAsset {id:string;name:string;x:number;y:number;width:number;height:number;status:'healthy'|'warning'|'offline';}
export function validateFloor(assets:FloorAsset[],width=800,height=400):string[]{const errors:string[]=[];for(const a of assets){if(![a.x,a.y,a.width,a.height].every(Number.isFinite)||a.x<0||a.y<0||a.width<=0||a.height<=0||a.x+a.width>width||a.y+a.height>height)errors.push(`${a.name}: out of bounds.`);}for(let i=0;i<assets.length;i++)for(let j=i+1;j<assets.length;j++){const a=assets[i]!,b=assets[j]!;if(a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y)errors.push(`${a.name} overlaps ${b.name}.`);}return errors;}
