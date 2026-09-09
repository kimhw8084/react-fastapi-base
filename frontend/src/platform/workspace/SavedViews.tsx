import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { TeamRead, ViewDefinition, ViewRead } from '../../generated/schema'
import { ApiError, type ApiClient } from '../api/client'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'

interface Props { api: ApiClient; workspace: string; tenant: string; user: string; definition: ViewDefinition; canShare: boolean; onApply: (view: ViewRead) => void }

export function SavedViews({ api, workspace, tenant, user, definition, canShare, onApply }: Props) {
  const client = useQueryClient(); const [params] = useSearchParams(); const requested = params.get('view'); const applied = useRef<string | null>(null)
  const key = ['views', user, tenant, workspace]; const base = `/api/v1/workspaces/${encodeURIComponent(workspace)}/views`
  const views = useQuery({ queryKey: key, queryFn: ({ signal }) => api.request<ViewRead[]>(base, { signal }) })
  const teams = useQuery({ queryKey: ['teams', tenant], queryFn: ({ signal }) => api.request<TeamRead[]>('/api/v1/teams', { signal }), enabled: canShare })
  const linked = useQuery({ queryKey: ['view-link', user, tenant, workspace, requested], queryFn: ({ signal }) => api.request<ViewRead>(`${base}/${encodeURIComponent(requested ?? '')}`, { signal }), enabled: Boolean(requested) })
  const [name, setName] = useState(''); const [scope, setScope] = useState<'personal' | 'team'>('personal'); const [teamId, setTeamId] = useState(''); const [isFavorite, setIsFavorite] = useState(false); const [isDefault, setIsDefault] = useState(false); const [open, setOpen] = useState(false); const [selected, setSelected] = useState<ViewRead | null>(null)
  useEffect(() => { if (!requested || applied.current === requested || !linked.data) return; applied.current = requested; setSelected(linked.data); setTeamId(linked.data.team_id ?? ''); onApply(linked.data) }, [requested, linked.data, onApply])
  const save = useMutation({ mutationFn: () => selected ? api.json<ViewRead>(`${base}/${selected.id}`, 'PUT', { name, scope, team_id: scope === 'team' ? (teamId || null) : null, is_favorite:isFavorite, is_default:isDefault, definition, revision: selected.revision }) : api.json<ViewRead>(base, 'POST', { name, scope, team_id: scope === 'team' ? (teamId || null) : null, is_favorite:isFavorite, is_default:isDefault, definition }), onSuccess: () => { setOpen(false); setName(''); setTeamId(''); setIsFavorite(false); setIsDefault(false); setSelected(null); void client.invalidateQueries({ queryKey: key }); void client.invalidateQueries({ queryKey: ['teams', tenant] }) } })
  const conflictView = saveErrorView(save.error)
  const remove = useMutation({ mutationFn: (view: ViewRead) => api.json<void>(`${base}/${view.id}?revision=${view.revision}`, 'DELETE'), onSuccess: () => { void client.invalidateQueries({ queryKey: key }) } })
  const teamName = (id: string | null) => teams.data?.find(team => team.id === id)?.name ?? 'Workspace team'
  return <div className="saved-views">
    <label className="sr-only" htmlFor="saved-views">Saved views</label>
    <select id="saved-views" defaultValue="" onChange={event => { const view = views.data?.find(row => row.id === event.target.value); if (view) { setSelected(view); setTeamId(view.team_id ?? ''); setIsFavorite(view.is_favorite); setIsDefault(view.is_default); onApply(view) } }}><option value="">Saved views</option>{views.data?.map(view => <option key={view.id} value={view.id}>{view.is_default?'◆ ':view.is_favorite?'★ ':''}{view.name}{view.scope === 'team' ? ` · ${teamName(view.team_id)}` : ''}</option>)}</select>
    <button onClick={() => { setSelected(null); setName(''); setScope('personal'); setTeamId(''); setIsFavorite(false); setIsDefault(false); save.reset(); setOpen(true) }}>Save view</button>
    {selected?.owner === user && <><button onClick={() => { setName(selected.name); setScope(selected.scope); setTeamId(selected.team_id ?? ''); setIsFavorite(selected.is_favorite); setIsDefault(selected.is_default); save.reset(); setOpen(true) }}>Update view</button><button onClick={() => { if (window.confirm(`Delete saved view “${selected.name}”? Records are not affected.`)) remove.mutate(selected) }}>Delete view</button></>}
    {linked.isError && <ErrorNotice error={linked.error}/>} {views.isError && <span className="muted" role="status">Saved views unavailable; current filters remain local.</span>} {remove.isError && <ErrorNotice error={remove.error}/>}
    {open && <Dialog title={selected ? 'Update saved view' : 'Save current view'} onClose={() => setOpen(false)} dirty={name.length > 0} busy={save.isPending} footer={<><button type="button" onClick={() => setOpen(false)} disabled={save.isPending}>Cancel</button><button form="save-view-form" type="submit" className="primary" disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save view'}</button></>}>
      <form id="save-view-form" className="form-stack" onSubmit={event => { event.preventDefault(); save.mutate() }}>{save.isError && <ErrorNotice error={save.error}/>} {conflictView && <p className="notice" role="alert">This view changed elsewhere. Reconcile with the server version before saving again. <button type="button" onClick={() => { setSelected(conflictView); setName(conflictView.name); setScope(conflictView.scope); setTeamId(conflictView.team_id ?? ''); save.reset() }}>Load server version</button></p>}
        <label>Name<input autoFocus required maxLength={120} value={name} onChange={event => setName(event.target.value)} /></label>
        <label>Visibility<select value={scope} onChange={event => { const next = event.target.value as 'personal' | 'team'; setScope(next); if (next === 'personal') setTeamId('') }}><option value="personal">Only me</option>{canShare && <option value="team">A team</option>}</select></label>
        {scope === 'team' && <label>Team<select value={teamId} onChange={event => setTeamId(event.target.value)}><option value="">Default workspace team</option>{teams.data?.filter(team => !team.is_default).map(team => <option value={team.id} key={team.id}>{team.name}</option>)}</select></label>}
        <label><input type="checkbox" checked={isFavorite} onChange={event => setIsFavorite(event.target.checked)} /> Favorite</label>
        <label><input type="checkbox" checked={isDefault} onChange={event => setIsDefault(event.target.checked)} /> Default for this {scope === 'team' ? 'team' : 'workspace'}</label>
        <p className="muted">Saves search, filters, layout and density—not record data. Team membership is enforced by the server.</p>
      </form>
    </Dialog>}
  </div>
}

function saveErrorView(error: unknown): ViewRead | null {
  if (!(error instanceof ApiError) || error.status !== 409 || !error.details || typeof error.details !== 'object') return null
  const current = (error.details as Record<string, unknown>).current
  return current && typeof current === 'object' && 'id' in current && 'revision' in current ? current as ViewRead : null
}
