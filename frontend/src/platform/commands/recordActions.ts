import { ActionRegistry, type CommandContext, type CommandPlacement, type RegisteredAction } from './registry'
import type { BaseRecord, WorkspaceAdapter } from '../workspace/types'

export interface RecordActionCallbacks {
  open:()=>void
  peek:()=>void
  edit?:()=>void
  transition?:(action:'archive'|'restore')=>void
  copyLink?:()=>void
  history?:()=>void
  bulkEdit?:()=>void
}

/** Record actions are registered once and projected into every surface. */
export function createRecordActionRegistry<T extends BaseRecord>(adapter:WorkspaceAdapter<T>,row:T,callbacks:RecordActionCallbacks,permissions:readonly string[],selectionCount=1):ActionRegistry{
 const actions:RegisteredAction[]=[]
 const canWrite=permissions.includes('write'),canRestore=permissions.includes('restore')
 const add=(id:string,label:string,run:()=>void,placements:CommandPlacement[],extra:Partial<RegisteredAction>={})=>actions.push({id,label,entity:adapter.entityKey??adapter.key,placements,run,...extra})
 add('record.open','Open dossier',callbacks.open,['context','keyboard','palette','dossier','inspector','selection'],{requiresSelection:true,maxSelection:1})
 add('record.peek','Quick look',callbacks.peek,['toolbar','context','keyboard','palette','selection','dossier','inspector'],{requiresSelection:true,maxSelection:1})
 if(callbacks.edit&&canWrite) add('record.edit','Edit record',callbacks.edit,['toolbar','context','keyboard','palette','selection','dossier','inspector'],{permission:'write',maxSelection:1})
 if(callbacks.bulkEdit&&canWrite) add('record.bulk-edit','Bulk edit',callbacks.bulkEdit,['toolbar','selection'],{permission:'write',requiresSelection:true})
 if(callbacks.copyLink) add('record.copy-link','Copy record link',callbacks.copyLink,['context','dossier','inspector','palette'])
 if(callbacks.history) add('record.history','Open history',callbacks.history,['dossier','inspector','palette'])
 if(callbacks.transition&&(row.archived?canRestore:canWrite)){const action=row.archived?'restore':'archive';add(`record.${action}`,row.archived?'Restore record':'Archive record',()=>callbacks.transition?.(action),['toolbar','context','keyboard','palette','selection','dossier','inspector'],{permission:row.archived?'restore':'write',destructive:!row.archived,requiresSelection:true,minSelection:selectionCount})}
 return new ActionRegistry(actions)
}

export function actionContext(adapter:Pick<WorkspaceAdapter<BaseRecord>,'key'|'entityKey'>,permissions:readonly string[],selectionCount:number,placement?:CommandPlacement):CommandContext{return{entity:adapter.entityKey??adapter.key,permissions,selectionCount,mode:placement??'browse',readOnly:!permissions.includes('write')}}
