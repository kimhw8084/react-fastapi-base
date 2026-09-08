import type { BaseRecord, WorkspaceAdapter } from './types'
import { FloatingPanelShell, type FloatingAnchor } from '../ui/FloatingPanelShell'

export function TableContextMenu<T extends BaseRecord>({row,anchor,adapter,canWrite,canRestore,onClose,onOpen,onPeek,onEdit,onTransition,onCopyLink}:{row:T|null;anchor:FloatingAnchor;adapter:WorkspaceAdapter<T>;canWrite:boolean;canRestore:boolean;onClose:()=>void;onOpen:(row:T)=>void;onPeek:(row:T)=>void;onEdit:(row:T)=>void;onTransition:(row:T,action:'archive'|'restore')=>void;onCopyLink:(row:T)=>void}){
 if(!row)return null
 const title=String(row[adapter.definition.primary_field as keyof T]??row.id)
 return <FloatingPanelShell open title={title} anchor={anchor} onClose={onClose} width={260} className="row-context-popover">
  <div className="context-action-list" role="menu">
   <button role="menuitem" onClick={()=>{onPeek(row);onClose()}}>◫ Quick Look</button>
   <button role="menuitem" onClick={()=>{onOpen(row);onClose()}}>↗ Open dossier</button>
   {canWrite&&<button role="menuitem" onClick={()=>{onEdit(row);onClose()}}>✎ Edit</button>}
   <button role="menuitem" onClick={()=>{onCopyLink(row);onClose()}}>⧉ Copy record link</button>
   {canWrite&&(!row.archived||canRestore)&&<button role="menuitem" className={row.archived?'':'danger-text'} onClick={()=>{onTransition(row,row.archived?'restore':'archive');onClose()}}>{row.archived?'↶ Restore':'⌫ Archive'}</button>}
  </div>
 </FloatingPanelShell>
}
