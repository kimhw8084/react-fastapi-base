export function activeNavigationScrollAdjustment(scrollport: { top: number; bottom: number }, item: { top: number; bottom: number }): number {
  if (item.top < scrollport.top) return item.top - scrollport.top
  if (item.bottom > scrollport.bottom) return item.bottom - scrollport.bottom
  return 0
}
