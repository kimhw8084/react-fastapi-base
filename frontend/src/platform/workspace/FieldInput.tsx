import type { FieldDefinition } from '../../generated/schema'
import type { Draft } from './types'

function selectedValues(raw:string):string[]{
 if(!raw)return []
 try{const value=JSON.parse(raw);return Array.isArray(value)&&value.every(item=>typeof item==='string')?value:[]}catch{return []}
}

export function FieldInput({field,draft,onChange,invalid,autoFocus=false,choices,onBlur}:{field:FieldDefinition;draft:Draft;onChange:(draft:Draft)=>void;invalid:boolean;autoFocus?:boolean;choices?:readonly string[];onBlur?:()=>void}){
 const value=String(draft[field.key]??'')
 const update=(next:string)=>onChange({...draft,[field.key]:next})
 const availableChoices=choices??field.choices
 if(field.kind==='textarea'||field.kind==='long_text'||field.kind==='markdown'||field.kind==='code'||field.kind==='json'||field.kind==='object'||field.kind==='array'||field.kind==='coordinates'){
  const rows=field.kind==='code'||field.kind==='json'||field.kind==='object'||field.kind==='array'||field.kind==='coordinates'?12:field.kind==='markdown'?9:5
  return <textarea id={`record-field-${field.key}`} className={field.kind==='code'||field.kind==='json'?'code-input':field.kind==='markdown'?'markdown-input':undefined} rows={rows} value={value} maxLength={field.max_length??undefined} required={field.required} spellCheck={field.kind==='code'||field.kind==='json'?false:undefined} aria-invalid={invalid} autoFocus={autoFocus} onBlur={onBlur} onChange={event=>update(event.target.value)}/>
 }
 if(field.kind==='select')return <select id={`record-field-${field.key}`} value={value} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onBlur={onBlur} onChange={event=>update(event.target.value)}>{field.required&&<option value="" disabled>Choose…</option>}{field.nullable&&<option value="">— None —</option>}{availableChoices.map(choice=><option key={choice} value={choice}>{choice.replaceAll('_',' ')}</option>)}</select>
 if(field.kind==='multiselect'||field.kind==='multi_enum'){
  const selected=new Set(selectedValues(value))
  return <select id={`record-field-${field.key}`} multiple value={[...selected]} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} size={Math.min(8,Math.max(3,availableChoices.length))} onBlur={onBlur} onChange={event=>update(JSON.stringify(Array.from(event.currentTarget.selectedOptions,option=>option.value)))}>{availableChoices.map(choice=><option key={choice} value={choice}>{choice.replaceAll('_',' ')}</option>)}</select>
 }
 if(field.kind==='boolean')return <select id={`record-field-${field.key}`} value={value||(field.nullable?'':'false')} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onBlur={onBlur} onChange={event=>update(event.target.value)}>{field.nullable&&<option value="">— None —</option>}<option value="false">False</option><option value="true">True</option></select>
 const numeric=['integer','number','decimal','percent','duration','scientific','unit_number','range','tolerance'].includes(field.kind)
 if(numeric){
  const input=<input id={`record-field-${field.key}`} type="number" inputMode={field.kind==='integer'?'numeric':'decimal'} step={field.kind==='integer'?1:field.step??'any'} min={field.minimum??undefined} max={field.maximum??undefined} value={value} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onBlur={onBlur} onChange={event=>update(event.target.value)}/>
  return field.unit?<span className="field-unit-input">{input}<span className="field-unit" aria-hidden="true">{field.unit}</span></span>:input
 }
 if(field.kind==='date')return <input id={`record-field-${field.key}`} type="date" value={value} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onBlur={onBlur} onChange={event=>update(event.target.value)}/>
 if(field.kind==='datetime')return <input id={`record-field-${field.key}`} type="datetime-local" value={value} required={field.required} aria-invalid={invalid} autoFocus={autoFocus} onBlur={onBlur} onChange={event=>update(event.target.value)}/>
 return <input id={`record-field-${field.key}`} type={field.kind==='email'?'email':field.kind==='url'?'url':'text'} value={value} required={field.required} maxLength={field.max_length??undefined} aria-invalid={invalid} autoFocus={autoFocus} onBlur={onBlur} onChange={event=>update(event.target.value)}/>
}
