import { useState } from 'react'
import type { BaseRecord,ProjectionProps } from './types'
import { ProjectionWorkspaceFrame } from './ProjectionWorkspaceFrame'
import { recordValue } from './projectionUtils'
import { capability, descriptive, ewma, imr, pareto, runRuleFlags } from '../engineering/spcModel'

function text(row:BaseRecord,key:string){const value=recordValue(row,key);return value==null?'':String(value)}
function number(row:BaseRecord,key:string):number|null{const value=recordValue(row,key);if(value==null||value==='')return null;const parsed=Number(value);return Number.isFinite(parsed)?parsed:null}
function streamKey(row:BaseRecord){return `${text(row,'process')}\u241f${text(row,'metric')}\u241f${text(row,'unit')}`}
function fmt(value:number|null|undefined,digits=3){return value==null||!Number.isFinite(value)?'—':value.toLocaleString(undefined,{maximumFractionDigits:digits})}
function linePoints(values:number[],min:number,max:number,width=900,height=240){const range=max-min||1;return values.map((value,index)=>`${values.length===1?width/2:(index/(values.length-1))*width},${height-((value-min)/range)*height}`).join(' ')}

export function SpcWorkspace<T extends BaseRecord>(props:ProjectionProps<T>){
 const[selectedStream,setSelectedStream]=useState('')
 return <ProjectionWorkspaceFrame {...props} projectionKey="spc" title="Statistical process control" description="I-MR control, capability, EWMA, run-rule and Pareto analysis over canonical measurement records." limit={1000} extraMetrics={rows=>[{label:'Samples',value:rows.length},{label:'Streams',value:new Set(rows.map(streamKey)).size}]}>{(rows,{openRow,peekRow})=>{
  const streams=[...new Map(rows.map(row=>[streamKey(row),{key:streamKey(row),process:text(row,'process'),metric:text(row,'metric'),unit:text(row,'unit')}])).values()].sort((a,b)=>a.key.localeCompare(b.key))
  const key=selectedStream&&streams.some(stream=>stream.key===selectedStream)?selectedStream:streams[0]?.key??''
  const samples=rows.filter(row=>streamKey(row)===key).sort((a,b)=>new Date(text(a,'sampled_at')).getTime()-new Date(text(b,'sampled_at')).getTime())
  const values=samples.map(row=>number(row,'value')).filter((value):value is number=>value!=null)
  const stats=values.length?descriptive(values):null
  const control=values.length?imr(values):null
  const rules=values.length?runRuleFlags(values,control?.center):{eightOnOneSide:[],sixPointTrend:[]}
  const lower=samples.map(row=>number(row,'lower_spec')).find(value=>value!=null)??null
  const upper=samples.map(row=>number(row,'upper_spec')).find(value=>value!=null)??null
  const target=samples.map(row=>number(row,'target')).find(value=>value!=null)??null
  let cap:ReturnType<typeof capability>|null=null
  if(values.length>=2&&(lower!=null||upper!=null)){try{cap=capability(values,lower,upper)}catch{cap=null}}
  const ewmaValues=values.length?ewma(values,.2,target??undefined):[]
  const bounds=[...values,control?.lowerControl,control?.upperControl,lower,upper,target].filter((value):value is number=>value!=null&&Number.isFinite(value))
  const min=bounds.length?Math.min(...bounds):0,max=bounds.length?Math.max(...bounds):1,pad=(max-min||1)*.08,chartMin=min-pad,chartMax=max+pad
  const defects=pareto(rows.filter(row=>text(row,'category')==='defect').map(row=>text(row,'metric')||'Unspecified'))
  const stream=streams.find(value=>value.key===key)
  return <div className="spc-workbench">
   <aside className="spc-streams"><header><strong>Measurement streams</strong><span>{streams.length}</span></header>{streams.map(item=><button key={item.key} className={item.key===key?'selected':''} onClick={()=>setSelectedStream(item.key)}><strong>{item.metric}</strong><span>{item.process}</span><small>{item.unit||'unitless'}</small></button>)}</aside>
   <main className="spc-main">
    <header><div><span className="eyebrow">{stream?.process||'Process'} · {stream?.unit||'unitless'}</span><h1>{stream?.metric||'Measurement stream'}</h1><p>{values.length} samples · I-MR within-sigma estimation · EWMA α 0.2</p></div><div className="toolbar-actions">{samples[0]&&<button onClick={()=>peekRow(samples.at(-1)!)}>Latest sample</button>}</div></header>
    <section className="spc-metrics">{[['Mean',fmt(stats?.mean)],['σ within',fmt(control?.sigmaWithin)],['Cpk',fmt(cap?.cpk,2)],['Ppk',fmt(cap?.ppk,2)],['Signals',String((control?.outOfControlIndexes.length??0)+rules.eightOnOneSide.length+rules.sixPointTrend.length)]].map(([label,value])=><article key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>
    {values.length>0&&<section className="spc-chart"><header><strong>I-MR control trace</strong><span>Control {fmt(control?.lowerControl)} – {fmt(control?.upperControl)}</span></header><div className="spc-chart-canvas"><svg viewBox="0 0 900 240" role="img" aria-label={`SPC trace for ${stream?.metric||'measurement'}`}>
      {[control?.lowerControl,control?.center,control?.upperControl,lower,upper,target].map((value,index)=>value==null?null:<line key={index} x1="0" x2="900" y1={240-((value-chartMin)/(chartMax-chartMin))*240} y2={240-((value-chartMin)/(chartMax-chartMin))*240} className={index===1?'center':index<3?'control':'spec'}/>)}
      <polyline points={linePoints(values,chartMin,chartMax)} className="trace"/><polyline points={linePoints(ewmaValues,chartMin,chartMax)} className="ewma"/>
      {values.map((value,index)=><circle key={samples[index]?.id??index} cx={values.length===1?450:(index/(values.length-1))*900} cy={240-((value-chartMin)/(chartMax-chartMin))*240} r={control?.outOfControlIndexes.includes(index)?6:4} className={control?.outOfControlIndexes.includes(index)?'signal':'sample'} onClick={()=>samples[index]&&openRow(samples[index])}><title>{samples[index]&&text(samples[index],'sample_label')}: {value}</title></circle>)}
     </svg></div><footer><span className="legend trace">Observed</span><span className="legend ewma">EWMA</span><span className="legend spec">Specification</span></footer></section>}
    <section className="spc-lower-grid"><article><h3>Capability</h3><dl><div><dt>Cp</dt><dd>{fmt(cap?.cp,2)}</dd></div><div><dt>Cpk</dt><dd>{fmt(cap?.cpk,2)}</dd></div><div><dt>Pp</dt><dd>{fmt(cap?.pp,2)}</dd></div><div><dt>Ppk</dt><dd>{fmt(cap?.ppk,2)}</dd></div><div><dt>Target</dt><dd>{fmt(target)}</dd></div><div><dt>Spec</dt><dd>{fmt(lower)} … {fmt(upper)}</dd></div></dl></article><article><h3>Rule signals</h3><p>Outside control: <strong>{control?.outOfControlIndexes.length??0}</strong></p><p>Eight one side: <strong>{rules.eightOnOneSide.length}</strong></p><p>Six-point trends: <strong>{rules.sixPointTrend.length}</strong></p></article><article><h3>Defect Pareto</h3>{defects.length?defects.slice(0,6).map(item=><div className="spc-pareto" key={item.category}><span>{item.category}</span><i style={{width:`${item.cumulativePercent}%`}}/><strong>{item.count}</strong></div>):<p className="muted">No defect-category samples in current scope.</p>}</article></section>
   </main>
  </div>
 }}</ProjectionWorkspaceFrame>
}
