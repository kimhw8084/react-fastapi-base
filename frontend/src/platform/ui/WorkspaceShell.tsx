import type { ReactNode } from 'react'
export interface WorkspaceMetric { label:string; value:ReactNode; className?:string }
export function WorkspaceShell({eyebrow,title,description,actions,metrics,commandBar,secondaryBar,notice,children,footer}:{eyebrow?:ReactNode;title:ReactNode;description?:ReactNode;actions?:ReactNode;metrics?:WorkspaceMetric[];commandBar?:ReactNode;secondaryBar?:ReactNode;notice?:ReactNode;children:ReactNode;footer?:ReactNode}){
 return <div className="workspace">
   <section className="page-heading"><div>{eyebrow&&<span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1>{description&&<p>{description}</p>}</div>{actions&&<div className="header-actions">{actions}</div>}</section>
   {metrics?.length?<section className="workspace-summary" aria-label="Workspace summary">{metrics.map(metric=><div key={metric.label}><span>{metric.label}</span><strong className={metric.className}>{metric.value}</strong></div>)}</section>:null}
   {commandBar&&<div className="command-bar">{commandBar}</div>}
   {secondaryBar&&<div className="secondary-bar">{secondaryBar}</div>}
   {notice}
   <div className="workspace-primary">{children}</div>
   {footer&&<footer className="workspace-footer">{footer}</footer>}
 </div>
}
