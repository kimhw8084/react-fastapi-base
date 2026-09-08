import { useEffect, useMemo, useState, type ReactNode } from 'react'
import type { FieldDefinition } from '../../generated/schema'
import type { Draft } from './types'
import { FieldInput } from './FieldInput'

export type FormPresentation = 'simple'|'sectioned'|'tabbed'|'wizard'|'bulk'
export interface FormSection { id:string; label:string; fieldKeys:string[]; description?:string }
export interface FormEngineProps {
  formId:string
  fields:readonly FieldDefinition[]
  draft:Draft
  initial:Draft
  onChange:(draft:Draft)=>void
  onSubmit:(draft:Draft)=>Promise<void>|void
  validateAsync?:(draft:Draft)=>Promise<Record<string,string>>
  presentation?:FormPresentation
  sections?:readonly FormSection[]
  busy?:boolean
  serverErrors?:Record<string,string>
  renderField?:(field:FieldDefinition, invalid:boolean)=>ReactNode
  footer?:ReactNode
}

function defaultSections(fields:readonly FieldDefinition[]):FormSection[]{
  return [{id:'details',label:'Details',fieldKeys:fields.map(field=>field.key)}]
}

export function FormEngine({formId,fields,draft,initial,onChange,onSubmit,validateAsync,presentation='simple',sections:declaredSections,busy=false,serverErrors={},renderField,footer}:FormEngineProps){
  const sections=declaredSections?.length?declaredSections:defaultSections(fields)
  const [active,setActive]=useState(0)
  const dirty=useMemo(()=>JSON.stringify(draft)!==JSON.stringify(initial),[draft,initial])
  const [clientErrors,setClientErrors]=useState<Record<string,string>>({})
  useEffect(()=>{
    const handler=(event:BeforeUnloadEvent)=>{if(dirty){event.preventDefault();event.returnValue=''}}
    window.addEventListener('beforeunload',handler);return()=>window.removeEventListener('beforeunload',handler)
  },[dirty])
  const errors={...clientErrors,...serverErrors}
  const visibleSections=presentation==='simple'||presentation==='bulk'?[sections[0]??defaultSections(fields)[0]!]:sections
  const current=visibleSections[Math.min(active,visibleSections.length-1)]!
  const render=(field:FieldDefinition)=>{
    const invalid=Boolean(errors[field.key])
    return <label htmlFor={`${formId}-${field.key}`} className={['textarea','markdown','code','json','object','array','multiselect','multi_enum'].includes(field.kind)?'full-width':''} key={field.key}>
      <span>{field.label}{field.required&&<span aria-label="required"> *</span>}{field.unit&&<small className="field-unit-hint"> · {field.unit}</small>}</span>
      {renderField?renderField(field,invalid):field.read_only?<output className="readonly-field">{String(draft[field.key]??'—')}</output>:<FieldInput field={field} draft={draft} onChange={onChange} invalid={invalid} autoFocus={false}/>} 
      {errors[field.key]&&<small className="field-error">{errors[field.key]}</small>}
    </label>
  }
  const validate=async()=>{
    const next:Record<string,string>={}
    for(const field of fields){if(field.required&&!field.read_only&&!String(draft[field.key]??'').trim())next[field.key]=`${field.label} is required.`}
    if(!Object.keys(next).length&&validateAsync){Object.assign(next,await validateAsync(draft))}
    setClientErrors(next)
    return Object.keys(next).length===0
  }
  const submit=async(event:React.FormEvent)=>{event.preventDefault();if(busy)return;if(!(await validate()))return;await onSubmit(draft)}
  const next=async()=>{if(!(await validate()))return;setActive(value=>Math.min(value+1,visibleSections.length-1))}
  return <form id={formId} onSubmit={submit} aria-label="Record form" noValidate>
    {Object.keys(errors).length>0&&<section className="form-error-summary" role="alert" aria-label="Form errors"><strong>Review {Object.keys(errors).length} field error{Object.keys(errors).length===1?'':'s'}.</strong><ul>{Object.entries(errors).map(([key,value])=><li key={key}><button type="button" onClick={()=>document.getElementById(`record-field-${key}`)?.focus()}>{value}</button></li>)}</ul></section>}
    {presentation==='tabbed'&&<div className="segmented" role="tablist" aria-label="Form sections">{sections.map((section,index)=><button type="button" role="tab" aria-selected={active===index} key={section.id} onClick={()=>setActive(index)}>{section.label}</button>)}</div>}
    {presentation==='wizard'&&<nav className="wizard-steps" aria-label="Form steps">{sections.map((section,index)=><button type="button" key={section.id} aria-current={active===index?'step':undefined} onClick={()=>index<=active&&setActive(index)}>{index+1}. {section.label}</button>)}</nav>}
    {presentation==='sectioned'||presentation==='simple'||presentation==='bulk'?visibleSections.map(section=><fieldset key={section.id}><legend>{section.label}</legend>{section.description&&<p className="muted">{section.description}</p>}<div className="form-grid">{section.fieldKeys.map(key=>fields.find(field=>field.key===key)).filter((field):field is FieldDefinition=>Boolean(field)).map(render)}</div></fieldset>):<fieldset key={current.id}><legend>{current.label}</legend>{current.description&&<p className="muted">{current.description}</p>}<div className="form-grid">{current.fieldKeys.map(key=>fields.find(field=>field.key===key)).filter((field):field is FieldDefinition=>Boolean(field)).map(render)}</div></fieldset>}
    {presentation==='wizard'&&<div className="wizard-actions"><button type="button" disabled={active===0||busy} onClick={()=>setActive(value=>Math.max(0,value-1))}>Back</button>{active<visibleSections.length-1?<button type="button" className="primary" disabled={busy} onClick={()=>{void next()}}>Continue</button>:<button type="submit" className="primary" disabled={busy}>Save</button>}</div>}
    {footer}
  </form>
}
