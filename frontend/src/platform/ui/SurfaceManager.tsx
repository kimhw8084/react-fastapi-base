import { createContext, useCallback, useContext, useEffect, useId, useMemo, useState, type ReactNode } from 'react'
import type { SurfaceKind } from './surface'
import { closeSurface, isTopSurface, openSurface, surfaceLayer, type SurfaceRegistration } from './surfaceStack'

interface SurfaceManagerValue {
 stack:readonly SurfaceRegistration[]
 register:(entry:SurfaceRegistration)=>void
 unregister:(id:string)=>void
}
const SurfaceManagerContext=createContext<SurfaceManagerValue|null>(null)

export function SurfaceManagerProvider({children}:{children:ReactNode}){
 const [stack,setStack]=useState<SurfaceRegistration[]>([])
 const register=useCallback((entry:SurfaceRegistration)=>setStack(current=>openSurface(current,entry)),[])
 const unregister=useCallback((id:string)=>setStack(current=>closeSurface(current,id)),[])
 const value=useMemo(()=>({stack,register,unregister}),[stack,register,unregister])
 return <SurfaceManagerContext.Provider value={value}>{children}</SurfaceManagerContext.Provider>
}

export function useSurfaceRegistration(kind:SurfaceKind,active=true){
 const manager=useContext(SurfaceManagerContext)
 const reactId=useId()
 const id=`surface-${reactId.replaceAll(':','')}`
 useEffect(()=>{
  if(!active||!manager)return
  manager.register({id,kind})
  return ()=>manager.unregister(id)
 },[active,manager?.register,manager?.unregister,id,kind])
 return {id,layer:manager?surfaceLayer(manager.stack,id):70,isTop:manager?isTopSurface(manager.stack,id):true}
}
