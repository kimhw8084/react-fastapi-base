import type { WorkspaceDefinition } from '../../generated/schema'

type AdvancedFilter = {key:string;operator:string;value:string}
const operators = ['eq', 'neq', 'contains', 'starts_with', 'gt', 'gte', 'lt', 'lte'] as const

export function AdvancedFilterBuilder({definition,filters,onChange}:{definition:WorkspaceDefinition;filters:readonly Record<string,unknown>[];onChange:(filters:Record<string,unknown>[])=>void}) {
  const items:AdvancedFilter[]=filters.flatMap(item=>typeof item.key==='string'&&typeof item.value==='string'?[{key:item.key,operator:typeof item.operator==='string'?item.operator:'eq',value:item.value}]:[])
  const add = () => {
    const key = definition.filter_keys[0] ?? definition.fields[0]?.key
    if (!key) return
    onChange([...items, {key, operator:'eq', value:''}])
  }
  const update = (index:number, patch:Partial<AdvancedFilter>) => onChange(items.map((filter,item)=>item===index?{...filter,...patch}:filter))
  return <section className="advanced-filter-builder" aria-label="Advanced filters">
    <header><h3>Advanced filters</h3><button type="button" onClick={add} disabled={!definition.filter_keys.length}>Add filter</button></header>
    {items.length===0?<p className="muted">No advanced filters. Add one to narrow the server query.</p>:<div className="advanced-filter-list">{items.map((filter,index)=>{const field=definition.fields.find(item=>item.key===filter.key);return <div className="advanced-filter-row" key={`${filter.key}-${index}`}>
      <label>Field<select value={filter.key} onChange={event=>update(index,{key:event.target.value})}>{definition.filter_keys.map(key=><option value={key} key={key}>{definition.fields.find(item=>item.key===key)?.label??key}</option>)}</select></label>
      <label>Operator<select value={filter.operator} onChange={event=>update(index,{operator:event.target.value})}>{operators.map(operator=><option key={operator} value={operator}>{operator.replaceAll('_',' ')}</option>)}</select></label>
      <label>Value{field?.choices.length?<select value={filter.value} onChange={event=>update(index,{value:event.target.value})}><option value="">Choose…</option>{field.choices.map(choice=><option value={choice} key={choice}>{choice.replaceAll('_',' ')}</option>)}</select>:<input value={filter.value} maxLength={200} onChange={event=>update(index,{value:event.target.value})}/>}</label>
      <button type="button" aria-label={`Remove filter ${index+1}`} onClick={()=>onChange(items.filter((_,item)=>item!==index))}>Remove</button>
    </div>})}</div>}
  </section>
}

export function MultiSortControl({definition,sorts,onChange}:{definition:WorkspaceDefinition;sorts:readonly {key:string;direction:'asc'|'desc'}[];onChange:(sorts:{key:string;direction:'asc'|'desc'}[])=>void}) {
  const add=()=>{const key=definition.sort_keys.find(item=>!sorts.some(sort=>sort.key===item))??definition.sort_keys[0];if(key)onChange([...sorts,{key,direction:'asc'}])}
  return <section className="multi-sort-control" aria-label="Multi-sort"><header><h3>Sort priority</h3><button type="button" onClick={add} disabled={!definition.sort_keys.length||sorts.length>=8}>Add sort</button></header>{sorts.length===0?<p className="muted">Primary sort applies. Add a secondary sort for deterministic ordering.</p>:sorts.map((sort,index)=><div className="multi-sort-row" key={`${sort.key}-${index}`}><span>{index+1}</span><select value={sort.key} onChange={event=>onChange(sorts.map((item,current)=>current===index?{...item,key:event.target.value}:item))}>{definition.sort_keys.map(key=><option value={key} key={key}>{definition.fields.find(field=>field.key===key)?.label??key}</option>)}</select><select value={sort.direction} onChange={event=>onChange(sorts.map((item,current)=>current===index?{...item,direction:event.target.value as 'asc'|'desc'}:item))}><option value="asc">Ascending</option><option value="desc">Descending</option></select><button type="button" aria-label={`Remove sort ${index+1}`} onClick={()=>onChange(sorts.filter((_,current)=>current!==index))}>Remove</button></div>)}</section>
}
