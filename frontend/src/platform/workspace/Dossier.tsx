import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'
import type { ApiClient } from '../api/client'
import { Relationships } from './Relationships'
import type { BaseRecord, WorkspaceAdapter } from './types'
import { FieldValue } from './FieldValue'

export function Dossier<T extends BaseRecord>({ adapter, api, row, tenant, user, canWrite, canRestore, onClose, onEdit, onChanged }: { adapter: WorkspaceAdapter<T>; api: ApiClient; row: T; tenant: string; user: string; canWrite: boolean; canRestore: boolean; onClose: () => void; onEdit?: () => void; onChanged: () => void }) {
  const tabs=['details','relationships','history','files'] as const
  const [tab, setTab] = useState<(typeof tabs)[number]>('details')
  const history = useQuery({ queryKey: ['history',user,tenant,adapter.key,row.id,row.revision], queryFn: () => adapter.history(row.id), enabled: tab === 'history' })
  const revert = useMutation({ mutationFn: (revision: number) => adapter.revert(row,revision), onSuccess: onChanged })
  return <Dialog title={String(row[adapter.definition.primary_field as keyof T]??row.id)} subtitle={`${adapter.singular} · revision ${row.revision}`} status={row.archived?<span className="status-chip">Archived</span>:undefined} wide expandable onClose={onClose} footer={<><span className="muted">Revision {row.revision}{row.archived ? ' · Archived / read-only' : ''}</span><button onClick={() => { void navigator.clipboard.writeText(window.location.href) }}>Copy link</button>{onEdit && !row.archived && <button className="primary" onClick={onEdit}>Edit record</button>}</>}>
    <div className="segmented" aria-label="Record sections">{tabs.map(name => <button key={name} aria-pressed={tab === name} onClick={() => setTab(name)}>{name[0]?.toUpperCase()}{name.slice(1)}</button>)}</div>
    {revert.isError && <ErrorNotice error={revert.error} />}
    {tab === 'details' && (adapter.renderDetails?.(row) ?? <dl className="record-details">{adapter.definition.fields.map(field => <div key={field.key}><dt>{field.label}</dt><dd><FieldValue field={field} value={row[field.key as keyof T]}/></dd></div>)}</dl>)}
    {tab === 'relationships' && <Relationships api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user} canWrite={canWrite} readOnly={row.archived}/>}
    {tab === 'files' && (adapter.renderAttachments?.(row) ?? <p>This workspace does not enable attachments.</p>)}
    {tab === 'history' && <section aria-label="Version history">
      {history.isPending && <p role="status">Loading version history…</p>}
      {history.isError && <ErrorNotice error={history.error} />}
      {history.data?.map(event => <article className="history-entry" key={event.id}><header><strong>Revision {event.revision} · {event.action}</strong><span>{event.actor} · {new Date(event.created_at).toLocaleString()}</span></header>
        <dl className="changes">{Object.keys(event.after ?? {}).filter(key => JSON.stringify(event.before?.[key]) !== JSON.stringify(event.after?.[key]) && !['created_at','updated_at','revision','id'].includes(key)).map(key => <div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd><del>{String(event.before?.[key] ?? '—')}</del> → <span>{String(event.after?.[key] ?? '—')}</span></dd></div>)}</dl>
        {canRestore && !row.archived && event.revision !== row.revision && <button disabled={revert.isPending} onClick={() => { if (window.confirm('Revert record fields to this version? This creates a new audited revision.')) revert.mutate(event.revision) }}>Revert to this version</button>}
      </article>)}
    </section>}
  </Dialog>
}
