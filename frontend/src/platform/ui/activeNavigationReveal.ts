export function activeNavigationScrollAdjustment(scrollport: { top: number; bottom: number }, item: { top: number; bottom: number }): number {
  if (item.top < scrollport.top) return item.top - scrollport.top - 1
  if (item.bottom > scrollport.bottom) return item.bottom - scrollport.bottom + 1
  return 0
}
