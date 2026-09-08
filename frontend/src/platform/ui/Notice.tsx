import { ApiError, errorMessage } from '../api/client'
export function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  return <div className="notice error" role="alert"><strong>{errorMessage(error)}</strong>{error instanceof ApiError && error.requestId && <span>Request: <code>{error.requestId}</code></span>}{retry && <button onClick={retry}>Retry</button>}</div>
}
export function EmptyState({ title, description }: { title: string; description: string }) {
  return <section className="empty-state"><div className="empty-mark" aria-hidden="true">◇</div><h2>{title}</h2><p>{description}</p></section>
}
