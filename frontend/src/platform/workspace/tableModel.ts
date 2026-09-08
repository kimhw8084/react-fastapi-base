import type { ViewColumn, WorkspaceDefinition } from '../../generated/schema'
import type { BaseRecord } from './types'

export interface RowGroup<T extends BaseRecord> { key:string; label:string; rows:T[] }

export function groupRows<T extends BaseRecord>(rows:readonly T[], key:string):RowGroup<T>[] {
  if(!key)return [{key:'',label:'All records',rows:[...rows]}]
  const grouped=new Map<string,T[]>()
  for(const row of rows){
    const raw=(row as Record<string,unknown>)[key]
    const value=raw==null||String(raw).trim()===''?'Unspecified':String(raw)
    const current=grouped.get(value)??[]
    current.push(row);grouped.set(value,current)
  }
  return [...grouped.entries()].sort(([a],[b])=>a.localeCompare(b,undefined,{numeric:true,sensitivity:'base'})).map(([label,values])=>({key:label,label,rows:values}))
}

export function materializeColumns(definition:WorkspaceDefinition, columns:readonly ViewColumn[]):ViewColumn[]{
  const existing=new Map(columns.map(column=>[column.colId,column]))
  return definition.columns.map((colId,index)=>({
    colId,
    width:Math.max(60,Math.min(1200,Math.round(existing.get(colId)?.width??(colId===definition.primary_field?320:160)))),
    hide:Boolean(existing.get(colId)?.hide),
    sort:existing.get(colId)?.sort??null,
    sortIndex:existing.get(colId)?.sortIndex??null,
    pinned:existing.get(colId)?.pinned??null,
    ...(index===0?{}:{}),
  }))
}

export function visibleColumnIds(definition:WorkspaceDefinition,columns:readonly ViewColumn[]):string[]{
  const state=materializeColumns(definition,columns)
  const visible=state.filter(column=>!column.hide).map(column=>column.colId)
  return visible.length?visible:[definition.primary_field]
}

export function setColumnVisible(definition:WorkspaceDefinition,columns:readonly ViewColumn[],colId:string,visible:boolean):ViewColumn[]{
  if(!definition.columns.includes(colId))return materializeColumns(definition,columns)
  const state=materializeColumns(definition,columns)
  const next=state.map(column=>column.colId===colId?{...column,hide:!visible}:column)
  if(next.every(column=>column.hide)){
    return next.map(column=>column.colId===definition.primary_field?{...column,hide:false}:column)
  }
  return next
}

export function resetColumns():ViewColumn[]{return []}
