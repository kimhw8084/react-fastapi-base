export function storageKey(app: string, user: string, tenant: string, feature: string, version = 1): string {
  return [app,user,tenant,feature,`v${version}`].map(encodeURIComponent).join(':')
}
export function readStorage<T>(key: string, fallback: T, parse: (value: unknown) => value is T): T
export function readStorage<T>(key: string, fallback: T, parse: (value: unknown) => T): T
export function readStorage<T>(key: string, fallback: T, parse: (value: unknown) => T | boolean): T {
  try {
    const value = localStorage.getItem(key)
    if (value === null) return fallback
    const parsed: unknown = JSON.parse(value)
    const validated = parse(parsed)
    return typeof validated === 'boolean' ? (validated ? parsed as T : fallback) : validated
  } catch { return fallback }
}
export function writeStorage(key: string, value: unknown): boolean {
  try { localStorage.setItem(key, JSON.stringify(value)); return true } catch { return false }
}
