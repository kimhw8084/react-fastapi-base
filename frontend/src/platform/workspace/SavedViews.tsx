import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ViewDefinition, ViewRead } from '../../generated/schema'
import type { ApiClient } from '../api/client'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'

interface Props { api: ApiClient; workspace: string; tenant: string; user: string; definition: ViewDefinition; canShare: boolean; onApply: (view: ViewRead) => void }
export function SavedViews({ api, workspace, tenant, user, definition, canShare, onApply }: Props) {
  const client = useQueryClient()
  const [params]=useSearchParams()
  const requested=params.get('view')
  const applied=useRef<string|null>(null)
  const key = ['views', user, tenant, workspace]
  const base = `/api/v1/workspaces/${encodeURIComponent(workspace)}/views`
  const views = useQuery({ queryKey: key, queryFn: ({ signal }) => api.request<ViewRead[]>(base, { signal }) })
  const linked=useQuery({queryKey:['view-link',user,tenant,workspace,requested],queryFn:({signal})=>api.request<ViewRead>(`${base}/${encodeURIComponent(requested??'')}`,{signal}),enabled:Boolean(requested)})
  useEffect(()=>{if(!requested||applied.current===requested||!linked.data)return;applied.current=requested;setSelected(linked.data);onApply(linked.data)},[requested,linked.data,onApply])
  const [name, setName] = useState('')
  const [scope, setScope] = useState<'personal'|'team'>('personal')
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState<ViewRead | null>(null)
  const save = useMutation({ mutationFn: () => selected ? api.json<ViewRead>(`${base}/${selected.id}`, 'PUT', { name, scope, definition, revision: selected.revision }) : api.json<ViewRead>(base, 'POST', { name, scope, definition }), onSuccess: () => { setOpen(false); setName(''); setSelected(null); void client.invalidateQueries({ queryKey: key }) } })
  const remove = useMutation({ mutationFn: (view: ViewRead) => api.json<void>(`${base}/${view.id}?revision=${view.revision}`, 'DELETE'), onSuccess: () => { void client.invalidateQueries({ queryKey: key }) } })
  return <div className="saved-views">
    <label className="sr-only" htmlFor="saved-views">Saved views</label>
    <select id="saved-views" defaultValue="" onChange={event => { const view = views.data?.find(row => row.id === event.target.value); if (view) { setSelected(view); onApply(view) } }}>
      <option value="">Saved views</option>{views.data?.map(view => <option key={view.id} value={view.id}>{view.name}{view.scope === 'team' ? ' · Shared' : ''}</option>)}
    </select>
    <button onClick={() => { setSelected(null); setName(''); setScope('personal'); save.reset(); setOpen(true) }}>Save view</button>
    {selected?.owner === user && <><button onClick={() => { setName(selected.name); setScope(selected.scope); save.reset(); setOpen(true) }}>Update view</button><button onClick={() => { if (window.confirm(`Delete saved view “${selected.name}”? Records are not affected.`)) remove.mutate(selected) }}>Delete view</button></>}
    {linked.isError && <ErrorNotice error={linked.error}/>}
    {views.isError && <span className="muted" role="status">Saved views unavailable; current filters remain local.</span>}
    {remove.isError && <ErrorNotice error={remove.error} />}
    {open && <Dialog title={selected ? 'Update saved view' : 'Save current view'} onClose={() => setOpen(false)} dirty={name.length > 0} busy={save.isPending} footer={<button form="save-view-form" type="submit" className="primary" disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save view'}</button>}>
      <form id="save-view-form" className="form-stack" onSubmit={e => { e.preventDefault(); save.mutate() }}>
        {save.isError && <ErrorNotice error={save.error} />}
        <label>Name<input autoFocus required maxLength={120} value={name} onChange={e => setName(e.target.value)} /></label>
        <label>Visibility<select value={scope} onChange={e => setScope(e.target.value as 'personal'|'team')}><option value="personal">Only me</option>{canShare && <option value="team">Everyone in this tenant</option>}</select></label>
        <p className="muted">Saves search, filters, layout and density—not record data. Shared means this tenant, not a separate corporate group.</p>
      </form>
    </Dialog>}
  </div>
}
