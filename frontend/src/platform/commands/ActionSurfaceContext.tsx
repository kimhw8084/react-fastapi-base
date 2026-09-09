import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { actionToPaletteCommand, type ActionRegistry, type CommandContext } from './registry'
import type { PaletteCommand } from './CommandPalette'

interface ActiveSurface { registry: ActionRegistry; context: CommandContext }
interface ActionSurfaceValue { surface: ActiveSurface|null; setSurface: (value: ActiveSurface|null) => void }
const ActionSurface = createContext<ActionSurfaceValue>({ surface:null, setSurface:()=>undefined })

export function ActionSurfaceProvider({ children }: { children: ReactNode }) {
  const [surface,setSurface]=useState<ActiveSurface|null>(null)
  return <ActionSurface.Provider value={{surface,setSurface}}>{children}</ActionSurface.Provider>
}

export function useActiveActionSurface(registry: ActionRegistry|null, context: CommandContext|null) {
  const {setSurface}=useContext(ActionSurface)
  useEffect(()=>{
    if(!registry||!context)return
    setSurface({registry,context})
    return ()=>setSurface(null)
  },[context,registry,setSurface])
}

export function useActionPaletteCommands(): readonly PaletteCommand[] {
  const {surface}=useContext(ActionSurface)
  return useMemo(()=>surface?.registry.all(surface.context,'palette').map(action=>actionToPaletteCommand(action,surface.context))??[],[surface])
}
