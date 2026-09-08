export type ThemeName = 'operations' | 'clarity' | 'minimal'
export interface RuntimeConfig { schemaVersion: 1; apiBase: string; defaultTheme: ThemeName; titleOverride: string }
const THEMES: readonly string[] = ['operations', 'clarity', 'minimal']

export function parseRuntime(value: unknown): RuntimeConfig {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Runtime configuration must be an object.')
  const v = value as Record<string, unknown>
  if (Object.keys(v).some(k => !['schemaVersion','apiBase','defaultTheme','titleOverride'].includes(k))) throw new Error('Unknown runtime configuration property.')
  if (v.schemaVersion !== 1 || typeof v.apiBase !== 'string' || typeof v.titleOverride !== 'string' || !THEMES.includes(String(v.defaultTheme))) throw new Error('Runtime configuration is invalid.')
  if (v.titleOverride.length > 80) throw new Error('Application title is too long.')
  if (v.apiBase) {
    const url = new URL(v.apiBase)
    if (!['https:','http:'].includes(url.protocol) || url.username || url.password || url.pathname !== '/' || url.search || url.hash || v.apiBase.endsWith('/')) throw new Error('API base must be an HTTP(S) origin without a trailing slash.')
    if (window.location.protocol === 'https:' && url.protocol !== 'https:') throw new Error('An HTTPS frontend requires an HTTPS API.')
  }
  return { schemaVersion: 1, apiBase: v.apiBase, defaultTheme: v.defaultTheme as ThemeName, titleOverride: v.titleOverride }
}

export async function loadRuntime(): Promise<RuntimeConfig> {
  const response = await fetch('/runtime-config.json', { cache: 'no-store', credentials: 'same-origin', signal: AbortSignal.timeout(10000) })
  if (!response.ok) throw new Error('Runtime configuration is unavailable.')
  return parseRuntime(await response.json())
}
