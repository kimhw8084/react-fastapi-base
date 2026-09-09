import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useDirtyGuard } from './dirtyGuard'

function Fixture({ dirty }: { dirty: boolean }) {
  useDirtyGuard(dirty)
  return <a href="/another-workspace">Leave workspace</a>
}

describe('platform dirty navigation guard', () => {
  it('protects internal route links when a form is dirty', () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<Fixture dirty />)
    fireEvent.click(screen.getByRole('link', { name: 'Leave workspace' }))
    expect(confirm).toHaveBeenCalledWith('You have unsaved changes. Leave this page and discard them?')
    confirm.mockRestore()
  })

  it('sets the browser unload protection only while dirty', () => {
    const event = new Event('beforeunload', { cancelable: true })
    const { rerender } = render(<Fixture dirty />)
    window.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(true)
    rerender(<Fixture dirty={false} />)
    const cleanEvent = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(cleanEvent)
    expect(cleanEvent.defaultPrevented).toBe(false)
  })

  it('restores the current URL when browser Back is cancelled', () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    window.history.pushState({}, '', '/current')
    const { unmount } = render(<Fixture dirty />)
    window.history.pushState({}, '', '/previous')
    window.dispatchEvent(new PopStateEvent('popstate'))
    expect(confirm).toHaveBeenCalledWith('You have unsaved changes. Leave this page and discard them?')
    expect(window.location.pathname).toBe('/current')
    unmount()
    window.history.pushState({}, '', '/')
    confirm.mockRestore()
  })
})
