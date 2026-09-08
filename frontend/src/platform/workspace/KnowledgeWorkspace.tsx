import { useState } from 'react'
import type { BaseRecord, ProjectionProps } from './types'
import { ProjectionWorkspaceFrame } from './ProjectionWorkspaceFrame'
import { recordValue } from './projectionUtils'

function text(row:BaseRecord,key:string){const value=recordValue(row,key);return value==null?'':String(value)}
function jsonValue(row:BaseRecord,key:string):unknown{return recordValue(row,key)}
function MarkdownView({value}:{value:string}){
 const lines=value.split(/\r?\n/);let code=false
 return <div className="knowledge-markdown">{lines.map((line,index)=>{
  if(line.trim().startsWith('```')){code=!code;return <div key={index} className="markdown-code-boundary"/>}
  if(code)return <code key={index}>{line||' '}</code>
  if(/^###\s+/.test(line))return <h3 key={index}>{line.replace(/^###\s+/,'')}</h3>
  if(/^##\s+/.test(line))return <h2 key={index}>{line.replace(/^##\s+/,'')}</h2>
  if(/^#\s+/.test(line))return <h1 key={index}>{line.replace(/^#\s+/,'')}</h1>
  if(/^[-*]\s+/.test(line))return <div className="markdown-list-item" key={index}>• <span>{line.replace(/^[-*]\s+/,'')}</span></div>
  return <p key={index}>{line||' '}</p>
 })}</div>
}
export function KnowledgeWorkspace<T extends BaseRecord>(props:ProjectionProps<T>){
 const [selected,setSelected]=useState<string|null>(null)
 return <ProjectionWorkspaceFrame {...props} projectionKey="knowledge" title="Engineering knowledge" description="Runbooks, procedures, standards and lessons with ownership, review state, relationships and revision history." extraMetrics={rows=>[{label:'Published',value:rows.filter(row=>text(row,'status')==='published').length},{label:'Needs review',value:rows.filter(row=>['needs_review','stale'].includes(text(row,'review_state'))).length}]}>{(rows,{openRow,peekRow})=>{
  const current=rows.find(row=>row.id===selected)??rows[0]
  const tags=current&&Array.isArray(jsonValue(current,'tags'))?jsonValue(current,'tags') as string[]:[]
  const procedures=current?jsonValue(current,'procedures'):null
  return <div className="knowledge-workbench">
   <nav className="knowledge-navigator" aria-label="Knowledge entries"><header><span className="eyebrow">Library</span><strong>{rows.length} matching entries</strong></header>{rows.map(row=><button key={row.id} className={current?.id===row.id?'selected':''} onClick={()=>setSelected(row.id)} onDoubleClick={()=>openRow(row)}><strong>{text(row,'title')}</strong><span>{text(row,'entry_type').replaceAll('_',' ')} · {text(row,'status')}</span><small>{text(row,'owner')||'Unowned'}</small></button>)}</nav>
   {current&&<article className="knowledge-document"><header><div><span className="eyebrow">{text(current,'entry_type').replaceAll('_',' ')}</span><h1>{text(current,'title')}</h1><p>{text(current,'criticality')} · {text(current,'review_state').replaceAll('_',' ')}</p></div><div className="toolbar-actions"><button onClick={()=>peekRow(current)}>Quick look</button><button className="primary" onClick={()=>openRow(current)}>Open dossier</button></div></header><MarkdownView value={text(current,'content')||'No authored content yet.'}/></article>}
   {current&&<aside className="knowledge-context"><section><span className="eyebrow">Governance</span><dl><div><dt>Status</dt><dd>{text(current,'status')}</dd></div><div><dt>Criticality</dt><dd>{text(current,'criticality')}</dd></div><div><dt>Owner</dt><dd>{text(current,'owner')||'Unowned'}</dd></div><div><dt>Review</dt><dd>{text(current,'review_state').replaceAll('_',' ')}</dd></div><div><dt>Next review</dt><dd>{text(current,'next_review_at')||'Unscheduled'}</dd></div><div><dt>Revision</dt><dd>{current.revision}</dd></div></dl></section><section><span className="eyebrow">Tags</span><div className="field-chip-list">{tags.length?tags.map(tag=><span key={tag} className="field-chip">{tag}</span>):<span className="muted">No tags</span>}</div></section><section><span className="eyebrow">Structured procedure</span><pre className="field-structured-value">{procedures&&typeof procedures==='object'&&Object.keys(procedures as object).length?JSON.stringify(procedures,null,2):'No structured procedure.'}</pre></section></aside>}
  </div>
 }}</ProjectionWorkspaceFrame>
}
