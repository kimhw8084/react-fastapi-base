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
