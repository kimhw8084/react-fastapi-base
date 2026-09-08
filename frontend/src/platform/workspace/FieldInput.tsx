import type { FieldDefinition } from '../../generated/schema'
import type { Draft } from './types'

function selectedValues(raw:string):string[]{
 if(!raw)return []
 try{const value=JSON.parse(raw);return Array.isArray(value)&&value.every(item=>typeof item==='string')?value:[]}catch{return []}
}

export function FieldInput({field,draft,onChange,invalid,autoFocus=false}:{field:FieldDefinition;draft:Draft;onChange:(draft:Draft)=>void;invalid:boolean;autoFocus?:boolean}){
 const value=String(draft[field.key]??'')
 const update=(next:string)=>onChange({...draft,[field.key]:next})
 if(field.kind==='textarea'||field.kind==='markdown'||field.kind==='code'||field.kind==='json'){
  const rows=field.kind==='code'||field.kind==='json'?12:field.kind==='markdown'?9:5
  return <textarea className={field.kind==='code'||field.kind==='json'?'code-input':field.kind==='markdown'?'markdown-input':undefined} rows={rows} value={value} maxLength={field.max_length??undefined} required={field.required} spellCheck={field.kind==='code'||field.kind==='json'?false:undefined} aria-invalid={invalid} autoFocus={autoFocus} onChange={event=>update(event.target.value)}/>
 }
 if(field.kind==='select')return <select value={value} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onChange={event=>update(event.target.value)}>{field.required&&<option value="" disabled>Choose…</option>}{field.nullable&&<option value="">— None —</option>}{field.choices.map(choice=><option key={choice} value={choice}>{choice.replaceAll('_',' ')}</option>)}</select>
 if(field.kind==='multiselect'){
  const selected=new Set(selectedValues(value))
  return <select multiple value={[...selected]} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} size={Math.min(8,Math.max(3,field.choices.length))} onChange={event=>update(JSON.stringify(Array.from(event.currentTarget.selectedOptions,option=>option.value)))}>{field.choices.map(choice=><option key={choice} value={choice}>{choice.replaceAll('_',' ')}</option>)}</select>
 }
 if(field.kind==='boolean')return <select value={value||(field.nullable?'':'false')} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onChange={event=>update(event.target.value)}>{field.nullable&&<option value="">— None —</option>}<option value="false">False</option><option value="true">True</option></select>
 const numeric=['integer','number','percent','duration','scientific','unit_number'].includes(field.kind)
 if(numeric){
  const input=<input type="number" inputMode={field.kind==='integer'?'numeric':'decimal'} step={field.kind==='integer'?1:field.step??'any'} min={field.minimum??undefined} max={field.maximum??undefined} value={value} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onChange={event=>update(event.target.value)}/>
  return field.unit?<span className="field-unit-input">{input}<span className="field-unit" aria-hidden="true">{field.unit}</span></span>:input
 }
 if(field.kind==='date')return <input type="date" value={value} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onChange={event=>update(event.target.value)}/>
 if(field.kind==='datetime')return <input type="datetime-local" value={value} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onChange={event=>update(event.target.value)}/>
 return <input type={field.kind==='email'?'email':field.kind==='url'?'url':'text'} value={value} required={field.required} maxLength={field.max_length??undefined} aria-invalid={invalid} autoFocus={autoFocus} onChange={event=>update(event.target.value)}/>
}
