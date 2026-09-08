export type LayoutRegion = 'navigator'|'primary'|'secondary'|'inspector'|'bottom'|'canvas'
export type LayoutPresentation = 'wide'|'desktop'|'tablet'|'mobile'
export interface LayoutState { hidden:LayoutRegion[]; inspector:'docked'|'drawer'|'sheet'|'hidden'; navigator:'docked'|'drawer'|'hidden'; bottom:'docked'|'hidden'; focusMode:boolean }
export interface LayoutContext { width:number; hasSelection?:boolean; focusMode?:boolean; preferInspector?:boolean }
export function layoutPresentation(width:number):LayoutPresentation{
  if(width<640)return 'mobile'
  if(width<960)return 'tablet'
  if(width<1600)return 'desktop'
  return 'wide'
}
export function resolveLayout(context:LayoutContext):LayoutState{
  const presentation=layoutPresentation(context.width)
  if(context.focusMode)return {hidden:['navigator','secondary','inspector','bottom'],inspector:'hidden',navigator:'hidden',bottom:'hidden',focusMode:true}
  if(presentation==='mobile')return {hidden:['navigator','secondary','bottom'],inspector:context.hasSelection?'sheet':'hidden',navigator:'drawer',bottom:'hidden',focusMode:false}
  if(presentation==='tablet')return {hidden:['secondary'],inspector:context.hasSelection?'drawer':'hidden',navigator:'drawer',bottom:'docked',focusMode:false}
  return {hidden:[],inspector:context.hasSelection||context.preferInspector?'docked':'hidden',navigator:'docked',bottom:'docked',focusMode:false}
}
