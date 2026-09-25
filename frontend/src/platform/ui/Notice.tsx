import { ApiError, errorMessage } from '../api/client'
import type { ReactNode } from 'react'
export function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  return <div className="notice error" role="alert"><strong>{errorMessage(error)}</strong>{error instanceof ApiError && error.requestId && <span>Request: <code>{error.requestId}</code></span>}{retry && <button onClick={retry}>Retry</button>}</div>
}
export function EmptyState({ title, description, actions }: { title: string; description: string; actions?:ReactNode }) {
  return <section className="empty-state"><div className="empty-mark" aria-hidden="true">◇</div><h2>{title}</h2><p>{description}</p>{actions&&<div className="empty-actions">{actions}</div>}</section>
}
