import type { ReactNode } from 'react'
import type { FieldDefinition, WorkspaceDefinition } from '../../generated/schema'

export function fieldLabel(definition:WorkspaceDefinition,key:string){return definition.fields.find(field=>field.key===key)?.label??key.replaceAll('_',' ')}

function humanize(value:string){return value.replaceAll('_',' ').replace(/\b\p{L}/gu,letter=>letter.toLocaleUpperCase())}

function parseStructured(value:unknown):string{
 try{if(typeof value!=='string')return JSON.stringify(value,null,2)??String(value);return JSON.stringify(JSON.parse(value),null,2)}catch{return String(value)}
}

function validDate(value:unknown):Date|null{
 const result=value instanceof Date?value:new Date(String(value))
 return Number.isNaN(result.getTime())?null:result
}

function displayNumber(value:unknown,field:FieldDefinition):string{
 const numeric=typeof value==='number'?value:typeof value==='string'&&value.trim()!==''?Number(value):Number.NaN
 if(!Number.isFinite(numeric))return String(value??'—')
 if(field.kind==='scientific')return numeric.toExponential(field.precision??4)
 const formatted=numeric.toLocaleString(undefined,typeof field.precision!=='number'?{}:{minimumFractionDigits:field.precision,maximumFractionDigits:field.precision})
 if(field.kind==='percent')return `${formatted}${field.unit??'%'}`
 if(field.kind==='duration'&&(field.unit==='min'||field.unit==='minute'||field.unit==='minutes')){const minutes=Math.max(0,numeric);const hours=Math.floor(minutes/60);const remainder=Math.round(minutes%60);return hours?`${hours}h${remainder?` ${remainder}m`:''}`:`${formatted} min`}
 if(field.kind==='duration'||field.kind==='unit_number'||field.unit)return `${formatted}${field.unit==='%'?'':' '}${field.unit??''}`.trim()
 return formatted
}

export function fieldDisplayText(field:FieldDefinition,value:unknown):string{
 if(value==null||value==='')return '—'
 if(field.kind==='boolean')return value===true||value==='true'||value===1?'Yes':value===false||value==='false'||value===0?'No':'—'
 if(field.kind==='select')return humanize(String(value))
 if(field.kind==='multiselect'||field.kind==='multi_enum'){
  const values=Array.isArray(value)?value:typeof value==='string'?(()=>{try{const parsed=JSON.parse(value);return Array.isArray(parsed)?parsed:[value]}catch{return [value]}})():[]
  return values.length?values.map(item=>humanize(String(item))).join(', '):'—'
 }
 if(['integer','number','decimal','percent','duration','scientific','unit_number','range','tolerance'].includes(field.kind))return displayNumber(value,field)
 if(field.kind==='datetime'){const date=validDate(value);return date?new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(date):String(value)}
 if(field.kind==='date'){const text=String(value),parts=/^(\d{4})-(\d{2})-(\d{2})$/.exec(text),date=parts?new Date(Number(parts[1]),Number(parts[2])-1,Number(parts[3])):validDate(value);return date?new Intl.DateTimeFormat(undefined,{dateStyle:'medium'}).format(date):text}
 if(typeof value==='object'||['json','object','array','formula','computed','range','tolerance'].includes(field.kind))return parseStructured(value)
 return String(value)
}

export function formatFieldValue(field:FieldDefinition,value:unknown):ReactNode{
 if(value==null||value==='')return <span className="muted" aria-label="No value">—</span>
 if(field.kind==='boolean')return <span>{value===true||value==='true'||value===1?'Yes':value===false||value==='false'||value===0?'No':'—'}</span>
 if(field.kind==='select')return <span>{humanize(String(value))}</span>
 if(field.kind==='json'||field.kind==='object'||field.kind==='array'||field.kind==='formula'||field.kind==='computed')return <pre className="field-structured-value"><code>{parseStructured(value)}</code></pre>
 if(field.kind==='multiselect'||field.kind==='multi_enum'){
  const values=Array.isArray(value)?value:typeof value==='string'?(()=>{try{const parsed=JSON.parse(value);return Array.isArray(parsed)?parsed:[value]}catch{return [value]}})():[]
  return <span className="field-chip-list">{values.map(item=><span className="field-chip" key={String(item)}>{humanize(String(item))}</span>)}</span>
 }
 if(field.kind==='code')return <pre className="field-structured-value"><code>{String(value)}</code></pre>
 if(field.kind==='markdown')return <div className="field-markdown-source">{String(value)}</div>
 if(['range','tolerance'].includes(field.kind)&&typeof value==='object')return <pre className="field-structured-value"><code>{parseStructured(value)}</code></pre>
 if(['integer','number','decimal','percent','duration','scientific','unit_number','range','tolerance'].includes(field.kind))return <span className="tabular-value">{displayNumber(value,field)}</span>
 if(field.kind==='datetime'){const date=validDate(value);return date?<time dateTime={date.toISOString()}>{new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(date)}</time>:<span>{String(value)}</span>}
 if(field.kind==='date'){const text=String(value);const parts=/^(\d{4})-(\d{2})-(\d{2})$/.exec(text);const date=parts?new Date(Number(parts[1]),Number(parts[2])-1,Number(parts[3])):validDate(value);return date?<time dateTime={text}>{new Intl.DateTimeFormat(undefined,{dateStyle:'medium'}).format(date)}</time>:<span>{text}</span>}
 if(typeof value==='object')return <pre className="field-structured-value"><code>{parseStructured(value)}</code></pre>
 return <span>{String(value)}</span>
}

export function FieldValue({field,value}:{field:FieldDefinition;value:unknown}){return <>{formatFieldValue(field,value)}</>}
