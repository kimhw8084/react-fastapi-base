import type { WorkspaceDefinition } from '../../generated/schema'
import type { BaseRecord } from './types'

export function recordValue<T extends BaseRecord>(row:T,key:string):unknown{return (row as unknown as Record<string,unknown>)[key]}
export function displayValue(value:unknown):string{
  if(value===null||value===undefined||value==='')return '—'
  if(typeof value==='boolean')return value?'Yes':'No'
  if(Array.isArray(value))return value.join(', ')
  if(typeof value==='object')return JSON.stringify(value)
  return String(value)
}
export function temporalFields(definition:WorkspaceDefinition):string[]{return definition.fields.filter(field=>field.kind==='date'||field.kind==='datetime').map(field=>field.key)}
export function chooseStartField(definition:WorkspaceDefinition):string{
  const fields=temporalFields(definition)
  return fields.find(key=>/(^|_)(start|begin|opened|occurred|planned)(_at|_on)?$/i.test(key))??fields[0]??'created_at'
}
export function chooseEndField(definition:WorkspaceDefinition,start:string):string{
  const fields=temporalFields(definition).filter(key=>key!==start)
  return fields.find(key=>/(^|_)(end|finish|due|closed|completed)(_at|_on)?$/i.test(key))??fields[0]??'updated_at'
}
export function dateValue(value:unknown):Date|null{
  if(typeof value!=='string'||!value)return null
  const date=new Date(value)
  return Number.isFinite(date.getTime())?date:null
}
export function recordDate<T extends BaseRecord>(row:T,key:string):Date|null{return dateValue(recordValue(row,key))}
export function primaryLabel<T extends BaseRecord>(row:T,definition:WorkspaceDefinition):string{return displayValue(recordValue(row,definition.primary_field)||row.id)}
export function categoricalField(definition:WorkspaceDefinition):string|undefined{return definition.fields.find(field=>field.choices.length>0&&definition.filter_keys.includes(field.key))?.key}
