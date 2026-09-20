function pixels(value: string): number {
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? Math.max(0, parsed) : 0
}

function focusExtent(element: HTMLElement): number {
  const style = getComputedStyle(element)
  if (style.outlineStyle === 'none') return 0
  return pixels(style.outlineWidth) + pixels(style.outlineOffset)
}

/** Keep a keyboard-focused control and its visible focus indicator inside one horizontal owner. */
export function revealHorizontalFocus(owner: HTMLElement, target: HTMLElement): void {
  if (!owner.contains(target)) return
  window.requestAnimationFrame(() => {
    if (!owner.isConnected || !target.isConnected || !owner.contains(target)) return
    const ownerBox = owner.getBoundingClientRect()
    const targetBox = target.getBoundingClientRect()
    const extent = focusExtent(target)
    const ownerStyle = getComputedStyle(owner)
    const borderLeft = pixels(ownerStyle.borderLeftWidth)
    const borderRight = pixels(ownerStyle.borderRightWidth)
    const leftInset = Math.max(extent, pixels(ownerStyle.scrollPaddingLeft))
    const rightInset = Math.max(extent, pixels(ownerStyle.scrollPaddingRight))
    const left = Math.max(ownerBox.left + borderLeft + leftInset, extent)
    const right = Math.min(ownerBox.right - borderRight - rightInset, window.innerWidth - extent)
    const targetLeft = targetBox.left - extent
    const targetRight = targetBox.right + extent
    let nextScrollLeft = owner.scrollLeft
    if (targetLeft < left) nextScrollLeft -= left - targetLeft
    if (targetRight > right) nextScrollLeft += targetRight - right
    const maximum = Math.max(0, owner.scrollWidth - owner.clientWidth)
    owner.scrollLeft = Math.min(maximum, Math.max(0, nextScrollLeft))
  })
}
