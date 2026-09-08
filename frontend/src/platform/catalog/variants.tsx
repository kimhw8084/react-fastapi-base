import type { ReactNode } from 'react'
import { ProgressBar, StatusBadge, Button, Heading, MonoText } from '../ui/primitives'
import { catalogVariants } from './generatedVariants'

export type CatalogFamily = 'content'|'control'|'indicator'|'surface'|'form'|'grid'|'workspace'|'chart'|'statistical'|'timeline'|'diagram'|'spatial'|'semiconductor'|'software'|'editor'|'collaboration'|'admin'|'layout'|'service'|'certification'
export interface CatalogVariant { id:string; category:string; family:CatalogFamily; required:boolean }
export interface CatalogVariantProps { variant:CatalogVariant; children?:ReactNode; value?:string|number; open?:boolean; rows?:Array<Record<string,string|number>> }

const sampleRows = [{name:'Alpha',status:'Active',value:82},{name:'Beta',status:'Review',value:61},{name:'Gamma',status:'Healthy',value:94}]

function ChartVariant({variant, rows}:Pick<CatalogVariantProps,'variant'|'rows'>) {
  const points=(rows??sampleRows).map((row,index)=>({x:24+index*48,y:112-(Number(row.value??index*20)%90)}))
  const path=points.map((point,index)=>`${index?'L':'M'} ${point.x} ${point.y}`).join(' ')
  return <figure className="catalog-chart" aria-label={variant.id}><svg viewBox="0 0 160 128" role="img"><path d="M16 112H152M16 16V112"/><path d={path} fill="none" stroke="currentColor" strokeWidth="3"/></svg><figcaption>{variant.id}</figcaption></figure>
}

function GridVariant({variant,rows}:Pick<CatalogVariantProps,'variant'|'rows'>) {
  const values=rows??sampleRows
  return <div className="catalog-grid" aria-label={variant.id}><table><caption>{variant.id}</caption><thead><tr><th scope="col">Name</th><th scope="col">Status</th><th scope="col">Value</th></tr></thead><tbody>{values.map((row,index)=><tr key={`${variant.id}-${index}`}><th scope="row">{String(row.name??'Record')}</th><td>{String(row.status??'Active')}</td><td>{String(row.value??0)}</td></tr>)}</tbody></table></div>
}

function FormVariant({variant}:Pick<CatalogVariantProps,'variant'>) {
  return <form className="catalog-form" aria-label={variant.id} onSubmit={event=>event.preventDefault()}><label>{variant.id}<input name={variant.id} placeholder={`Enter ${variant.id}`} /></label><Button type="submit">Validate</Button></form>
}

function SurfaceVariant({variant,children,open=true}:CatalogVariantProps) {
  if (!open) return null
  return <section className="catalog-surface" role="region" aria-label={variant.id}><header><Heading level={3}>{variant.id}</Heading><button type="button" aria-label={`Close ${variant.id}`}>×</button></header>{children??<p>Surface content remains available without losing context.</p>}</section>
}

export function CatalogVariant({variant,children,value=72,open=true,rows}:CatalogVariantProps) {
  switch (variant.family) {
    case 'content': return <article className="catalog-content" aria-label={variant.id}><Heading level={3}>{variant.id}</Heading><p>{children??`Reusable ${variant.category.toLowerCase()} content.`}</p></article>
    case 'control': return <Button type="button" aria-label={variant.id}>{children??variant.id}</Button>
    case 'indicator': return <div className="catalog-indicator" aria-label={variant.id}><StatusBadge status={variant.id}/><ProgressBar value={Number(value)} label="Current"/></div>
    case 'surface': return <SurfaceVariant variant={variant} open={open}>{children}</SurfaceVariant>
    case 'form': return <FormVariant variant={variant}/>
    case 'grid': return <GridVariant variant={variant} rows={rows}/>
    case 'chart': case 'statistical': return <ChartVariant variant={variant} rows={rows}/>
    case 'timeline': return <ol className="catalog-timeline" aria-label={variant.id}>{(rows??sampleRows).map((row,index)=><li key={`${variant.id}-${index}`}><time>{`2026-09-0${index+1}`}</time><strong>{String(row.name)}</strong><span>{String(row.status)}</span></li>)}</ol>
    case 'diagram': case 'spatial': return <section className="catalog-canvas" aria-label={variant.id}><div className="catalog-node">{variant.id}</div><div className="catalog-node">Canonical record</div></section>
    case 'semiconductor': return <section className="catalog-engineering" aria-label={variant.id}><MonoText>{variant.id}</MonoText><ChartVariant variant={variant} rows={rows}/></section>
    case 'software': case 'editor': return <section className="catalog-editor" aria-label={variant.id}><Heading level={3}>{variant.id}</Heading><pre>{children??'Read-only canonical view'}</pre></section>
    case 'collaboration': case 'admin': case 'service': case 'certification': case 'workspace': case 'layout': return <section className={`catalog-${variant.family}`} aria-label={variant.id}><Heading level={3}>{variant.id}</Heading><p>{children??'Platform-owned reusable surface.'}</p></section>
  }
}

export function CatalogVariantGallery({rows=sampleRows}:{rows?:Array<Record<string,string|number>>}) {
  return <div className="catalog-variant-gallery">{catalogVariants.map(variant=><CatalogVariant key={variant.id} variant={variant} rows={rows}/>)}</div>
}
