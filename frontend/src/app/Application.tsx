import { useEffect, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import type { Bootstrap, TenantInfo, WorkspaceDefinition } from '../generated/schema'
import { ApiClient } from '../platform/api/client'
import type { RuntimeConfig, ThemeName } from '../platform/api/runtime'
import { ErrorNotice, EmptyState } from '../platform/ui/Notice'
import { storageKey, readStorage, writeStorage } from '../platform/state/storage'
import { workspaceRenderers } from './registry'
import { AppShell } from '../platform/ui/AppShell'
import { CommandPalette, type PaletteCommand } from '../platform/commands/CommandPalette'
import { isColorModePreference, resolveColorMode, type ColorModePreference } from '../platform/ui/theme'
import { ActionSurfaceProvider, useActionPaletteCommands } from '../platform/commands/ActionSurfaceContext'
import { ApplicationHeader, WorkspaceNavigation } from './ApplicationChrome'

export function Application({runtime}:{runtime:RuntimeConfig}){
 const api=useMemo(()=>new ApiClient(runtime),[runtime])
 const boot=useQuery({queryKey:['bootstrap'],queryFn:()=>api.bootstrap(),retry:1,refetchInterval:900000,refetchOnWindowFocus:true})
 if(boot.isPending)return <main className="startup"><h1>Opening your workspace</h1><p role="status">Checking identity, configuration and tenant access…</p></main>
 if(boot.isError)return <main className="startup"><h1>Workspace unavailable</h1><ErrorNotice error={boot.error} retry={()=>{void boot.refetch()}}/><p>Confirm that the FastAPI service is reachable from this browser and company sign-in is complete.</p></main>
 if(!boot.data.tenants.length)return <main className="startup"><EmptyState title="Access has not been assigned" description="The company identity was resolved, but an operator must explicitly grant tenant membership."/></main>
 return <TenantApplication key={boot.data.user_id} boot={boot.data} runtime={runtime}/>
}
function TenantApplication({boot,runtime}:{boot:Bootstrap;runtime:RuntimeConfig}){
 return <ActionSurfaceProvider><TenantApplicationContent boot={boot} runtime={runtime}/></ActionSurfaceProvider>
}
function TenantApplicationContent({boot,runtime}:{boot:Bootstrap;runtime:RuntimeConfig}){
 const client=useQueryClient()
 const navigate=useNavigate()
 const [commandOpen,setCommandOpen]=useState(false)
 const [tenant,setTenant]=useState<TenantInfo>(()=>boot.tenants[0]!)
 const api=useMemo(()=>{const scoped=new ApiClient(runtime);scoped.setScope(tenant.id,boot.csrf_token);return scoped},[runtime,tenant.id,boot.csrf_token])
 const preference=storageKey(boot.application.id,boot.user_id,'global','theme')
 const appearancePreference=storageKey(boot.application.id,boot.user_id,'global','appearance')
 const contrastPreference=storageKey(boot.application.id,boot.user_id,'global','contrast')
 const [theme,setTheme]=useState<ThemeName>(()=>readStorage(preference,runtime.defaultTheme,v=>v==='clarity'||v==='minimal'||v==='operations'?v:runtime.defaultTheme))
 const [modePreference,setModePreference]=useState<ColorModePreference>(()=>readStorage(appearancePreference,'system' as ColorModePreference,value=>isColorModePreference(value)?value:'system'))
 const [contrast,setContrast]=useState<'normal'|'high'>(()=>readStorage(contrastPreference,'normal' as const,value=>value==='high'?'high':'normal'))
 const [prefersDark,setPrefersDark]=useState(()=>window.matchMedia?.('(prefers-color-scheme: dark)').matches??true)
 useEffect(()=>{const query=window.matchMedia?.('(prefers-color-scheme: dark)');if(!query)return;const change=()=>setPrefersDark(query.matches);change();query.addEventListener('change',change);return()=>query.removeEventListener('change',change)},[])
 const mode=resolveColorMode(modePreference,prefersDark)
 useEffect(()=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.mode=mode;document.documentElement.dataset.contrast=contrast;writeStorage(preference,theme);writeStorage(appearancePreference,modePreference);writeStorage(contrastPreference,contrast)},[theme,mode,modePreference,contrast,preference,appearancePreference,contrastPreference])
 const title=runtime.titleOverride||boot.application.name
 useEffect(()=>{document.title=title},[title])
 const definitions=useQuery({queryKey:['workspaces',boot.user_id,tenant.id],queryFn:()=>api.request<WorkspaceDefinition[]>('/api/v1/workspaces')})
 const actionCommands=useActionPaletteCommands()
 const commands=useMemo<PaletteCommand[]>(()=>[...(definitions.data?.map(definition=>({id:`workspace.${definition.key}`,label:`Open ${boot.application.navigation.find(item=>item.workspace===definition.key)?.label??definition.label}`,description:definition.description,keywords:[definition.key,definition.label,'workspace','navigation'],action:()=>navigate(`/${definition.key.replaceAll('_','-')}`)}))??[]),...actionCommands],[actionCommands,definitions.data,boot.application.navigation,navigate])
 useEffect(()=>{const handler=(event:KeyboardEvent)=>{if((event.metaKey||event.ctrlKey)&&event.key.toLocaleLowerCase()==='k'){event.preventDefault();setCommandOpen(value=>!value)}};window.addEventListener('keydown',handler);return()=>window.removeEventListener('keydown',handler)},[])
 const switchTenant=(id:string)=>{const next=boot.tenants.find(t=>t.id===id);if(next){void client.cancelQueries();client.removeQueries({predicate:q=>q.queryKey[0]!=='bootstrap'});setTenant(next)}}
 const sidebar=<><div className="brand"><span className="brand-mark" aria-hidden="true">{title.slice(0,1).toUpperCase()}</span><div><strong>{title}</strong><span>{boot.application.description}</span></div></div>{definitions.data&&<WorkspaceNavigation application={boot.application} definitions={definitions.data}/>}<div className="sidebar-bottom"><span className="status-dot" aria-hidden="true"/><span>Revision-safe · Audit-backed</span><small>Review build {boot.build_version}</small></div></>
 const header=<ApplicationHeader tenant={tenant} tenants={boot.tenants} userId={boot.user_id} onSwitchTenant={switchTenant} onOpenCommand={()=>setCommandOpen(true)} theme={theme} onTheme={setTheme} mode={modePreference} onMode={setModePreference} contrast={contrast} onContrast={setContrast}/>
 const release=<><span className="release-desktop">Implementation review build. Company identity, mounted storage and real deployment certification remain required.</span><span className="release-mobile">Review build · company identity, storage and deployment qualification remain required.</span></>
 return <AppShell sidebar={sidebar} header={header} release={release}><CommandPalette open={commandOpen} onClose={()=>setCommandOpen(false)} commands={commands}/><div key={`${boot.user_id}:${tenant.id}`}>{definitions.isError?<ErrorNotice error={definitions.error}/>:definitions.isPending?<p role="status">Loading workspace definitions…</p>:<Routes><Route path="/" element={<Navigate replace to={definitions.data?.[0]?`/${definitions.data[0].key.replaceAll('_','-')}`:'/unconfigured'}/>}/>{definitions.data?.map(definition=>{const Renderer=workspaceRenderers[definition.key];return <Route key={definition.key} path={`/${definition.key.replaceAll('_','-')}`} element={Renderer?<Renderer api={api} definition={definition} appId={boot.application.id} tenant={tenant.id} user={boot.user_id} permissions={tenant.permissions} defaultDensity={boot.application.density}/>:<EmptyState title="Workspace renderer missing" description="Register the feature component in app/registry.tsx."/>}/>})}<Route path="*" element={<EmptyState title="Page not found" description="Choose a registered workspace from the navigation."/>}/></Routes>}</div></AppShell>
}
