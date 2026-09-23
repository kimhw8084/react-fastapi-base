import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { FieldDefinition, WorkspaceDefinition } from '../../generated/schema'
import { FieldValue, fieldDisplayText, fieldLabel } from './FieldValue'

const definition=(key:string,kind:FieldDefinition['kind'],extra:Partial<FieldDefinition>={}):FieldDefinition=>({key,label:key.replaceAll('_',' '),kind,required:false,nullable:true,max_length:null,choices:[],minimum:null,maximum:null,step:null,unit:null,precision:null,display_format:null,searchable:true,filterable:true,sortable:true,exportable:true,computed:false,read_only:false,...extra})

describe('shared field-aware record presentation',()=>{
 it('humanizes enum values without changing stored values',()=>{
  render(<FieldValue field={definition('status','select',{choices:['in_progress']})} value="in_progress"/>)
  expect(screen.getByText('In Progress')).toBeVisible()
 })
 it('renders false as false and formats governed numeric values',()=>{
  const {rerender}=render(<FieldValue field={definition('enabled','boolean')} value={false}/> )
  expect(screen.getByText('No')).toBeVisible()
  rerender(<FieldValue field={definition('yield','percent',{unit:'%',precision:1})} value={97.5}/> )
  expect(screen.getByText('97.5%')).toBeVisible()
  rerender(<FieldValue field={definition('duration','duration',{unit:'min'})} value={135}/> )
  expect(screen.getByText('2h 15m')).toBeVisible()
 })
 it('renders multiselect, structured, missing and date values safely',()=>{
  const {rerender}=render(<FieldValue field={definition('teams','multiselect')} value={['line_a','line_b']}/> )
  expect(screen.getByText('Line A')).toBeVisible();expect(screen.getByText('Line B')).toBeVisible()
  rerender(<FieldValue field={definition('settings','json')} value='{"mode":"safe"}'/> )
  expect(screen.getByText(/"mode": "safe"/)).toBeVisible()
  rerender(<FieldValue field={definition('owner','text')} value={null}/> )
  expect(screen.getByLabelText('No value')).toBeVisible()
  rerender(<FieldValue field={definition('started_at','datetime')} value="not a timestamp"/> )
  expect(screen.getByText('not a timestamp')).toBeVisible()
 })
 it('uses the governed field label and safe key fallback',()=>{
  const workspace={fields:[definition('run_id','text',{label:'Run ID'})]} as WorkspaceDefinition
  expect(fieldLabel(workspace,'run_id')).toBe('Run ID')
  expect(fieldLabel(workspace,'missing_value')).toBe('missing value')
 })
 it('shares canonical text formatting with projection labels',()=>{
  expect(fieldDisplayText(definition('status','select'),'in_progress')).toBe('In Progress')
  expect(fieldDisplayText(definition('enabled','boolean'),false)).toBe('No')
  expect(fieldDisplayText(definition('load','unit_number',{unit:'kg',precision:1}),2.4)).toBe('2.4 kg')
 })
})
