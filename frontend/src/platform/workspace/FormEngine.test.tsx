import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { FormEngine } from './FormEngine'
import type { FieldDefinition } from '../../generated/schema'
import type { Draft } from './types'

const fields:FieldDefinition[]=[
  {key:'category',label:'Category',kind:'select',required:true,nullable:false,max_length:null,choices:['hardware','software'],minimum:null,maximum:null,step:null,unit:null,precision:null,display_format:null,searchable:true,filterable:true,sortable:true,exportable:true,computed:false,read_only:false},
  {key:'part',label:'Part',kind:'select',required:true,nullable:false,max_length:null,choices:[],minimum:null,maximum:null,step:null,unit:null,precision:null,display_format:null,searchable:true,filterable:true,sortable:true,exportable:true,computed:false,read_only:false},
]

describe('definition-driven form extensions',()=>{
  it('resolves dependent choices and protects against stale async validation',async()=>{
    let draft:Draft={category:'hardware',part:''}
    const onChange=vi.fn((next:Draft)=>{draft=next})
    const validateFieldAsync=vi.fn(async()=>undefined)
    const {rerender}=render(<FormEngine formId="dependent" fields={fields} draft={draft} initial={{category:'',part:''}} onChange={onChange} onSubmit={()=>{}} resolveChoices={(field,current)=>field.key==='part'?(current.category==='hardware'?['cpu','disk']:['api','queue']):undefined} validateFieldAsync={validateFieldAsync}/>)
    expect(screen.getByRole('option',{name:'cpu'})).toBeInTheDocument()
    fireEvent.blur(document.getElementById('record-field-category')!)
    await waitFor(()=>expect(validateFieldAsync).toHaveBeenCalled())
    draft={category:'software',part:''}
    rerender(<FormEngine formId="dependent" fields={fields} draft={draft} initial={{category:'',part:''}} onChange={onChange} onSubmit={()=>{}} resolveChoices={(field,current)=>field.key==='part'?(current.category==='hardware'?['cpu','disk']:['api','queue']):undefined} validateFieldAsync={validateFieldAsync}/>)
    expect(screen.getByRole('option',{name:'api'})).toBeInTheDocument()
    expect(screen.queryByRole('option',{name:'cpu'})).not.toBeInTheDocument()
 })
})

describe('form validation recovery',()=>{
 it('keeps pending async field checks out of the linked error summary',async()=>{
  let finish:(message:string|undefined)=>void=()=>{}
  const validateFieldAsync=vi.fn(()=>new Promise<string|undefined>(resolve=>{finish=resolve}))
  const draft={category:'hardware',part:'cpu'}
  render(<FormEngine formId="pending" fields={fields} draft={draft} initial={draft} onChange={()=>{}} onSubmit={()=>{}} validateFieldAsync={validateFieldAsync}/> )
  fireEvent.blur(document.getElementById('record-field-category')!)
  fireEvent.submit(screen.getByRole('form',{name:'Record form'}))
  expect(await screen.findByText('Wait for field validation to finish before saving.')).toBeVisible()
  expect(screen.queryByRole('button',{name:/Wait for field validation/})).not.toBeInTheDocument()
  expect(screen.queryByRole('region',{name:'Form errors'})).not.toBeInTheDocument()
  finish(undefined)
 })
 it('routes field summary actions to an eligible input and keeps form-level errors unlinked',async()=>{
  const draft={category:'hardware',part:'cpu'}
  const {rerender}=render(<FormEngine formId="summary" fields={fields} draft={draft} initial={draft} onChange={()=>{}} onSubmit={()=>{}} validateAsync={async()=>({part:'Choose a supported part.'})}/> )
  fireEvent.submit(screen.getByRole('form',{name:'Record form'}))
  const summaryAction=await screen.findByRole('button',{name:'Choose a supported part.'})
  const target=document.getElementById('record-field-part')!
  target.getClientRects=()=>[{width:10,height:10} as DOMRect] as unknown as DOMRectList
  fireEvent.click(summaryAction)
  expect(target).toHaveFocus()
  rerender(<FormEngine formId="summary" fields={fields} draft={draft} initial={draft} onChange={()=>{}} onSubmit={()=>{}} validateAsync={async()=>({__form:'This combination needs a policy review.'})}/> )
  fireEvent.submit(screen.getByRole('form',{name:'Record form'}))
  expect(await screen.findByRole('alert',{name:'Form-level errors'})).toHaveTextContent('policy review')
  expect(screen.queryByRole('button',{name:/policy review/})).not.toBeInTheDocument()
 })
})
