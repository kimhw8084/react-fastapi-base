import type { BaseRecord, WorkspaceAdapter } from './types'
import { FloatingPanelShell, type FloatingAnchor } from '../ui/FloatingPanelShell'
import { FieldValue, fieldLabel } from './FieldValue'

export function HoverRecordPreview<T extends BaseRecord>({row,anchor,adapter,onClose}:{row:T|null;anchor:FloatingAnchor;adapter:WorkspaceAdapter<T>;onClose:()=>void}){
 if(!row)return null
 const title=String(row[adapter.definition.primary_field as keyof T]??row.id)
 const keys=adapter.definition.columns.filter(key=>key!==adapter.definition.primary_field).slice(0,4)
 return <FloatingPanelShell open title={title} anchor={anchor} onClose={onClose} width={330} className="hover-record-preview">
  <dl className="hover-preview-fields">{keys.map(key=>{const field=adapter.definition.fields.find(item=>item.key===key);return <div key={key}><dt>{fieldLabel(adapter.definition,key)}</dt><dd>{field?<FieldValue field={field} value={row[key as keyof T]}/>:<span>{row[key as keyof T]==null?'—':String(row[key as keyof T])}</span>}</dd></div>})}</dl>
  <p className="muted">Quick preview · open the dossier for relationships, history, files and actions.</p>
 </FloatingPanelShell>
}
