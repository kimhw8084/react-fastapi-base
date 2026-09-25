const acronymLabels: Record<string, string> = {
  spc: 'SPC',
  slo: 'SLO',
}

/** Human-facing labels for visualization IDs. IDs remain canonical in state and routes. */
export function visualizationDisplayLabel(key: string): string {
  const normalized = key.trim().toLocaleLowerCase()
  const acronym = acronymLabels[normalized]
  if (acronym) return acronym

  return key
    .trim()
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part, index) => index === 0 ? `${part[0]?.toLocaleUpperCase() ?? ''}${part.slice(1).toLocaleLowerCase()}` : part.toLocaleLowerCase())
    .join(' ')
}
