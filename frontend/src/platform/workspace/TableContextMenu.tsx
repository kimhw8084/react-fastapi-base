import type { BaseRecord, WorkspaceAdapter } from './types'
import { FloatingPanelShell, type FloatingAnchor } from '../ui/FloatingPanelShell'
import { RecordActionMenu } from '../commands/RecordActionMenu'

export function TableContextMenu<T extends BaseRecord>({row,anchor,adapter,canWrite,canRestore,onClose,onOpen,onPeek,onEdit,onTransition,onCopyLink}:{row:T|null;anchor:FloatingAnchor;adapter:WorkspaceAdapter<T>;canWrite:boolean;canRestore:boolean;onClose:()=>void;onOpen:(row:T)=>void;onPeek:(row:T)=>void;onEdit:(row:T)=>void;onTransition:(row:T,action:'archive'|'restore')=>void;onCopyLink:(row:T)=>void}){
 if(!row)return null
 const title=String(row[adapter.definition.primary_field as keyof T]??row.id)
 return <FloatingPanelShell open title={title} anchor={anchor} onClose={onClose} width={260} className="row-context-popover">
  <RecordActionMenu adapter={adapter} row={row} permissions={[...(canWrite?['write']:[]),...(canRestore?['restore']:[]),'read']} callbacks={{open:()=>{onOpen(row);onClose()},peek:()=>{onPeek(row);onClose()},edit:canWrite?()=>{onEdit(row);onClose()}:undefined,copyLink:()=>{onCopyLink(row);onClose()},transition:action=>{onTransition(row,action);onClose()}}}/>
 </FloatingPanelShell>
}
