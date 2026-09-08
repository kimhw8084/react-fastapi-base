import { PeekShell } from '../ui/OverlayShell'
import { RecordActionMenu } from '../commands/RecordActionMenu'
import type { BaseRecord, WorkspaceAdapter } from './types'

export function RecordPeek<T extends BaseRecord>({adapter,row,onClose,onOpen,onEdit,permissions=['read']}:{adapter:WorkspaceAdapter<T>;row:T|null;onClose:()=>void;onOpen:(row:T)=>void;onEdit?:(row:T)=>void;permissions?:readonly string[]}){
 if(!row)return null
 const title=String((row as unknown as Record<string,unknown>)[adapter.definition.primary_field]??row.id)
 return <PeekShell open onClose={onClose} title={title} subtitle={`Quick look · ${adapter.singular} · revision ${row.revision}`} status={row.archived?<span className="status-chip">Archived</span>:undefined} footer={<><RecordActionMenu adapter={adapter} row={row} permissions={permissions} placement="inspector" callbacks={{open:()=>{onOpen(row);onClose()},peek:()=>undefined,edit:onEdit&&!row.archived?()=>{onEdit(row);onClose()}:undefined,copyLink:()=>{void navigator.clipboard.writeText(window.location.href)},history:()=>undefined}}/><button onClick={()=>onOpen(row)}>Open full details</button>{onEdit&&!row.archived&&<button className="primary" onClick={()=>onEdit(row)}>Edit</button>}</>}>
  <dl className="record-details peek-details">{adapter.definition.fields.map(field=><div key={field.key}><dt>{field.label}</dt><dd>{String((row as unknown as Record<string,unknown>)[field.key]??'—')}</dd></div>)}</dl>
 </PeekShell>
}
