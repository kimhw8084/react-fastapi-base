import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import type { SurfaceKind } from './surface'
import { SurfaceShell } from './SurfaceShell'
import { useSurfaceRegistration } from './SurfaceManager'

const focusable='a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'
function focusables(root:HTMLElement|null){return root?Array.from(root.querySelectorAll<HTMLElement>(focusable)).filter(node=>node.getAttribute('aria-hidden')!=='true'):[]}

export interface OverlayShellProps {
 open:boolean
 kind:SurfaceKind
 title:ReactNode
 subtitle?:ReactNode
 status?:ReactNode
 footer?:ReactNode
 onClose:()=>void
 children:ReactNode
 className?:string
 modal?:boolean
 expandable?:boolean
 wide?:boolean
 busy?:boolean
}
export function OverlayShell({open,kind,title,subtitle,status,footer,onClose,children,className='',modal=true,expandable=false,wide=false,busy=false}:OverlayShellProps){
 const ref=useRef<HTMLDivElement>(null)
 const returnFocus=useRef<HTMLElement|null>(null)
 const [expanded,setExpanded]=useState(false)
 const {layer,isTop}=useSurfaceRegistration(kind,open)
 const requestClose=useCallback(()=>{if(!busy)onClose()},[busy,onClose])
 useEffect(()=>{
  if(!open)return
  returnFocus.current=document.activeElement instanceof HTMLElement?document.activeElement:null
  queueMicrotask(()=>{const nodes=focusables(ref.current);(nodes[0]??ref.current)?.focus()})
  return ()=>{const previous=returnFocus.current;returnFocus.current=null;if(previous?.isConnected)previous.focus()}
 },[open])
 useEffect(()=>{if(!open)setExpanded(false)},[open])
 useEffect(()=>{const node=ref.current;if(!open||!node)return;const handler=()=>requestClose();node.addEventListener('golden-request-close',handler);return()=>node.removeEventListener('golden-request-close',handler)},[open,requestClose])
 if(!open)return null
 const onKeyDown=(event:React.KeyboardEvent<HTMLDivElement>)=>{
  if(event.key==='Escape'&&isTop){event.preventDefault();requestClose();return}
  if(event.key!=='Tab'||!modal)return
  const nodes=focusables(ref.current);if(!nodes.length){event.preventDefault();ref.current?.focus();return}
  const first=nodes[0]!,last=nodes[nodes.length-1]!,active=document.activeElement
  if(event.shiftKey&&active===first){event.preventDefault();last.focus()}
  else if(!event.shiftKey&&active===last){event.preventDefault();first.focus()}
 }
 return <div className={`overlay-layer ${className}`.trim()} data-surface-kind={kind} data-expanded={expanded||undefined} data-wide={wide||undefined} style={{zIndex:layer}}>
  <button className="surface-backdrop" aria-label={`Close ${String(title)}`} onClick={requestClose} disabled={busy}/>
  <div ref={ref} className="overlay-surface" role="dialog" aria-modal={modal||undefined} tabIndex={-1} onKeyDown={onKeyDown}>
   <SurfaceShell title={title} subtitle={subtitle} status={status} controls={<>{expandable&&<button type="button" className="icon-button" onClick={()=>setExpanded(value=>!value)} disabled={busy} aria-label={expanded?`Restore ${String(title)}`:`Expand ${String(title)}`}>{expanded?'↙':'↗'}</button>}<button type="button" className="icon-button" onClick={requestClose} disabled={busy} aria-label={`Close ${String(title)}`}>×</button></>} footer={footer}>{children}</SurfaceShell>
  </div>
 </div>
}

export function BottomSheetShell(props:Omit<OverlayShellProps,'kind'|'className'>){return <OverlayShell {...props} kind="sheet" className="bottom-sheet-layer"/>}
export function PeekShell(props:Omit<OverlayShellProps,'kind'|'className'>){return <OverlayShell {...props} kind="peek" className="peek-layer"/>}
export function CommandPaletteShell(props:Omit<OverlayShellProps,'kind'|'className'>){return <OverlayShell {...props} kind="command" className="command-palette-layer"/>}
