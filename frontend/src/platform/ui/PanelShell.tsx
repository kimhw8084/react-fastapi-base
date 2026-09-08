import type { ReactNode } from 'react'
import { SurfaceShell } from './SurfaceShell'
import { OverlayShell } from './OverlayShell'
export interface PanelShellProps {title:ReactNode;subtitle?:ReactNode;status?:ReactNode;controls?:ReactNode;footer?:ReactNode;children:ReactNode;className?:string}
export function PanelShell({title,subtitle,status,controls,footer,children,className=''}:PanelShellProps){
 return <section className={`panel-shell ${className}`.trim()}><SurfaceShell title={title} subtitle={subtitle} status={status} controls={controls} footer={footer}>{children}</SurfaceShell></section>
}
export function InspectorShell(props:PanelShellProps){return <PanelShell {...props} className={`inspector-shell ${props.className??''}`.trim()}/>}
export function DrawerShell({open,onClose,...props}:PanelShellProps&{open:boolean;onClose:()=>void}){return <OverlayShell open={open} kind="drawer" title={props.title} subtitle={props.subtitle} status={props.status} footer={props.footer} onClose={onClose} wide>{props.children}</OverlayShell>}
