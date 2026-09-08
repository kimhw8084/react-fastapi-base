import { useState, type ReactNode } from 'react'
export function SplitPaneShell({primary,secondary,initial=68,minPrimary=35,maxPrimary=80,label='Resize workspace panels'}:{primary:ReactNode;secondary:ReactNode;initial?:number;minPrimary?:number;maxPrimary?:number;label?:string}){
 const [primarySize,setPrimarySize]=useState(initial)
 return <div className="split-pane-shell" style={{gridTemplateColumns:`minmax(0,${primarySize}fr) auto minmax(0,${100-primarySize}fr)`}}><div className="split-pane-primary">{primary}</div><label className="split-pane-divider"><span className="sr-only">{label}</span><input aria-label={label} type="range" min={minPrimary} max={maxPrimary} value={primarySize} onChange={event=>setPrimarySize(Number(event.target.value))}/></label><div className="split-pane-secondary">{secondary}</div></div>
}
