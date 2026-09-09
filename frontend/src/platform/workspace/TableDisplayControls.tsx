import type { ViewDefinition, WorkspaceDefinition } from '../../generated/schema'
import { FloatingPanelShell, type FloatingAnchor } from '../ui/FloatingPanelShell'
import { materializeColumns, resetColumns, setColumnVisible } from './tableModel'
import { AdvancedFilterBuilder, MultiSortControl } from './AdvancedFilterBuilder'

export function TableDisplayControls({open,anchor,definition,view,onChange,onClose}:{open:boolean;anchor:FloatingAnchor;definition:WorkspaceDefinition;view:ViewDefinition;onChange:(view:ViewDefinition)=>void;onClose:()=>void}){
 const columns=materializeColumns(definition,view.columns??[])
 const label=(key:string)=>definition.fields.find(field=>field.key===key)?.label??key.replaceAll('_',' ')
 return <FloatingPanelShell open={open} title="Display controls" anchor={anchor} onClose={onClose} width={360} className="display-controls-popover">
  <div className="display-controls-grid">
   <section><h3>Density</h3><div className="segmented"><button aria-pressed={view.density==='comfortable'} onClick={()=>onChange({...view,density:'comfortable'})}>Comfortable</button><button aria-pressed={view.density==='compact'} onClick={()=>onChange({...view,density:'compact'})}>Compact</button></div></section>
   <section><h3>Grouping</h3><label>Group current page<select value={view.group_by??''} onChange={event=>onChange({...view,group_by:event.target.value})}><option value="">No grouping</option>{definition.filter_keys.map(key=><option key={key} value={key}>{label(key)}</option>)}</select></label><p className="muted">Grouping reorganizes the loaded result page without requiring a commercial grid license. Search/filter/sort remain server-scoped.</p></section>
   <MultiSortControl definition={definition} sorts={view.sorts??[]} onChange={sorts=>onChange({...view,sorts})}/>
   <AdvancedFilterBuilder definition={definition} filters={view.advanced_filters??[]} onChange={advanced_filters=>onChange({...view,advanced_filters})}/>
   <section><div className="display-heading"><h3>Columns</h3><button onClick={()=>onChange({...view,columns:resetColumns()})}>Reset</button></div><div className="column-picker">{columns.map(column=><label key={column.colId}><input type="checkbox" checked={!column.hide} onChange={event=>onChange({...view,columns:setColumnVisible(definition,columns,column.colId,event.target.checked)})}/><span>{label(column.colId)}</span></label>)}</div></section>
  </div>
 </FloatingPanelShell>
}
