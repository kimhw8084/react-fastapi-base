import { useMemo, useRef, useState, useEffect } from 'react'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'
import { ApiError } from '../api/client'
import type { BaseRecord, Draft, WorkspaceAdapter } from './types'
import { FieldInput } from './FieldInput'

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
  return <Dialog title={row ? `Edit ${adapter.singular}` : `New ${adapter.singular}`} onClose={onClose} dirty={dirty} busy={busy} footer={<><span className="muted">{row ? `Editing revision ${row.revision}` : 'Saved changes are recorded in audit history.'}</span><button type="button" disabled={busy} onClick={event => event.currentTarget.closest('.overlay-surface')?.dispatchEvent(new Event('golden-request-close'))}>Cancel</button><button type="submit" form="record-form" className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save changes'}</button></>}>
    <form id="record-form" onSubmit={e => { e.preventDefault(); void save() }}>
      {error !== null && <ErrorNotice error={error} />}
      {adapter.renderForm ? adapter.renderForm(draft, setDraft) : <div className="form-grid">{adapter.definition.fields.map((field,index) => <label className={['textarea','markdown','code','json','multiselect'].includes(field.kind) ? 'full-width' : ''} key={field.key}>
        <span>{field.label}{field.required && <span aria-label="required"> *</span>}{field.unit&&<small className="field-unit-hint"> · {field.unit}</small>}</span>
        {field.read_only ? <output className="readonly-field">{String(draft[field.key]??'—')}</output> : <FieldInput field={field} draft={draft} onChange={setDraft} invalid={Boolean(fieldErrors[field.key])} autoFocus={index===0}/>}
        {fieldErrors[field.key] && <small className="field-error">{fieldErrors[field.key]}</small>}
      </label>)}</div>}
    </form>
  </Dialog>
}
