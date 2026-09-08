export type SurfaceKind = 'popover'|'peek'|'modal'|'drawer'|'inspector'|'sheet'|'dossier'|'designer'|'fullscreen'|'command'
export interface SurfaceCapabilities { closable?: boolean; expandable?: boolean; fullscreen?: boolean; dockable?: boolean; pinnable?: boolean; resizable?: boolean }
export interface SurfaceState { kind: SurfaceKind; expanded: boolean; fullscreen: boolean; docked: boolean; pinned: boolean }
export interface Viewport { width: number; height: number }

export function normalizeSurfaceCapabilities(kind:SurfaceKind, requested:SurfaceCapabilities={}):Required<SurfaceCapabilities>{
  const defaults:Record<SurfaceKind,Required<SurfaceCapabilities>>={
    popover:{closable:true,expandable:false,fullscreen:false,dockable:false,pinnable:false,resizable:false},
    peek:{closable:true,expandable:true,fullscreen:false,dockable:false,pinnable:true,resizable:true},
    modal:{closable:true,expandable:true,fullscreen:true,dockable:false,pinnable:false,resizable:true},
    drawer:{closable:true,expandable:true,fullscreen:true,dockable:true,pinnable:true,resizable:true},
    inspector:{closable:true,expandable:true,fullscreen:false,dockable:true,pinnable:true,resizable:true},
    sheet:{closable:true,expandable:true,fullscreen:true,dockable:false,pinnable:false,resizable:true},
    dossier:{closable:true,expandable:true,fullscreen:true,dockable:true,pinnable:true,resizable:true},
    designer:{closable:true,expandable:true,fullscreen:true,dockable:true,pinnable:true,resizable:true},
    fullscreen:{closable:true,expandable:false,fullscreen:true,dockable:false,pinnable:false,resizable:false},
    command:{closable:true,expandable:false,fullscreen:false,dockable:false,pinnable:false,resizable:false},
  }
  return {...defaults[kind],...requested}
}

export function resolveSurfaceKind(kind:SurfaceKind,viewport:Viewport):SurfaceKind{
  if(viewport.width<640){
    if(kind==='drawer'||kind==='inspector'||kind==='dossier'||kind==='modal'||kind==='command')return 'sheet'
  }
  return kind
}
