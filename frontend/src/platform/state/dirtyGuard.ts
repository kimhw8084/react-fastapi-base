import { useEffect, useRef } from 'react'

const dirtySources = new Set<string>()
let listeners = 0

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

function addListeners() {
  if (listeners++ > 0) return
  window.addEventListener('beforeunload', beforeUnload)
  document.addEventListener('click', routeClick, true)
}

function removeListeners() {
  if (--listeners > 0) return
  window.removeEventListener('beforeunload', beforeUnload)
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
