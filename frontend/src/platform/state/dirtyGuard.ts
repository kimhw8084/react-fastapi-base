import { useEffect, useRef } from 'react'

const dirtySources = new Set<string>()
const dirtyHistoryKey = '__golden_dirty_guard'
let listeners = 0
let lastLocation = window.location.href
let lastHistoryState: unknown = window.history.state
let lastHistoryIndex: number | null = null
let suppressPopstate = false
let dirtyEntry: { href: string; state: unknown } | null = null

function beforeUnload(event: BeforeUnloadEvent) {
  if (!dirtySources.size) return
  event.preventDefault()
  event.returnValue = ''
}

function routeClick(event: MouseEvent) {
  if (!dirtySources.size || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  const target = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null
  if (!target || target.target === '_blank' || target.hasAttribute('download')) return
  const destination = new URL(target.href, window.location.href)
  if (destination.origin !== window.location.origin || destination.href === window.location.href) return
  if (!window.confirm('You have unsaved changes. Leave this page and discard them?')) {
    event.preventDefault()
    event.stopPropagation()
  }
}

function historyIndex(state: unknown): number | null {
  if (!state || typeof state !== 'object') return null
  const value = (state as Record<string, unknown>).idx
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function dirtyHistoryState(state: unknown) {
  return { ...(state && typeof state === 'object' ? state : {}), [dirtyHistoryKey]: true }
}

function isDirtyHistoryState(state: unknown) {
  return Boolean(state && typeof state === 'object' && (state as Record<string, unknown>)[dirtyHistoryKey] === true)
}

function armDirtyEntry() {
  dirtyEntry = { href: window.location.href, state: window.history.state }
  window.history.pushState(dirtyHistoryState(dirtyEntry.state), '', dirtyEntry.href)
}

function routePopstate(event: PopStateEvent) {
  const destination = window.location.href
  if (suppressPopstate) {
    suppressPopstate = false
    lastLocation = destination
    lastHistoryState = event.state
    lastHistoryIndex = historyIndex(event.state)
    return
  }
  if (dirtyEntry && destination === dirtyEntry.href) {
    if (window.confirm('You have unsaved changes. Leave this page and discard them?')) {
      // The first pop only leaves the guard entry. Let the next pop reach the
      // actual destination, while suppressing a second confirmation.
      dirtyEntry = null
      suppressPopstate = true
      window.history.go(-1)
      return
    }
    // Re-arm the guard entry. React Router may observe the intermediate pop,
    // but the URL and route remain the same and local form state is retained.
    armDirtyEntry()
    lastLocation = dirtyEntry.href
    lastHistoryState = dirtyEntry.state
    lastHistoryIndex = historyIndex(dirtyEntry.state)
    return
  }
  if (!dirtySources.size) {
    lastLocation = destination
    lastHistoryState = event.state
    lastHistoryIndex = historyIndex(event.state)
    return
  }
  if (window.confirm('You have unsaved changes. Leave this page and discard them?')) {
    lastLocation = destination
    lastHistoryState = event.state
    lastHistoryIndex = historyIndex(event.state)
    return
  }
  const destinationIndex = historyIndex(event.state)
  if (destinationIndex !== null && lastHistoryIndex !== null && destinationIndex !== lastHistoryIndex) {
    // React Router owns the history index. Reverse the attempted delta so its
    // location state and rendered route return together with the URL.
    suppressPopstate = true
    window.history.go(lastHistoryIndex - destinationIndex)
    return
  }
  // Fallback for plain browser entries without an index. Push the previous
  // entry back and notify history consumers explicitly; React Router listens
  // to popstate rather than observing pushState on its own.
  suppressPopstate = true
  window.history.pushState(lastHistoryState, '', lastLocation)
  window.dispatchEvent(new PopStateEvent('popstate', { state: lastHistoryState }))
}

function addListeners() {
  if (listeners++ > 0) return
  lastLocation = window.location.href
  lastHistoryState = window.history.state
  lastHistoryIndex = historyIndex(lastHistoryState)
  armDirtyEntry()
  window.addEventListener('beforeunload', beforeUnload)
  window.addEventListener('popstate', routePopstate)
  document.addEventListener('click', routeClick, true)
}

function removeListeners() {
  if (--listeners > 0) return
  if (dirtyEntry && window.location.href === dirtyEntry.href && isDirtyHistoryState(window.history.state)) {
    window.history.replaceState(dirtyEntry.state, '', dirtyEntry.href)
  }
  dirtyEntry = null
  window.removeEventListener('beforeunload', beforeUnload)
  window.removeEventListener('popstate', routePopstate)
  document.removeEventListener('click', routeClick, true)
}

/** Platform-owned protection for route and browser navigation with dirty forms. */
export function useDirtyGuard(dirty: boolean) {
  const id = useRef(crypto.randomUUID())
  useEffect(() => {
    if (!dirty) return
    dirtySources.add(id.current)
    addListeners()
    return () => {
      dirtySources.delete(id.current)
      removeListeners()
    }
  }, [dirty])
}
