import { useEffect, useMemo, useState } from 'react'
import { CommandPaletteShell } from '../ui/OverlayShell'

export interface PaletteCommand {
 id:string
 label:string
 description?:string
 keywords?:readonly string[]
 shortcut?:string
 action:()=>void
}
function normalize(value:string){return value.trim().toLocaleLowerCase()}
export function CommandPalette({open,onClose,commands}:{open:boolean;onClose:()=>void;commands:readonly PaletteCommand[]}){
 const [query,setQuery]=useState('')
 const [active,setActive]=useState(0)
 useEffect(()=>{if(open){setQuery('');setActive(0)}},[open])
 const filtered=useMemo(()=>{
  const needle=normalize(query)
  if(!needle)return [...commands]
  return commands.filter(command=>normalize([command.label,command.description??'',...(command.keywords??[])].join(' ')).includes(needle))
 },[commands,query])
 useEffect(()=>{if(active>=filtered.length)setActive(Math.max(0,filtered.length-1))},[active,filtered.length])
 const choose=(command:PaletteCommand|undefined)=>{if(!command)return;onClose();command.action()}
 return <CommandPaletteShell open={open} onClose={onClose} title="Command palette" subtitle="Navigate and run registered application commands.">
  <div className="command-palette">
   <label className="command-search"><span className="sr-only">Search commands</span><input value={query} onChange={event=>{setQuery(event.target.value);setActive(0)}} onKeyDown={event=>{if(event.key==='ArrowDown'){event.preventDefault();setActive(value=>Math.min(filtered.length-1,value+1))}else if(event.key==='ArrowUp'){event.preventDefault();setActive(value=>Math.max(0,value-1))}else if(event.key==='Home'){event.preventDefault();setActive(0)}else if(event.key==='End'){event.preventDefault();setActive(Math.max(0,filtered.length-1))}else if(event.key==='Enter'){event.preventDefault();choose(filtered[active])}}} placeholder="Search workspaces and commands…" autoComplete="off"/></label>
   <div className="command-results" role="listbox" aria-label="Available commands">{filtered.length?filtered.map((command,index)=><button type="button" key={command.id} role="option" aria-selected={index===active} className="command-result" onMouseEnter={()=>setActive(index)} onClick={()=>choose(command)}><span><strong>{command.label}</strong>{command.description&&<small>{command.description}</small>}</span>{command.shortcut&&<kbd>{command.shortcut}</kbd>}</button>):<p className="command-empty">No matching command.</p>}</div>
  </div>
 </CommandPaletteShell>
}
