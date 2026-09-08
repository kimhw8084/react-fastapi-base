export function storageKey(app: string, user: string, tenant: string, feature: string, version = 1): string {
  return [app,user,tenant,feature,`v${version}`].map(encodeURIComponent).join(':')
}
export function readStorage<T>(key: string, fallback: T, parse: (value: unknown) => T): T {
  try { const value = localStorage.getItem(key); return value === null ? fallback : parse(JSON.parse(value)) } catch { return fallback }
}
export function writeStorage(key: string, value: unknown): boolean {
  try { localStorage.setItem(key, JSON.stringify(value)); return true } catch { return false }
}
