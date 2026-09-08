import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { SurfaceShell } from './SurfaceShell'
import { useSurfaceRegistration } from './SurfaceManager'

export interface FloatingAnchor { x:number; y:number }
export function FloatingPanelShell({open,title,anchor,onClose,children,className='',width=300}:{open:boolean;title:ReactNode;anchor:FloatingAnchor;onClose:()=>void;children:ReactNode;className?:string;width?:number}){
 const ref=useRef<HTMLDivElement>(null)
 const [position,setPosition]=useState(anchor)
 const {layer,isTop}=useSurfaceRegistration('popover',open)
 useLayoutEffect(()=>{
  if(!open)return
  const node=ref.current;if(!node)return
  const rect=node.getBoundingClientRect();const margin=10
  setPosition({x:Math.max(margin,Math.min(anchor.x,window.innerWidth-rect.width-margin)),y:Math.max(margin,Math.min(anchor.y,window.innerHeight-rect.height-margin))})
 },[open,anchor.x,anchor.y,width])
 useEffect(()=>{
  if(!open)return
  const pointer=(event:PointerEvent)=>{if(ref.current&&!ref.current.contains(event.target as Node))onClose()}
  const key=(event:KeyboardEvent)=>{if(event.key==='Escape'&&isTop){event.preventDefault();onClose()}}
  document.addEventListener('pointerdown',pointer,true);document.addEventListener('keydown',key,true)
  return()=>{document.removeEventListener('pointerdown',pointer,true);document.removeEventListener('keydown',key,true)}
 },[open,isTop,onClose])
 if(!open)return null
 return <div ref={ref} className={`floating-panel-shell ${className}`.trim()} style={{left:position.x,top:position.y,width,zIndex:layer}} role="dialog" aria-label={typeof title==='string'?title:undefined}>
  <SurfaceShell title={title}>{children}</SurfaceShell>
 </div>
}
