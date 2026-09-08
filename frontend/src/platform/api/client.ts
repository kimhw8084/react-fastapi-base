import type { RuntimeConfig } from './runtime'
import { operationRoutes, type OperationInputs, type OperationOutputs } from '../../generated/schema'

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly code: string, message: string, public readonly requestId: string, public readonly details: unknown = null) { super(message) }
}
export const errorMessage = (error: unknown): string => error instanceof Error ? error.message : 'Unexpected error.'

export class ApiClient {
  private tenantId = ''
  private csrfToken = ''
  constructor(private readonly runtime: RuntimeConfig) {}
  setScope(tenantId: string, csrfToken: string): void { this.tenantId = tenantId; this.csrfToken = csrfToken }

  private async response(path: string, init: RequestInit = {}): Promise<Response> {
    if (!path.startsWith('/api/v1/') || path.includes('://')) throw new Error('API paths must be scoped to /api/v1/.')
    const headers = new Headers(init.headers)
    if (this.tenantId) headers.set('X-Tenant-Id', this.tenantId)
    if (init.method && !['GET','HEAD'].includes(init.method)) {
      headers.set('X-CSRF-Token', this.csrfToken)
      if (init.body) headers.set('Content-Type', 'application/json')
    }
    let response: Response
    try {
      response = await fetch(`${this.runtime.apiBase}${path}`, { ...init, headers, credentials: 'include', cache: 'no-store', redirect: 'error', signal: init.signal ?? AbortSignal.timeout(20000) })
    } catch {
      throw new ApiError(0, 'transport_error', 'The API could not be reached. Check the company route, network and sign-in session.', '')
    }
    if (!response.ok) {
      const payload: unknown = await response.json().catch(() => null)
      const record = payload && typeof payload === 'object' ? payload as Record<string, unknown> : {}
      const error = record.error && typeof record.error === 'object' ? record.error as Record<string, unknown> : {}
      throw new ApiError(response.status, String(error.code ?? 'api_error'), String(error.message ?? 'The API request failed.'), String(error.request_id ?? response.headers.get('X-Request-ID') ?? ''), error.details)
    }
    return response
  }
  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await this.response(path, init)
    if (response.status === 204) return undefined as T
    if (!(response.headers.get('Content-Type') ?? '').includes('application/json')) throw new ApiError(response.status, 'unexpected_content', 'The API returned a page instead of JSON. Check company routing and sign-in.', response.headers.get('X-Request-ID') ?? '')
    return response.json() as Promise<T>
  }
  async download(path: string, filename: string): Promise<void> {
    const response = await this.response(path)
    const url = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  call<K extends keyof OperationInputs>(operation: K, input: OperationInputs[K], options: { signal?: AbortSignal; key?: string } = {}): Promise<OperationOutputs[K]> {
    const route = operationRoutes[operation]
    const data = input as { path?: Record<string,string>; query?: Record<string,unknown>; body?: unknown }
    const path = route.path.replace(/\{([^}]+)\}/g, (_, key: string) => {
      const value = data.path?.[key]
      if (value === undefined) throw new Error(`Missing route parameter: ${key}`)
      return encodeURIComponent(value)
    })
    const query = new URLSearchParams()
    for (const [key,value] of Object.entries(data.query ?? {})) if (value !== undefined && value !== null) query.set(key,String(value))
    return this.request<OperationOutputs[K]>(path+(query.size?`?${query.toString()}`:''), {
      method: route.method, signal: options.signal,
      ...(data.body === undefined ? {} : {body:JSON.stringify(data.body)}),
      headers: options.key ? {'Idempotency-Key':options.key} : {},
    })
  }
  json<T>(path: string, method: 'POST' | 'PUT' | 'DELETE', body?: unknown, key?: string): Promise<T> {
    return this.request<T>(path, { method, ...(body === undefined ? {} : { body: JSON.stringify(body) }), headers: key ? { 'Idempotency-Key': key } : {} })
  }
}
