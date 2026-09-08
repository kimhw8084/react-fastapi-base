import { useMemo, useRef, useState, useEffect } from 'react'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'
import { ApiError } from '../api/client'
import type { BaseRecord, Draft, WorkspaceAdapter } from './types'
import { FormEngine } from './FormEngine'

export function RecordForm<T extends BaseRecord>({ adapter, row, onClose, onSaved }: { adapter: WorkspaceAdapter<T>; row?: T; onClose: () => void; onSaved: (row: T) => void }) {
  const initial = useMemo(() => adapter.draft(row), [adapter, row])
  const [draft, setDraft] = useState<Draft>(initial)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const operationKey = useRef(crypto.randomUUID())
  const dirty = JSON.stringify(draft) !== JSON.stringify(initial)
  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => { if (dirty) { event.preventDefault(); event.returnValue = '' } }
    window.addEventListener('beforeunload', handler); return () => window.removeEventListener('beforeunload', handler)
  }, [dirty])
  const fieldErrors: Record<string, string> = {}
  if (error instanceof ApiError && Array.isArray(error.details)) {
    for (const detail of error.details) if (detail && typeof detail === 'object' && 'field' in detail && 'message' in detail) fieldErrors[String(detail.field)] = String(detail.message)
  }
  const save = async () => {
    setBusy(true); setError(null)
    try { const result = row ? await adapter.update(row, draft) : await adapter.create(draft, operationKey.current); onSaved(result) } catch (e) { setError(e) } finally { setBusy(false) }
  }
  return <Dialog title={row ? `Edit ${adapter.singular}` : `New ${adapter.singular}`} onClose={onClose} dirty={dirty} busy={busy} footer={<><span className="muted">{row ? `Editing revision ${row.revision}` : 'Saved changes are recorded in audit history.'}</span><button type="button" disabled={busy} onClick={event => event.currentTarget.closest('.overlay-surface')?.dispatchEvent(new Event('golden-request-close'))}>Cancel</button>{!adapter.renderForm&&<button type="submit" form="record-form" className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save changes'}</button>}</>}> 
    {error !== null && <ErrorNotice error={error} />}
    {adapter.renderForm ? <form id="record-form" onSubmit={e => { e.preventDefault(); void save() }}>{adapter.renderForm(draft,setDraft)}<button type="submit" className="primary" disabled={busy}>{busy?'Saving…':'Save changes'}</button></form> : <FormEngine formId="record-form" fields={adapter.definition.fields} draft={draft} initial={initial} onChange={setDraft} onSubmit={save} presentation="sectioned" busy={busy} serverErrors={fieldErrors} />}
  </Dialog>
}
