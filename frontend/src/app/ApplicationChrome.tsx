import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import type { TenantInfo, WorkspaceDefinition } from '../generated/schema'
import type { ApplicationConfig } from '../generated/schema'
import type { ThemeName } from '../platform/api/runtime'
import type { ColorModePreference } from '../platform/ui/theme'
import { Dialog } from '../platform/ui/Dialog'
import { Icon, type IconKey } from '../platform/ui/Icon'

export function WorkspaceNavigation({application,definitions}:{application:ApplicationConfig;definitions:WorkspaceDefinition[]}){
 const definitionsByKey=new Map(definitions.map(definition=>[definition.key,definition]))
 const groups=new Map<string,Array<{workspace:string;label:string;icon:IconKey}>>()
 for(const item of application.navigation){
  const definition=definitionsByKey.get(item.workspace)
  if(!definition)continue
  const group=item.group||'Workspaces'
  const entries=groups.get(group)??[]
  entries.push({workspace:item.workspace,label:item.label||definition.label,icon:(item.icon||'work-items') as IconKey})
  groups.set(group,entries)
 }
 return <nav aria-label="Main navigation">{[...groups].map(([group,items])=><section className="sidebar-nav-section" key={group}><h2>{group}</h2><div className="sidebar-nav-group">{items.map(item=><NavLink key={item.workspace} to={`/${item.workspace.replaceAll('_','-')}`}><Icon name={item.icon}/><span className="nav-item-label">{item.label}</span></NavLink>)}</div></section>)}</nav>
}

function DisplayControls({idPrefix,theme,onTheme,mode,onMode,contrast,onContrast}:{idPrefix:string;theme:ThemeName;onTheme:(value:ThemeName)=>void;mode:ColorModePreference;onMode:(value:ColorModePreference)=>void;contrast:'normal'|'high';onContrast:(value:'normal'|'high')=>void}){
 return <div className="display-preferences-controls">
  <label htmlFor={`${idPrefix}-appearance`}>Appearance<select id={`${idPrefix}-appearance`} value={mode} onChange={event=>onMode(event.target.value as ColorModePreference)}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
  <label htmlFor={`${idPrefix}-contrast`}>Contrast<select id={`${idPrefix}-contrast`} value={contrast} onChange={event=>onContrast(event.target.value as 'normal'|'high')}><option value="normal">Normal contrast</option><option value="high">High contrast</option></select></label>
  <label htmlFor={`${idPrefix}-theme`}>Theme<select id={`${idPrefix}-theme`} value={theme} onChange={event=>onTheme(event.target.value as ThemeName)}><option value="operations">Operations</option><option value="clarity">Clarity</option><option value="minimal">Minimal</option></select></label>
 </div>
}

export function ApplicationHeader({tenant,tenants,userId,onSwitchTenant,onOpenCommand,theme,onTheme,mode,onMode,contrast,onContrast}:{tenant:TenantInfo;tenants:TenantInfo[];userId:string;onSwitchTenant:(id:string)=>void;onOpenCommand:()=>void;theme:ThemeName;onTheme:(value:ThemeName)=>void;mode:ColorModePreference;onMode:(value:ColorModePreference)=>void;contrast:'normal'|'high';onContrast:(value:'normal'|'high')=>void}){
 const [preferencesOpen,setPreferencesOpen]=useState(false)
 return <>
  <div className="breadcrumb">Workspace / <strong>{tenant.name}</strong></div>
  <div className="shell-controls">
   <button type="button" className="command-trigger" onClick={onOpenCommand} aria-label="Open command palette"><Icon name="command"/><kbd>K</kbd></button>
   <label className="sr-only" htmlFor="tenant-select">Tenant</label><select id="tenant-select" value={tenant.id} onChange={event=>onSwitchTenant(event.target.value)}>{tenants.map(value=><option value={value.id} key={value.id}>{value.name}</option>)}</select>
   <div className="desktop-display-controls"><DisplayControls idPrefix="desktop" theme={theme} onTheme={onTheme} mode={mode} onMode={onMode} contrast={contrast} onContrast={onContrast}/></div>
   <button type="button" className="mobile-display-trigger" onClick={()=>setPreferencesOpen(true)}><Icon name="system"/> Display</button>
   <div className="user-chip"><span aria-hidden="true">{userId.slice(0,1).toUpperCase()}</span><span>{userId}</span></div>
  </div>
  {preferencesOpen&&<Dialog title="Display preferences" onClose={()=>setPreferencesOpen(false)}><DisplayControls idPrefix="mobile" theme={theme} onTheme={onTheme} mode={mode} onMode={onMode} contrast={contrast} onContrast={onContrast}/></Dialog>}
 </>
}
