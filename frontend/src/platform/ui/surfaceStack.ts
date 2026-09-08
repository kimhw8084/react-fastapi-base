import type { SurfaceKind } from './surface'
export interface SurfaceRegistration { id:string; kind:SurfaceKind }
export function openSurface(stack:readonly SurfaceRegistration[],entry:SurfaceRegistration):SurfaceRegistration[]{
 if(!entry.id)throw new Error('Surface id is required.')
 if(stack.some(value=>value.id===entry.id))return [...stack]
 return [...stack,entry]
}
export function closeSurface(stack:readonly SurfaceRegistration[],id:string):SurfaceRegistration[]{
 const index=stack.findIndex(value=>value.id===id)
 if(index<0)return [...stack]
 // Closing a parent also closes descendants so focus/context cannot be orphaned.
 return stack.slice(0,index)
}
export function topSurface(stack:readonly SurfaceRegistration[]):SurfaceRegistration|undefined{return stack[stack.length-1]}
export function isTopSurface(stack:readonly SurfaceRegistration[],id:string):boolean{return topSurface(stack)?.id===id}
export function surfaceLayer(stack:readonly SurfaceRegistration[],id:string,base=70,step=10):number{
 const index=stack.findIndex(value=>value.id===id)
 return index<0?base:base+index*step
}
