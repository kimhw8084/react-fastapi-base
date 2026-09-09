import { useMemo } from 'react'
import type { CommandPlacement } from './registry'
import { actionContext, createRecordActionRegistry, type RecordActionCallbacks } from './recordActions'
import type { BaseRecord, WorkspaceAdapter } from '../workspace/types'

export function RecordActionMenu<T extends BaseRecord>({adapter,row,permissions,placement='context',callbacks,selectionCount=1}:{adapter:WorkspaceAdapter<T>;row:T;permissions:readonly string[];placement?:CommandPlacement;callbacks:RecordActionCallbacks;selectionCount?:number}){
 const registry=useMemo(()=>createRecordActionRegistry(adapter,row,callbacks,permissions,selectionCount),[adapter,row,callbacks,permissions,selectionCount])
 const context=actionContext(adapter as unknown as Pick<WorkspaceAdapter<BaseRecord>,'key'|'entityKey'>,permissions,selectionCount,placement)
 return <div className="record-action-menu" role="menu" aria-label="Record actions">{registry.all(context,placement).map(action=><button role="menuitem" key={action.id} className={action.destructive?'danger-text':undefined} onClick={()=>{void registry.execute(action.id,context)}}>{action.label}</button>)}</div>
}
